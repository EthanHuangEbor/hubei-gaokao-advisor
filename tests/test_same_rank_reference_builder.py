from __future__ import annotations

from services.recommender.same_rank_reference_builder import (
    SameRankReferenceBuilder,
    rank_window_for,
)


def test_rank_window_rules():
    assert rank_window_for(4000) == 300
    assert rank_window_for(12000) == 800
    assert rank_window_for(50000) == 1500
    assert rank_window_for(70000) == 3000


def test_same_rank_reference_builder(dataset):
    refs = SameRankReferenceBuilder().build(
        target_year=2026,
        candidate_rank=26000,
        province="湖北",
        first_subject="physics",
        batch="本科普通批",
        records=dataset.admission_records,
    )
    assert refs
    assert all(ref.reference_type == "observed_min_rank_nearby" for ref in refs)
    assert all(ref.first_subject == "physics" for ref in refs)

