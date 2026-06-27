from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_rank_segment_adapter import HubeiRankSegmentAdapter


def test_hubei_rank_segment_adapter_parses_uploaded_csv(tmp_path: Path) -> None:
    path = tmp_path / "rank-segments.csv"
    path.write_text(
        "year,province,category,first_subject,score,same_score_count,cumulative_rank,"
        "rank_start,rank_end,source_id,source_url,confidence_score\n"
        "2026,湖北,普通类,physics,620,352,11200,8401,11200,admin-rank,"
        "https://www.hbksw.com/info/38/1746.html,0.96\n",
        encoding="utf-8",
    )

    result = HubeiRankSegmentAdapter().parse_uploaded_csv(path)

    assert result.summary == {
        "parser_version": "hubei-rank-segment-v1",
        "candidate_count": 1,
        "valid_count": 1,
        "invalid_count": 0,
        "low_confidence_count": 0,
    }
    assert result.segments[0].score == 620
    assert result.segments[0].rank_start == 8401
    assert result.segments[0].rank_end == 11200


def test_hubei_rank_segment_adapter_reports_invalid_rows(tmp_path: Path) -> None:
    path = tmp_path / "bad-rank-segments.csv"
    path.write_text(
        "year,province,category,first_subject,score,same_score_count,cumulative_rank,"
        "rank_start,rank_end,source_id,source_url,confidence_score\n"
        "2027,湖北,普通类,physics,620,352,11200,11200,8401,admin-rank,,0.70\n",
        encoding="utf-8",
    )

    result = HubeiRankSegmentAdapter().parse_uploaded_csv(path)

    assert result.summary["candidate_count"] == 1
    assert result.summary["valid_count"] == 0
    assert result.summary["invalid_count"] == 1
    assert result.summary["low_confidence_count"] == 1
    assert result.row_errors
