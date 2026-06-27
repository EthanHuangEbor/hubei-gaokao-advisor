from __future__ import annotations

from services.recommender.models import CandidateProfile
from tests.conftest import recommend_for


def test_chemistry_required_groups_filtered_when_missing_chemistry(dataset):
    candidate = CandidateProfile(
        year=2026,
        province="湖北",
        first_subject="physics",
        second_subjects=("biology", "geography"),
        score=610,
        rank=26000,
        preferences={"max_tuition": 60000, "accept_private_college": True, "accept_sino_foreign": True},
    )
    items = recommend_for(candidate, dataset)
    requirements = {
        plan.major_group_code: plan.second_subject_requirement for plan in dataset.admission_plans
    }
    assert all(requirements[item.major_group_code] != "化学" for item in items)

