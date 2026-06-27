from __future__ import annotations


def test_plan_change_ratio_matches_formula(dataset, physics_candidate):
    from tests.conftest import recommend_for

    item = recommend_for(physics_candidate, dataset)[0]
    expected = item.current_plan_seats / max(item.last_year_plan_seats, 1) - 1
    assert item.plan_change_ratio == expected

