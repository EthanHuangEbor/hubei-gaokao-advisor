from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.recommender.models import AdmissionPlan, bool_from_text


@dataclass(frozen=True)
class PlanParseResult:
    plans: list[AdmissionPlan]
    row_errors: list[str]
    low_confidence_count: int
    parser_version: str

    @property
    def summary(self) -> dict[str, object]:
        return {
            "parser_version": self.parser_version,
            "candidate_count": len(self.plans) + len(self.row_errors),
            "valid_count": len(self.plans),
            "invalid_count": len(self.row_errors),
            "low_confidence_count": self.low_confidence_count,
        }


class HubeiPlanAdapter:
    parser_version = "hubei-plan-v1"

    def parse_fixture_csv(self, fixture_dir: str | Path) -> list[AdmissionPlan]:
        return StaticCsvHubeiFixtureAdapter(fixture_dir).load_admission_plans()

    def parse_uploaded_csv(self, path: str | Path) -> PlanParseResult:
        plans: list[AdmissionPlan] = []
        row_errors: list[str] = []
        low_confidence_count = 0
        with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
            for index, row in enumerate(csv.DictReader(file), start=2):
                try:
                    plan = self._row_to_plan(row)
                except (KeyError, TypeError, ValueError) as exc:
                    row_errors.append(f"row {index}: {exc}")
                    continue
                errors = self.validate_plan(plan)
                if plan.confidence_score < 0.85:
                    low_confidence_count += 1
                if errors:
                    row_errors.append(f"row {index}: {'; '.join(errors)}")
                    continue
                plans.append(plan)
        return PlanParseResult(
            plans=plans,
            row_errors=row_errors,
            low_confidence_count=low_confidence_count,
            parser_version=self.parser_version,
        )

    def validate_plan(self, plan: AdmissionPlan) -> list[str]:
        errors: list[str] = []
        if plan.year != 2026:
            errors.append("MVP admission plans must be 2026")
        if not plan.major_group_code:
            errors.append("major_group_code is required")
        if not plan.major_name:
            errors.append("major_name is required")
        if plan.plan_seats <= 0:
            errors.append("plan_seats must be positive")
        if plan.confidence_score < 0.85:
            errors.append("confidence_score below production threshold")
        return errors

    def _row_to_plan(self, row: dict[str, Any]) -> AdmissionPlan:
        return AdmissionPlan(
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
            major_code=str(row["major_code"]),
            major_name=str(row["major_name"]),
            plan_seats=int(row["plan_seats"]),
            tuition=int(row["tuition"]),
            schooling_years=str(row["schooling_years"]),
            campus=str(row["campus"]),
            is_sino_foreign=bool_from_text(row.get("is_sino_foreign")),
            is_private=bool_from_text(row.get("is_private")),
            notes=str(row.get("notes", "")),
            physical_limit_note=str(row.get("physical_limit_note", "")),
            single_subject_limit_note=str(row.get("single_subject_limit_note", "")),
            source_id=str(row["source_id"]),
            source_url=str(row["source_url"]),
            confidence_score=float(row["confidence_score"]),
        )
