from __future__ import annotations

from services.recommender.models import AdmissionRecord, SameRankReference


def rank_window_for(candidate_rank: int) -> int:
    if candidate_rank <= 5000:
        return 300
    if candidate_rank <= 20000:
        return 800
    if candidate_rank <= 60000:
        return 1500
    return 3000


class SameRankReferenceBuilder:
    """Builds aggregated same-rank historical references without personal tracing."""

    def build(
        self,
        *,
        target_year: int,
        candidate_rank: int,
        province: str,
        first_subject: str,
        batch: str,
        records: list[AdmissionRecord],
    ) -> list[SameRankReference]:
        window = rank_window_for(candidate_rank)
        start = max(1, candidate_rank - window)
        end = candidate_rank + window
        references: list[SameRankReference] = []
        for record in records:
            if record.province != province:
                continue
            if record.first_subject != first_subject or record.batch != batch:
                continue
            if record.year not in {2023, 2024, 2025}:
                continue
            if start <= record.min_rank <= end:
                references.append(
                    SameRankReference(
                        target_year=target_year,
                        history_year=record.year,
                        province=province,
                        first_subject=record.first_subject,
                        candidate_rank=candidate_rank,
                        rank_window_start=start,
                        rank_window_end=end,
                        university_code=record.university_code,
                        university_name=record.university_name,
                        major_group_code=record.major_group_code,
                        major_group_name=record.major_group_name,
                        min_score=record.min_score,
                        min_rank=record.min_rank,
                        rank_gap=candidate_rank - record.min_rank,
                        reference_type="observed_min_rank_nearby",
                        confidence_score=record.confidence_score,
                        source_url=record.source_url,
                    )
                )
        return sorted(references, key=lambda item: abs(item.rank_gap))

