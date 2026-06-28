from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from services.data.hubei.authenticity import FIXTURE_MARKERS
from services.data.hubei.quality import REQUIRED_PROVENANCE_FIELDS, run_quality_checks

OUTPUT_FILES = {
    "admission_lines": ("admission_records", "admission_records_2023_2025.csv"),
    "rank_segments": ("rank_segments", "rank_segments_2023_2026.csv"),
    "plans": ("admission_plans", "admission_plans_2026.csv"),
}


@dataclass(frozen=True)
class PromoteResult:
    promoted_counts: dict[str, int]
    curated_dir: Path


def promote_candidates(candidate_root: str | Path, curated_dir: str | Path) -> PromoteResult:
    root = Path(candidate_root)
    quality = run_quality_checks(root)
    if quality.has_errors:
        raise RuntimeError(f"quality errors block promotion: {len(quality.errors)}")

    curated = Path(curated_dir)
    curated.mkdir(parents=True, exist_ok=True)
    promoted_counts = {dataset_name: 0 for dataset_name, _ in OUTPUT_FILES.values()}

    for subdir, (dataset_name, output_name) in OUTPUT_FILES.items():
        candidate_dir = root / subdir
        rows = _eligible_rows(candidate_dir)
        promoted_counts[dataset_name] = len(rows)
        _write_csv(
            curated / output_name,
            rows,
            fieldnames=_candidate_fieldnames(candidate_dir),
        )

    return PromoteResult(promoted_counts=promoted_counts, curated_dir=curated)


def candidate_eligible_counts(candidate_root: str | Path) -> dict[str, int]:
    root = Path(candidate_root)
    return {
        dataset_name: len(_eligible_rows(root / subdir))
        for subdir, (dataset_name, _) in OUTPUT_FILES.items()
    }


def _eligible_rows(directory: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not directory.exists():
        return rows
    for path in sorted(directory.rglob("*.csv")):
        for row in _read_rows(path):
            if _is_promotable(row):
                rows.append(row)
    return rows


def _is_promotable(row: dict[str, str]) -> bool:
    if row.get("review_status", "").strip().lower() != "approved":
        return False
    try:
        if float(row.get("confidence_score", "0")) < 0.85:
            return False
    except ValueError:
        return False
    if any(not str(row.get(field, "")).strip() for field in REQUIRED_PROVENANCE_FIELDS):
        return False
    haystack = " ".join(str(value) for value in row.values()).lower()
    return not any(marker.lower() in haystack for marker in FIXTURE_MARKERS)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _candidate_fieldnames(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    for path in sorted(directory.rglob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as file:
            fieldnames = csv.DictReader(file).fieldnames
        if fieldnames:
            return list(fieldnames)
    return []


def _write_csv(
    path: Path,
    rows: list[dict[str, str]],
    *,
    fieldnames: list[str] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved_fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in resolved_fieldnames:
                resolved_fieldnames.append(key)
    for key in fieldnames or []:
        if key not in resolved_fieldnames:
            resolved_fieldnames.append(key)
    if not resolved_fieldnames:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=resolved_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
