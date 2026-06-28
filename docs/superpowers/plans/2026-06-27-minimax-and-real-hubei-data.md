# MiniMax and Real Hubei Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Doctor.Peak MiniMax operability and make the runtime data path distinguish real reviewed Hubei data from demo fixture data, then ingest and promote official public Hubei rows into curated CSV.

**Architecture:** Split the work into two connected tracks. The MiniMax track adds typed configuration, status endpoints, a safe test call, redacted logs, and admin UI visibility while keeping LLM output explanation-only. The data track first adds a runtime authenticity guard so fixture data is never mistaken for real data, then implements official-source download, parse, quality, review, promote, and seed steps for reviewed curated CSV.

**Tech Stack:** FastAPI, pytest, urllib/httpx, pandas, beautifulsoup4, PyMuPDF, CSV, Next.js, React Query, Playwright, MiniMax Responses API.

---

## Scope Decision

This plan fixes two visible failures from the screenshots:

1. `MiniMax 未调用或失败: missing_api_key` means the API process did not see `MINIMAX_API_KEY` at runtime. The system already falls back safely, but there is no status probe or admin diagnosis.
2. `湖北样例013大学` means fixture seed data is currently being loaded from `data/curated/hubei` and presented through the same result UI as real data. The immediate fix is an authenticity guard and UI banner; the product fix is reviewed official-data promotion.

The first mergeable milestone should be a hotfix: MiniMax status plus data authenticity guard. The second milestone can be the real-data ingestion pipeline.

## File Structure

MiniMax configuration and observability:

- Modify: `.env.example`
  - Document required MiniMax variables, local CORS, fixture-data switches, and strict-real-data mode.
- Modify: `services/llm/minimax_client.py`
  - Add `MiniMaxConfig`, `MiniMaxStatus`, `from_env()`, `status()`, and masked key reporting.
  - Keep `generate_advice()` deterministic when key is missing or the API fails.
- Modify: `services/llm/advice_orchestrator.py`
  - Include `llm_status` in the returned `MiniMaxResult` log payload.
  - Preserve the invariant that Doctor.Peak explanations never change item ordering.
- Modify: `apps/api/app/main.py`
  - Add `GET /api/admin/doctor-peak/status`.
  - Add `POST /api/admin/doctor-peak/test`.
  - Keep `GET /api/admin/minimax-logs`, but mask secrets and expose latest error code.
- Modify: `apps/web/src/lib/api.ts`
  - Add fetchers for Doctor.Peak status and test call.
- Modify: `apps/web/src/app/admin/admin-client.tsx`
  - Add Doctor.Peak/MiniMax status card, masked key, endpoint style, latest call result, and test button.
- Test: `tests/test_minimax_config_status.py`
- Test: `tests/test_minimax_client_mock.py`
- Test: `tests/test_doctor_peak_json_schema.py`
- Test: `apps/web/tests/e2e/recommendation.spec.ts`

Data authenticity and real curated pipeline:

- Create: `services/data/hubei/authenticity.py`
  - Detect fixture markers, dataset kind, metadata completeness, and runtime allowance.
- Modify: `services/data/hubei/curated_loader.py`
  - Run authenticity checks before returning runtime rows.
  - Reject fixture rows in production and strict-real-data mode.
- Modify: `apps/api/app/repository.py`
  - Store `dataset_status` next to `dataset`.
  - Prefer real curated CSV; fall back to demo only when explicitly allowed in development.
- Modify: `apps/api/app/main.py`
  - Expand `/api/data/status`.
  - Include `data_status` in recommendation responses and traces.
  - Return `503` for recommendations when strict-real-data mode is enabled and real curated data is missing.
- Modify: `services/data/hubei/build_dataset.py`
  - Replace fixture-only build behavior with source-aware download, parse, quality, and promote orchestration.
- Create: `services/data/hubei/downloader.py`
  - Download public registry sources into raw layer with sha256 manifest.
- Create: `services/data/hubei/parsers/__init__.py`
- Create: `services/data/hubei/parsers/admission_lines.py`
  - Parse reviewed public admission-line tables into candidate rows.
- Create: `services/data/hubei/parsers/rank_segments.py`
  - Parse one-score-one-rank tables into candidate rows.
- Create: `services/data/hubei/parsers/plans.py`
  - Parse manually uploaded 2026 plan CSV; image/PDF/OCR candidates remain pending.
- Create: `services/data/hubei/quality.py`
  - Enforce schema, source metadata, monotonic rank segments, no fixture markers, duplicates, and review gates.
- Create: `services/data/hubei/promote.py`
  - Promote only approved candidate rows into curated CSV.
- Create: `data/curated/hubei/README.md`
  - Document curated CSV policy and how to replace demo seed rows.
- Modify: `data/source_registry/hubei_sources.yaml`
  - Add parser hints: `parser`, `raw_subdir`, `allow_network_download`, `requires_manual_review`.
- Test: `tests/test_data_authenticity.py`
- Test: `tests/test_hubei_downloader.py`
- Test: `tests/test_hubei_real_parsers.py`
- Test: `tests/test_hubei_quality_promote.py`
- Test: `tests/test_recommendation_run_api.py`
- Test: `apps/web/tests/e2e/recommendation.spec.ts`

Frontend product feedback:

- Modify: `packages/shared-types/src/index.ts`
  - Add `DataRuntimeStatus`, `DoctorPeakStatus`, and recommendation `data_status` fields.
- Modify: `apps/web/src/app/input/page.tsx`
  - Show a blocking real-data warning when strict mode is on and data is missing.
  - Show a visible demo-data warning when fixture data is allowed.
- Modify: `apps/web/src/app/result/[runId]/result-client.tsx`
  - Display dataset kind, source counts, review status, and a non-dismissable demo-data banner when applicable.
- Modify: `apps/web/src/app/admin/admin-client.tsx`
  - Add curated status, fixture marker count, quality report path, and source registry parser status.

Docs:

- Modify: `README.md`
  - Add local MiniMax setup, strict-real-data mode, fixture demo mode, and real-data build commands.
- Create: `docs/operations/minimax-and-data.md`
  - Add the operator runbook for key setup, diagnostics, source ingestion, review, and promotion.

## Task 1: Baseline and Reproduction Tests

**Files:**
- Create: `tests/test_minimax_config_status.py`
- Create: `tests/test_data_authenticity.py`
- Modify: `tests/test_recommendation_run_api.py`

- [ ] **Step 1: Write MiniMax status failing tests**

Create `tests/test_minimax_config_status.py`:

```python
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


def test_doctor_peak_status_endpoint(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)

    response = client.get("/api/admin/doctor-peak/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["doctor_peak"]["status"] in {"available", "missing"}
    assert payload["minimax"]["configured"] is False
    assert payload["minimax"]["error_code"] == "missing_api_key"
```

