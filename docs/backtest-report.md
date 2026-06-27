# Backtest Report

The current MVP includes a fixture backtest runner in `services/recommender/backtest.py`.

Because the repository currently ships with虚构湖北 fixtures, this report does not claim real accuracy. It validates the pipeline shape only:

- Build candidate samples.
- Generate recommendations with historical rows.
- Count tier output.
- Report data missing rate.

Real 2025 backtest must be rerun after official 2023-2025 admission records and 2026 plan data pass quality audit.

No frontend copy may advertise “准确率” before a real official-data backtest exists.

