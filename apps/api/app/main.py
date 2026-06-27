from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.jobs import ParseJobStore
from apps.api.app.raw_documents import RawDocumentStore
from apps.api.app.repository import Repository
from apps.api.app.schemas import ParseJobRequest, RecommendationRequest, ReviewRequest
from services.crawler.adapters.hubei.hubei_admission_line_adapter import HubeiAdmissionLineAdapter
from services.crawler.adapters.hubei.hubei_plan_adapter import HubeiPlanAdapter
from services.crawler.quality.hubei_quality_checks import run_quality_checks
from services.llm.advice_orchestrator import AdviceOrchestrator
from services.recommender.admission_risk_model import HubeiAdmissionRiskModel
from services.recommender.models import CandidateProfile, RecommendationRun
from services.recommender.same_rank_reference_builder import SameRankReferenceBuilder
from services.recommender.volunteer_plan_builder import VolunteerPlanBuilder

ROOT = Path(__file__).resolve().parents[3]
repo = Repository(ROOT)
raw_store = RawDocumentStore(ROOT)
job_store = ParseJobStore(ROOT / ".tmp" / "jobs")
admission_line_adapter = HubeiAdmissionLineAdapter()
plan_adapter = HubeiPlanAdapter()
model = HubeiAdmissionRiskModel()
reference_builder = SameRankReferenceBuilder()
plan_builder = VolunteerPlanBuilder()
advice = AdviceOrchestrator()
RUNS: dict[str, RecommendationRun] = {}
LLM_LOGS: list[dict[str, object]] = []

app = FastAPI(title="Hubei Gaokao Advisor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hubei/sources")
def hubei_sources() -> list[dict[str, object]]:
    return repo.sources()


@app.post("/api/hubei/sources/discover")
def discover_sources() -> dict[str, object]:
    return {"sources": repo.sources(), "note": "MVP uses audited seed registry; live crawling is disabled."}


@app.post("/api/hubei/parse-jobs")
def create_parse_job(request: ParseJobRequest) -> dict[str, object]:
    job = job_store.create(request.job_type, request.payload)
    return job.to_dict()


@app.get("/api/hubei/parse-jobs")
def parse_jobs() -> list[dict[str, object]]:
    return [job.to_dict() for job in job_store.list_jobs()]


@app.get("/api/hubei/data-quality")
def data_quality() -> dict[str, object]:
    findings = run_quality_checks(repo.dataset)
    return {"findings": [finding.__dict__ for finding in findings]}


@app.post("/api/hubei/data-quality/run")
def run_data_quality() -> dict[str, object]:
    repo.reload()
    findings = run_quality_checks(repo.dataset)
    return {"findings": [finding.__dict__ for finding in findings]}


@app.get("/api/provinces")
def provinces() -> list[dict[str, str]]:
    return [{"name": "湖北", "code": "HB"}]


@app.get("/api/universities")
def universities() -> list[dict[str, str]]:
    return repo.dataset.universities


@app.get("/api/majors")
def majors() -> list[dict[str, str]]:
    return repo.dataset.majors


@app.get("/api/hubei/rank-segments")
def rank_segments() -> list[dict[str, object]]:
    return [item.__dict__ for item in repo.dataset.rank_segments]


@app.get("/api/hubei/admission-records")
def admission_records() -> list[dict[str, object]]:
    return [item.__dict__ for item in repo.dataset.admission_records]


@app.get("/api/hubei/admission-plans")
def admission_plans() -> list[dict[str, object]]:
    return [item.__dict__ for item in repo.dataset.admission_plans]


@app.post("/api/recommendations/run")
def run_recommendations(request: RecommendationRequest) -> dict[str, object]:
    candidate = CandidateProfile(
        year=request.year,
        province=request.province,
        first_subject=request.first_subject,
        second_subjects=tuple(request.second_subjects),
        score=request.score,
        rank=request.rank,
        batch=request.batch,
        category=request.category,
        preferences=request.preferences(),
    )
    refs = reference_builder.build(
        target_year=request.year,
        candidate_rank=request.rank,
        province=request.province,
        first_subject=request.first_subject,
        batch=request.batch,
        records=repo.dataset.admission_records,
    )
    items = model.recommend(candidate, repo.dataset.admission_records, repo.dataset.admission_plans, refs)
    run = plan_builder.build(run_id=str(uuid4()), candidate=candidate, items=items)
    advice_result = advice.explain(run)
    LLM_LOGS.append(advice_result.__dict__)
    RUNS[run.run_id] = run
    return run.to_dict()


