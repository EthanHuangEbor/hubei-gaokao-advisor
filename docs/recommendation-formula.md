# Recommendation Formula

The model recommends at院校专业组 granularity.

Hard filters:

- Province, batch, category, first subject.
- Secondary subject requirement.
- Tuition cap.
- Private college acceptance.
- Sino-foreign program acceptance.
- Data confidence threshold, default 0.85.

Core metrics:

- `rank_gap = candidate_rank - historical_min_rank_median`.
- `rank_gap_ratio = rank_gap / candidate_rank`.
- `volatility_score = std(min_rank_3y) / mean(min_rank_3y)`.
- `plan_change_ratio = current_plan_seats / max(last_year_plan_seats, 1) - 1`.
- `seat_abs_change = current_plan_seats - last_year_plan_seats`.
- preference match score and restriction penalty.

Probability bands are only bands:

- 冲: `[0.20, 0.45)`.
- 稳: `[0.45, 0.75)`.
- 保: `[0.75, 0.92)`.
- 垫: `>= 0.92`.

The MVP maps rank gap to base probability, adjusts for plan change, volatility, preference match, restrictions, and confidence, then emits a tier label. It does not present precision admission probabilities.

