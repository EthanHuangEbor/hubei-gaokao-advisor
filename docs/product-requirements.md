# Product Requirements

Project: `hubei-gaokao-advisor`

The MVP serves Hubei普通类本科普通批 candidates. A user enters 2026 score, rank, first subject, second subjects, and preferences. The system recommends a 45-item volunteer draft by院校专业组, split into 冲、稳、保、垫.

## In Scope

- 湖北省 only.
- 普通类、本科普通批、平行志愿.
- 首选物理 and 首选历史.
- 院校专业组 as the recommendation unit.
- Public historical admission records for 2023-2025.
- 2026 admission plan import through admin upload or fixtures.
- MiniMax JSON explanation with deterministic fallback.

## Out Of Scope

艺术类、体育类、技能高考、强基计划、综合评价、军警院校、高校专项、免费医学生、港澳独立招生、专科批.

## Acceptance Notes

The current MVP ships with虚构湖北 fixtures to prove the pipeline without inventing real school claims. Real production data must be imported from audited official or quasi-official public sources.

