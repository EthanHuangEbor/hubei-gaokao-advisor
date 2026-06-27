from __future__ import annotations

from pathlib import Path

from apps.api.app.jobs import ParseJob, ParseJobStore

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ParseJobStore(ROOT / ".tmp" / "jobs")


def process_next_job(store: ParseJobStore | None = None) -> ParseJob | None:
    active_store = store or DEFAULT_STORE
    job = active_store.next_queued()
    if job is None:
        return None
    active_store.mark_running(job.job_id)
    return active_store.mark_completed(
        job.job_id,
        f"MVP worker processed {job.job_type}; crawler execution remains policy-gated.",
    )


def main() -> None:
    processed = process_next_job()
    if processed is None:
        print("Worker idle: no queued parse jobs.")
        return
    print(f"Worker completed parse job {processed.job_id}: {processed.result_summary}")


if __name__ == "__main__":
    main()
