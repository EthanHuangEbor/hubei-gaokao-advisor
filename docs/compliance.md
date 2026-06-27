# Compliance

## Privacy

The input form and API must not request or store:

- Name.
- ID card.
- Admission ticket number.
- Phone number.
- 14-digit gaokao registration number.
- Candidate account credentials.
- Admission screenshots or personal admission destinations.

## Same-Rank References

The system may show “同位次区间历史可达专业组参考”. It must not call this “真实考生去向” unless a public aggregated official dataset exists.

## K-Anonymity

Default `k=20`. Buckets below k show “样本不足”.

## Crawling

Public pages only. Login-only pages require manual official file upload. OCR-derived data enters manual review and is not used in production recommendations until approved.

## Disclaimer

Every recommendation result must say it is an estimate based on public historical data, current plan data, and rule models; it is not an admission promise.

