# Hubei Gaokao Advisor

湖北高考志愿冲稳保推荐 MVP，按“院校专业组”口径生成本科普通批平行志愿草表。

## Local Start

Generate fixtures:

```bash
python scripts/generate_fixtures.py
python scripts/import_hubei_fixtures.py
```

Start API:

```bash
uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Start web:

```bash
npm install
npm --workspace apps/web run dev
```

## Docker Compose

```bash
docker compose up --build
```

Services:

- Web: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/health

## Environment

Copy `.env.example` to `.env` and fill optional values. MiniMax is optional; when `MINIMAX_API_KEY` is missing, deterministic JSON fallback is used.

## Import Hubei Fixtures

Fixtures live in `data/fixtures/hubei`. They are虚构 but schema-realistic and contain no personal candidate information.

```bash
python scripts/generate_fixtures.py
python scripts/import_hubei_fixtures.py
```

## Upload 2026 Plan

Use `POST /api/admin/upload/hubei-plan` or the `/admin` page. Uploaded files are saved under `data/raw/uploads`, assigned a sha256 hash, and accepted for manual review. CSV plan files are parsed into candidate admission-plan rows with a visible parse summary, and CSV admission-line uploads are parsed into candidate admission-record rows with the same review metadata; Excel/PDF files remain in the manual review queue. The admin page can also queue a policy-gated parse job, and the worker records queued/running/completed status in the local MVP job store. The system does not log in to 湖北招生数智综合平台 or any candidate account system.

## Run Recommendation

Use the `/input` page or call:

```bash
curl -X POST http://localhost:8000/api/recommendations/run ^
  -H "Content-Type: application/json" ^
  -d "{\"first_subject\":\"physics\",\"second_subjects\":[\"chemistry\",\"biology\"],\"score\":610,\"rank\":26000}"
```

## MiniMax

Set:

- `MINIMAX_API_KEY`
- `MINIMAX_BASE_URL`
- `MINIMAX_MODEL`
- `MINIMAX_API_STYLE`

LLM advice only explains results. It never changes ranking.

## Nuwa Skill Audit

`nuwa-skill` was audited and installed into `.agents/skills/nuwa-skill` via direct GitHub download after `npx skills add` failed due missing `git`. See `docs/skill-audit.md`.

Doctor.Peak is local at `.agents/skills/doctor-peak/SKILL.md`.

## Doctor.Peak Boundary

Doctor.Peak is a virtual business advisor, not a public-person imitation. It cannot promise admission, cannot use personal identity data, and must explain recommendations using湖北院校专业组口径.

## Quality Gates

```bash
pytest
ruff check .
mypy services apps/api tests
npm --workspace apps/web run lint
npm --workspace apps/web run typecheck
npm --workspace apps/web run build
npm --workspace apps/web run test:e2e
```

The Playwright E2E runner starts the local FastAPI service and Next.js dev server automatically when they are not already running. Current E2E coverage includes privacy-safe input rendering, physics recommendation submission with result-card explainability fields, history recommendation submission without physics group mixing, sino-foreign exclusion, five-strategy compare generation, and admin plan upload with parsed candidate count, parse-job queueing, and data-quality checks.

The current MVP is designed to run with fixtures first. Production use requires audited official data.








