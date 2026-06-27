from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_recommendation_run_api(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)
    response = client.post(
        "/api/recommendations/run",
        json={
            "first_subject": "physics",
            "second_subjects": ["chemistry", "biology"],
            "score": 610,
            "rank": 26000,
            "max_tuition": 60000,
            "accept_private_college": True,
            "accept_sino_foreign": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"]
    assert payload["items"]
    assert all(item["major_group_code"] for item in payload["items"])
    assert payload["doctor_peak_advice"]["summary"]
    assert payload["doctor_peak_advice"]["doctor_peak_view"]
    assert payload["doctor_peak_advice"]["disclaimer"]
    assert payload["items"][0]["doctor_peak_explanation"]
