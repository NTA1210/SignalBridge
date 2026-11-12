# Continue SignalBridge in a new ChatGPT conversation

## Goal and owner
Repository: https://github.com/NTA1210/SignalBridge
Project: GenAI Fund (AI Application Engineer Internship / FDE) take-home. The candidate confirmed participation to hr@genaifund.ai on 12 Nov 2026. **Submission deadline: 17 Nov 2026, 12:00 (Asia/Ho_Chi_Minh).** Never claim the exercise was already submitted.

## Original brief
https://docs.google.com/document/d/1SLHdAz1NNmxZ7OOkEKKsWkEMV48oDTxtbQjv-MiXdj0/edit

Build a **working, independent prototype** to:
- discover relevant AI/robotics builders, founders and researchers using target segments or seed accounts;
- display evidence-backed fit/rank reasons;
- draft personalized outreach DMs grounded in evidence;
- require human review before each send, avoid duplicate recipients across runs/campaigns;
- show delivery/replies/follow-ups and clearly represent errors/unknown outcomes.

Deliverables: source/hosted prototype with **setup under 15 minutes**; a **3–5-minute video**; **one-page write-up** explaining approach, trade-offs, cost, and AI-tool usage.

HR clarified **AI Application Engineer Internship and FDE are the same role**. HR **does not provide X API keys or credits**; free tiers, mock data and controlled test accounts are acceptable. Real sends only to self/consenting participants. No scraping/automation violating X terms; no secrets in commits.

## Sprint 1 status
- Application name: **SignalBridge**.
- Stack: Python FastAPI + SQLite; static HTML/CSS/JS frontend, optional Docker.
- Tests: **16/16 passed on 12 Nov 2026** (pytest tests/test_workflow.py, fresh extract). The ZIP source integrity manifest was checked: 27/27 file hashes matched. These results are local tests, not proof of production readiness.
- Modules: `app/main.py`, `app/core.py`, `app/drafter.py`, `app/x_api.py`, `app/static/`; tests at `tests/test_workflow.py`.
- Implemented: mock discovery, heuristic relevance scoring, evidence-backed draft, manual approval, mock delivery and event/reply tracking, SQLite audit trail, recipient deduplication, safe handling of uncertain delivery.
- Real X credentials have **not** been used or tested; do not claim real DMs have been delivered.
- No public deployment, no cloud API keys, no HR submission.
- Preview pictures: `docs/ui-workflow-preview.png` and `docs/ui-mobile-preview.png`.
- Details: `README.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_MATRIX.md`, `docs/TEST_REPORT.md`, `docs/DEMO_SCRIPT.md`, `docs/ONE_PAGE_WRITEUP_DRAFT.md`, `docs/SUBMISSION_CHECKLIST.md`, `docs/VERSION_MANIFEST.json`.

## Run and test
```bash
git clone https://github.com/NTA1210/SignalBridge.git
cd SignalBridge
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000. Windows: use `.venv\\Scripts\\activate` and `copy` instead of `cp`.

## Next sprint
1. Review repo and do local smoke test on the user's machine; independently inspect actual UX.
2. Improve discovery with verifiable people/evidence and add explicit data provenance, pagination, rate and cost limits.
3. Improve personalization quality; separate template fallback from any real LLM access.
4. Keep X transport pluggable and gated by consent, user OAuth scopes, and spending cap. Verify X APIs before promising live delivery.
5. Strengthen reliability and UX, then create the 3–5-minute demo and one-page technical write-up. Only send submission to HR after user explicitly authorizes it.

## Pasteable starting request for a new conversation
"Continue the GenAI Fund FDE SignalBridge take-home using https://github.com/NTA1210/SignalBridge. Read README.md and docs/CONTINUE_IN_NEW_CHAT.md first. Audit Sprint 1, then plan and implement Sprint 2 without exposing secrets, sending unsolicited DMs, or pretending mock X calls are real. Keep tests passing and target 17 Nov 2026 at noon Vietnam time."
