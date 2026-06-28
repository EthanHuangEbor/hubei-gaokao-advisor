from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, cast
from uuid import uuid4

from services.compliance.pii_redactor import contains_pii, redact_text, stable_redacted_hash


@dataclass(frozen=True)
class MiniMaxResult:
    request_id: str
    model: str
    endpoint_style: str
    latency_ms: int
    token_usage: dict[str, Any]
    input_redacted_hash: str
    output_json: dict[str, Any]
    error_code: str | None


@dataclass(frozen=True)
class MiniMaxConfig:
    api_key: str
    base_url: str
    model: str
    endpoint_style: str
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> MiniMaxConfig:
        timeout_raw = os.getenv("MINIMAX_TIMEOUT_SECONDS", "30")
        try:
            timeout_seconds = int(timeout_raw)
        except ValueError:
            timeout_seconds = 30
        return cls(
            api_key=os.getenv("MINIMAX_API_KEY", "").strip(),
            base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1").rstrip("/"),
            model=os.getenv("MINIMAX_MODEL", "MiniMax-M3").strip() or "MiniMax-M3",
            endpoint_style=os.getenv("MINIMAX_API_STYLE", "responses").strip() or "responses",
            timeout_seconds=max(timeout_seconds, 1),
        )

    def masked_api_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 4:
            return "***"
        if len(self.api_key) <= 8:
            return f"{self.api_key[:1]}***{self.api_key[-1:]}"
        return f"{self.api_key[:4]}***{self.api_key[-4:]}"


@dataclass(frozen=True)
class MiniMaxStatus:
    configured: bool
    base_url: str
    model: str
    endpoint_style: str
    timeout_seconds: int
    masked_api_key: str
    error_code: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "base_url": self.base_url,
            "model": self.model,
            "endpoint_style": self.endpoint_style,
            "timeout_seconds": self.timeout_seconds,
            "masked_api_key": self.masked_api_key,
            "error_code": self.error_code,
        }


