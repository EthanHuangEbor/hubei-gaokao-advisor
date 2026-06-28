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
    assert payload["data_status"]["dataset_kind"] in {"fixture_seed", "real_curated", "mixed", "missing", "incomplete"}
    assert payload["llm_status"]["error_code"] == "missing_api_key"


def test_recommendation_rejects_fixture_data_in_strict_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("REQUIRE_REAL_DATA", "true")
    monkeypatch.delenv("ALLOW_FIXTURE_DATA", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/recommendations/run",
        json={
            "year": 2026,
            "province": "湖北",
            "first_subject": "physics",
            "second_subjects": ["化学"],
            "score": 620,
            "rank": 12000,
            "batch": "本科普通批",
            "category": "普通类",
            "preferred_cities": ["武汉"],
            "preferred_majors": ["计算机科学与技术"],
            "max_tuition": 60000,
            "accept_private_college": False,
            "accept_sino_foreign": False,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "real_data_required"
