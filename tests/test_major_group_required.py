from __future__ import annotations


def test_all_fixture_records_have_major_group_code(dataset):
    assert all(record.major_group_code for record in dataset.admission_records)
    assert all(plan.major_group_code for plan in dataset.admission_plans)

