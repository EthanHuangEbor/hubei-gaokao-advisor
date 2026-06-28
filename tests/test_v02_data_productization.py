from __future__ import annotations

import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_source_registry_loads_official_hubei_sources() -> None:
    from services.data.hubei.source_registry import load_source_registry

    registry = load_source_registry(ROOT / "data" / "source_registry" / "hubei_sources.yaml")
    urls = {source.source_url for source in registry.sources}

    assert "https://www.hbksw.com/info/38/1771.html" in urls
    assert "https://www.hbksw.com/info/38/1746.html" in urls
    assert "https://www.hbksw.com/info/38/2289.html" in urls
    assert "https://platform.minimax.io/docs/api-reference/responses-create" in urls
    assert {source.data_type for source in registry.sources} >= {
        "admission_lines",
        "rank_segments",
        "policy",
        "platform",
        "llm_docs",
    }


def test_build_dataset_promotes_curated_csvs_and_quality_report(tmp_path: Path) -> None:
    from services.data.hubei.build_dataset import build_dataset

    result = build_dataset(
        root=ROOT,
        output_root=tmp_path,
        download=False,
        parse=True,
        quality=True,
        promote=True,
    )

    curated_dir = tmp_path / "data" / "curated" / "hubei"
    quality_dir = tmp_path / "data" / "quality" / "hubei"

    assert result.curated_records > 0
    assert result.curated_rank_segments > 0
    assert result.curated_plans > 0
    assert (curated_dir / "admission_records_2023_2025.csv").exists()
    assert (curated_dir / "rank_segments_2023_2026.csv").exists()
    assert (curated_dir / "admission_plans_2026.csv").exists()
    assert (quality_dir / "data_build_report.md").exists()

    with (curated_dir / "admission_records_2023_2025.csv").open(encoding="utf-8-sig") as file:
        first_row = next(csv.DictReader(file))
    assert first_row["source_url"]
    assert first_row["raw_document_sha256"]
    assert first_row["parser_version"]
    assert first_row["review_status"] == "approved"


def test_production_mode_rejects_fixture_curated_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.data.hubei.build_dataset import build_dataset
    from services.data.hubei.curated_loader import load_curated_dataset

    build_dataset(
        root=ROOT,
        output_root=tmp_path,
        download=False,
        parse=True,
        quality=True,
        promote=True,
    )
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="fixture"):
        load_curated_dataset(tmp_path / "data" / "curated" / "hubei")


def test_repository_uses_empty_dataset_for_fixture_curated_data_in_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from apps.api.app.repository import Repository
    from services.data.hubei.build_dataset import build_dataset

    build_dataset(
        root=ROOT,
        output_root=tmp_path,
        download=False,
        parse=True,
        quality=True,
        promote=True,
    )
    monkeypatch.setenv("APP_ENV", "production")

    repository = Repository(tmp_path)

    assert repository.dataset_status.curated_ready is True
    assert repository.dataset_status.real_curated_ready is False
    assert repository.dataset.admission_records == []
    assert repository.dataset.admission_plans == []
    assert repository.dataset.rank_segments == []


def test_recommendation_trace_and_csv_export(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)

    run_response = client.post(
        "/api/recommendations/run",
        json={
            "first_subject": "physics",
            "second_subjects": ["chemistry", "biology"],
            "score": 610,
            "rank": 26000,
            "accept_private_college": True,
            "accept_sino_foreign": True,
        },
    )
    assert run_response.status_code == 200
    run = run_response.json()
    assert run["items"][0]["position"] == 1
    assert run["items"][0]["plan_status"] in {"ready", "missing_current_plan"}
    assert "main_reasons" in run["items"][0]
    assert "main_warnings" in run["items"][0]

    trace_response = client.get(f"/api/recommendations/{run['run_id']}/trace")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert trace["input_normalized"]["province"] == "湖北"
    assert trace["pool_counts"]["raw_pool"] >= trace["pool_counts"]["after_subject_filter"] > 0
    assert trace["tier_counts"]
    assert len(trace["final_plan"]) == len(run["items"])

    export_response = client.get(f"/api/recommendations/{run['run_id']}/export.csv")
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")
    csv_text = export_response.content.decode("utf-8-sig")
    assert "position,tier,university_code" in csv_text
    assert run["items"][0]["major_group_code"] in csv_text


