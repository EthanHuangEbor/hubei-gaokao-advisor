from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.recommender.models import AdmissionRecord


@dataclass(frozen=True)
class AdmissionLineParseResult:
    records: list[AdmissionRecord]
    row_errors: list[str]
    low_confidence_count: int
    parser_version: str

    @property
    def summary(self) -> dict[str, object]:
        return {
            "parser_version": self.parser_version,
            "candidate_count": len(self.records) + len(self.row_errors),
            "valid_count": len(self.records),
            "invalid_count": len(self.row_errors),
            "low_confidence_count": self.low_confidence_count,
        }


class HubeiAdmissionLineAdapter:
    parser_version = "hubei-admission-line-v1"

    def parse_fixture_csv(self, fixture_dir: str | Path) -> list[AdmissionRecord]:
        return StaticCsvHubeiFixtureAdapter(fixture_dir).load_admission_records()

    def parse_uploaded_csv(self, path: str | Path) -> AdmissionLineParseResult:
        records: list[AdmissionRecord] = []
        row_errors: list[str] = []
        low_confidence_count = 0
        with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
            for index, row in enumerate(csv.DictReader(file), start=2):
                try:
                    record = self._row_to_record(row)
                except (KeyError, TypeError, ValueError) as exc:
                    row_errors.append(f"row {index}: {exc}")
                    continue
                errors = self.validate_record(record)
                if record.confidence_score < 0.85:
                    low_confidence_count += 1
                    errors.append("confidence_score below production threshold")
                if errors:
                    row_errors.append(f"row {index}: {'; '.join(errors)}")
                    continue
                records.append(record)
        return AdmissionLineParseResult(
            records=records,
            row_errors=row_errors,
            low_confidence_count=low_confidence_count,
            parser_version=self.parser_version,
        )

    def validate_record(self, record: AdmissionRecord) -> list[str]:
        errors: list[str] = []
        if record.year not in {2023, 2024, 2025}:
            errors.append("year must be 2023, 2024, or 2025")
        if record.province != "湖北":
            errors.append("province must be 湖北")
        if not record.major_group_code:
            errors.append("major_group_code is required")
        if record.min_rank <= 0:
            errors.append("min_rank must be positive")
        if not 0 <= record.min_score <= 750:
            errors.append("min_score must be within 0-750")
        if not record.source_url:
            errors.append("source_url is required")
        return errors

    def _row_to_record(self, row: dict[str, Any]) -> AdmissionRecord:
        plan_seats = row.get("plan_seats")
        return AdmissionRecord(
            year=int(row["year"]),
            province=str(row["province"]),
            batch=str(row["batch"]),
            category=str(row["category"]),
            first_subject=str(row["first_subject"]),  # type: ignore[arg-type]
            second_subject_requirement=str(row["second_subject_requirement"]),
            university_code=str(row["university_code"]),
            university_name=str(row["university_name"]),
            major_group_code=str(row["major_group_code"]),
            major_group_name=str(row["major_group_name"]),
            admission_category=str(row.get("admission_category", "平行志愿")),
            min_score=int(row["min_score"]),
            min_rank=int(row["min_rank"]),
            plan_seats=int(plan_seats) if plan_seats else None,
            source_id=str(row["source_id"]),
            source_url=str(row["source_url"]),
            confidence_score=float(row["confidence_score"]),
            parser_version=str(row.get("parser_version") or self.parser_version),
        )
