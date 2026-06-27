from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.recommender.models import RankSegment


@dataclass(frozen=True)
class RankSegmentParseResult:
    segments: list[RankSegment]
    row_errors: list[str]
    low_confidence_count: int
    parser_version: str

    @property
    def summary(self) -> dict[str, object]:
        return {
            "parser_version": self.parser_version,
            "candidate_count": len(self.segments) + len(self.row_errors),
            "valid_count": len(self.segments),
            "invalid_count": len(self.row_errors),
            "low_confidence_count": self.low_confidence_count,
        }


class HubeiRankSegmentAdapter:
    parser_version = "hubei-rank-segment-v1"

    def parse_fixture_csv(self, fixture_dir: str | Path) -> list[RankSegment]:
        return StaticCsvHubeiFixtureAdapter(fixture_dir).load_rank_segments()

    def parse_uploaded_csv(self, path: str | Path) -> RankSegmentParseResult:
        segments: list[RankSegment] = []
        row_errors: list[str] = []
        low_confidence_count = 0
        with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
            for index, row in enumerate(csv.DictReader(file), start=2):
                try:
                    segment = self._row_to_segment(row)
                except (KeyError, TypeError, ValueError) as exc:
                    row_errors.append(f"row {index}: {exc}")
                    continue
                errors = self.validate_segment(segment)
                if segment.confidence_score < 0.85:
                    low_confidence_count += 1
                if errors:
                    row_errors.append(f"row {index}: {'; '.join(errors)}")
                    continue
                segments.append(segment)
        return RankSegmentParseResult(
            segments=segments,
            row_errors=row_errors,
            low_confidence_count=low_confidence_count,
            parser_version=self.parser_version,
        )

    def validate_segment(self, segment: RankSegment) -> list[str]:
        errors: list[str] = []
        if segment.year not in {2023, 2024, 2025, 2026}:
            errors.append("year must be within 2023-2026")
        if segment.province != "湖北":
            errors.append("province must be 湖北")
        if segment.first_subject not in {"physics", "history"}:
            errors.append("first_subject must be physics or history")
        if not 0 <= segment.score <= 750:
            errors.append("score must be within 0-750")
        if segment.same_score_count < 0 or segment.cumulative_rank <= 0:
            errors.append("rank counts must be non-negative and cumulative_rank positive")
        if segment.rank_start <= 0 or segment.rank_end < segment.rank_start:
            errors.append("rank range is invalid")
        if not segment.source_url:
            errors.append("source_url is required")
        if segment.confidence_score < 0.85:
            errors.append("confidence_score below production threshold")
        return errors

    def _row_to_segment(self, row: dict[str, Any]) -> RankSegment:
        return RankSegment(
            year=int(row["year"]),
            province=str(row["province"]),
            category=str(row["category"]),
            first_subject=str(row["first_subject"]),  # type: ignore[arg-type]
            score=int(row["score"]),
            same_score_count=int(row["same_score_count"]),
            cumulative_rank=int(row["cumulative_rank"]),
            rank_start=int(row["rank_start"]),
            rank_end=int(row["rank_end"]),
            source_id=str(row["source_id"]),
            source_url=str(row["source_url"]),
            confidence_score=float(row["confidence_score"]),
        )
