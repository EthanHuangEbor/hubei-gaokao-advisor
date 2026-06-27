CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS provinces (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS hubei_subject_types (
  id SERIAL PRIMARY KEY,
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  label TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS universities (
  id SERIAL PRIMARY KEY,
  university_code TEXT UNIQUE NOT NULL,
  university_name TEXT NOT NULL,
  province TEXT,
  city TEXT,
  is_private BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS university_aliases (
  id SERIAL PRIMARY KEY,
  university_code TEXT NOT NULL REFERENCES universities(university_code),
  alias TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS major_categories (
  id SERIAL PRIMARY KEY,
  category_code TEXT UNIQUE NOT NULL,
  category_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS majors (
  id SERIAL PRIMARY KEY,
  major_code TEXT NOT NULL,
  major_name TEXT NOT NULL,
  category_code TEXT
);

CREATE TABLE IF NOT EXISTS major_groups (
  id SERIAL PRIMARY KEY,
  university_code TEXT NOT NULL,
  major_group_code TEXT NOT NULL,
  major_group_name TEXT NOT NULL,
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  second_subject_requirement TEXT NOT NULL,
  UNIQUE (university_code, major_group_code)
);

CREATE TABLE IF NOT EXISTS data_sources (
  id TEXT PRIMARY KEY,
  source_url TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_type TEXT NOT NULL,
  fetched_at TIMESTAMPTZ,
  published_at TIMESTAMPTZ,
  parser_version TEXT,
  confidence_score NUMERIC(4,3) NOT NULL DEFAULT 0,
  license_note TEXT,
  review_status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS admission_records (
  id BIGSERIAL PRIMARY KEY,
  year INT NOT NULL CHECK (year IN (2023, 2024, 2025)),
  province TEXT NOT NULL DEFAULT '湖北',
  batch TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '普通类',
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  second_subject_requirement TEXT,
  university_code TEXT NOT NULL,
  university_name TEXT NOT NULL,
  major_group_code TEXT NOT NULL,
  major_group_name TEXT NOT NULL,
  admission_category TEXT,
  min_score INT NOT NULL CHECK (min_score BETWEEN 0 AND 750),
  min_rank INT NOT NULL CHECK (min_rank > 0),
  plan_seats INT,
  source_id TEXT,
  source_url TEXT NOT NULL,
  confidence_score NUMERIC(4,3) NOT NULL,
  parser_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (year, province, batch, category, first_subject, university_code, major_group_code)
);

CREATE TABLE IF NOT EXISTS admission_plans (
  id BIGSERIAL PRIMARY KEY,
  year INT NOT NULL,
  province TEXT NOT NULL,
  batch TEXT NOT NULL,
  category TEXT NOT NULL,
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  second_subject_requirement TEXT NOT NULL,
  university_code TEXT NOT NULL,
  university_name TEXT NOT NULL,
  major_group_code TEXT NOT NULL,
  major_group_name TEXT NOT NULL,
  major_code TEXT NOT NULL,
  major_name TEXT NOT NULL,
  plan_seats INT NOT NULL CHECK (plan_seats > 0),
  tuition INT,
  schooling_years TEXT,
  campus TEXT,
  is_sino_foreign BOOLEAN DEFAULT FALSE,
  is_private BOOLEAN DEFAULT FALSE,
  notes TEXT,
  physical_limit_note TEXT,
  single_subject_limit_note TEXT,
  source_id TEXT,
  confidence_score NUMERIC(4,3) NOT NULL
);

CREATE TABLE IF NOT EXISTS rank_segments (
  id BIGSERIAL PRIMARY KEY,
  year INT NOT NULL,
  province TEXT NOT NULL,
  category TEXT NOT NULL,
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  score INT NOT NULL,
  same_score_count INT NOT NULL,
  cumulative_rank INT NOT NULL,
  rank_start INT NOT NULL,
  rank_end INT NOT NULL,
  source_id TEXT,
  confidence_score NUMERIC(4,3) NOT NULL
);

CREATE TABLE IF NOT EXISTS same_rank_reference_groups (
  id BIGSERIAL PRIMARY KEY,
  target_year INT NOT NULL,
  history_year INT NOT NULL,
  province TEXT NOT NULL,
  first_subject TEXT NOT NULL,
  candidate_rank INT NOT NULL,
  rank_window_start INT NOT NULL,
  rank_window_end INT NOT NULL,
  university_code TEXT NOT NULL,
  university_name TEXT NOT NULL,
  major_group_code TEXT NOT NULL,
  major_group_name TEXT NOT NULL,
  min_score INT NOT NULL,
  min_rank INT NOT NULL,
  rank_gap INT NOT NULL,
  reference_type TEXT NOT NULL CHECK (reference_type IN ('observed_min_rank_nearby', 'estimated_available_group')),
  confidence_score NUMERIC(4,3) NOT NULL
);

CREATE TABLE IF NOT EXISTS destination_aggregates (
  id BIGSERIAL PRIMARY KEY,
  province TEXT NOT NULL,
  first_subject TEXT NOT NULL,
  rank_window_start INT NOT NULL,
  rank_window_end INT NOT NULL,
  sample_count INT NOT NULL,
  aggregate_json JSONB NOT NULL,
  k_anonymity_passed BOOLEAN NOT NULL DEFAULT FALSE,
  source_id TEXT
);

CREATE TABLE IF NOT EXISTS raw_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id TEXT,
  file_name TEXT NOT NULL,
  sha256_hash TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS parse_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_document_id UUID,
  parser_version TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw_document_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  raw_document_id UUID,
  reviewer_note TEXT,
  review_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_quality_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  province TEXT NOT NULL,
  year INT NOT NULL,
  first_subject TEXT NOT NULL CHECK (first_subject IN ('physics', 'history')),
  second_subjects JSONB NOT NULL,
  score INT NOT NULL,
  rank INT NOT NULL,
  batch TEXT NOT NULL,
  preferences JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id UUID,
  result_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_items (
  id BIGSERIAL PRIMARY KEY,
  recommendation_run_id UUID NOT NULL,
  major_group_code TEXT NOT NULL,
  tier TEXT NOT NULL,
  result_json JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS volunteer_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recommendation_run_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS volunteer_plan_items (
  id BIGSERIAL PRIMARY KEY,
  volunteer_plan_id UUID NOT NULL,
  position INT NOT NULL,
  major_group_code TEXT NOT NULL,
  tier TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_advice_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id TEXT NOT NULL,
  model TEXT NOT NULL,
  endpoint_style TEXT NOT NULL,
  latency_ms INT,
  token_usage JSONB,
  input_redacted_hash TEXT NOT NULL,
  output_json JSONB,
  error_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS compliance_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  event_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skill_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_name TEXT NOT NULL,
  source_url TEXT,
  license TEXT,
  adopted BOOLEAN NOT NULL DEFAULT FALSE,
  adoption_method TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS skill_audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_name TEXT NOT NULL,
  audit_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
