export type FirstSubject = "physics" | "history";
export type Tier = "冲" | "稳" | "保" | "垫";

export interface RecommendationRequest {
  year: number;
  province: "湖北";
  batch: "本科普通批";
  category: "普通类";
  first_subject: FirstSubject;
  second_subjects: string[];
  score: number;
  rank: number;
  preferred_cities: string[];
  avoid_cities: string[];
  preferred_majors: string[];
  avoid_majors: string[];
  max_tuition?: number;
  accept_private_college: boolean;
  accept_sino_foreign: boolean;
  accept_adjustment: boolean;
  priority_strategy: "school_first" | "major_first" | "city_first" | "employment_first" | "balanced";
}

export interface RecommendationItem {
  position: number;
  plan_status: "ready" | "missing_current_plan" | string;
  university_code: string;
  university_name: string;
  major_group_code: string;
  major_group_name: string;
  included_majors: string[];
  current_plan_seats: number;
  last_year_plan_seats: number;
  plan_change_ratio: number | null;
  seat_abs_change: number;
  historical_min_rank_median?: number | null;
  years_available: number;
  plan_abs_change?: number | null;
  min_rank_2023?: number;
  min_rank_2024?: number;
  min_rank_2025?: number;
  min_score_2023?: number;
  min_score_2024?: number;
  min_score_2025?: number;
  rank_gap: number;
  rank_gap_ratio: number;
  volatility_score: number;
  risk_level: string;
  estimated_probability_band: string;
  tier: Tier;
  group_change_flag: string;
  subject_requirement_change_flag: string;
  same_rank_hit_count: number;
  same_rank_reference_confidence: number;
  preference_match_score: number;
  city_match_score: number;
  major_match_score: number;
  employment_preference_score: number;
  restriction_penalty: number;
  restriction_risk_score: number;
  data_confidence_score: number;
  reasons: string[];
  warnings: string[];
  main_reasons: string[];
  main_warnings: string[];
  source_links: string[];
  doctor_peak_explanation: string;
}

export interface DoctorPeakAdviceItem {
  major_group_id?: string;
  tier?: string;
  why?: string;
  main_risks?: string[];
  plan_change_explanation?: string;
  rank_explanation?: string;
  employment_angle?: string;
  parent_explanation?: string;
  student_explanation?: string;
  next_checks?: string[];
  [key: string]: unknown;
}

export interface DoctorPeakAdvice {
  summary?: string;
  overall_strategy?: string;
  doctor_peak_view?: string;
  items?: DoctorPeakAdviceItem[];
  risks?: string[];
  parent_talking_points?: string[];
  student_talking_points?: string[];
  next_checks?: string[];
  disclaimer?: string;
  [key: string]: unknown;
}

export interface RecommendationRun {
  run_id: string;
  strategy_note: string;
  tier_counts: Record<Tier, number>;
  items: RecommendationItem[];
  disclaimer: string;
  doctor_peak_advice?: DoctorPeakAdvice;
}

export interface DataStatus {
  runtime_source: string;
  curated_ready: boolean;
  quality_report_ready: boolean;
  counts: {
    admission_records: number;
    rank_segments: number;
    admission_plans: number;
  };
  curated_files: Record<string, string>;
  policy: string;
}

export interface RankSegment {
  year: number;
  province: string;
  category: string;
  first_subject: FirstSubject;
  score: number;
  same_score_count: number;
  cumulative_rank: number;
  rank_start: number;
  rank_end: number;
}

export interface RecommendationTrace {
  input_normalized: Record<string, unknown>;
  score_rank_validation: Record<string, unknown>;
  pool_counts: Record<string, number>;
  tier_counts: Record<string, number>;
  data_quality: Record<string, unknown>;
  warnings: string[];
  final_plan: Array<{
    position: number;
    tier: string;
    university_code: string;
    major_group_code: string;
    plan_status: string;
  }>;
}