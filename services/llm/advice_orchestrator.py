from __future__ import annotations

from typing import Any

from services.llm.minimax_client import MiniMaxClient, MiniMaxResult
from services.recommender.models import RecommendationRun


class AdviceOrchestrator:
    def __init__(self, client: MiniMaxClient | None = None):
        self.client = client or MiniMaxClient()

    def explain(self, run: RecommendationRun) -> MiniMaxResult:
        payload: dict[str, Any] = {
            "province": run.candidate.province,
            "year": run.candidate.year,
            "first_subject": run.candidate.first_subject,
            "second_subjects": list(run.candidate.second_subjects),
            "score": run.candidate.score,
            "rank": run.candidate.rank,
            "preferences": run.candidate.preferences,
            "strategy_note": run.strategy_note,
            "items": [item.to_dict() for item in run.items],
        }
        result = self.client.generate_advice(payload)
        run.doctor_peak_advice = result.output_json
        explanations = {
            item.get("major_group_id"): item.get("why", "")
            for item in result.output_json.get("items", [])
            if isinstance(item, dict)
        }
        for item in run.items:
            item.doctor_peak_explanation = explanations.get(
                item.major_group_code,
                "Doctor.Peak fallback：请结合专业组、计划变化、位次差和限制条件复核。",
            )
        return result