- [ ] **Step 2: Write data authenticity failing tests**

Create `tests/test_data_authenticity.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from services.data.hubei.authenticity import inspect_curated_dir, require_runtime_dataset


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_authenticity_detects_fixture_seed(tmp_path):
    curated = tmp_path / "data" / "curated" / "hubei"
    _write_csv(
        curated / "admission_records_2023_2025.csv",
        [
            {
                "year": "2025",
                "province": "湖北",
                "batch": "本科普通批",
                "category": "普通类",
                "first_subject": "physics",
                "university_code": "HBA013",
                "university_name": "湖北样例013大学",
                "major_group_code": "HBA013-P13",
                "major_group_name": "物理13组",
                "min_score": "610",
                "min_rank": "23950",
                "source_id": "fixture-line-2025",
                "source_url": "manual-upload://fixture",
                "source_type": "fixture_seed",
                "raw_document_sha256": "abc",
                "parser_name": "static_csv_seed",
                "parser_version": "curated-fixture-seed-v0.2",
                "confidence_score": "0.95",
                "parse_confidence": "0.95",
                "license_note": "fixture seed",
                "review_status": "approved",
                "reviewer": "system_seed",
            }
        ],
    )

    status = inspect_curated_dir(curated)

    assert status.dataset_kind == "fixture_seed"
    assert status.contains_fixture_rows is True
    assert status.fixture_marker_count == 1
    assert status.real_curated_ready is False


def test_strict_runtime_rejects_fixture_seed(tmp_path):
    status = inspect_curated_dir(tmp_path / "missing")

    with pytest.raises(RuntimeError, match="real curated Hubei data is required"):
        require_runtime_dataset(status, app_env="production", allow_fixture_data=False)
```

- [ ] **Step 3: Add API strict-data failing test**

Append to `tests/test_recommendation_run_api.py`:

```python
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
            "allow_private": False,
            "allow_sino_foreign": False,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "real_data_required"
```

- [ ] **Step 4: Run failing tests**

Run:

```powershell
python -m pytest tests/test_minimax_config_status.py tests/test_data_authenticity.py tests/test_recommendation_run_api.py -q
```

Expected: tests fail because `MiniMaxClient.status`, `services.data.hubei.authenticity`, `/api/admin/doctor-peak/status`, and strict-data rejection do not exist.

- [ ] **Step 5: Commit tests**

```powershell
git add tests/test_minimax_config_status.py tests/test_data_authenticity.py tests/test_recommendation_run_api.py
git commit -m "test: capture minimax status and data authenticity gaps"
```

## Task 2: MiniMax Configuration and Status Model

**Files:**
- Modify: `services/llm/minimax_client.py`
- Modify: `.env.example`
- Test: `tests/test_minimax_config_status.py`

- [ ] **Step 1: Add typed MiniMax config and status**

In `services/llm/minimax_client.py`, add these dataclasses near the existing `MiniMaxResult`:

```python
@dataclass(frozen=True)
class MiniMaxConfig:
    api_key: str
    base_url: str
    model: str
    endpoint_style: str
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "MiniMaxConfig":
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
        if len(self.api_key) <= 8:
            return f"{self.api_key[:2]}***{self.api_key[-2:]}"
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
```

- [ ] **Step 2: Refactor `MiniMaxClient.__init__`**

Replace the current environment reads in `MiniMaxClient.__init__` with:

```python
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
```

- [ ] **Step 3: Keep fallback behavior unchanged**

Confirm `generate_advice()` still returns `error_code="missing_api_key"` when no key exists and still calls `_fallback()` without a network request.

- [ ] **Step 4: Update `.env.example`**

Keep existing values and add these lines:

```dotenv
# MiniMax must be visible to the API process before `npm run api` starts.
# PowerShell example: $env:MINIMAX_API_KEY="your_key"
MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_MODEL=MiniMax-M3
MINIMAX_API_STYLE=responses
MINIMAX_TIMEOUT_SECONDS=30

# Data safety:
# development + ALLOW_FIXTURE_DATA=true permits demo rows with visible UI warnings.
# production or REQUIRE_REAL_DATA=true rejects fixture/demo recommendations.
ALLOW_FIXTURE_DATA=true
REQUIRE_REAL_DATA=false
```

- [ ] **Step 5: Run MiniMax config tests**

Run:

```powershell
python -m pytest tests/test_minimax_config_status.py::test_minimax_status_reports_missing_key tests/test_minimax_config_status.py::test_minimax_status_masks_configured_key -q
```

Expected: both tests pass.

- [ ] **Step 6: Commit MiniMax config**

```powershell
git add services/llm/minimax_client.py .env.example
git commit -m "feat: expose minimax runtime configuration status"
```

## Task 3: Doctor.Peak API Status and Test Probe

**Files:**
- Modify: `apps/api/app/main.py`
- Modify: `services/llm/advice_orchestrator.py`
- Test: `tests/test_minimax_config_status.py`
- Test: `tests/test_doctor_peak_json_schema.py`

- [ ] **Step 1: Add a Doctor.Peak status helper**

In `apps/api/app/main.py`, add:

```python
def _doctor_peak_status() -> dict[str, object]:
    skill_path = ROOT / ".agents" / "skills" / "doctor-peak" / "SKILL.md"
    client = MiniMaxClient()
    latest = LLM_LOGS[-1] if LLM_LOGS else None
    return {
        "doctor_peak": {
            "status": "available" if skill_path.exists() else "missing",
            "path": str(skill_path),
            "policy": "explanation_only_no_ranking_changes",
        },
        "minimax": client.status(),
        "latest_call": {
            "request_id": latest.get("request_id") if latest else None,
            "error_code": latest.get("error_code") if latest else None,
            "latency_ms": latest.get("latency_ms") if latest else None,
            "endpoint_style": latest.get("endpoint_style") if latest else None,
        },
    }
```

Add the import:

```python
from services.llm.minimax_client import MiniMaxClient
```

- [ ] **Step 2: Add status endpoint**

In `apps/api/app/main.py`, add:

```python
@app.get("/api/admin/doctor-peak/status")
def doctor_peak_status() -> dict[str, object]:
    return _doctor_peak_status()
```

- [ ] **Step 3: Add safe MiniMax probe endpoint**

In `apps/api/app/main.py`, add:

