from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class SourceAuditStamp:
    source_url: str
    source_name: str
    source_type: str
    fetched_at: str
    published_at: str | None
    parser_version: str
    confidence_score: float
    license_note: str
    review_status: str


def make_source_stamp(
    *,
    source_url: str,
    source_name: str,
    source_type: str,
    parser_version: str,
    confidence_score: float,
    license_note: str = "public official or quasi-official source; verify before production use",
    review_status: str = "pending",
    published_at: str | None = None,
) -> SourceAuditStamp:
    return SourceAuditStamp(
        source_url=source_url,
        source_name=source_name,
        source_type=source_type,
        fetched_at=datetime.now(UTC).isoformat(),
        published_at=published_at,
        parser_version=parser_version,
        confidence_score=confidence_score,
        license_note=license_note,
        review_status=review_status,
    )

