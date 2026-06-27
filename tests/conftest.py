from __future__ import annotations

from pathlib import Path

import pytest

from services.crawler.adapters.static_csv_adapter import (
    FixtureDataset,
    StaticCsvHubeiFixtureAdapter,
)
from services.recommender.admission_risk_model import HubeiAdmissionRiskModel
from services.recommender.models import CandidateProfile
from services.recommender.same_rank_reference_builder import SameRankReferenceBuilder


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "fixtures" / "hubei"


@pytest.fixture(scope="session")
def dataset(fixture_dir: Path) -> FixtureDataset:
    return StaticCsvHubeiFixtureAdapter(fixture_dir).load()


@pytest.fixture()
def physics_candidate() -> CandidateProfile:
    return CandidateProfile(
        year=2026,
        province="湖北",
        first_subject="physics",
        second_subjects=("chemistry", "biology"),
        score=610,
        rank=26000,
        preferences={
            "max_tuition": 60000,
            "accept_private_college": True,
            "accept_sino_foreign": True,
            "priority_strategy": "balanced",
        },
    )


@pytest.fixture()
def model() -> HubeiAdmissionRiskModel:
    return HubeiAdmissionRiskModel()


def recommend_for(candidate: CandidateProfile, dataset: FixtureDataset):
    refs = SameRankReferenceBuilder().build(
        target_year=2026,
        candidate_rank=candidate.rank,
        province=candidate.province,
        first_subject=candidate.first_subject,
        batch=candidate.batch,
        records=dataset.admission_records,
    )
    return HubeiAdmissionRiskModel().recommend(
        candidate,
        dataset.admission_records,
        dataset.admission_plans,
        refs,
    )