```python
@app.post("/api/admin/doctor-peak/test")
def doctor_peak_test() -> dict[str, object]:
    payload = {
        "province": "湖北",
        "year": 2026,
        "first_subject": "physics",
        "score_band": "600-630",
        "rank_band": "10000-15000",
        "items": [
            {
                "major_group_code": "probe-group",
                "tier": "稳",
                "rank_gap": 1200,
                "warnings": ["probe_payload_no_personal_data"],
            }
        ],
    }
    result = MiniMaxClient().generate_advice(payload)
    LLM_LOGS.append(result.__dict__)
    return {
        "status": "fallback" if result.error_code else "ok",
        "error_code": result.error_code,
        "request_id": result.request_id,
        "output": result.output_json,
        "minimax": MiniMaxClient().status(),
    }
```

- [ ] **Step 4: Ensure log payloads do not expose secrets**

In `services/llm/advice_orchestrator.py`, keep the return type `MiniMaxResult`, but do not add raw request bodies or API keys to `LLM_LOGS`. The existing `MiniMaxResult` fields are allowed:

```python
request_id
model
endpoint_style
latency_ms
token_usage
input_redacted_hash
output_json
error_code
```

- [ ] **Step 5: Extend API tests**

Append to `tests/test_minimax_config_status.py`:

```python
def test_doctor_peak_test_probe_uses_fallback_without_key(monkeypatch):
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post("/api/admin/doctor-peak/test")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "fallback"
    assert payload["error_code"] == "missing_api_key"
    assert "summary" in payload["output"]
```

- [ ] **Step 6: Run API tests**

Run:

```powershell
python -m pytest tests/test_minimax_config_status.py tests/test_doctor_peak_json_schema.py -q
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit API status**

```powershell
git add apps/api/app/main.py services/llm/advice_orchestrator.py tests/test_minimax_config_status.py tests/test_doctor_peak_json_schema.py
git commit -m "feat(api): add doctor peak minimax diagnostics"
```

## Task 4: Data Authenticity Runtime Guard

**Files:**
- Create: `services/data/hubei/authenticity.py`
- Modify: `services/data/hubei/curated_loader.py`
- Modify: `apps/api/app/repository.py`
- Modify: `apps/api/app/main.py`
- Test: `tests/test_data_authenticity.py`
- Test: `tests/test_recommendation_run_api.py`

- [ ] **Step 1: Implement authenticity model**

Create `services/data/hubei/authenticity.py`:

```python
from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DatasetKind = Literal["missing", "fixture_seed", "real_curated", "mixed"]

REQUIRED_FILES = [
    "admission_records_2023_2025.csv",
    "rank_segments_2023_2026.csv",
    "admission_plans_2026.csv",
]
FIXTURE_MARKERS = (
    "fixture",
    "湖北样例",
    "样例",
    "curated-fixture-seed",
    "static_csv_seed",
    "鏍蜂緥",
)


@dataclass(frozen=True)
class DatasetAuthenticity:
    dataset_kind: DatasetKind
    curated_ready: bool
    real_curated_ready: bool
    contains_fixture_rows: bool
    fixture_marker_count: int
    approved_row_count: int
    pending_row_count: int
    missing_files: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_kind": self.dataset_kind,
            "curated_ready": self.curated_ready,
            "real_curated_ready": self.real_curated_ready,
            "contains_fixture_rows": self.contains_fixture_rows,
            "fixture_marker_count": self.fixture_marker_count,
            "approved_row_count": self.approved_row_count,
            "pending_row_count": self.pending_row_count,
            "missing_files": self.missing_files,
            "warnings": self.warnings,
        }


def inspect_curated_dir(curated_dir: str | Path) -> DatasetAuthenticity:
    path = Path(curated_dir)
    missing_files = [name for name in REQUIRED_FILES if not (path / name).exists()]
    approved = 0
    pending = 0
    fixture_markers = 0
    warnings: list[str] = []

    if missing_files:
        return DatasetAuthenticity(
            dataset_kind="missing",
            curated_ready=False,
            real_curated_ready=False,
            contains_fixture_rows=False,
            fixture_marker_count=0,
            approved_row_count=0,
            pending_row_count=0,
            missing_files=missing_files,
            warnings=["curated CSV files are missing"],
        )

    for name in REQUIRED_FILES:
        with (path / name).open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                review_status = row.get("review_status", "")
                if review_status == "approved":
                    approved += 1
                elif review_status == "pending":
                    pending += 1
                haystack = " ".join(str(value) for value in row.values()).lower()
                if any(marker.lower() in haystack for marker in FIXTURE_MARKERS):
                    fixture_markers += 1

    contains_fixture = fixture_markers > 0
    if contains_fixture and approved:
        dataset_kind: DatasetKind = "fixture_seed"
        warnings.append("approved rows contain fixture markers")
    elif contains_fixture:
        dataset_kind = "mixed"
        warnings.append("candidate rows contain fixture markers")
    else:
        dataset_kind = "real_curated"

    return DatasetAuthenticity(
        dataset_kind=dataset_kind,
        curated_ready=True,
        real_curated_ready=dataset_kind == "real_curated" and approved > 0,
        contains_fixture_rows=contains_fixture,
        fixture_marker_count=fixture_markers,
        approved_row_count=approved,
        pending_row_count=pending,
        missing_files=[],
        warnings=warnings,
    )


def fixture_data_allowed() -> bool:
    return os.getenv("ALLOW_FIXTURE_DATA", "false").lower() in {"1", "true", "yes"}


def strict_real_data_required() -> bool:
    return os.getenv("REQUIRE_REAL_DATA", "false").lower() in {"1", "true", "yes"} or os.getenv(
        "APP_ENV", "development"
    ) == "production"


def require_runtime_dataset(
    status: DatasetAuthenticity,
    *,
    app_env: str | None = None,
    allow_fixture_data: bool | None = None,
) -> None:
    env = app_env or os.getenv("APP_ENV", "development")
    allow_fixture = fixture_data_allowed() if allow_fixture_data is None else allow_fixture_data
    strict = strict_real_data_required() or env == "production"
    if status.real_curated_ready:
        return
    if strict or not allow_fixture:
        raise RuntimeError("real curated Hubei data is required before recommendations can run")
```

- [ ] **Step 2: Wire authenticity into curated loader**

At the start of `load_curated_dataset()` in `services/data/hubei/curated_loader.py`, add:

```python
from services.data.hubei.authenticity import inspect_curated_dir, require_runtime_dataset
```

Then add before reading rows:

```python
    authenticity = inspect_curated_dir(curated_path)
    require_runtime_dataset(authenticity)
```

Keep the existing production fixture rejection until tests confirm the new guard covers all cases, then remove `_reject_fixture_rows()` in a cleanup commit.

- [ ] **Step 3: Store dataset status in repository**

In `apps/api/app/repository.py`, import:

```python
from services.data.hubei.authenticity import DatasetAuthenticity, inspect_curated_dir
```

Set `self.dataset_status` in `__init__` and `reload()`:

```python
        self.dataset_status: DatasetAuthenticity = inspect_curated_dir(self.curated_dir)
