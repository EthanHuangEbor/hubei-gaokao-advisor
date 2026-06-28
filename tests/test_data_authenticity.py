from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from services.data.hubei.authenticity import inspect_curated_dir, require_runtime_dataset

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_authenticity_detects_fixture_seed(tmp_path):
    curated = tmp_path / "data" / "curated" / "hubei"
    _write_csv(
        curated / "admission_records_2023_2025.csv",
        [
            {
                "year": "2025",
                "province": "Hubei",
                "batch": "undergraduate",
                "category": "general",
                "first_subject": "physics",
                "university_code": "HBA013",
                "university_name": "Hubei fixture university 013",
                "major_group_code": "HBA013-P13",
                "major_group_name": "group-13",
                "min_score": "610",
                "min_rank": "23950",
                "source_id": "fixture-line-2025",
                "source_url": "manual-upload://fixture",
                "source_type": "fixture_seed",
                "raw_document_sha256": "abc",
                "parser_name": "static_csv_seed",
                "parser_version": "curated-fixture-seed-v0.2",
                "confidence_score": "0.95",
                "parse_confidence": "0.95",
                "license_note": "fixture seed 湖北样例 样例 鏍蜂緥 婀栧寳鏍蜂緥",
                "review_status": "approved",
                "reviewer": "system_seed",
            }
        ],
    )
    _write_csv(curated / "rank_segments_2023_2026.csv", [{"review_status": "approved", "source_id": "official-rank"}])
    _write_csv(curated / "admission_plans_2026.csv", [{"review_status": "approved", "source_id": "official-plan"}])

    status = inspect_curated_dir(curated)

    assert status.dataset_kind == "fixture_seed"
    assert status.contains_fixture_rows is True
    assert status.fixture_marker_count == 1
    assert status.real_curated_ready is False
    assert {"fixture", "湖北样例", "样例", "curated-fixture-seed", "static_csv_seed", "鏍蜂緥", "婀栧寳鏍蜂緥"}.issubset(set(status.fixture_markers))


def test_strict_runtime_rejects_fixture_seed(tmp_path):
    status = inspect_curated_dir(tmp_path / "missing")

    with pytest.raises(RuntimeError, match="real curated Hubei data is required"):
        require_runtime_dataset(status, app_env="production", allow_fixture_data=False)

def test_repository_strict_mode_returns_empty_dataset_when_curated_csvs_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.api.app.repository import Repository

    fixture_dir = tmp_path / "data" / "fixtures" / "hubei"
    shutil.copytree(ROOT / "data" / "fixtures" / "hubei", fixture_dir)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("REQUIRE_REAL_DATA", "true")

    repository = Repository(tmp_path)

    assert repository.dataset_status.real_curated_ready is False
    assert repository.dataset.admission_records == []
    assert repository.dataset.admission_plans == []
    assert repository.dataset.rank_segments == []
