from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


@dataclass
class RawDocument:
    id: str
    filename: str
    document_type: str
    source_type: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    saved_path: str
    review_status: str
    reviewer_note: str
    created_at: str
    parse_summary: dict[str, object] = field(default_factory=dict)
    parse_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class RawDocumentStore:
    def __init__(self, root: Path):
        self.upload_dir = root / "data" / "raw" / "uploads"
        self.documents: dict[str, RawDocument] = {}

    async def save_upload(self, file: UploadFile, document_type: str) -> RawDocument:
        content = await file.read()
        if not content:
            raise ValueError("uploaded file is empty")

        document_id = str(uuid4())
        filename = self._safe_filename(file.filename or "upload.bin")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        saved_path = self.upload_dir / f"{document_id}_{filename}"
        saved_path.write_bytes(content)

        document = RawDocument(
            id=document_id,
            filename=filename,
            document_type=document_type,
            source_type="admin_upload",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            sha256_hash=sha256(content).hexdigest(),
            saved_path=str(saved_path),
            review_status="pending",
            reviewer_note="",
            created_at=datetime.now(UTC).isoformat(),
        )
        self.documents[document_id] = document
        return document

    def list_documents(self) -> list[RawDocument]:
        return list(self.documents.values())

    def get(self, document_id: str) -> RawDocument | None:
        return self.documents.get(document_id)

    def attach_parse_result(
        self,
        document_id: str,
        parse_summary: dict[str, object],
        parse_errors: list[str],
    ) -> RawDocument | None:
        document = self.documents.get(document_id)
        if document is None:
            return None
        document.parse_summary = parse_summary
        document.parse_errors = parse_errors
        return document

    def review(self, document_id: str, review_status: str, reviewer_note: str) -> RawDocument | None:
        document = self.documents.get(document_id)
        if document is None:
            return None
        document.review_status = review_status
        document.reviewer_note = reviewer_note
        return document

    @staticmethod
    def _safe_filename(filename: str) -> str:
        name = Path(filename).name.strip() or "upload.bin"
        return re.sub(r"[^A-Za-z0-9._-]", "_", name)

