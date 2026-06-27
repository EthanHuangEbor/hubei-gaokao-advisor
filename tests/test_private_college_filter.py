from __future__ import annotations

from services.recommender.models import CandidateProfile
from tests.conftest import recommend_for


def test_private_college_filter(dataset):
    candidate = CandidateProfile(
        year=2026,
        province="湖北",
        first_subject="physics",
        second_subjects=("chemistry", "biology"),
        score=610,
        rank=26000,
        preferences={"max_tuition": 60000, "accept_private_college": False, "accept_sino_foreign": True},
    )
    items = recommend_for(candidate, dataset)
    private_codes = {plan.major_group_code for plan in dataset.admission_plans if plan.is_private}
    assert all(item.major_group_code not in private_codes for item in items)

