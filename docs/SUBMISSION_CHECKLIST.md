# GenAI Fund — final candidate delivery checklist

**Deadline:** Tuesday, **17 Nov 2026 at 12:00 (GMT+7)**. Confirmation to HR was previously sent. Submission has **not** been sent.

## Product and repository
- [x] Source code on candidate-owned public repository: https://github.com/NTA1210/SignalBridge
- [x] Seven focused Sprint 2 PRs #2–#8 merged into `main`.
- [x] README, architecture, local verification runbook, demo script and one-page write-up prepared.
- [x] Default safe synthetic/Mock mode, explicit human approval, deduplication and audit trail implemented.
- [ ] Run `python scripts/verify_offline.py` then `python -m pytest -q` from latest `main`; record actual output and Python/commit SHA.
- [ ] Test the actual browser workflow on a clean setup, including installation under 15 minutes.
- [ ] Review committed files for secrets/private data (local `.env` and SQLite database must not be included).

## External integrations
- [ ] Only if legally available, verify official X read/send against owned or consenting test accounts. Never contact unconsenting strangers.
- [x] Otherwise disclose that real X authorization/delivery and optional AI API have **not** been exercised, and use Mock in demonstration.
- [ ] Verify X access plans, scopes, limits and credit costs for an actual account if relevant; do not invent price figures.

## Required submission
- [ ] Record and host an actual 3–5 minute end-to-end demo of the running application; use [demo script](DEMO_SCRIPT.md).
- [x] Draft a concise [one-page explanation](ONE_PAGE_WRITEUP.md) of architecture, trade-offs, costs and AI use.
- [ ] Replace any unverified test statements in the write-up with real results once verified.
- [ ] Reply in original HR thread with repository/setup, video URL and one-page explanation by the deadline.
- [ ] Confirm receipt; only then mark submission delivered.

**No automatic CI on PRs** (requested); optional manual GitHub Actions may remain unavailable due the account-side billing lock. This does not count as a passing or failing pytest run.
