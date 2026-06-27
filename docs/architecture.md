# Architecture

The repository is a monorepo:

- `apps/api`: FastAPI application.
- `apps/web`: Next.js frontend.
- `apps/worker`: lightweight parse-job worker for the local MVP, with a file-backed job store standing in for Redis/RQ until deployment wiring is available.
- `services/crawler`: source registry, parsers, fixture adapter, quality checks.
- `services/recommender`: hard filters, risk model, same-rank reference, volunteer plan builder, backtest.
- `services/llm`: MiniMax client, fallback, Doctor.Peak prompt.
- `services/compliance`: PII redaction, k-anonymity, crawler policy, source audit helpers.
- `db/migrations`: PostgreSQL schema with pgvector enabled.
- `.agents/skills`: audited skills and local project skills.

## Data Flow

1. Seed or discover source registry.
2. Store raw documents with source metadata and hash.
3. Parse CSV plan, admission-line, and rank-segment uploads with confidence score; keep Excel/PDF and low-confidence rows in manual review.
4. Route low-confidence or OCR-derived data to manual review.
5. Load approved admission records, rank segments, and plans.
6. Apply hard filters by province, batch, first subject, second subjects, tuition, private/sino-foreign preference, and confidence.
7. Score by rank gap, plan change, volatility, preference match, restrictions, and confidence.
8. Build a 45-item major-group volunteer draft with three-year ranks/scores, plan-change, volatility, group-change, same-rank reference, confidence, reasons, warnings, and source links rendered on the result page; the compare page runs the same deterministic API across five priority strategies.
9. Ask MiniMax for JSON explanation only; fallback if unavailable.

## Safety Invariant

LLM advice is never used for final ranking. The ranking is deterministic and inspectable.


## Frontend/API Boundary

The FastAPI app enables CORS for `http://localhost:3000` and `http://127.0.0.1:3000` so the browser-hosted Next.js input page can call `/api/recommendations/run` directly during local development and Playwright E2E runs.

## Verification

Playwright E2E starts both API and Web when needed, then exercises the real browser path from `/input` to `/result/[runId]` and the admin path for uploading a 2026 plan fixture, confirming its parsed candidate count, queueing a parse job, and running data-quality checks. Backend tests cover upload persistence, raw-document review status updates, CORS preflight, subject filtering, hard filters, k-anonymity, MiniMax fallback, Doctor.Peak JSON shape, and recommendation API execution.






