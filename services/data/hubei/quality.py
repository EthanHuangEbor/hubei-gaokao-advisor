from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from services.data.hubei.authenticity import FIXTURE_MARKERS

REQUIRED_PROVENANCE_FIELDS = (
    "source_id",
    "source_url",
    "source_type",
    "raw_document_sha256",
    "parser_name",
    "parser_version",
    "parse_confidence",
    "confidence_score",
    "license_note",
    "review_status",
)


@dataclass(frozen=True)
class QualityReport:
    candidate_root: Path
    checked_files: int
    checked_rows: int
    errors: list[str]
    warnings: list[str]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def run_quality_checks(candidate_root: str | Path) -> QualityReport:
    root = Path(candidate_root)
    errors: list[str] = []
    warnings: list[str] = []
    checked_files = 0
    checked_rows = 0

    for csv_path in sorted(root.rglob("*.csv")):
        checked_files += 1
        rows = _read_rows(csv_path)
        checked_rows += len(rows)
        for index, row in enumerate(rows, start=2):
            _check_fixture_markers(csv_path, index, row, errors)
            _check_required_provenance(csv_path, index, row, errors)
        if "rank_segments" in csv_path.parts:
            _check_rank_monotonicity(csv_path, rows, errors)

    return QualityReport(
        candidate_root=root,
        checked_files=checked_files,
        checked_rows=checked_rows,
        errors=errors,
        warnings=warnings,
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _check_fixture_markers(
    path: Path,
    line_number: int,
    row: dict[str, str],
    errors: list[str],
) -> None:
    haystack = " ".join(str(value) for value in row.values()).lower()
    marker = next((item for item in FIXTURE_MARKERS if item.lower() in haystack), None)
    if marker:
        errors.append(f"{path}:{line_number} contains fixture marker {marker}")


def _check_required_provenance(
    path: Path,
    line_number: int,
    row: dict[str, str],
    errors: list[str],
) -> None:
    for field in REQUIRED_PROVENANCE_FIELDS:
        if not str(row.get(field, "")).strip():
            errors.append(f"{path}:{line_number} missing provenance field {field}")


def _check_rank_monotonicity(
    path: Path,
    rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    groups: dict[tuple[str, str, str], list[tuple[int, int, int]]] = {}
    for line_number, row in enumerate(rows, start=2):
        try:
            score = int(row.get("score", ""))
            cumulative_rank = int(row.get("cumulative_rank", ""))
        except ValueError:
            errors.append(f"{path}:{line_number} invalid rank numeric fields")
            continue
        key = (row.get("year", ""), row.get("category", ""), row.get("first_subject", ""))
        groups.setdefault(key, []).append((line_number, score, cumulative_rank))

    for values in groups.values():
        ordered = sorted(values, key=lambda item: item[1], reverse=True)
        previous_rank: int | None = None
        previous_score: int | None = None
        for line_number, score, cumulative_rank in ordered:
            if previous_rank is not None and cumulative_rank < previous_rank:
                errors.append(
                    f"{path}:{line_number} cumulative_rank decreased from {previous_rank} "
                    f"at higher score {previous_score} to {cumulative_rank} at score {score}"
                )
            previous_rank = cumulative_rank
            previous_score = score
