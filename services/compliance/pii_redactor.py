from __future__ import annotations

import hashlib
import re
from typing import Any

PII_PATTERNS = [
    re.compile(r"\b\d{17}[\dXx]\b"),
    re.compile(r"\b1[3-9]\d{9}\b"),
    re.compile(r"\b\d{14}\b"),
    re.compile(r"(准考证号|身份证|手机号|报名号)[:：]?\s*[\w-]+"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in PII_PATTERNS:
        redacted = pattern.sub("[REDACTED_PII]", redacted)
    return redacted


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS)


def stable_redacted_hash(payload: Any) -> str:
    text = redact_text(str(payload))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

