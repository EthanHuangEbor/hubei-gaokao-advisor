# Crawler Policy

Allowed:

- Official public downloads.
- Official public webpages.
- Admin-uploaded official PDF, Excel, CSV.
- User-exported non-sensitive volunteer draft files.

Forbidden:

- Candidate-login automation.
- Captcha bypass.
- Asking for account, password, SMS code, ID-card suffix, or registration number.
- Storing personal candidate destinations.
- Using OCR output directly as approved production data.

Each parser must emit `confidence_score`, `parser_version`, source metadata, and review status.

