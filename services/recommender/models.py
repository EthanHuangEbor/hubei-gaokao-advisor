from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any, Literal

FirstSubject = Literal["physics", "history"]
Tier = str


@dataclass(frozen=True)
class CandidateProfile:
    year: int
    province: str
    first_subject: FirstSubject
    second_subjects: tuple[str, ...]
    score: int
    rank: int
    batch: str = "本科普通批"
    category: str = "普通类"
    preferences: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdmissionRecord:
    year: int
    province: str
    batch: str
    category: str
    first_subject: FirstSubject
    second_subject_requirement: str
    university_code: str
    university_name: str
    major_group_code: str
    major_group_name: str
    admission_category: str
    min_score: int
    min_rank: int
    plan_seats: int | None
    source_id: str
    source_url: str
    confidence_score: float
    parser_version: str = "fixture-v1"


@dataclass(frozen=True)
class AdmissionPlan:
    year: int
    province: str
    batch: str
    category: str
    first_subject: FirstSubject
    second_subject_requirement: str
    university_code: str
    university_name: str
    major_group_code: str
    major_group_name: str
    major_code: str
    major_name: str
    plan_seats: int
    tuition: int
    schooling_years: str
    campus: str
    is_sino_foreign: bool
    is_private: bool
    notes: str
    physical_limit_note: str
    single_subject_limit_note: str
    source_id: str
    source_url: str
    confidence_score: float


@dataclass(frozen=True)
class RankSegment:
    year: int
    province: str
    category: str
    first_subject: FirstSubject
    score: int
    same_score_count: int
    cumulative_rank: int
    rank_start: int
    rank_end: int
    source_id: str
    source_url: str
    confidence_score: float


@dataclass(frozen=True)
class SameRankReference:
    target_year: int
    history_year: int
    province: str
    first_subject: FirstSubject
    candidate_rank: int
    rank_window_start: int
    rank_window_end: int
    university_code: str
    university_name: str
    major_group_code: str
    major_group_name: str
    min_score: int
    min_rank: int
    rank_gap: int
    reference_type: str
    confidence_score: float
    source_url: str


@dataclass
class RecommendationItem:
    university_code: str
    university_name: str
    major_group_code: str
    major_group_name: str
    included_majors: list[str]
    current_plan_seats: int
    last_year_plan_seats: int
    plan_change_ratio: float
    seat_abs_change: int
    min_rank_3y: dict[int, int]
    min_score_3y: dict[int, int]
    rank_gap: int
    rank_gap_ratio: float
    volatility_score: float
    adjusted_probability: float
    estimated_probability_band: str
    tier: Tier
    risk_level: str
    group_change_flag: str
    subject_requirement_change_flag: str
    same_rank_hit_count: int
    same_rank_reference_confidence: float
    preference_match_score: float
    restriction_penalty: float
    data_confidence_score: float
    reasons: list[str]
    warnings: list[str]
    source_links: list[str]
    doctor_peak_explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "university_code": self.university_code,
            "university_name": self.university_name,
            "major_group_code": self.major_group_code,
            "major_group_name": self.major_group_name,
            "included_majors": self.included_majors,
            "current_plan_seats": self.current_plan_seats,
            "last_year_plan_seats": self.last_year_plan_seats,
            "plan_change_ratio": round(self.plan_change_ratio, 4),
            "seat_abs_change": self.seat_abs_change,
            "min_rank_2023": self.min_rank_3y.get(2023),
            "min_rank_2024": self.min_rank_3y.get(2024),
            "min_rank_2025": self.min_rank_3y.get(2025),
            "min_score_2023": self.min_score_3y.get(2023),
            "min_score_2024": self.min_score_3y.get(2024),
            "min_score_2025": self.min_score_3y.get(2025),
            "rank_gap": self.rank_gap,
            "rank_gap_ratio": round(self.rank_gap_ratio, 4),
            "volatility_score": round(self.volatility_score, 4),
            "risk_level": self.risk_level,
            "estimated_probability_band": self.estimated_probability_band,
            "tier": self.tier,
            "group_change_flag": self.group_change_flag,
            "subject_requirement_change_flag": self.subject_requirement_change_flag,
            "same_rank_hit_count": self.same_rank_hit_count,
            "same_rank_reference_confidence": round(self.same_rank_reference_confidence, 4),
            "preference_match_score": round(self.preference_match_score, 4),
            "restriction_penalty": round(self.restriction_penalty, 4),
            "data_confidence_score": round(self.data_confidence_score, 4),
            "reasons": self.reasons,
            "warnings": self.warnings,
            "source_links": self.source_links,
            "doctor_peak_explanation": self.doctor_peak_explanation,
        }


@dataclass
class RecommendationRun:
    run_id: str
    candidate: CandidateProfile
    items: list[RecommendationItem]
    strategy_note: str
    tier_counts: dict[str, int]
    disclaimer: str
    doctor_peak_advice: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "candidate": {
                "year": self.candidate.year,
                "province": self.candidate.province,
                "first_subject": self.candidate.first_subject,
                "second_subjects": list(self.candidate.second_subjects),
                "score": self.candidate.score,
                "rank": self.candidate.rank,
                "batch": self.candidate.batch,
                "category": self.candidate.category,
                "preferences": self.candidate.preferences,
            },
            "strategy_note": self.strategy_note,
            "tier_counts": self.tier_counts,
            "items": [item.to_dict() for item in self.items],
            "disclaimer": self.disclaimer,
            "doctor_peak_advice": self.doctor_peak_advice,
        }


def bool_from_text(value: str | bool | int | None) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是", "有"}


def median_int(values: list[int]) -> int:
    return int(median(values)) if values else 0