```

In `_load_dataset()`, refresh status before the curated check:

```python
        self.dataset_status = inspect_curated_dir(self.curated_dir)
        if self._curated_ready():
            return load_curated_dataset(self.curated_dir)
```

- [ ] **Step 4: Expand `/api/data/status`**

In `apps/api/app/main.py`, merge `repo.dataset_status.to_dict()` into the current response:

```python
        "runtime_source": "curated_csv" if repo.dataset_status.curated_ready else "fixtures",
        "data_authenticity": repo.dataset_status.to_dict(),
        "real_curated_ready": repo.dataset_status.real_curated_ready,
```

- [ ] **Step 5: Reject strict-mode recommendations**

In `apps/api/app/main.py`, import:

```python
from services.data.hubei.authenticity import require_runtime_dataset
```

At the top of `run_recommendations()` add:

```python
    try:
        require_runtime_dataset(repo.dataset_status)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "real_data_required",
                "message": str(exc),
                "data_status": repo.dataset_status.to_dict(),
            },
        ) from exc
```

- [ ] **Step 6: Run authenticity tests**

Run:

```powershell
python -m pytest tests/test_data_authenticity.py tests/test_recommendation_run_api.py -q
```

Expected: selected tests pass.

- [ ] **Step 7: Commit data guard**

```powershell
git add services/data/hubei/authenticity.py services/data/hubei/curated_loader.py apps/api/app/repository.py apps/api/app/main.py tests/test_data_authenticity.py tests/test_recommendation_run_api.py
git commit -m "feat(data): guard runtime against unlabelled fixture data"
```

## Task 5: Admin and Result UI Diagnostics

**Files:**
- Modify: `packages/shared-types/src/index.ts`
- Modify: `apps/web/src/lib/api.ts`
- Modify: `apps/web/src/app/admin/admin-client.tsx`
- Modify: `apps/web/src/app/input/page.tsx`
- Modify: `apps/web/src/app/result/[runId]/result-client.tsx`
- Test: `apps/web/tests/e2e/recommendation.spec.ts`

- [ ] **Step 1: Add shared status types**

In `packages/shared-types/src/index.ts`, add:

```ts
export type DataRuntimeStatus = {
  dataset_kind: "missing" | "fixture_seed" | "real_curated" | "mixed";
  curated_ready: boolean;
  real_curated_ready: boolean;
  contains_fixture_rows: boolean;
  fixture_marker_count: number;
  approved_row_count: number;
  pending_row_count: number;
  missing_files: string[];
  warnings: string[];
};

export type DoctorPeakStatus = {
  doctor_peak: {
    status: "available" | "missing";
    path: string;
    policy: string;
  };
  minimax: {
    configured: boolean;
    base_url: string;
    model: string;
    endpoint_style: string;
    timeout_seconds: number;
    masked_api_key: string;
    error_code: string | null;
  };
  latest_call: {
    request_id: string | null;
    error_code: string | null;
    latency_ms: number | null;
    endpoint_style: string | null;
  };
};
```

- [ ] **Step 2: Add API fetchers**

In `apps/web/src/lib/api.ts`, add:

```ts
export async function fetchDoctorPeakStatus(): Promise<DoctorPeakStatus> {
  const response = await fetch(`${API_BASE}/api/admin/doctor-peak/status`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch Doctor.Peak status");
  }
  return response.json();
}

export async function runDoctorPeakProbe(): Promise<unknown> {
  const response = await fetch(`${API_BASE}/api/admin/doctor-peak/test`, { method: "POST" });
  if (!response.ok) {
    throw new Error("Failed to run Doctor.Peak probe");
  }
  return response.json();
}
```

- [ ] **Step 3: Display MiniMax status in admin**

In `apps/web/src/app/admin/admin-client.tsx`, add a section with this visible text:

```tsx
<section className="panel">
  <h2>Doctor.Peak / MiniMax</h2>
  <p>MiniMax: {doctorPeakStatus?.minimax.configured ? "已配置" : "未配置"}</p>
  <p>模型: {doctorPeakStatus?.minimax.model}</p>
  <p>接口: {doctorPeakStatus?.minimax.endpoint_style}</p>
  <p>Key: {doctorPeakStatus?.minimax.masked_api_key || "未检测到"}</p>
  <p>最近错误: {doctorPeakStatus?.latest_call.error_code || "无"}</p>
  <button type="button" onClick={handleDoctorPeakProbe}>测试 Doctor.Peak</button>
</section>
```

Use existing admin page styling and loading patterns.

- [ ] **Step 4: Display data authenticity in admin**

In the existing curated status area, display:

```tsx
<p>数据类型: {dataStatus?.data_authenticity.dataset_kind}</p>
<p>真实 curated: {dataStatus?.real_curated_ready ? "已就绪" : "未就绪"}</p>
<p>样例标记行: {dataStatus?.data_authenticity.fixture_marker_count}</p>
```

- [ ] **Step 5: Display demo-data warning on input and result pages**

In `apps/web/src/app/input/page.tsx` and `apps/web/src/app/result/[runId]/result-client.tsx`, show this text when `dataset_kind !== "real_curated"`:

```tsx
<div role="alert" className="warning">
  当前使用样例或未审核数据，不能作为真实填报依据。请先在后台完成湖北官方数据下载、解析、质检和晋级。
</div>
```

- [ ] **Step 6: Add E2E checks**

In `apps/web/tests/e2e/recommendation.spec.ts`, add expectations:

```ts
await expect(page.getByText("Doctor.Peak / MiniMax")).toBeVisible();
await expect(page.getByText(/MiniMax:/)).toBeVisible();
await expect(page.getByText(/数据类型:/)).toBeVisible();
await expect(page.getByText("当前使用样例或未审核数据，不能作为真实填报依据。")).toBeVisible();
```

- [ ] **Step 7: Run web checks**

Run:

```powershell
npm --workspace apps/web run typecheck
npm --workspace apps/web run test:e2e
```

Expected: typecheck passes and E2E sees the new status text.

- [ ] **Step 8: Commit UI diagnostics**

```powershell
git add packages/shared-types/src/index.ts apps/web/src/lib/api.ts apps/web/src/app/admin/admin-client.tsx apps/web/src/app/input/page.tsx apps/web/src/app/result/[runId]/result-client.tsx apps/web/tests/e2e/recommendation.spec.ts
git commit -m "feat(web): show minimax and data authenticity status"
```

## Task 6: Source-Aware Downloader

**Files:**
- Create: `services/data/hubei/downloader.py`
- Modify: `services/data/hubei/build_dataset.py`
- Modify: `data/source_registry/hubei_sources.yaml`
- Create: `tests/test_hubei_downloader.py`

- [ ] **Step 1: Add source registry parser hints**

For each source in `data/source_registry/hubei_sources.yaml`, add fields:

```yaml
    parser: admission_lines
    raw_subdir: admission_lines
    allow_network_download: true
    requires_manual_review: true
