from __future__ import annotations

from pathlib import Path

from services.data.hubei.source_registry import HubeiSource


def _source(data_type: str) -> HubeiSource:
    return HubeiSource(
        source_id=f"official_{data_type}",
        title=f"Official {data_type}",
        source_url=f"https://www.hbksw.com/{data_type}.csv",
        source_type="official",
        owner="Hubei",
        data_type=data_type,
        years="2026",
        status="verified",
        license_note="public",
        parser=f"{data_type}.csv",
        raw_subdir=data_type,
        allow_network_download=True,
        requires_manual_review=True,
    )


def test_rank_segment_csv_parser_outputs_pending_candidate_metadata(tmp_path: Path) -> None:
    from services.data.hubei.parsers.rank_segments import parse_csv

    path = tmp_path / "rank.csv"
    path.write_text(
        "year,province,category,first_subject,score,same_score_count,cumulative_rank,"
        "rank_start,rank_end\n"
        "2026,湖北,普通类,physics,650,100,1000,901,1000\n",
        encoding="utf-8",
    )

    rows = parse_csv(path, source=_source("rank_segments"), raw_document_sha256="abc123")

    assert rows == [
        {
            "year": "2026",
            "province": "湖北",
            "category": "普通类",
            "first_subject": "physics",
            "score": "650",
            "same_score_count": "100",
            "cumulative_rank": "1000",
            "rank_start": "901",
            "rank_end": "1000",
            "source_id": "official_rank_segments",
            "source_url": "https://www.hbksw.com/rank_segments.csv",
            "source_type": "official",
            "raw_document_sha256": "abc123",
            "parser_name": "rank_segments.csv",
            "parser_version": "hubei-rank-segments-csv-v0.2",
            "parse_confidence": "0.90",
            "confidence_score": "0.90",
            "license_note": "public",
            "review_status": "pending",
            "reviewer": "",
        }
    ]


def test_admission_line_csv_parser_outputs_pending_candidate_metadata(tmp_path: Path) -> None:
    from services.data.hubei.parsers.admission_lines import parse_csv

    path = tmp_path / "lines.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,admission_category,"
        "min_score,min_rank,plan_seats\n"
        "2025,湖北,本科普通批,普通类,physics,化学,HBA001,湖北真实大学,"
        "HBA001-P01,物理01组,平行志愿,612,26000,18\n",
        encoding="utf-8",
    )

    row = parse_csv(path, source=_source("admission_lines"), raw_document_sha256="def456")[0]

    assert row["university_code"] == "HBA001"
    assert row["min_rank"] == "26000"
    assert row["source_id"] == "official_admission_lines"
    assert row["parser_version"] == "hubei-admission-lines-csv-v0.2"
    assert row["review_status"] == "pending"


def test_plan_csv_parser_wraps_uploaded_csv_shape_as_pending_candidates(tmp_path: Path) -> None:
    from services.data.hubei.parsers.plans import parse_csv

    path = tmp_path / "plans.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,major_code,major_name,"
        "plan_seats,tuition,schooling_years,campus,is_sino_foreign,is_private,notes,"
        "physical_limit_note,single_subject_limit_note\n"
        "2026,湖北,本科普通批,普通类,physics,化学,HBA001,湖北真实大学,"
        "HBA001-P01,物理01组,080901,计算机科学与技术,12,5800,4年,武汉,否,否,"
        "公开计划,,\n",
        encoding="utf-8",
    )

    row = parse_csv(path, source=_source("plans"), raw_document_sha256="fedcba")[0]

    assert row["major_code"] == "080901"
    assert row["source_type"] == "official"
    assert row["parser_name"] == "plans.csv"
    assert row["parser_version"] == "hubei-plans-csv-v0.2"
    assert row["review_status"] == "pending"
