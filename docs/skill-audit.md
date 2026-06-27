# Skill Audit

Audit date: 2026-06-27

This project searched and reviewed GitHub-hosted Codex/Agent skill candidates before writing business code. Only skills with explicit commercial-friendly licenses are eligible for install or copy. Unclear or broad skills are learn-only.

| repo | skill name | URL | license | stars | last updated | intended use | commercial suitability | security concern | adopted | adoption method |
|---|---|---|---|---:|---|---|---|---|---|---|
| alchaincyf/nuwa-skill | huashu-nuwa | https://github.com/alchaincyf/nuwa-skill | MIT | public GitHub value at audit time | 2026-era active README examples | Generate a theme/business skill from structured research | Yes, MIT permits commercial use | Contains scripts for YouTube subtitle download via `yt-dlp`; do not run network scripts automatically. Includes public-person examples; do not copy persona examples into Doctor.Peak. | Yes | install |
| openai/skills | skill-creator | https://github.com/openai/skills | license in installed system skill bundle | not checked | bundled | Skill creation workflow and validation ideas | Learn only from installed system skill | System skill is already installed; no external copy needed. | Yes | learn only |
| openai/skills | skill-installer | https://github.com/openai/skills | license in installed system skill bundle | not checked | bundled | GitHub skill install helper | Learn only from installed system skill | Network install requires audit and approval. | Yes | learn only |
| openai-curated-remote/github | gh-fix-ci / gh-address-comments / yeet | bundled GitHub plugin skills | bundled plugin license | not checked | bundled | CI repair, PR review, publish workflow | Learn only; plugin already enabled | GitHub access can mutate repo state, only use on explicit user request. | No | learn only |
| openai-curated-remote/product-design | audit / image-to-code | bundled Product Design plugin skills | bundled plugin license | not checked | bundled | Frontend QA and product design workflows | Learn only; plugin already enabled | Can drive browser and screenshots; use only for local verification. | No | learn only |
| vercel-labs/skills | skills CLI | https://github.com/vercel-labs/skills | public repo, license must be verified per version before vendoring | not checked | active npm package used by `npx skills` | Cross-runtime skill installer | Do not copy without per-version license check | Requires `git`; first install attempt failed with `spawn git ENOENT`. | No | learn only |
| local project | github-skill-hunter | .agents/skills/github-skill-hunter/SKILL.md | project-owned | n/a | 2026-06-27 | Repeatable GitHub skill audit checklist | Yes | No external scripts. | Yes | local |
| local project | hubei-data-pipeline | .agents/skills/hubei-data-pipeline/SKILL.md | project-owned | n/a | 2026-06-27 | Hubei source registry and parser policy | Yes | No external scripts. | Yes | local |
| local project | admission-risk-model | .agents/skills/admission-risk-model/SKILL.md | project-owned | n/a | 2026-06-27 | Recommendation model review | Yes | No external scripts. | Yes | local |
| local project | minimax-advisor | .agents/skills/minimax-advisor/SKILL.md | project-owned | n/a | 2026-06-27 | MiniMax fallback and JSON advice | Yes | No external scripts. | Yes | local |
| local project | privacy-compliance-audit | .agents/skills/privacy-compliance-audit/SKILL.md | project-owned | n/a | 2026-06-27 | Privacy and k-anonymity review | Yes | No external scripts. | Yes | local |
| local project | doctor-peak | .agents/skills/doctor-peak/SKILL.md | project-owned | n/a | 2026-06-27 | Virtual Hubei gaokao employment-oriented advisor | Yes | Explicitly avoids real-person imitation and PII. | Yes | local |

## Nuwa Install Log

1. `npx skills add alchaincyf/nuwa-skill -a codex --copy -y` failed because the current environment has no `git` executable (`spawn git ENOENT`).
2. Codex `skill-installer` with GitHub direct download succeeded and installed `nuwa-skill` into `.agents/skills/nuwa-skill`.
3. `nuwa-skill` license is MIT. README states MIT and suggests `npx skills add alchaincyf/nuwa-skill`.
4. Script audit:
   - `download_subtitles.sh`: uses `yt-dlp` and external network; not used by this project.
   - `srt_to_transcript.py`: local subtitle cleanup; safe but not needed.
   - `merge_research.py`: local markdown summarizer; safe but not needed.
   - `quality_check.py`: local SKILL.md heuristics; safe for optional validation.
5. `nuwa-skill` includes public-person examples. Doctor.Peak does not copy those examples and is intentionally a theme/business advisor, not a public-person simulation.
6. `skill-creator` init script was attempted for `doctor-peak` but failed with Windows access denied when creating `.agents/skills/doctor-peak`; the project created the local skill manually with `apply_patch` and records the failure here.

## Coverage Map

- codebase analysis / architecture audit: local docs and bundled review workflows, learn-only.
- FastAPI / API design: local implementation plus official framework patterns, no third-party skill copied.
- Next.js / React / frontend testing: local implementation and Playwright test, no third-party skill copied.
- Playwright e2e testing: local Playwright config and smoke spec.
- data pipeline / ETL / scraping: local `hubei-data-pipeline` skill and adapters.
- security audit / secrets scanning: local `privacy-compliance-audit` skill.
- docs generation / README generation: local docs.
- CI repair / PR review: bundled GitHub plugin skills available, learn-only.
- Python data validation: local quality checks.
- SQLAlchemy/PostgreSQL migration: local SQL migration, no third-party skill copied.

