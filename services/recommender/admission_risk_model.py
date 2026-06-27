from __future__ import annotations

from collections import defaultdict
from math import sqrt

from services.recommender.hubei_rules import (
    probability_band_label,
    requirement_satisfied,
    tier_for_probability,
)
from services.recommender.models import (
    AdmissionPlan,
    AdmissionRecord,
    CandidateProfile,
    RecommendationItem,
    SameRankReference,
    median_int,
)


def clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def population_std(values: list[int]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sqrt(sum((item - mean) ** 2 for item in values) / len(values))


def base_probability_from_gap(rank_gap_ratio: float) -> float:
    if rank_gap_ratio <= -0.18:
        return 0.94
    if rank_gap_ratio <= -0.10:
        return 0.86
    if rank_gap_ratio <= -0.04:
        return 0.76
    if rank_gap_ratio <= 0.03:
        return 0.62
    if rank_gap_ratio <= 0.10:
        return 0.43
    if rank_gap_ratio <= 0.20:
        return 0.30
    return 0.18


class HubeiAdmissionRiskModel:
    def __init__(self, data_confidence_threshold: float = 0.85):
        self.data_confidence_threshold = data_confidence_threshold

    def recommend(
        self,
        candidate: CandidateProfile,
        admission_records: list[AdmissionRecord],
        admission_plans: list[AdmissionPlan],
        same_rank_references: list[SameRankReference] | None = None,
    ) -> list[RecommendationItem]:
        same_rank_references = same_rank_references or []
        history_by_group: dict[tuple[str, str], list[AdmissionRecord]] = defaultdict(list)
        for record in admission_records:
            if record.year in {2023, 2024, 2025}:
                history_by_group[(record.university_code, record.major_group_code)].append(record)

        majors_by_group: dict[tuple[str, str], list[str]] = defaultdict(list)
        plans_by_group: dict[tuple[str, str], list[AdmissionPlan]] = defaultdict(list)
        for plan in admission_plans:
            key = (plan.university_code, plan.major_group_code)
            plans_by_group[key].append(plan)
            if plan.major_name not in majors_by_group[key]:
                majors_by_group[key].append(plan.major_name)

        items: list[RecommendationItem] = []
        for key, plan_rows in plans_by_group.items():
            primary_plan = plan_rows[0]
            if not self._passes_hard_filters(candidate, primary_plan):
                continue
            history = [
                record
                for record in history_by_group.get(key, [])
                if record.province == candidate.province
                and record.batch == candidate.batch
                and record.category == candidate.category
                and record.first_subject == candidate.first_subject
                and record.confidence_score >= self.data_confidence_threshold
            ]
            if not history:
                item = self._build_new_group_item(candidate, primary_plan, plan_rows, majors_by_group[key])
                if item.adjusted_probability >= 0.20:
                    items.append(item)
                continue

            min_rank_3y = {record.year: record.min_rank for record in history}
            min_score_3y = {record.year: record.min_score for record in history}
            historical_ranks = list(min_rank_3y.values())
            rank_median = median_int(historical_ranks)
            rank_gap = candidate.rank - rank_median
            rank_gap_ratio = rank_gap / max(candidate.rank, 1)
            volatility = population_std(historical_ranks) / max(sum(historical_ranks) / len(historical_ranks), 1)

            current_plan_seats = sum(plan.plan_seats for plan in plan_rows)
            last_year_plan = next((record.plan_seats for record in history if record.year == 2025), None)
            last_year_plan_seats = last_year_plan or max(current_plan_seats, 1)
            plan_change_ratio = current_plan_seats / max(last_year_plan_seats, 1) - 1
            seat_abs_change = current_plan_seats - last_year_plan_seats
            preference_score = self._preference_match_score(candidate, primary_plan, majors_by_group[key])
            restriction_penalty, restriction_warnings = self._restriction_penalty(primary_plan)
            data_confidence = min([record.confidence_score for record in history] + [primary_plan.confidence_score])

            probability = base_probability_from_gap(rank_gap_ratio)
            probability += clamp(plan_change_ratio, -0.5, 0.5) * 0.12
            probability -= clamp(volatility, 0.0, 0.35) * 0.35
            probability += preference_score * 0.08
            probability -= restriction_penalty
            probability *= clamp(data_confidence, 0.0, 1.0)
            adjusted = clamp(probability, 0.05, 0.96)
            if adjusted < 0.12:
                continue

            tier = tier_for_probability(adjusted)
            refs = self._references_for_group(same_rank_references, key)
            reasons = [
                f"近三年最低位次中位数约为 {rank_median}，考生位次差为 {rank_gap}",
                f"2026 计划数 {current_plan_seats}，较上一年变化 {plan_change_ratio:.1%}",
                f"近三年位次波动系数 {volatility:.2f}",
            ]
            if preference_score > 0:
                reasons.append("与用户城市或专业偏好存在匹配")
            warnings = []
            if plan_change_ratio < -0.15:
                warnings.append("2026 计划明显缩招，需要谨慎")
            if volatility > 0.12:
                warnings.append("近三年位次波动较大")
            warnings.extend(restriction_warnings)
            if primary_plan.is_sino_foreign:
                warnings.append("中外合作项目，需核对学费、培养模式和证书规则")
            if primary_plan.is_private:
                warnings.append("民办本科项目，需重点核对学费和办学条件")

            items.append(
                RecommendationItem(
                    university_code=primary_plan.university_code,
                    university_name=primary_plan.university_name,
                    major_group_code=primary_plan.major_group_code,
                    major_group_name=primary_plan.major_group_name,
                    included_majors=majors_by_group[key],
                    current_plan_seats=current_plan_seats,
                    last_year_plan_seats=last_year_plan_seats,
                    plan_change_ratio=plan_change_ratio,
                    seat_abs_change=seat_abs_change,
                    min_rank_3y=min_rank_3y,
                    min_score_3y=min_score_3y,
                    rank_gap=rank_gap,
                    rank_gap_ratio=rank_gap_ratio,
                    volatility_score=volatility,
                    adjusted_probability=adjusted,
                    estimated_probability_band=probability_band_label(tier),
                    tier=tier,
                    risk_level=self._risk_level(tier, volatility, plan_change_ratio),
                    group_change_flag="stable" if len(history) == 3 else "unknown",
                    subject_requirement_change_flag="stable",
                    same_rank_hit_count=len(refs),
                    same_rank_reference_confidence=self._reference_confidence(refs),
                    preference_match_score=preference_score,
                    restriction_penalty=restriction_penalty,
                    data_confidence_score=data_confidence,
                    reasons=reasons,
                    warnings=warnings,
                    source_links=sorted({record.source_url for record in history} | {primary_plan.source_url}),
                )
            )
        return sorted(items, key=lambda item: (self._tier_order(item.tier), -item.adjusted_probability))

    def _passes_hard_filters(self, candidate: CandidateProfile, plan: AdmissionPlan) -> bool:
        if plan.province != candidate.province:
            return False
        if plan.batch != candidate.batch or plan.category != candidate.category:
            return False
        if plan.first_subject != candidate.first_subject:
            return False
        if plan.confidence_score < self.data_confidence_threshold:
            return False
        if not requirement_satisfied(plan.second_subject_requirement, candidate.second_subjects):
            return False
        max_tuition = candidate.preferences.get("max_tuition")
        if max_tuition is not None and plan.tuition > int(max_tuition):
            return False
        if not candidate.preferences.get("accept_sino_foreign", True) and plan.is_sino_foreign:
            return False
        if not candidate.preferences.get("accept_private_college", True) and plan.is_private:
            return False
        return True

    def _build_new_group_item(
        self,
        candidate: CandidateProfile,
        primary_plan: AdmissionPlan,
        plan_rows: list[AdmissionPlan],
        majors: list[str],
    ) -> RecommendationItem:
        current_plan_seats = sum(plan.plan_seats for plan in plan_rows)
        preference_score = self._preference_match_score(candidate, primary_plan, majors)
        data_confidence = primary_plan.confidence_score
        adjusted = clamp((0.35 + preference_score * 0.05) * data_confidence, 0.20, 0.45)
        tier = tier_for_probability(adjusted)
        return RecommendationItem(
            university_code=primary_plan.university_code,
            university_name=primary_plan.university_name,
            major_group_code=primary_plan.major_group_code,
            major_group_name=primary_plan.major_group_name,
            included_majors=majors,
            current_plan_seats=current_plan_seats,
            last_year_plan_seats=0,
            plan_change_ratio=1.0,
            seat_abs_change=current_plan_seats,
            min_rank_3y={},
            min_score_3y={},
            rank_gap=0,
            rank_gap_ratio=0.0,
            volatility_score=0.0,
            adjusted_probability=adjusted,
            estimated_probability_band=probability_band_label(tier),
            tier=tier,
            risk_level="high",
            group_change_flag="new_group",
            subject_requirement_change_flag="unknown",
            same_rank_hit_count=0,
            same_rank_reference_confidence=0.0,
            preference_match_score=preference_score,
            restriction_penalty=0.0,
            data_confidence_score=data_confidence,
            reasons=["2026 新增或缺少历史投档线，按低置信冲档处理"],
            warnings=["新增专业组无近三年投档线，必须人工核对高校招生章程"],
            source_links=[primary_plan.source_url],
        )

    def _preference_match_score(
        self, candidate: CandidateProfile, plan: AdmissionPlan, majors: list[str]
    ) -> float:
        score = 0.0
        preferred_cities = set(candidate.preferences.get("preferred_cities", []) or [])
        avoid_cities = set(candidate.preferences.get("avoid_cities", []) or [])
        preferred_majors = set(candidate.preferences.get("preferred_majors", []) or [])
        avoid_majors = set(candidate.preferences.get("avoid_majors", []) or [])
        if plan.campus in preferred_cities:
            score += 0.4
        if plan.campus in avoid_cities:
            score -= 0.6
        joined = " ".join(majors)
        if any(item and item in joined for item in preferred_majors):
            score += 0.5
        if any(item and item in joined for item in avoid_majors):
            score -= 0.8
        strategy = candidate.preferences.get("priority_strategy")
        if strategy == "employment_first":
            score += 0.1
        return clamp(score, -1.0, 1.0)

    def _restriction_penalty(self, plan: AdmissionPlan) -> tuple[float, list[str]]:
        penalty = 0.0
        warnings: list[str] = []
        if plan.physical_limit_note:
            penalty += 0.04
            warnings.append(f"体检限制需核对：{plan.physical_limit_note}")
        if plan.single_subject_limit_note:
            penalty += 0.04
            warnings.append(f"单科限制需核对：{plan.single_subject_limit_note}")
        return penalty, warnings

    def _references_for_group(
        self, references: list[SameRankReference], key: tuple[str, str]
    ) -> list[SameRankReference]:
        return [
            ref
            for ref in references
            if (ref.university_code, ref.major_group_code) == key
            and ref.reference_type == "observed_min_rank_nearby"
        ]

    def _reference_confidence(self, references: list[SameRankReference]) -> float:
        if not references:
            return 0.0
        return sum(ref.confidence_score for ref in references) / len(references)

    def _risk_level(self, tier: str, volatility: float, plan_change_ratio: float) -> str:
        if tier == "冲" or volatility > 0.18 or plan_change_ratio < -0.25:
            return "high"
        if tier == "稳" or volatility > 0.10:
            return "medium"
        return "low"

    def _tier_order(self, tier: str) -> int:
        return {"冲": 0, "稳": 1, "保": 2, "垫": 3}.get(tier, 9)


