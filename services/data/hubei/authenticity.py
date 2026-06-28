from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DatasetKind = Literal["missing", "fixture_seed", "real_curated", "mixed", "incomplete"]

REQUIRED_FILES = {
    "admission_records": "admission_records_2023_2025.csv",
    "rank_segments": "rank_segments_2023_2026.csv",
    "admission_plans": "admission_plans_2026.csv",
}
FIXTURE_MARKERS = (
    "fixture",
    "湖北样例",
    "样例",
    "curated-fixture-seed",
    "static_csv_seed",
    "鏍蜂緥",
    "婀栧寳鏍蜂緥",
)


@dataclass(frozen=True)
class DatasetAuthenticity:
    dataset_kind: DatasetKind
    curated_ready: bool
    real_curated_ready: bool
    contains_fixture_rows: bool
    fixture_marker_count: int
    approved_row_count: int
    pending_row_count: int
    missing_files: list[str]
    warnings: list[str]
    curated_dir: str
    required_files: dict[str, bool]
    approved_rows: dict[str, int]
    fixture_markers: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_kind": self.dataset_kind,
            "curated_ready": self.curated_ready,
            "real_curated_ready": self.real_curated_ready,
            "contains_fixture_rows": self.contains_fixture_rows,
            "fixture_marker_count": self.fixture_marker_count,
            "approved_row_count": self.approved_row_count,
            "pending_row_count": self.pending_row_count,
            "missing_files": self.missing_files,
            "warnings": self.warnings,
            "curated_dir": self.curated_dir,
            "required_files": self.required_files,
            "approved_rows": self.approved_rows,
            "fixture_markers": self.fixture_markers,
            "strict_real_data_required": strict_real_data_required(),
            "fixture_data_allowed": fixture_data_allowed(),
        }


def inspect_curated_dir(curated_dir: str | Path) -> DatasetAuthenticity:
    path = Path(curated_dir)
    required_files = {name: (path / filename).exists() for name, filename in REQUIRED_FILES.items()}
    missing_files = [filename for filename in REQUIRED_FILES.values() if not (path / filename).exists()]
    if not path.exists() or missing_files:
        return DatasetAuthenticity(
            dataset_kind="missing",
            curated_ready=False,
            real_curated_ready=False,
            contains_fixture_rows=False,
            fixture_marker_count=0,
            approved_row_count=0,
            pending_row_count=0,
            missing_files=missing_files or list(REQUIRED_FILES.values()),
            warnings=["curated CSV files are missing"],
            curated_dir=str(path),
            required_files=required_files,
            approved_rows={},
            fixture_markers=[],
        )

    approved_rows: dict[str, int] = {}
    approved_total = 0
    pending_total = 0
    fixture_marker_count = 0
    fixture_markers: set[str] = set()
    warnings: list[str] = []

    for name, filename in REQUIRED_FILES.items():
        rows = _read_rows(path / filename)
        approved = 0
        for row in rows:
            status = row.get("review_status", "").strip().lower()
            if status == "approved":
                approved += 1
                approved_total += 1
            elif status == "pending":
                pending_total += 1
            markers = _fixture_markers_in_row(row)
            if markers:
                fixture_marker_count += 1
                fixture_markers.update(markers)
        approved_rows[name] = approved
        if approved == 0:
            warnings.append(f"{name} has no approved rows")

    contains_fixture = fixture_marker_count > 0
    if contains_fixture and approved_total:
        dataset_kind: DatasetKind = "fixture_seed"
        warnings.append("approved rows contain fixture markers")
    elif contains_fixture:
        dataset_kind = "mixed"
        warnings.append("candidate rows contain fixture markers")
    elif warnings:
        dataset_kind = "incomplete"
    else:
        dataset_kind = "real_curated"

    return DatasetAuthenticity(
        dataset_kind=dataset_kind,
        curated_ready=True,
        real_curated_ready=dataset_kind == "real_curated" and approved_total > 0,
        contains_fixture_rows=contains_fixture,
        fixture_marker_count=fixture_marker_count,
        approved_row_count=approved_total,
        pending_row_count=pending_total,
        missing_files=[],
        warnings=warnings,
        curated_dir=str(path),
        required_files=required_files,
        approved_rows=approved_rows,
        fixture_markers=sorted(fixture_markers),
    )


def fixture_data_allowed() -> bool:
    explicit = _truthy(os.getenv("ALLOW_FIXTURE_DATA"))
    if explicit is not None:
        return explicit
    return os.getenv("APP_ENV", "development").strip().lower() != "production" and not strict_real_data_required()


def strict_real_data_required() -> bool:
    return _truthy(os.getenv("REQUIRE_REAL_DATA")) is True or os.getenv(
        "APP_ENV", "development"
    ).strip().lower() == "production"


def require_runtime_dataset(
    status: DatasetAuthenticity | str | Path,
    *,
    app_env: str | None = None,
    allow_fixture_data: bool | None = None,
) -> DatasetAuthenticity:
    authenticity = inspect_curated_dir(status) if isinstance(status, (str, Path)) else status
    env = app_env or os.getenv("APP_ENV", "development")
    if env is None:
        env = "development"
    allow_fixture = fixture_data_allowed() if allow_fixture_data is None else allow_fixture_data
    strict = strict_real_data_required() or env.strip().lower() == "production"
    if authenticity.real_curated_ready:
        return authenticity
    if strict or not allow_fixture:
        raise RuntimeError("real curated Hubei data is required before recommendations can run")
    return authenticity


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _fixture_markers_in_row(row: dict[str, str]) -> list[str]:
    haystack = " ".join(str(value) for value in row.values()).lower()
    return [marker for marker in FIXTURE_MARKERS if marker.lower() in haystack]


def _truthy(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return False