def test_missing_current_plan_mode_uses_historical_data(monkeypatch: pytest.MonkeyPatch) -> None:
    from apps.api.app import main as api_main
    from services.crawler.adapters.static_csv_adapter import FixtureDataset

    original_dataset = api_main.repo.dataset
    api_main.repo.dataset = FixtureDataset(
        admission_records=original_dataset.admission_records,
        admission_plans=[],
        rank_segments=original_dataset.rank_segments,
        universities=original_dataset.universities,
        majors=original_dataset.majors,
        major_groups=original_dataset.major_groups,
    )
    try:
        client = TestClient(api_main.app)
        response = client.post(
            "/api/recommendations/run",
            json={
                "first_subject": "physics",
                "second_subjects": ["chemistry"],
                "score": 610,
                "rank": 26000,
            },
        )
    finally:
        api_main.repo.dataset = original_dataset

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    assert {item["plan_status"] for item in payload["items"]} == {"missing_current_plan"}
    assert all(item["plan_change_ratio"] is None for item in payload["items"])
    assert all(item["included_majors"] == ["待导入招生计划"] for item in payload["items"])


def test_local_dev_cors_allows_web_port_3001() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/recommendations/run",
        headers={
            "Origin": "http://127.0.0.1:3001",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3001"


def _write_curated_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_production_mode_rejects_fixture_marker_in_rank_segments_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from services.data.hubei.curated_loader import load_curated_dataset

    curated = tmp_path / "data" / "curated" / "hubei"
    _write_curated_csv(
        curated / "admission_records_2023_2025.csv",
        [
            {
                "year": "2025",
                "province": "Hubei",
                "batch": "undergraduate",
                "category": "general",
                "first_subject": "physics",
                "second_subject_requirement": "none",
                "university_code": "HBU001",
                "university_name": "Hubei Real University",
                "major_group_code": "HBU001-P01",
                "major_group_name": "Physics Group",
                "admission_category": "general",
                "min_score": "610",
                "min_rank": "23950",
                "plan_seats": "12",
                "source_id": "official-line-2025",
                "source_url": "https://example.edu/official-line",
                "confidence_score": "0.95",
                "parse_confidence": "0.95",
                "parser_version": "curated-v0.2",
                "review_status": "approved",
            }
        ],
    )
    _write_curated_csv(
        curated / "admission_plans_2026.csv",
        [
            {
                "year": "2026",
                "province": "Hubei",
                "batch": "undergraduate",
                "category": "general",
                "first_subject": "physics",
                "second_subject_requirement": "none",
                "university_code": "HBU001",
                "university_name": "Hubei Real University",
                "major_group_code": "HBU001-P01",
                "major_group_name": "Physics Group",
                "major_code": "080901",
                "major_name": "Computer Science",
                "plan_seats": "20",
                "tuition": "5000",
                "schooling_years": "4",
                "campus": "Main",
                "is_sino_foreign": "false",
                "is_private": "false",
                "notes": "",
                "physical_limit_note": "",
                "single_subject_limit_note": "",
                "source_id": "official-plan-2026",
                "source_url": "https://example.edu/official-plan",
                "confidence_score": "0.95",
                "parse_confidence": "0.95",
                "review_status": "approved",
            }
        ],
    )
    _write_curated_csv(
        curated / "rank_segments_2023_2026.csv",
        [
            {
                "year": "2026",
                "province": "Hubei",
                "category": "general",
                "first_subject": "physics",
                "score": "610",
                "same_score_count": "500",
                "cumulative_rank": "24000",
                "rank_start": "23501",
                "rank_end": "24000",
                "source_id": "official-rank-2026",
                "source_url": "manual-upload://fixture-rank",
                "confidence_score": "0.95",
                "parse_confidence": "0.95",
                "review_status": "approved",
            }
        ],
    )
    monkeypatch.setenv("APP_ENV", "production")

    with pytest.raises(ValueError, match="fixture"):
        load_curated_dataset(curated)
