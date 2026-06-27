from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from services.crawler.adapters.static_csv_adapter import FixtureDataset
from services.recommender.models import AdmissionPlan, AdmissionRecord, RankSegment


@dataclass(frozen=True)
class QualityFinding:
    severity: str
    entity: str
    message: str


def check_admission_records(records: list[AdmissionRecord]) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    keys = Counter(
        (
            item.year,
            item.first_subject,
            item.university_code,
            item.major_group_code,
        )
        for item in records
    )
    for record in records:
        if record.year not in {2023, 2024, 2025}:
            findings.append(QualityFinding("error", "admission_records", "year must be 2023/2024/2025"))
        if record.first_subject not in {"physics", "history"}:
            findings.append(QualityFinding("error", "admission_records", "first_subject invalid"))
        if not record.major_group_code:
            findings.append(QualityFinding("error", "admission_records", "major_group_code required"))
        if record.min_rank <= 0:
            findings.append(QualityFinding("error", "admission_records", "min_rank must be positive"))
        if not 0 <= record.min_score <= 750:
            findings.append(QualityFinding("error", "admission_records", "min_score out of range"))
        if record.confidence_score < 0.85:
            findings.append(QualityFinding("warning", "admission_records", "low confidence excluded"))
        if not record.source_url:
            findings.append(QualityFinding("error", "admission_records", "source_url required"))
    duplicates = [key for key, count in keys.items() if count > 1]
    if duplicates:
        findings.append(QualityFinding("error", "admission_records", f"duplicate keys: {len(duplicates)}"))
    return findings


def check_admission_plans(plans: list[AdmissionPlan]) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    for plan in plans:
        if plan.year != 2026:
            findings.append(QualityFinding("error", "admission_plans", "year must be 2026"))
        if not plan.major_group_code:
            findings.append(QualityFinding("error", "admission_plans", "major_group_code required"))
        if not plan.major_name:
            findings.append(QualityFinding("error", "admission_plans", "major_name required"))
        if plan.plan_seats <= 0:
            findings.append(QualityFinding("error", "admission_plans", "plan_seats must be positive"))
        if plan.confidence_score < 0.85:
            findings.append(QualityFinding("warning", "admission_plans", "low confidence excluded"))
    return findings


def check_rank_segments(segments: list[RankSegment]) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    coverage = Counter((segment.year, segment.first_subject) for segment in segments)
    for year in [2023, 2024, 2025, 2026]:
        for first_subject in ("physics", "history"):
            if coverage[(year, first_subject)] < 4:
                findings.append(
                    QualityFinding(
                        "warning",
                        "rank_segments",
                        f"{year} {first_subject} score coverage is thin",
                    )
                )
    return findings


def run_quality_checks(dataset: FixtureDataset) -> list[QualityFinding]:
    return [
        *check_admission_records(dataset.admission_records),
        *check_admission_plans(dataset.admission_plans),
        *check_rank_segments(dataset.rank_segments),
    ]

