# MiniMax Integration

Environment variables:

- `MINIMAX_API_KEY`
- `MINIMAX_BASE_URL`, default `https://api.minimax.io/v1`
- `MINIMAX_MODEL`, default `MiniMax-M3`
- `MINIMAX_API_STYLE`, default `responses`
- `MINIMAX_TIMEOUT_SECONDS`, default `30`

The client first calls `/responses` in OpenAI-compatible style. It can fallback to chat completions when configured.

Privacy:

- Do not send names, ID cards, exam numbers, phone numbers, or registration numbers.
- Send only province, year, first subject, second subjects, score, rank, preferences, recommendation items, and explanation context.
- Log only `input_redacted_hash`, not complete sensitive input.

Failure:

- Missing API key returns deterministic JSON fallback.
- API failure returns deterministic JSON fallback.
- Fallback never changes recommendation ranking.

