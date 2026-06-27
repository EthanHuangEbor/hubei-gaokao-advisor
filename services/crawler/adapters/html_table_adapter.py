from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedHtmlTable:
    rows: list[dict[str, str]]
    confidence_score: float
    parser_version: str


class HtmlTableAdapter:
    parser_version = "html-table-v1"

    def parse(self, html: str) -> ParsedHtmlTable:
        """Parse public HTML tables using pandas when available.

        Falls back to a low-confidence empty result instead of guessing table structure.
        """

        try:
            import pandas as pd

            tables = pd.read_html(html)
        except Exception:
            return ParsedHtmlTable(rows=[], confidence_score=0.0, parser_version=self.parser_version)
        if not tables:
            return ParsedHtmlTable(rows=[], confidence_score=0.0, parser_version=self.parser_version)
        rows = tables[0].fillna("").astype(str).to_dict(orient="records")
        return ParsedHtmlTable(rows=rows, confidence_score=0.9, parser_version=self.parser_version)

