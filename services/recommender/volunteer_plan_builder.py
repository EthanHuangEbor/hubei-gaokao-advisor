from __future__ import annotations

from collections import Counter

from services.recommender.models import CandidateProfile, RecommendationItem, RecommendationRun

DISCLAIMER = (
    "本系统仅基于公开历史数据、当年招生计划和规则模型进行估计，不构成录取承诺；"
    "最终填报应以湖北省考试院、湖北省招办、湖北招生考试网、湖北省招生数智综合平台"
    "和高校招生章程为准。"
)


class VolunteerPlanBuilder:
    default_targets = {"冲": 9, "稳": 17, "保": 14, "垫": 5}

    def build(
        self,
        *,
        run_id: str,
        candidate: CandidateProfile,
        items: list[RecommendationItem],
        target_total: int = 45,
    ) -> RecommendationRun:
        buckets = {tier: [item for item in items if item.tier == tier] for tier in self.default_targets}
        selected: list[RecommendationItem] = []
        shortage: list[str] = []
        for tier, count in self.default_targets.items():
            take = buckets[tier][:count]
            selected.extend(take)
            if len(take) < count:
                shortage.append(f"{tier}档不足 {count - len(take)} 个")

        if len(selected) < target_total:
            existing = {(item.university_code, item.major_group_code) for item in selected}
            fill = [
                item
                for item in items
                if (item.university_code, item.major_group_code) not in existing
            ]
            selected.extend(fill[: target_total - len(selected)])

        selected = selected[:target_total]
        for position, item in enumerate(selected, start=1):
            item.position = position
        counts = Counter(item.tier for item in selected)
        strategy_note = "按湖北本科普通批院校专业组口径生成志愿草表。"
        if shortage:
            strategy_note += " 推荐池不足时已自动调整比例：" + "；".join(shortage) + "。"
        return RecommendationRun(
            run_id=run_id,
            candidate=candidate,
            items=selected,
            strategy_note=strategy_note,
            tier_counts={tier: counts.get(tier, 0) for tier in ["冲", "稳", "保", "垫"]},
            disclaimer=DISCLAIMER,
        )

