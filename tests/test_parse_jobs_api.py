from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_parse_job_create_and_list_returns_persistent_job() -> None:
    client = TestClient(app)

    create_response = client.post("/api/hubei/parse-jobs", json={"job_type": "hubei_plan_parse"})

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "queued"
    assert created["job_type"] == "hubei_plan_parse"
    assert created["job_id"]
    assert created["created_at"]

    list_response = client.get("/api/hubei/parse-jobs")
    assert list_response.status_code == 200
    assert any(job["job_id"] == created["job_id"] for job in list_response.json())
