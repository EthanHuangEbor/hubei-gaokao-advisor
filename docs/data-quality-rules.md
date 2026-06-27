# Data Quality Rules

Implemented checks include:

- `admission_records.year` must be 2023, 2024, or 2025.
- First subject must be `physics` or `history`.
- `major_group_code` is required.
- `min_rank` must be positive.
- `min_score` must be 0-750.
- Duplicate `(year, first_subject, university_code, major_group_code)` is an error.
- `confidence_score < 0.85` is excluded from recommendation pool.
- `source_url` is required.
- 2026 plans require major group, major name, and seats.
- Rank segment coverage is checked and warns on thin coverage.

OCR-derived rows default to `review_status=pending` and must not enter production recommendations until reviewed.

