from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedPdfText:
    text: str
    confidence_score: float
    parser_version: str
    review_status: str


class PdfTableAdapter:
    parser_version = "pdf-text-v1"

    def extract_text(self, path: str | Path) -> ParsedPdfText:
        try:
            import fitz

            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
            return ParsedPdfText(
                text=text,
                confidence_score=0.75,
                parser_version=self.parser_version,
                review_status="pending",
            )
        except Exception:
            return ParsedPdfText(
                text="",
                confidence_score=0.0,
                parser_version=self.parser_version,
                review_status="failed",
            )

