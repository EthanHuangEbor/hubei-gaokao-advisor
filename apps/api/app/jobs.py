from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class ParseJob:
    job_id: str
    job_type: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)
    result_summary: str = ""
    error_message: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ParseJobStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.path = self.root / "parse_jobs.json"

    def create(self, job_type: str, payload: dict[str, Any] | None = None) -> ParseJob:
        now = self._now()
        job = ParseJob(
            job_id=str(uuid4()),
            job_type=job_type,
            status="queued",
            payload=payload or {},
            created_at=now,
            updated_at=now,
        )
        jobs = self.list_jobs()
        jobs.append(job)
        self._write(jobs)
        return job

    def list_jobs(self) -> list[ParseJob]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [ParseJob(**item) for item in data]

    def next_queued(self) -> ParseJob | None:
        for job in self.list_jobs():
            if job.status == "queued":
                return job
        return None

    def mark_running(self, job_id: str) -> ParseJob | None:
        return self._update(job_id, status="running")

    def mark_completed(self, job_id: str, result_summary: str) -> ParseJob | None:
        return self._update(job_id, status="completed", result_summary=result_summary, error_message="")

    def mark_failed(self, job_id: str, error_message: str) -> ParseJob | None:
        return self._update(job_id, status="failed", error_message=error_message)

    def _update(self, job_id: str, **changes: Any) -> ParseJob | None:
        jobs = self.list_jobs()
        updated: ParseJob | None = None
        for job in jobs:
            if job.job_id == job_id:
                for key, value in changes.items():
                    setattr(job, key, value)
                job.updated_at = self._now()
                updated = job
                break
        if updated is None:
            return None
        self._write(jobs)
        return updated

    def _write(self, jobs: list[ParseJob]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = [job.to_dict() for job in jobs]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
