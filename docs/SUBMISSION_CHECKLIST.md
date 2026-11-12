# Final delivery checklist — GenAI Fund

Deadline from HR: **Tuesday, 17 November 2026, 12:00 PM (GMT+7)**.

## Complete so far

- [x] Candidate explicitly confirmed participation to HR on 12/11/2026 (do not send again).
- [x] Documented the official technical requirements and consent/privacy restrictions.
- [x] Created local working prototype with synthetic prospect discovery, evidence scoring, drafts, human approval, mock sending, immutable lock on recipient and reply simulation.
- [x] Added optional official X v2 adapter (not validated with real credentials).
- [x] Added installation guide, architecture, test suite, demo script and write-up draft.
- [x] Chromium desktop/mobile UI smoke passed with locally bridged FastAPI backend; zero JavaScript errors.
- [ ] Independently inspect browser on the user's own machine and repeat end-to-end workflow.

## Required before submitting

- [ ] Read full HR brief again and resolve any changed instructions.
- [ ] Run `python -m pytest -q` and `python scripts/smoke_demo.py` from a clean install. Sprint 2 Actions attempt failed with **no job steps recorded** (https://github.com/NTA1210/SignalBridge/actions/runs/43185101371); diagnose runner/account configuration and do not claim tests passed.
- [ ] If possible, test legitimate X access with a consenting account; otherwise clearly state what is mock and why. Never fabricate send event IDs or scrape without permission.
- [ ] Update one-page write-up with *actual* outcomes and observed API costs/limitations.
- [ ] Record a genuine 3–5 minute video showing an unedited end-to-end run, errors/limitations and the audit log.
- [ ] Remove `.env`, `outreach.db`, tokens, private data and other secrets before sharing source.
- [x] Candidate-owned public repository created: https://github.com/NTA1210/SignalBridge. Before submission verify HR can access the intended branch and files. Sprint 2 is currently on draft PR #1; do not imply it is merged.
- [ ] Check setup on a clean laptop under 15 minutes, including dependency install.
- [ ] Submit repo/hosted link + setup steps, video and one-page explanation by **17/11 noon GMT+7**.
- [ ] Verify outgoing application email/ATS receipt and update tracker only after real submission.

## Next sessions (suggested)

**12 Nov:** Operator reviews Sprint 1 code/demo and scope. **13–14 Nov:** Validate X developer-access constraints, improve live source evidence and scoring without prohibited scraping. **15 Nov:** Tighten UI and exception paths. **16 Nov:** Candidate screen-records, prepares one-page writeup, retests clean setup. **Before noon 17 Nov:** Submit complete packet and verify.
