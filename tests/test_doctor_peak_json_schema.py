from __future__ import annotations

from services.llm.minimax_client import MiniMaxClient


def test_doctor_peak_fallback_schema(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    result = MiniMaxClient().generate_advice({"items": []})
    for key in [
        "summary",
        "overall_strategy",
        "doctor_peak_view",
        "items",
        "risks",
        "parent_talking_points",
        "student_talking_points",
        "next_checks",
        "disclaimer",
    ]:
        assert key in result.output_json

