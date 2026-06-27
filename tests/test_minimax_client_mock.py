from __future__ import annotations

from services.llm.minimax_client import MiniMaxClient


def test_minimax_missing_key_returns_fallback(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    result = MiniMaxClient().generate_advice({"items": [{"major_group_code": "HBA001-P01", "tier": "稳"}]})
    assert result.error_code == "missing_api_key"
    assert result.output_json["items"][0]["major_group_id"] == "HBA001-P01"

