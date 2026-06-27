from __future__ import annotations

from services.recommender.models import CandidateProfile
from tests.conftest import recommend_for


def test_sino_foreign_filter(dataset):
    candidate = CandidateProfile(
        year=2026,
        province="湖北",
        first_subject="physics",
        second_subjects=("chemistry", "biology"),
        score=610,
        rank=26000,
        preferences={"max_tuition": 60000, "accept_private_college": True, "accept_sino_foreign": False},
    )
    items = recommend_for(candidate, dataset)
    sino_codes = {plan.major_group_code for plan in dataset.admission_plans if plan.is_sino_foreign}
    assert all(item.major_group_code not in sino_codes for item in items)

