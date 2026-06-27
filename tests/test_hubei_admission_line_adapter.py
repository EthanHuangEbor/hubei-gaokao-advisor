from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_admission_line_adapter import HubeiAdmissionLineAdapter


def test_hubei_admission_line_adapter_parses_uploaded_csv(tmp_path: Path) -> None:
    path = tmp_path / "records.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,admission_category,"
        "min_score,min_rank,plan_seats,source_id,source_url,confidence_score,parser_version\n"
        "2025,湖北,本科普通批,普通类,physics,化学,HBA999,湖北上传样例大学,"
        "HBA999-P01,物理上传01组,平行志愿,612,26000,18,admin-lines,"
        "https://www.hbksw.com/info/38/1771.html,0.96,admin-upload\n",
        encoding="utf-8",
    )

    result = HubeiAdmissionLineAdapter().parse_uploaded_csv(path)

    assert result.summary == {
        "parser_version": "hubei-admission-line-v1",
        "candidate_count": 1,
        "valid_count": 1,
        "invalid_count": 0,
        "low_confidence_count": 0,
    }
    assert result.records[0].major_group_code == "HBA999-P01"
    assert result.records[0].min_rank == 26000


def test_hubei_admission_line_adapter_reports_invalid_rows(tmp_path: Path) -> None:
    path = tmp_path / "bad-records.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,admission_category,"
        "min_score,min_rank,plan_seats,source_id,source_url,confidence_score,parser_version\n"
        "2026,湖北,本科普通批,普通类,physics,化学,HBA999,湖北上传样例大学,"
        ",物理上传01组,平行志愿,900,0,18,admin-lines,,0.70,admin-upload\n",
        encoding="utf-8",
    )

    result = HubeiAdmissionLineAdapter().parse_uploaded_csv(path)

    assert result.summary["candidate_count"] == 1
    assert result.summary["valid_count"] == 0
    assert result.summary["invalid_count"] == 1
    assert result.summary["low_confidence_count"] == 1
    assert result.row_errors
