from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _rank_row(**overrides: str) -> dict[str, str]:
    row = {
        "year": "2026",
        "province": "湖北",
        "category": "普通类",
        "first_subject": "physics",
        "score": "650",
        "same_score_count": "100",
        "cumulative_rank": "1000",
        "rank_start": "901",
        "rank_end": "1000",
        "source_id": "official-rank",
        "source_url": "https://www.hbksw.com/rank.csv",
        "source_type": "official",
        "raw_document_sha256": "abc",
        "parser_name": "rank_segments.csv",
        "parser_version": "hubei-rank-segments-csv-v0.2",
        "parse_confidence": "0.95",
        "confidence_score": "0.95",
        "license_note": "public",
        "review_status": "approved",
        "reviewer": "reviewer-a",
    }
    row.update(overrides)
    return row


def _line_row(**overrides: str) -> dict[str, str]:
    row = {
        "year": "2025",
        "province": "湖北",
        "batch": "本科普通批",
        "category": "普通类",
        "first_subject": "physics",
        "second_subject_requirement": "化学",
        "university_code": "HBA001",
        "university_name": "湖北真实大学",
        "major_group_code": "HBA001-P01",
        "major_group_name": "物理01组",
        "admission_category": "平行志愿",
        "min_score": "612",
        "min_rank": "26000",
        "plan_seats": "18",
        "source_id": "official-line",
        "source_url": "https://www.hbksw.com/line.csv",
        "source_type": "official",
        "raw_document_sha256": "def",
        "parser_name": "admission_lines.csv",
        "parser_version": "hubei-admission-lines-csv-v0.2",
        "parse_confidence": "0.95",
        "confidence_score": "0.95",
        "license_note": "public",
        "review_status": "approved",
        "reviewer": "reviewer-a",
    }
    row.update(overrides)
    return row


def test_quality_checks_candidate_files_for_fixture_metadata_and_rank_monotonicity(
    tmp_path: Path,
) -> None:
    from services.data.hubei.quality import run_quality_checks

    candidate_root = tmp_path / "data" / "candidate" / "hubei"
    _write_csv(
        candidate_root / "rank_segments" / "candidate_rank_segments_2026.csv",
        [
            _rank_row(score="650", cumulative_rank="1000"),
            _rank_row(score="640", cumulative_rank="900", source_id="fixture-rank"),
        ],
    )
    _write_csv(
        candidate_root / "admission_lines" / "candidate_admission_records_2025.csv",
        [_line_row(raw_document_sha256="")],
    )

    report = run_quality_checks(candidate_root)

    assert report.has_errors is True
    assert any("fixture marker" in error for error in report.errors)
    assert any("missing provenance field raw_document_sha256" in error for error in report.errors)
    assert any("cumulative_rank decreased" in error for error in report.errors)


def test_promote_candidates_only_writes_approved_confident_non_fixture_rows(tmp_path: Path) -> None:
    from services.data.hubei.promote import promote_candidates

    candidate_root = tmp_path / "data" / "candidate" / "hubei"
    curated_dir = tmp_path / "data" / "curated" / "hubei"
    _write_csv(
        candidate_root / "admission_lines" / "candidate_admission_records_2025.csv",
        [
            _line_row(university_code="APPROVED"),
            _line_row(university_code="PENDING", review_status="pending"),
            _line_row(university_code="LOWCONF", confidence_score="0.84"),
        ],
    )
    _write_csv(
        candidate_root / "rank_segments" / "candidate_rank_segments_2026.csv",
        [_rank_row()],
    )

    result = promote_candidates(candidate_root, curated_dir)

    assert result.promoted_counts["admission_records"] == 1
    with (curated_dir / "admission_records_2023_2025.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))
    assert [row["university_code"] for row in rows] == ["APPROVED"]


def test_promote_candidates_overwrites_stale_output_when_zero_rows_are_eligible(
    tmp_path: Path,
) -> None:
    from services.data.hubei.promote import promote_candidates

    candidate_root = tmp_path / "data" / "candidate" / "hubei"
    curated_dir = tmp_path / "data" / "curated" / "hubei"
    output_path = curated_dir / "admission_records_2023_2025.csv"
    _write_csv(
        candidate_root / "admission_lines" / "candidate_admission_records_2025.csv",
        [_line_row(university_code="PENDING", review_status="pending")],
    )
    _write_csv(output_path, [_line_row(university_code="STALE")])

    result = promote_candidates(candidate_root, curated_dir)

    assert result.promoted_counts["admission_records"] == 0
    assert "STALE" not in output_path.read_text(encoding="utf-8-sig")
    with output_path.open(encoding="utf-8-sig", newline="") as file:
        assert list(csv.DictReader(file)) == []


def test_promote_candidates_blocks_when_quality_errors_exist(tmp_path: Path) -> None:
    from services.data.hubei.promote import promote_candidates

    candidate_root = tmp_path / "data" / "candidate" / "hubei"
    _write_csv(
        candidate_root / "admission_lines" / "candidate_admission_records_2025.csv",
        [_line_row(source_id="fixture-line")],
    )

    with pytest.raises(RuntimeError, match="quality errors"):
        promote_candidates(candidate_root, tmp_path / "curated")


def test_build_dataset_parses_real_raw_csvs_but_preserves_fixture_seed_promotion(
    tmp_path: Path,
) -> None:
    from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
    from services.data.hubei.build_dataset import build_dataset

    manual_note = (
        tmp_path
        / "data"
        / "candidate"
        / "hubei_real"
        / "rank_segments"
        / "reviewer_notes.txt"
    )
    manual_note.parent.mkdir(parents=True)
    manual_note.write_text("keep reviewer notes", encoding="utf-8")
    raw_rank = tmp_path / "data" / "raw" / "hubei" / "rank_segments"
    raw_rank.mkdir(parents=True)
    raw_csv = raw_rank / "official_rank.csv"
    raw_csv.write_text(
        "year,province,category,first_subject,score,same_score_count,cumulative_rank,"
        "rank_start,rank_end,source_id,source_url,source_type,raw_document_sha256,"
        "parser_name,parser_version,parse_confidence,confidence_score,license_note,"
        "review_status,reviewer\n"
        "2026,???,?????,physics,650,100,1000,901,1000,official-rank,"
        "https://www.hbksw.com/rank.csv,official,abc,rank_segments.csv,"
        "hubei-rank-segments-csv-v0.2,0.95,0.95,public,approved,reviewer-a\n",
        encoding="utf-8",
    )

    result = build_dataset(
        root=Path(__file__).resolve().parents[1],
        output_root=tmp_path,
        download=False,
        parse=True,
        quality=True,
        promote=True,
    )

    curated_rank = tmp_path / "data" / "curated" / "hubei" / "rank_segments_2023_2026.csv"
    with curated_rank.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    fixture_dataset = StaticCsvHubeiFixtureAdapter(
        Path(__file__).resolve().parents[1] / "data" / "fixtures" / "hubei"
    ).load()
    report = json.loads(
        (tmp_path / "data" / "quality" / "hubei" / "data_build_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert manual_note.read_text(encoding="utf-8") == "keep reviewer notes"
    assert len(rows) == len(fixture_dataset.rank_segments)
    assert not any(row["source_id"] == "official-rank" for row in rows)
    assert result.curated_rank_segments == len(rows)
    assert report["real_promotion_status"] == "skipped_incomplete"
    assert report["real_promotable_counts"]["rank_segments"] == 1
