import type { RecommendationRequest, RecommendationRun } from "@hubei-gaokao-advisor/shared-types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface ParseSummary {
  parser_version?: string;
  candidate_count?: number;
  valid_count?: number;
  invalid_count?: number;
  low_confidence_count?: number;
  note?: string;
}

export interface RawDocument {
  id: string;
  filename: string;
  document_type: string;
  source_type: string;
  content_type: string;
  size_bytes: number;
  sha256_hash: string;
  saved_path: string;
  review_status: string;
  reviewer_note: string;
  created_at: string;
  parse_summary: ParseSummary;
  parse_errors: string[];
}

export interface UploadResponse extends RawDocument {
  status: string;
  document_id: string;
}

export interface ParseJob {
  job_id: string;
  job_type: string;
  status: string;
  payload: Record<string, unknown>;
  result_summary: string;
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface QualityFinding {
  severity: string;
  entity: string;
  message: string;
}

export async function runRecommendation(payload: RecommendationRequest): Promise<RecommendationRun> {
  const response = await fetch(`${API_BASE}/api/recommendations/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`recommendation failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchRun(runId: string): Promise<RecommendationRun> {
  const response = await fetch(`${API_BASE}/api/recommendations/${runId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`run not found: ${response.status}`);
  }
  return response.json();
}

export async function fetchRawDocuments(): Promise<RawDocument[]> {
  const response = await fetch(`${API_BASE}/api/admin/raw-documents`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`raw documents failed: ${response.status}`);
  }
  return response.json();
}

export async function uploadHubeiPlan(file: File): Promise<UploadResponse> {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE}/api/admin/upload/hubei-plan`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    throw new Error(`upload failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchParseJobs(): Promise<ParseJob[]> {
  const response = await fetch(`${API_BASE}/api/hubei/parse-jobs`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`parse jobs failed: ${response.status}`);
  }
  return response.json();
}

export async function createParseJob(jobType = "hubei_plan_parse"): Promise<ParseJob> {
  const response = await fetch(`${API_BASE}/api/hubei/parse-jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_type: jobType }),
  });
  if (!response.ok) {
    throw new Error(`create parse job failed: ${response.status}`);
  }
  return response.json();
}

export async function runDataQuality(): Promise<{ findings: QualityFinding[] }> {
  const response = await fetch(`${API_BASE}/api/hubei/data-quality/run`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`data quality failed: ${response.status}`);
  }
  return response.json();
}
