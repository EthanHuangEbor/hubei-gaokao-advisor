from __future__ import annotations

import csv
from pathlib import Path

from services.data.hubei.source_registry import HubeiSource


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def append_metadata(
    row: dict[str, str],
    *,
    source: HubeiSource,
    raw_document_sha256: str,
    parser_version: str,
    confidence: str = "0.90",
) -> dict[str, str]:
    output = {key: value or "" for key, value in row.items()}
    output.update(
        {
            "source_id": source.source_id,
            "source_url": source.source_url,
            "source_type": source.source_type,
            "raw_document_sha256": raw_document_sha256,
            "parser_name": source.parser,
            "parser_version": parser_version,
            "parse_confidence": confidence,
            "confidence_score": confidence,
            "license_note": source.license_note,
            "review_status": "pending",
            "reviewer": "",
        }
    )
    return output
