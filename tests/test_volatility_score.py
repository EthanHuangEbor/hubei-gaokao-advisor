from __future__ import annotations


def test_volatility_score_is_non_negative(dataset, physics_candidate):
    from tests.conftest import recommend_for

    items = recommend_for(physics_candidate, dataset)
    assert items
    assert all(item.volatility_score >= 0 for item in items)