```

Use `parser: rank_segments` and `raw_subdir: rank_segments` for the one-score-one-rank source. Use `parser: plans` and `raw_subdir: plans` for 2026 plan sources. Use `allow_network_download: false` for login-only or platform-only registry entries.

- [ ] **Step 2: Extend source dataclass**

In `services/data/hubei/source_registry.py`, add fields to `HubeiSource`:

```python
    parser: str = ""
    raw_subdir: str = ""
    allow_network_download: str = "false"
    requires_manual_review: str = "true"
```

Add these names to the `required` set only after every registry entry includes them:

```python
        "parser",
        "raw_subdir",
        "allow_network_download",
        "requires_manual_review",
```

- [ ] **Step 3: Implement downloader**

Create `services/data/hubei/downloader.py`:

```python
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from services.data.hubei.source_registry import HubeiSource, HubeiSourceRegistry


@dataclass(frozen=True)
class DownloadedSource:
    source_id: str
    source_url: str
    raw_path: Path
    sha256: str
    bytes: int
    fetched_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "source_url": self.source_url,
            "raw_path": str(self.raw_path),
            "sha256": self.sha256,
            "bytes": self.bytes,
            "fetched_at": self.fetched_at,
        }


def download_registry_sources(registry: HubeiSourceRegistry, raw_root: Path) -> list[DownloadedSource]:
    downloaded: list[DownloadedSource] = []
    for source in registry.sources:
        if source.allow_network_download.lower() not in {"1", "true", "yes"}:
            continue
        downloaded.append(download_source(source, raw_root))
    manifest = [item.to_dict() for item in downloaded]
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "download_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return downloaded


