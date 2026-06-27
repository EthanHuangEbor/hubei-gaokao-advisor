from __future__ import annotations

from services.recommender.models import CandidateProfile
from tests.conftest import recommend_for


def test_rank_gap_is_candidate_rank_minus_history_median(dataset):
    candidate = CandidateProfile(
        year=2026,
        province="湖北",
        first_subject="physics",
        second_subjects=("chemistry", "biology"),
        score=650,
        rank=15000,
        preferences={"max_tuition": 60000, "accept_private_college": True, "accept_sino_foreign": True},
    )
    item = recommend_for(candidate, dataset)[0]
    history = [
        record.min_rank
        for record in dataset.admission_records
        if record.university_code == item.university_code
        and record.major_group_code == item.major_group_code
    ]
    assert item.rank_gap == candidate.rank - sorted(history)[len(history) // 2]