class MiniMaxClient:
    def __init__(self, config: MiniMaxConfig | None = None) -> None:
        self.config = config or MiniMaxConfig.from_env()
        self.api_key = self.config.api_key
        self.base_url = self.config.base_url
        self.model = self.config.model
        self.api_style = self.config.endpoint_style
        self.timeout_seconds = self.config.timeout_seconds

    def status(self) -> dict[str, Any]:
        error_code = None if self.config.api_key else "missing_api_key"
        return MiniMaxStatus(
            configured=bool(self.config.api_key),
            base_url=self.config.base_url,
            model=self.config.model,
            endpoint_style=self.config.endpoint_style,
            timeout_seconds=self.config.timeout_seconds,
            masked_api_key=self.config.masked_api_key(),
            error_code=error_code,
        ).to_dict()

    def generate_advice(self, payload: dict[str, Any]) -> MiniMaxResult:
        request_id = str(uuid4())
        started = time.perf_counter()
        sanitized = self._sanitize_payload(payload)
        input_hash = stable_redacted_hash(sanitized)
        if not self.api_key:
            return self._result(
                request_id=request_id,
                started=started,
                input_hash=input_hash,
                output=self._fallback(sanitized, "missing_api_key"),
                error_code="missing_api_key",
            )
        try:
            if self.api_style == "chat_completions":
                output = self._chat_completions(sanitized)
                endpoint_style = "chat_completions"
            else:
                output = self._responses(sanitized)
                endpoint_style = "responses"
            return MiniMaxResult(
                request_id=request_id,
                model=self.model,
                endpoint_style=endpoint_style,
                latency_ms=int((time.perf_counter() - started) * 1000),
                token_usage=output.get("usage", {}) if isinstance(output, dict) else {},
                input_redacted_hash=input_hash,
                output_json=self._coerce_output_json(output),
                error_code=None,
            )
        except Exception as exc:
            error_code = self._error_code(exc)
            return self._result(
                request_id=request_id,
                started=started,
                input_hash=input_hash,
                output=self._fallback(sanitized, error_code),
                error_code=error_code,
            )

    def _error_code(self, exc: Exception) -> str:
        if isinstance(exc, RuntimeError) and exc.args:
            message = str(exc.args[0])
            if message.startswith("minimax_"):
                return message
        return type(exc).__name__

    def _sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(payload, ensure_ascii=False)
        if contains_pii(text):
            text = redact_text(text)
        allowed = cast(dict[str, Any], json.loads(text))
        allowed.pop("name", None)
        allowed.pop("phone", None)
        allowed.pop("id_card", None)
        return allowed

    def _responses(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "temperature": 0.2,
            "reasoning": {"effort": "none"},
            "stream": False,
            "input": [
                {
                    "role": "system",
                    "content": "You are Doctor.Peak, a virtual Hubei gaokao advisor. Output strict JSON only.",
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "text": {"format": {"type": "json_object"}},
        }
        return self._post_json(f"{self.base_url}/responses", body)

    def _chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Doctor.Peak, a virtual Hubei gaokao advisor. Output strict JSON only.",
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        return self._post_json(f"{self.base_url}/chat/completions", body)

    def _post_json(self, url: str, body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"minimax_http_{exc.code}") from exc

    def _coerce_output_json(self, output: dict[str, Any]) -> dict[str, Any]:
        if "summary" in output:
            return output
        text = ""
        if "output_text" in output:
            text = str(output["output_text"])
        elif "choices" in output and output["choices"]:
            text = output["choices"][0].get("message", {}).get("content", "")
        try:
            return cast(dict[str, Any], json.loads(text))
        except Exception:
            return self._fallback({"raw_output": text}, "invalid_json")

    def _fallback(self, payload: dict[str, Any], reason: str) -> dict[str, Any]:
        items = payload.get("items", [])[:45]
        return {
            "summary": "\u5df2\u751f\u6210\u89c4\u5219\u63a8\u8350\uff1b\u5f53\u524d\u4f7f\u7528\u786e\u5b9a\u6027\u89e3\u91ca fallback\u3002",
            "overall_strategy": "\u6309\u9662\u6821\u4e13\u4e1a\u7ec4\u53e3\u5f84\u5e73\u8861\u51b2\u3001\u7a33\u3001\u4fdd\u3001\u57ab\uff0c\u4f18\u5148\u6838\u5bf9\u9009\u79d1\u3001\u8ba1\u5212\u53d8\u5316\u3001\u5b66\u8d39\u548c\u9650\u5236\u6761\u4ef6\u3002",
            "doctor_peak_view": "Doctor.Peak \u53ea\u89e3\u91ca\u7ed3\u6784\u5316\u63a8\u8350\u7ed3\u679c\uff0c\u4e0d\u627f\u8bfa\u5f55\u53d6\uff0c\u4e5f\u4e0d\u66ff\u4ee3\u6e56\u5317\u7701\u62db\u529e\u548c\u9ad8\u6821\u62db\u751f\u7ae0\u7a0b\u3002",
            "items": [
                {
                    "major_group_id": item.get("major_group_code", ""),
                    "tier": item.get("tier", ""),
                    "why": "\u8be5\u9879\u7531\u5386\u53f2\u4f4d\u6b21\u3001\u8ba1\u5212\u53d8\u5316\u3001\u6ce2\u52a8\u548c\u504f\u597d\u5339\u914d\u5171\u540c\u8fdb\u5165\u89c4\u5219\u6a21\u578b\u3002",
                    "main_risks": item.get("warnings", [])[:3],
                    "plan_change_explanation": f"\u8ba1\u5212\u53d8\u5316\uff1a{item.get('plan_change_ratio', 0)}",
                    "rank_explanation": f"\u4f4d\u6b21\u5dee\uff1a{item.get('rank_gap', 0)}",
                    "employment_angle": "\u5efa\u8bae\u7ed3\u5408\u4e13\u4e1a\u7ec4\u5185\u4e13\u4e1a\u3001\u57ce\u5e02\u4ea7\u4e1a\u548c\u4e2a\u4eba\u5b66\u4e60\u5f3a\u9879\u590d\u6838\u3002",
                    "parent_explanation": "\u5bb6\u957f\u4fa7\u91cd\u70b9\uff1a\u6210\u672c\u3001\u515c\u5e95\u3001\u5b89\u5168\u8fb9\u754c\u548c\u62db\u751f\u7ae0\u7a0b\u3002",
                    "student_explanation": "\u5b66\u751f\u4fa7\u91cd\u70b9\uff1a\u5174\u8da3\u3001\u5b66\u4e60\u96be\u5ea6\u3001\u4e13\u4e1a\u8def\u5f84\u548c\u957f\u671f\u53d1\u5c55\u3002",
                    "next_checks": ["\u6838\u5bf9\u9ad8\u6821\u62db\u751f\u7ae0\u7a0b", "\u6838\u5bf9\u4f53\u68c0/\u5355\u79d1\u9650\u5236", "\u6838\u5bf9\u4e13\u4e1a\u7ec4\u5185\u5168\u90e8\u4e13\u4e1a"],
                }
                for item in items
            ],
            "risks": [f"MiniMax \u672a\u8c03\u7528\u6216\u5931\u8d25\uff1a{reason}", "LLM \u89e3\u91ca\u4e0d\u53c2\u4e0e\u6392\u5e8f"],
            "parent_talking_points": ["\u4e0d\u8981\u53ea\u770b\u5b66\u6821\u540d\u6c14\uff0c\u5fc5\u987b\u770b\u4e13\u4e1a\u7ec4\u5185\u4e13\u4e1a\u548c\u6210\u672c\u3002"],
            "student_talking_points": ["\u4e0d\u8981\u53ea\u770b\u70ed\u95e8\u4e13\u4e1a\uff0c\u5fc5\u987b\u770b\u8bfe\u7a0b\u96be\u5ea6\u548c\u957f\u671f\u8def\u5f84\u3002"],
            "next_checks": ["\u4ee5\u6e56\u5317\u5b98\u65b9\u5e73\u53f0\u548c\u9ad8\u6821\u62db\u751f\u7ae0\u7a0b\u4e3a\u51c6"],
            "disclaimer": "\u672c\u7cfb\u7edf\u4ec5\u57fa\u4e8e\u516c\u5f00\u5386\u53f2\u6570\u636e\u3001\u5f53\u5e74\u62db\u751f\u8ba1\u5212\u548c\u89c4\u5219\u6a21\u578b\u8fdb\u884c\u4f30\u8ba1\uff0c\u4e0d\u6784\u6210\u5f55\u53d6\u627f\u8bfa\u3002",
        }
    def _result(
        self,
        *,
        request_id: str,
        started: float,
        input_hash: str,
        output: dict[str, Any],
        error_code: str | None,
    ) -> MiniMaxResult:
        return MiniMaxResult(
            request_id=request_id,
            model=self.model,
            endpoint_style=self.api_style,
            latency_ms=int((time.perf_counter() - started) * 1000),
            token_usage={},
            input_redacted_hash=input_hash,
            output_json=output,
            error_code=error_code,
        )