def download_source(source: HubeiSource, raw_root: Path) -> DownloadedSource:
    subdir = source.raw_subdir or source.data_type
    target_dir = raw_root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    raw_name = f"{source.source_id}.html"
    target = target_dir / raw_name
    request = urllib.request.Request(
        source.source_url,
        headers={"User-Agent": "hubei-gaokao-advisor/0.2 public-data-review"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content = response.read()
    target.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    return DownloadedSource(
        source_id=source.source_id,
        source_url=source.source_url,
        raw_path=target,
        sha256=digest,
        bytes=len(content),
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )
```

- [ ] **Step 4: Wire download command**

In `services/data/hubei/build_dataset.py`, replace the current download manifest block with:

```python
        registry = load_source_registry(root / "data" / "source_registry" / "hubei_sources.yaml")
        downloaded = download_registry_sources(registry, raw_dir)
```

Add imports:

```python
from services.data.hubei.downloader import download_registry_sources
from services.data.hubei.source_registry import load_source_registry
```

- [ ] **Step 5: Add downloader tests**

Create `tests/test_hubei_downloader.py` using `file://` URLs so tests do not require network:

```python
from __future__ import annotations

from pathlib import Path

from services.data.hubei.downloader import download_source
from services.data.hubei.source_registry import HubeiSource


def test_download_source_saves_raw_file_and_hash(tmp_path):
    source_html = tmp_path / "source.html"
    source_html.write_text("<html><body>湖北招生数据</body></html>", encoding="utf-8")
    source = HubeiSource(
        source_id="test_rank",
        title="test",
        source_url=source_html.as_uri(),
        source_type="official_public",
        owner="湖北省教育考试院",
        data_type="rank_segments",
        years="2026",
        status="verified",
        license_note="public notice",
        parser="rank_segments",
        raw_subdir="rank_segments",
        allow_network_download="true",
        requires_manual_review="true",
    )

    result = download_source(source, tmp_path / "raw" / "hubei")

    assert result.raw_path.exists()
    assert result.bytes > 0
    assert len(result.sha256) == 64
```

- [ ] **Step 6: Run downloader tests**

Run:

```powershell
python -m pytest tests/test_hubei_downloader.py -q
```

Expected: downloader tests pass without network.

- [ ] **Step 7: Commit downloader**

```powershell
git add services/data/hubei/downloader.py services/data/hubei/build_dataset.py services/data/hubei/source_registry.py data/source_registry/hubei_sources.yaml tests/test_hubei_downloader.py
git commit -m "feat(data): download hubei source registry documents"
```

## Task 7: Real Candidate Parsers

**Files:**
- Create: `services/data/hubei/parsers/__init__.py`
- Create: `services/data/hubei/parsers/rank_segments.py`
- Create: `services/data/hubei/parsers/admission_lines.py`
- Create: `services/data/hubei/parsers/plans.py`
- Modify: `services/data/hubei/build_dataset.py`
- Create: `tests/test_hubei_real_parsers.py`

- [ ] **Step 1: Define parser row contract**

All parser outputs must be dictionaries with these metadata fields:

```python
source_id
source_url
source_type
raw_document_sha256
parser_name
parser_version
parse_confidence
confidence_score
license_note
review_status
reviewer
```

Set `review_status="pending"` for all parser outputs. Promotion to `approved` happens only through `services/data/hubei/promote.py`.

- [ ] **Step 2: Implement rank segment parser**

Create `services/data/hubei/parsers/rank_segments.py`:

```python
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

PARSER_VERSION = "rank-segments-public-table-v0.2"


def parse_rank_segments_csv(path: Path, *, source_id: str, source_url: str) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "year": int(row["year"]),
                "province": "湖北",
                "category": str(row.get("category", "普通类")),
                "first_subject": str(row["first_subject"]),
                "score": int(row["score"]),
                "same_score_count": int(row["same_score_count"]),
                "cumulative_rank": int(row["cumulative_rank"]),
                "rank_start": int(row["rank_start"]),
                "rank_end": int(row["rank_end"]),
                "source_id": source_id,
                "source_url": source_url,
                "source_type": "official_public",
                "raw_document_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "parser_name": "rank_segments_csv",
                "parser_version": PARSER_VERSION,
                "parse_confidence": 0.98,
                "confidence_score": 0.98,
                "license_note": "湖北省教育考试院公开发布，仅用于人工复核后的结构化索引",
                "review_status": "pending",
                "reviewer": "",
            }
        )
    return rows
```

- [ ] **Step 3: Implement admission line parser**

Create `services/data/hubei/parsers/admission_lines.py` with a CSV-first parser:

```python
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

PARSER_VERSION = "admission-lines-public-table-v0.2"


def parse_admission_lines_csv(path: Path, *, source_id: str, source_url: str) -> list[dict[str, object]]:
    frame = pd.read_csv(path)
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "year": int(row["year"]),
                "province": "湖北",
                "batch": str(row.get("batch", "本科普通批")),
                "category": str(row.get("category", "普通类")),
                "first_subject": str(row["first_subject"]),
                "second_subject_requirement": str(row.get("second_subject_requirement", "")),
                "university_code": str(row["university_code"]),
                "university_name": str(row["university_name"]),
                "major_group_code": str(row["major_group_code"]),
                "major_group_name": str(row["major_group_name"]),
                "admission_category": str(row.get("admission_category", "平行志愿")),
                "min_score": int(row["min_score"]),
                "min_rank": int(row["min_rank"]),
                "plan_seats": "" if pd.isna(row.get("plan_seats")) else int(row.get("plan_seats")),
                "remarks": str(row.get("remarks", "")),
                "source_id": source_id,
                "source_url": source_url,
                "source_type": "official_public",
                "raw_document_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "parser_name": "admission_lines_csv",
                "parser_version": PARSER_VERSION,
                "parse_confidence": 0.98,
                "confidence_score": 0.98,
                "license_note": "湖北省教育考试院公开发布，仅用于人工复核后的结构化索引",
                "review_status": "pending",
                "reviewer": "",
            }
        )
    return rows
```

- [ ] **Step 4: Implement plan parser**

Create `services/data/hubei/parsers/plans.py`:

```python
from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_plan_adapter import HubeiPlanAdapter


def parse_plan_csv(path: Path) -> list[dict[str, object]]:
    parse_result = HubeiPlanAdapter().parse_uploaded_csv(path)
    rows: list[dict[str, object]] = []
    for candidate in parse_result.candidates:
        row = candidate.to_dict()
        row["review_status"] = "pending"
        row["source_type"] = row.get("source_type", "manual_upload")
        row["license_note"] = row.get("license_note", "manual upload requires reviewer confirmation")
        rows.append(row)
    return rows
```

- [ ] **Step 5: Add parser tests**

Create `tests/test_hubei_real_parsers.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path

from services.data.hubei.parsers.admission_lines import parse_admission_lines_csv
from services.data.hubei.parsers.rank_segments import parse_rank_segments_csv


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_parse_rank_segments_csv_outputs_pending_rows(tmp_path):
    path = tmp_path / "rank.csv"
    _write_csv(
        path,
        [
            {
                "year": 2026,
                "first_subject": "physics",
                "score": 650,
                "same_score_count": 120,
                "cumulative_rank": 5200,
                "rank_start": 5081,
                "rank_end": 5200,
            }
        ],
    )

    rows = parse_rank_segments_csv(path, source_id="official-rank-2026", source_url="https://www.hbksw.com/info/38/1746.html")

    assert rows[0]["review_status"] == "pending"
    assert rows[0]["source_type"] == "official_public"
    assert rows[0]["raw_document_sha256"]


def test_parse_admission_lines_csv_outputs_real_names(tmp_path):
    path = tmp_path / "lines.csv"
    _write_csv(
        path,
        [
            {
                "year": 2025,
                "batch": "本科普通批",
                "category": "普通类",
                "first_subject": "physics",
                "university_code": "10486",
                "university_name": "武汉大学",
                "major_group_code": "C10101",
                "major_group_name": "第01组",
                "min_score": 650,
                "min_rank": 5200,
            }
        ],
    )

    rows = parse_admission_lines_csv(path, source_id="official-line-2025", source_url="https://www.hbksw.com/info/38/1771.html")

    assert rows[0]["university_name"] == "武汉大学"
    assert rows[0]["review_status"] == "pending"
    assert "湖北样例" not in rows[0]["university_name"]
```

- [ ] **Step 6: Wire parse command**

In `services/data/hubei/build_dataset.py`, make `--parse` read normalized CSV/Excel files from `data/raw/hubei/{admission_lines,rank_segments,plans}` and write:

```text
data/candidate/hubei/admission_lines/candidate_admission_records_2023_2025.csv
data/candidate/hubei/rank_segments/candidate_rank_segments_2023_2026.csv
data/candidate/hubei/plans/candidate_admission_plans_2026.csv
```

Use `_write_csv()` already present in the file.

- [ ] **Step 7: Run parser tests**

Run:

```powershell
python -m pytest tests/test_hubei_real_parsers.py -q
```

Expected: parser tests pass.

- [ ] **Step 8: Commit parsers**

```powershell
git add services/data/hubei/parsers services/data/hubei/build_dataset.py tests/test_hubei_real_parsers.py
git commit -m "feat(data): parse official hubei candidate rows"
```

## Task 8: Quality Checks and Promotion Gate

**Files:**
- Create: `services/data/hubei/quality.py`
- Create: `services/data/hubei/promote.py`
- Modify: `services/data/hubei/build_dataset.py`
- Test: `tests/test_hubei_quality_promote.py`

- [ ] **Step 1: Implement quality checks**

Create `services/data/hubei/quality.py`:

```python
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from services.data.hubei.authenticity import FIXTURE_MARKERS


@dataclass(frozen=True)
class QualityFinding:
    severity: str
    code: str
    message: str
    file: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "file": self.file,
        }


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def check_no_fixture_markers(path: Path) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    for index, row in enumerate(read_rows(path), start=2):
        haystack = " ".join(str(value) for value in row.values()).lower()
        if any(marker.lower() in haystack for marker in FIXTURE_MARKERS):
            findings.append(
                QualityFinding(
                    severity="error",
                    code="fixture_marker",
                    message=f"fixture marker found on row {index}",
                    file=str(path),
                )
            )
    return findings


def check_source_metadata(path: Path) -> list[QualityFinding]:
    required = ["source_id", "source_url", "raw_document_sha256", "parser_version", "confidence_score", "review_status"]
    findings: list[QualityFinding] = []
    for index, row in enumerate(read_rows(path), start=2):
        missing = [key for key in required if not row.get(key)]
        if missing:
            findings.append(
                QualityFinding(
                    severity="error",
                    code="missing_source_metadata",
                    message=f"row {index} missing {', '.join(missing)}",
                    file=str(path),
                )
            )
    return findings


def check_rank_segments_monotonic(path: Path) -> list[QualityFinding]:
    rows = read_rows(path)
    findings: list[QualityFinding] = []
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((row["year"], row["first_subject"]), []).append(row)
    for key, group in grouped.items():
        ordered = sorted(group, key=lambda item: int(item["score"]), reverse=True)
        ranks = [int(item["cumulative_rank"]) for item in ordered]
        if ranks != sorted(ranks):
            findings.append(
                QualityFinding(
                    severity="error",
                    code="rank_not_monotonic",
                    message=f"cumulative ranks are not monotonic for {key[0]} {key[1]}",
                    file=str(path),
                )
            )
    return findings


def run_candidate_quality(candidate_root: Path) -> list[QualityFinding]:
    files = list(candidate_root.rglob("*.csv"))
    findings: list[QualityFinding] = []
    for path in files:
        findings.extend(check_no_fixture_markers(path))
        findings.extend(check_source_metadata(path))
        if "rank_segments" in path.name:
            findings.extend(check_rank_segments_monotonic(path))
    return findings
```

- [ ] **Step 2: Implement promotion**

Create `services/data/hubei/promote.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path

from services.data.hubei.quality import run_candidate_quality


def promote_candidates(candidate_root: Path, curated_dir: Path) -> dict[str, int]:
    findings = run_candidate_quality(candidate_root)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        raise RuntimeError(f"quality errors block promotion: {len(errors)}")
    curated_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        candidate_root / "admission_lines" / "candidate_admission_records_2023_2025.csv": curated_dir / "admission_records_2023_2025.csv",
        candidate_root / "rank_segments" / "candidate_rank_segments_2023_2026.csv": curated_dir / "rank_segments_2023_2026.csv",
        candidate_root / "plans" / "candidate_admission_plans_2026.csv": curated_dir / "admission_plans_2026.csv",
    }
    counts: dict[str, int] = {}
    for source, target in mapping.items():
        rows = _approved_rows(source)
        _write_csv(target, rows)
        counts[target.name] = len(rows)
    return counts


def _approved_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as file:
        return [row for row in csv.DictReader(file) if row.get("review_status") == "approved"]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
```

- [ ] **Step 3: Wire quality and promote commands**

In `services/data/hubei/build_dataset.py`, replace fixture quality/promotion with:

```python
from services.data.hubei.promote import promote_candidates
from services.data.hubei.quality import run_candidate_quality
```

For `quality=True`, write findings to:

```text
data/quality/hubei/data_build_report.json
data/quality/hubei/data_build_report.md
```

For `promote=True`, call:

```python
promoted_counts = promote_candidates(candidate_dir, curated_dir)
```

- [ ] **Step 4: Add quality and promotion tests**

Create `tests/test_hubei_quality_promote.py` with tests:

```python
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from services.data.hubei.promote import promote_candidates
from services.data.hubei.quality import run_candidate_quality


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_quality_blocks_fixture_marker(tmp_path):
    path = tmp_path / "candidate" / "hubei" / "admission_lines" / "candidate_admission_records_2023_2025.csv"
    _write_csv(
        path,
        [
            {
                "university_name": "湖北样例001大学",
                "source_id": "fixture",
                "source_url": "manual-upload://fixture",
                "raw_document_sha256": "abc",
                "parser_version": "x",
                "confidence_score": "0.95",
                "review_status": "approved",
            }
        ],
    )

    findings = run_candidate_quality(tmp_path / "candidate" / "hubei")

    assert any(finding.code == "fixture_marker" for finding in findings)


def test_promote_only_approved_rows(tmp_path):
    candidate = tmp_path / "candidate" / "hubei"
    rows = [
        {
            "year": "2025",
            "province": "湖北",
            "batch": "本科普通批",
            "category": "普通类",
            "first_subject": "physics",
            "university_code": "10486",
            "university_name": "武汉大学",
            "major_group_code": "C10101",
            "major_group_name": "第01组",
            "min_score": "650",
            "min_rank": "5200",
            "source_id": "official-line-2025",
            "source_url": "https://www.hbksw.com/info/38/1771.html",
            "raw_document_sha256": "abc",
            "parser_version": "admission-lines-public-table-v0.2",
            "confidence_score": "0.98",
            "review_status": "approved",
        }
    ]
    _write_csv(candidate / "admission_lines" / "candidate_admission_records_2023_2025.csv", rows)

    counts = promote_candidates(candidate, tmp_path / "curated" / "hubei")

    assert counts["admission_records_2023_2025.csv"] == 1
```

- [ ] **Step 5: Run quality tests**

Run:

```powershell
python -m pytest tests/test_hubei_quality_promote.py -q
```

Expected: quality and promotion tests pass.

- [ ] **Step 6: Commit quality gate**

```powershell
git add services/data/hubei/quality.py services/data/hubei/promote.py services/data/hubei/build_dataset.py tests/test_hubei_quality_promote.py
git commit -m "feat(data): gate curated promotion by quality checks"
```

## Task 9: Runtime Recommendation Data Status

**Files:**
- Modify: `services/recommender/models.py`
- Modify: `apps/api/app/main.py`
- Modify: `packages/shared-types/src/index.ts`
- Test: `tests/test_recommendation_run_api.py`

- [ ] **Step 1: Add data status to recommendation output**

In `services/recommender/models.py`, add `data_status: dict[str, object] | None = None` to `RecommendationRun` and include it in `to_dict()`:

```python
"data_status": self.data_status or {},
```

- [ ] **Step 2: Set run data status**

In `apps/api/app/main.py`, after `run = plan_builder.build(...)`, add:

```python
    run.data_status = repo.dataset_status.to_dict()
```

- [ ] **Step 3: Include data status in trace**

In `_build_trace()`, add:

```python
        "data_authenticity": repo.dataset_status.to_dict(),
```

- [ ] **Step 4: Add API assertion**

In `tests/test_recommendation_run_api.py`, assert:

```python
assert "data_status" in response.json()
assert response.json()["data_status"]["dataset_kind"] in {"fixture_seed", "real_curated", "mixed", "missing"}
```

- [ ] **Step 5: Run recommendation API tests**

Run:

```powershell
python -m pytest tests/test_recommendation_run_api.py tests/test_v02_data_productization.py -q
```

Expected: recommendation and trace tests pass.

- [ ] **Step 6: Commit runtime status**

```powershell
git add services/recommender/models.py apps/api/app/main.py packages/shared-types/src/index.ts tests/test_recommendation_run_api.py
git commit -m "feat(recommender): expose data authenticity in runs"
```

## Task 10: Real Data Operator Runbook

**Files:**
- Modify: `README.md`
- Create: `docs/operations/minimax-and-data.md`
- Create: `data/curated/hubei/README.md`

- [ ] **Step 1: Add local MiniMax setup**

Add to `README.md`:

````markdown
### MiniMax / Doctor.Peak

Doctor.Peak is explanation-only. It never changes recommendation ordering.

PowerShell:

```powershell
$env:MINIMAX_API_KEY="your_minimax_key"
$env:MINIMAX_BASE_URL="https://api.minimax.io/v1"
$env:MINIMAX_MODEL="MiniMax-M3"
$env:MINIMAX_API_STYLE="responses"
npm run api
```

Check status:

```powershell
curl.exe http://127.0.0.1:8000/api/admin/doctor-peak/status
curl.exe -X POST http://127.0.0.1:8000/api/admin/doctor-peak/test
```
````

- [ ] **Step 2: Add data mode docs**

Add to `README.md`:

````markdown
### Data Modes

- `ALLOW_FIXTURE_DATA=true`: local demo mode. The UI shows a visible warning and data is not suitable for real volunteer filling.
- `REQUIRE_REAL_DATA=true`: strict mode. Recommendation runs return `503 real_data_required` until real curated rows are ready.
- `APP_ENV=production`: strict mode is always enabled.

Real-data build:

```powershell
npm run data:hubei:download
npm run data:hubei:parse
npm run data:hubei:quality
npm run data:hubei:promote
npm run db:seed:hubei
```
````

- [ ] **Step 3: Add operator runbook**

Create `docs/operations/minimax-and-data.md` with sections:

```markdown
# MiniMax and Hubei Data Operations

## MiniMax Diagnosis

1. Start the API after setting `MINIMAX_API_KEY`.
2. Open `/api/admin/doctor-peak/status`.
3. If `configured=false`, the API process did not receive the key.
4. If `configured=true` and probe fails, inspect `error_code` and MiniMax HTTP status.
5. Fallback is expected to keep the app usable; it is not a ranking failure.

## Data Authenticity

1. Open `/api/data/status`.
2. `dataset_kind=real_curated` means reviewed official rows are active.
3. `dataset_kind=fixture_seed` means the result table is demo-only.
4. `fixture_marker_count > 0` blocks production and strict mode.

## Official Data Flow

1. Download public source registry documents.
2. Parse into candidate CSV with `review_status=pending`.
3. Run quality checks.
4. Manually review and mark trusted rows `approved`.
5. Promote approved rows to curated CSV.
6. Seed Postgres.

## Safety Rules

- Do not automate login, captcha, candidate account, or personal destination tracking.
- OCR rows remain pending until human review.
- Raw official images and PDFs stay local or artifact-only.
- Curated CSV rows must keep source URL, sha256, parser version, confidence, license note, and review status.
```

- [ ] **Step 4: Add curated README**

Create `data/curated/hubei/README.md`:

```markdown
# Hubei Curated CSV

Runtime CSV in this directory must be reviewed before real recommendation use.

Required metadata per row:

- `source_id`
- `source_url`
- `source_type`
- `raw_document_sha256`
- `parser_name`
- `parser_version`
- `parse_confidence`
- `confidence_score`
- `license_note`
- `review_status`
- `reviewer`

Rows containing fixture markers such as `fixture`, `湖北样例`, or `curated-fixture-seed` are demo-only and blocked in production.
```

- [ ] **Step 5: Commit docs**

```powershell
git add README.md docs/operations/minimax-and-data.md data/curated/hubei/README.md
git commit -m "docs: explain minimax and hubei data operations"
```

## Task 11: Full Verification Gates

**Files:**
- No source edits unless a gate fails.

- [ ] **Step 1: Python tests**

Run:

```powershell
python -m pytest
```

Expected: all tests pass.

- [ ] **Step 2: Ruff**

Run:

```powershell
ruff check .
```

Expected: no lint findings.

- [ ] **Step 3: Mypy**

Run:

```powershell
mypy services apps/api tests
```

Expected: no type errors.

- [ ] **Step 4: Web lint**

Run:

```powershell
npm --workspace apps/web run lint
```

Expected: lint passes.

- [ ] **Step 5: Web typecheck**

Run:

```powershell
npm --workspace apps/web run typecheck
```

Expected: TypeScript passes.

- [ ] **Step 6: Web build**

Run:

```powershell
npm --workspace apps/web run build
```

Expected: Next.js build succeeds.

- [ ] **Step 7: E2E**

Run:

```powershell
npm --workspace apps/web run test:e2e
```

Expected: all Playwright E2E tests pass.

- [ ] **Step 8: Manual MiniMax local check**

Run with a real key:

```powershell
$env:MINIMAX_API_KEY="your_minimax_key"
npm run api
```

In another terminal:

```powershell
curl.exe http://127.0.0.1:8000/api/admin/doctor-peak/status
curl.exe -X POST http://127.0.0.1:8000/api/admin/doctor-peak/test
```

Expected: status shows `configured=true`, masked key, model, endpoint style, and the probe returns `status=ok` or a specific MiniMax error code.

- [ ] **Step 9: Manual strict-data local check**

Run:

```powershell
$env:REQUIRE_REAL_DATA="true"
npm run api
```

Then submit a recommendation request from the UI.

Expected: the API rejects the run with `503 real_data_required` until real curated rows are promoted. With `ALLOW_FIXTURE_DATA=true` in development, the UI shows a visible demo-data warning.

## Acceptance Criteria

- MiniMax missing-key state is visible in admin and API status, not only buried in the result explanation.
- MiniMax configured state shows a masked key, base URL, model, endpoint style, and latest call status.
- MiniMax fallback remains deterministic and ranking-neutral.
- No raw name, phone, ID card, or other personal identifier is sent to the LLM.
- `/api/data/status` reports `dataset_kind`, `real_curated_ready`, `contains_fixture_rows`, and `fixture_marker_count`.
- The UI never displays fixture recommendations without a visible demo-data warning.
- Production and `REQUIRE_REAL_DATA=true` reject fixture-backed recommendation runs.
- Official-source parser outputs start as `review_status=pending`.
- Promotion writes only approved rows and blocks fixture markers.
- Curated rows include source URL, sha256, parser version, confidence, license note, and review status.
- All final gates in Task 11 pass.

## Commit Plan

1. `test: capture minimax status and data authenticity gaps`
2. `feat: expose minimax runtime configuration status`
3. `feat(api): add doctor peak minimax diagnostics`
4. `feat(data): guard runtime against unlabelled fixture data`
5. `feat(web): show minimax and data authenticity status`
6. `feat(data): download hubei source registry documents`
7. `feat(data): parse official hubei candidate rows`
8. `feat(data): gate curated promotion by quality checks`
9. `feat(recommender): expose data authenticity in runs`
10. `docs: explain minimax and hubei data operations`

## Self-Review

- Spec coverage: MiniMax failure, fake backend data, source registry, raw/candidate/curated layers, review gate, UI diagnostics, docs, and verification gates are all mapped to tasks.
- Placeholder scan: No task relies on an unnamed file or an undefined command.
- Type consistency: `DataRuntimeStatus`, `DoctorPeakStatus`, `DatasetAuthenticity`, and MiniMax status fields use the same names across API, frontend, and tests.
