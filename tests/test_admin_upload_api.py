from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from apps.api.app.main import app

PLAN_CSV = (
    b"year,province,batch,category,first_subject,second_subject_requirement,"
    b"university_code,university_name,major_group_code,major_group_name,major_code,major_name,"
    b"plan_seats,tuition,schooling_years,campus,is_sino_foreign,is_private,notes,"
    b"physical_limit_note,single_subject_limit_note,source_id,source_url,confidence_score\n"
    b"2026,\xe6\xb9\x96\xe5\x8c\x97,\xe6\x9c\xac\xe7\xa7\x91\xe6\x99\xae\xe9\x80\x9a\xe6\x89\xb9,\xe6\x99\xae\xe9\x80\x9a\xe7\xb1\xbb,physics,\xe5\x8c\x96\xe5\xad\xa6,"
    b"HBA999,\xe6\xb9\x96\xe5\x8c\x97\xe4\xb8\x8a\xe4\xbc\xa0\xe6\xa0\xb7\xe4\xbe\x8b\xe5\xa4\xa7\xe5\xad\xa6,HBA999-P01,\xe7\x89\xa9\xe7\x90\x86\xe4\xb8\x8a\xe4\xbc\xa001\xe7\xbb\x84,080901,\xe8\xae\xa1\xe7\xae\x97\xe6\x9c\xba\xe7\xa7\x91\xe5\xad\xa6\xe4\xb8\x8e\xe6\x8a\x80\xe6\x9c\xaf,"
    b"12,5800,4\xe5\xb9\xb4,\xe6\xad\xa6\xe6\xb1\x89,\xe5\x90\xa6,\xe5\x90\xa6,admin-upload-sample,,,admin-upload,manual-upload://plan.csv,0.96\n"
)

ADMISSION_RECORDS_CSV = (
    "year,province,batch,category,first_subject,second_subject_requirement,"
    "university_code,university_name,major_group_code,major_group_name,admission_category,"
    "min_score,min_rank,plan_seats,source_id,source_url,confidence_score,parser_version\n"
    "2025,湖北,本科普通批,普通类,physics,化学,HBA999,湖北上传样例大学,"
    "HBA999-P01,物理上传01组,平行志愿,612,26000,18,admin-lines,"
    "https://www.hbksw.com/info/38/1771.html,0.96,admin-upload\n"
).encode()


def test_admin_upload_hubei_plan_persists_raw_document_metadata() -> None:
    client = TestClient(app)
    expected_hash = hashlib.sha256(PLAN_CSV).hexdigest()

    response = client.post(
        "/api/admin/upload/hubei-plan",
        files={"file": ("plan.csv", PLAN_CSV, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted_for_manual_review"
    assert payload["document_type"] == "hubei_plan"
    assert payload["filename"] == "plan.csv"
    assert payload["review_status"] == "pending"
    assert payload["sha256_hash"] == expected_hash
    assert payload["size_bytes"] == len(PLAN_CSV)
    assert payload["document_id"]
    assert payload["parse_summary"]["parser_version"] == "hubei-plan-v1"
    assert payload["parse_summary"]["candidate_count"] == 1
    assert payload["parse_summary"]["valid_count"] == 1
    assert payload["parse_summary"]["invalid_count"] == 0

    documents_response = client.get("/api/admin/raw-documents")
    assert documents_response.status_code == 200
    document = next(
        item for item in documents_response.json() if item["id"] == payload["document_id"]
    )
    assert document["filename"] == "plan.csv"
    assert document["document_type"] == "hubei_plan"
    assert document["sha256_hash"] == expected_hash
    assert document["review_status"] == "pending"
    assert document["parse_summary"]["valid_count"] == 1


def test_admin_upload_hubei_admission_records_parses_csv() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/admin/upload/hubei-admission-records",
        files={"file": ("records.csv", ADMISSION_RECORDS_CSV, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "accepted_for_manual_review"
    assert payload["document_type"] == "hubei_admission_records"
    assert payload["parse_summary"]["parser_version"] == "hubei-admission-line-v1"
    assert payload["parse_summary"]["candidate_count"] == 1
    assert payload["parse_summary"]["valid_count"] == 1
    assert payload["parse_summary"]["invalid_count"] == 0


def test_admin_raw_document_review_updates_status() -> None:
    client = TestClient(app)
    upload_response = client.post(
        "/api/admin/upload/hubei-plan",
        files={"file": ("review-plan.csv", PLAN_CSV, "text/csv")},
    )
    document_id = upload_response.json()["document_id"]

    review_response = client.post(
        f"/api/admin/raw-documents/{document_id}/review",
        json={"review_status": "approved", "reviewer_note": "fixture schema checked"},
    )

    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "approved"
    assert review_response.json()["reviewer_note"] == "fixture schema checked"

    document_response = client.get(f"/api/admin/raw-documents/{document_id}")
    assert document_response.status_code == 200
    assert document_response.json()["review_status"] == "approved"
    assert document_response.json()["reviewer_note"] == "fixture schema checked"


def test_local_frontend_cors_preflight() -> None:
    client = TestClient(app)
    response = client.options(
        "/api/recommendations/run",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"

