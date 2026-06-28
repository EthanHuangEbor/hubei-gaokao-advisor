from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app
from services.llm.minimax_client import MiniMaxClient


def test_minimax_status_reports_missing_key(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.setenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    monkeypatch.setenv("MINIMAX_MODEL", "MiniMax-M3")

    status = MiniMaxClient().status()

    assert status["configured"] is False
    assert status["error_code"] == "missing_api_key"
    assert status["masked_api_key"] == ""
    assert status["base_url"] == "https://api.minimax.io/v1"
    assert status["model"] == "MiniMax-M3"
    assert status["endpoint_style"] == "responses"


def test_minimax_status_masks_configured_key(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "secret-minimax-key-1234567890")

    status = MiniMaxClient().status()

    assert status["configured"] is True
    assert status["error_code"] is None
    assert status["masked_api_key"].startswith("secr")
    assert status["masked_api_key"].endswith("7890")
    assert "minimax-key" not in status["masked_api_key"]


def test_minimax_status_masks_short_keys(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "abcd")

    status = MiniMaxClient().status()

    assert status["masked_api_key"] == "***"

    monkeypatch.setenv("MINIMAX_API_KEY", "abc123")

    status = MiniMaxClient().status()

    assert status["masked_api_key"] == "a***3"


def test_minimax_runtime_error_code_is_preserved(monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "dummy-key")

    def raise_http_error(_self, _payload):
        raise RuntimeError("minimax_http_401")

    monkeypatch.setattr(MiniMaxClient, "_responses", raise_http_error)

    result = MiniMaxClient().generate_advice({"items": []})

    assert result.error_code == "minimax_http_401"
    assert any("minimax_http_401" in risk for risk in result.output_json["risks"])


def test_doctor_peak_status_endpoint(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)

    response = client.get("/api/admin/doctor-peak/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["doctor_peak"]["status"] in {"available", "missing"}
    assert payload["minimax"]["configured"] is False
    assert payload["minimax"]["error_code"] == "missing_api_key"


def test_doctor_peak_test_probe_uses_fallback_without_key(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post("/api/admin/doctor-peak/test")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "fallback"
    assert payload["error_code"] == "missing_api_key"
    assert "summary" in payload["output"]
