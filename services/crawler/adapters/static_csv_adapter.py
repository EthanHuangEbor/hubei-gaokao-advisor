from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from services.recommender.models import (
    AdmissionPlan,
    AdmissionRecord,
    RankSegment,
    bool_from_text,
)


@dataclass
class FixtureDataset:
    admission_records: list[AdmissionRecord]
    admission_plans: list[AdmissionPlan]
    rank_segments: list[RankSegment]
    universities: list[dict[str, str]]
    majors: list[dict[str, str]]
    major_groups: list[dict[str, str]]


class StaticCsvHubeiFixtureAdapter:
    def __init__(self, fixture_dir: str | Path):
        self.fixture_dir = Path(fixture_dir)

    def load(self) -> FixtureDataset:
        return FixtureDataset(
            admission_records=self.load_admission_records(),
            admission_plans=self.load_admission_plans(),
            rank_segments=self.load_rank_segments(),
            universities=self._read_dicts("hubei_sample_universities.csv"),
            majors=self._read_dicts("hubei_sample_majors.csv"),
            major_groups=self._read_dicts("hubei_sample_major_groups.csv"),
        )

    def load_admission_records(self) -> list[AdmissionRecord]:
        records: list[AdmissionRecord] = []
        for year in [2023, 2024, 2025]:
            for row in self._read_dicts(f"hubei_sample_admission_records_{year}.csv"):
                records.append(
                    AdmissionRecord(
                        year=int(row["year"]),
                        province=row["province"],
                        batch=row["batch"],
                        category=row["category"],
                        first_subject=row["first_subject"],  # type: ignore[arg-type]
                        second_subject_requirement=row["second_subject_requirement"],
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
                        confidence_score=float(row["confidence_score"]),
                        parser_version=row.get("parser_version", "fixture-v1"),
                    )
                )
        return records

    def load_admission_plans(self) -> list[AdmissionPlan]:
        plans: list[AdmissionPlan] = []
        for row in self._read_dicts("hubei_sample_admission_plans_2026.csv"):
            plans.append(
                AdmissionPlan(
                    year=int(row["year"]),
                    province=row["province"],
                    batch=row["batch"],
                    category=row["category"],
                    first_subject=row["first_subject"],  # type: ignore[arg-type]
                    second_subject_requirement=row["second_subject_requirement"],
                    university_code=row["university_code"],
                    university_name=row["university_name"],
                    major_group_code=row["major_group_code"],
                    major_group_name=row["major_group_name"],
                    major_code=row["major_code"],
                    major_name=row["major_name"],
                    plan_seats=int(row["plan_seats"]),
                    tuition=int(row["tuition"]),
                    schooling_years=row["schooling_years"],
                    campus=row["campus"],
                    is_sino_foreign=bool_from_text(row["is_sino_foreign"]),
                    is_private=bool_from_text(row["is_private"]),
                    notes=row.get("notes", ""),
                    physical_limit_note=row.get("physical_limit_note", ""),
                    single_subject_limit_note=row.get("single_subject_limit_note", ""),
                    source_id=row["source_id"],
                    source_url=row["source_url"],
                    confidence_score=float(row["confidence_score"]),
                )
            )
        return plans

    def load_rank_segments(self) -> list[RankSegment]:
        segments: list[RankSegment] = []
        for year in [2023, 2024, 2025, 2026]:
            for row in self._read_dicts(f"hubei_sample_rank_segments_{year}.csv"):
                segments.append(
                    RankSegment(
                        year=int(row["year"]),
                        province=row["province"],
                        category=row["category"],
                        first_subject=row["first_subject"],  # type: ignore[arg-type]
                        score=int(row["score"]),
                        same_score_count=int(row["same_score_count"]),
                        cumulative_rank=int(row["cumulative_rank"]),
                        rank_start=int(row["rank_start"]),
                        rank_end=int(row["rank_end"]),
                        source_id=row["source_id"],
                        source_url=row["source_url"],
                        confidence_score=float(row["confidence_score"]),
                    )
                )
        return segments

    def _read_dicts(self, name: str) -> list[dict[str, str]]:
        path = self.fixture_dir / name
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

