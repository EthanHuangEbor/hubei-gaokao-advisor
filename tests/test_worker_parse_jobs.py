from __future__ import annotations

from apps.api.app.jobs import ParseJobStore
from apps.worker.main import process_next_job


def test_worker_processes_next_queued_parse_job(tmp_path) -> None:
    store = ParseJobStore(tmp_path)
    created = store.create("hubei_plan_parse")

    processed = process_next_job(store)

    assert processed is not None
    assert processed.job_id == created.job_id
    assert processed.status == "completed"
    assert "MVP worker" in processed.result_summary
    assert store.list_jobs()[0].status == "completed"
