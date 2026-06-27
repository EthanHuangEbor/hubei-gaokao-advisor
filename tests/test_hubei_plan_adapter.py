from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_plan_adapter import HubeiPlanAdapter


def test_hubei_plan_adapter_parses_uploaded_csv(tmp_path: Path) -> None:
    path = tmp_path / "plan.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,major_code,major_name,"
        "plan_seats,tuition,schooling_years,campus,is_sino_foreign,is_private,notes,"
        "physical_limit_note,single_subject_limit_note,source_id,source_url,confidence_score\n"
        "2026,湖北,本科普通批,普通类,physics,化学,HBA999,湖北上传样例大学,"
        "HBA999-P01,物理上传01组,080901,计算机科学与技术,12,5800,4年,武汉,否,否,"
        "管理员上传样例,,,admin-upload,manual-upload://plan.csv,0.96\n",
        encoding="utf-8",
    )

    result = HubeiPlanAdapter().parse_uploaded_csv(path)

    assert result.summary == {
        "parser_version": "hubei-plan-v1",
        "candidate_count": 1,
        "valid_count": 1,
        "invalid_count": 0,
        "low_confidence_count": 0,
    }
    assert result.plans[0].major_group_code == "HBA999-P01"
    assert result.plans[0].major_name == "计算机科学与技术"


def test_hubei_plan_adapter_reports_invalid_rows(tmp_path: Path) -> None:
    path = tmp_path / "bad-plan.csv"
    path.write_text(
        "year,province,batch,category,first_subject,second_subject_requirement,"
        "university_code,university_name,major_group_code,major_group_name,major_code,major_name,"
        "plan_seats,tuition,schooling_years,campus,is_sino_foreign,is_private,notes,"
        "physical_limit_note,single_subject_limit_note,source_id,source_url,confidence_score\n"
        "2026,湖北,本科普通批,普通类,physics,化学,HBA999,湖北上传样例大学,"
        ",物理上传01组,080901,,0,5800,4年,武汉,否,否,管理员上传样例,,,admin-upload,,0.70\n",
        encoding="utf-8",
    )

    result = HubeiPlanAdapter().parse_uploaded_csv(path)

    assert result.summary["candidate_count"] == 1
    assert result.summary["valid_count"] == 0
    assert result.summary["invalid_count"] == 1
    assert result.summary["low_confidence_count"] == 1
    assert result.row_errors
