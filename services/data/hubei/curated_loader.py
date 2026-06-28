from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Literal, cast

from services.crawler.adapters.static_csv_adapter import FixtureDataset
from services.data.hubei.authenticity import (
    FIXTURE_MARKERS,
    inspect_curated_dir,
    strict_real_data_required,
)
from services.recommender.models import AdmissionPlan, AdmissionRecord, RankSegment, bool_from_text

FirstSubjectValue = Literal["physics", "history"]


def load_curated_dataset(curated_dir: str | Path) -> FixtureDataset:
    curated_path = Path(curated_dir)
    authenticity = inspect_curated_dir(curated_path)
    strict_required = os.environ.get("APP_ENV") == "production" or strict_real_data_required()
    if strict_required and authenticity.contains_fixture_rows:
        raise ValueError("fixture curated data is not allowed in production mode")

    records = _load_admission_records(curated_path / "admission_records_2023_2025.csv")
    plans = _load_admission_plans(curated_path / "admission_plans_2026.csv")
    rank_segments = _load_rank_segments(curated_path / "rank_segments_2023_2026.csv")
    if strict_required:
        _reject_fixture_rows(records, plans)
    return FixtureDataset(
        admission_records=records,
        admission_plans=plans,
        rank_segments=rank_segments,
        universities=_derive_universities(records, plans),
        majors=_derive_majors(plans),
        major_groups=_derive_major_groups(records, plans),
    )


def _load_admission_records(path: Path) -> list[AdmissionRecord]:
    return [
        AdmissionRecord(
            year=int(row["year"]),
            province=row["province"],
            batch=row["batch"],
            category=row["category"],
            first_subject=cast(FirstSubjectValue, row["first_subject"]),
            second_subject_requirement=row.get("second_subject_requirement", ""),
            university_code=row["university_code"],
            university_name=row["university_name"],
            major_group_code=row["major_group_code"],
            major_group_name=row["major_group_name"],
            admission_category=row.get("admission_category", "平行志愿"),
            min_score=int(row["min_score"]),
            min_rank=int(row["min_rank"]),
            plan_seats=int(row["plan_seats"]) if row.get("plan_seats") else None,
            source_id=row["source_id"],
            source_url=row["source_url"],
            confidence_score=float(row.get("confidence_score") or row["parse_confidence"]),
            parser_version=row.get("parser_version", "curated-v0.2"),
        )
        for row in _read_dicts(path)
        if row.get("review_status") == "approved"
    ]


def _load_admission_plans(path: Path) -> list[AdmissionPlan]:
    return [
        AdmissionPlan(
            year=int(row["year"]),
            province=row["province"],
            batch=row["batch"],
            category=row["category"],
            first_subject=cast(FirstSubjectValue, row["first_subject"]),
            second_subject_requirement=row.get("second_subject_requirement", ""),
            university_code=row["university_code"],
            university_name=row["university_name"],
            major_group_code=row["major_group_code"],
            major_group_name=row["major_group_name"],
            major_code=row["major_code"],
            major_name=row["major_name"],
            plan_seats=int(row["plan_seats"]),
            tuition=int(row.get("tuition") or 0),
            schooling_years=row.get("schooling_years", ""),
            campus=row.get("campus", ""),
            is_sino_foreign=bool_from_text(row.get("is_sino_foreign")),
            is_private=bool_from_text(row.get("is_private")),
            notes=row.get("notes", ""),
            physical_limit_note=row.get("physical_limit_note", ""),
            single_subject_limit_note=row.get("single_subject_limit_note", ""),
            source_id=row["source_id"],
            source_url=row["source_url"],
            confidence_score=float(row.get("confidence_score") or row["parse_confidence"]),
        )
        for row in _read_dicts(path)
        if row.get("review_status") == "approved"
    ]


def _load_rank_segments(path: Path) -> list[RankSegment]:
    return [
        RankSegment(
            year=int(row["year"]),
            province=row["province"],
            category=row["category"],
            first_subject=cast(FirstSubjectValue, row["first_subject"]),
            score=int(row["score"]),
            same_score_count=int(row["same_score_count"]),
            cumulative_rank=int(row["cumulative_rank"]),
            rank_start=int(row["rank_start"]),
            rank_end=int(row["rank_end"]),
            source_id=row["source_id"],
            source_url=row["source_url"],
            confidence_score=float(row.get("confidence_score") or row["parse_confidence"]),
        )
        for row in _read_dicts(path)
        if row.get("review_status") == "approved"
    ]


def _read_dicts(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _reject_fixture_rows(records: list[AdmissionRecord], plans: list[AdmissionPlan]) -> None:
    fixture_markers = FIXTURE_MARKERS
    rows: list[AdmissionRecord | AdmissionPlan] = [*records, *plans]
    for row in rows:
        haystack = " ".join(
            [row.source_id, row.source_url, row.university_name, row.major_group_name]
        ).lower()
        if any(marker.lower() in haystack for marker in fixture_markers):
            raise ValueError("fixture curated data is not allowed in production mode")


def _derive_universities(
    records: list[AdmissionRecord], plans: list[AdmissionPlan]
) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    rows: list[AdmissionRecord | AdmissionPlan] = [*records, *plans]
    for row in rows:
        seen.setdefault(row.university_code, row.university_name)
    return [
        {"university_code": code, "university_name": name}
        for code, name in sorted(seen.items())
    ]


def _derive_majors(plans: list[AdmissionPlan]) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    for plan in plans:
        seen.setdefault(plan.major_code, plan.major_name)
    return [{"major_code": code, "major_name": name} for code, name in sorted(seen.items())]


def _derive_major_groups(
    records: list[AdmissionRecord], plans: list[AdmissionPlan]
) -> list[dict[str, str]]:
    seen: dict[str, str] = {}
    rows: list[AdmissionRecord | AdmissionPlan] = [*records, *plans]
    for row in rows:
        seen.setdefault(row.major_group_code, row.major_group_name)
    return [
        {"major_group_code": code, "major_group_name": name}
        for code, name in sorted(seen.items())
    ]