@app.get("/api/recommendations/{run_id}")
def recommendation(run_id: str) -> dict[str, object]:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="recommendation run not found")
    return run.to_dict()


@app.get("/api/recommendations/{run_id}/volunteer-plan")
def volunteer_plan(run_id: str) -> dict[str, object]:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="recommendation run not found")
    return {
        "run_id": run_id,
        "items": [{"position": idx + 1, **item.to_dict()} for idx, item in enumerate(run.items)],
        "disclaimer": run.disclaimer,
    }


@app.post("/api/recommendations/{run_id}/llm-advice")
def llm_advice(run_id: str) -> dict[str, object]:
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="recommendation run not found")
    result = advice.explain(run)
    LLM_LOGS.append(result.__dict__)
    return result.output_json


@app.get("/api/admin/raw-documents")
def raw_documents() -> list[dict[str, object]]:
    return [document.to_dict() for document in raw_store.list_documents()]


@app.get("/api/admin/raw-documents/{document_id}")
def raw_document(document_id: str) -> dict[str, object]:
    document = raw_store.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="raw document not found")
    return document.to_dict()


@app.post("/api/admin/raw-documents/{document_id}/review")
def review_raw_document(document_id: str, request: ReviewRequest) -> dict[str, object]:
    document = raw_store.review(document_id, request.review_status, request.reviewer_note)
    if document is None:
        raise HTTPException(status_code=404, detail="raw document not found")
    return document.to_dict()


async def _accept_upload(file: UploadFile, document_type: str) -> dict[str, object]:
    try:
        document = await raw_store.save_upload(file, document_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "accepted_for_manual_review", "document_id": document.id, **document.to_dict()}


async def _accept_hubei_plan_upload(file: UploadFile) -> dict[str, object]:
    payload = await _accept_upload(file, "hubei_plan")
    document_id = str(payload["document_id"])
    document = raw_store.get(document_id)
    if document and document.filename.lower().endswith(".csv"):
        parse_result = plan_adapter.parse_uploaded_csv(document.saved_path)
        document = raw_store.attach_parse_result(document_id, parse_result.summary, parse_result.row_errors)
    elif document:
        document = raw_store.attach_parse_result(
            document_id,
            {
                "parser_version": plan_adapter.parser_version,
                "candidate_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "low_confidence_count": 0,
                "note": "non-csv upload kept for manual review",
            },
            [],
        )
    if document is None:
        raise HTTPException(status_code=404, detail="raw document not found")
    return {"status": "accepted_for_manual_review", "document_id": document.id, **document.to_dict()}



async def _accept_hubei_admission_records_upload(file: UploadFile) -> dict[str, object]:
    payload = await _accept_upload(file, "hubei_admission_records")
    document_id = str(payload["document_id"])
    document = raw_store.get(document_id)
    if document and document.filename.lower().endswith(".csv"):
        parse_result = admission_line_adapter.parse_uploaded_csv(document.saved_path)
        document = raw_store.attach_parse_result(document_id, parse_result.summary, parse_result.row_errors)
    elif document:
        document = raw_store.attach_parse_result(
            document_id,
            {
                "parser_version": admission_line_adapter.parser_version,
                "candidate_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "low_confidence_count": 0,
                "note": "non-csv upload kept for manual review",
            },
            [],
        )
    if document is None:
        raise HTTPException(status_code=404, detail="raw document not found")
    return {"status": "accepted_for_manual_review", "document_id": document.id, **document.to_dict()}

@app.post("/api/admin/upload/hubei-plan")
async def upload_hubei_plan(file: Annotated[UploadFile, File(...)]) -> dict[str, object]:
    return await _accept_hubei_plan_upload(file)


@app.post("/api/admin/upload/hubei-admission-records")
async def upload_hubei_admission_records(file: Annotated[UploadFile, File(...)]) -> dict[str, object]:
    return await _accept_hubei_admission_records_upload(file)


@app.get("/api/skills")
def skills() -> list[dict[str, str]]:
    return [
        {"name": "nuwa-skill", "status": "installed_for_audit"},
        {"name": "doctor-peak", "status": "local_business_skill"},
    ]


@app.post("/api/skills/audit")
def skill_audit() -> dict[str, str]:
    return {"status": "see docs/skill-audit.md"}


@app.get("/api/skills/doctor-peak")
def doctor_peak_skill() -> dict[str, str]:
    path = ROOT / ".agents" / "skills" / "doctor-peak" / "SKILL.md"
    return {"path": str(path), "status": "available" if path.exists() else "missing"}


@app.get("/api/admin/minimax-logs")
def minimax_logs() -> list[dict[str, object]]:
    return LLM_LOGS
