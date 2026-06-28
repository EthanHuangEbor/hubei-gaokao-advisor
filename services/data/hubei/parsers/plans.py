from __future__ import annotations

from pathlib import Path

from services.data.hubei.parsers import append_metadata, read_csv_rows
from services.data.hubei.source_registry import HubeiSource

PARSER_VERSION = "hubei-plans-csv-v0.2"


def parse_csv(
    path: str | Path,
    *,
    source: HubeiSource,
    raw_document_sha256: str,
) -> list[dict[str, str]]:
    return [
        append_metadata(
            row,
            source=source,
            raw_document_sha256=raw_document_sha256,
            parser_version=PARSER_VERSION,
        )
        for row in read_csv_rows(path)
    ]
