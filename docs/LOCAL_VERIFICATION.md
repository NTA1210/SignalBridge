# Local verification and demo readiness (Sprint 2)

**This is a runbook, not a claim that this environment has passed the tests.**

## Prerequisites
- Python 3.10 or 3.12 (project supports Python 3.10+; the CI matrix tests 3.10 and 3.12).
- A cloned copy of the intended feature branch/merged revision.
- Network access once to download Python packages; **no X account, OpenAI key or paid credits** for offline verification.

## Fresh checkout commands

```bash
git clone https://github.com/NTA1210/SignalBridge.git
cd SignalBridge
git switch ci/offline-regression-checks
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/verify_offline.py
python -m pytest -q
```

For Windows PowerShell, use `.venv\\Scripts\\Activate.ps1` instead of `source`.
The offline verification intentionally sets safe read/send flags, removes API credentials from its process environment and uses a **temporary SQLite database** that is deleted on exit. It does not send any real DM or access any cloud provider.

Expected evidence to capture:
- `PASS: offline mock workflow; no real X/OpenAI calls, no persistent test DB`
- A complete pytest passing summary, plus the Python version and git commit SHA
- Whether the app works from a clean checkout with setup completed within 15 minutes

If anything fails, record the exact traceback and **do not claim a pass**.

## Manual browser acceptance

```bash
cp .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and verify:
1. The banner says **Demo / Mock safe**, unless test-only X configuration has been explicitly set.
2. Discover fictional examples; inspect role, scoring reason, fictional provenance and evidence.
3. Create a draft, edit the exact text, approve it and send to **mock**.
4. Duplicate send must be rejected (HTTP 409), simulated reply updates activity, and refreshing preserves state.
5. Inspect Advanced: manual evidence import, optional X query, and optional seed-mention discovery. X reads are disabled by default; no API call should be made without authorized test setup.
6. Review counts: **MOCK** and **X API** sends are explicitly separated.
7. No credentials or `.env` contents appear in the browser or committed source.

Never bind to 0.0.0.0 or put this local single-user app on the public internet.

## Optional Real X test: authorization and limitations

Only attempt when a controlled X account and explicitly consenting test recipient exist:
- Use officially issued OAuth2 PKCE user-context credentials with needed X scopes and a developer plan that permits the relevant endpoints.
- Place credentials only in the local ignored `.env`; set `X_TEST_ALLOWLIST_IDS` to a numeric ID of a consenting/owned recipient.
- Before real sends, explicitly approve the exact text and enable the isolated test-send flag. Leave live sending disabled otherwise.
- Any outbound timeout/ambiguous response remains `uncertain` with no retry. Inspect X history manually before reconciliation.
- Recent search and reply scans make **at most two API requests each**; results can be incomplete.
- Record actual platform status/credits and any real event ID privately; redact recipients and tokens from the submitted demo.

No controlled X credentials or live test evidence have been supplied yet.

## CI policy: manual only

Pull requests do **not** trigger GitHub Actions. The optional workflow is dispatched manually from the Actions tab and is **not required for PR review or merge**. On this account, GitHub previously refused to start hosted jobs with the message "account is locked due to a billing issue", even though the displayed monthly usage was fully discounted. This is an account-side block, not evidence of a Python or pytest failure.

Use locally recorded verification instead:

```bash
python scripts/verify_offline.py
python -m pytest -q
```

Record the branch and commit SHA, Python version, commands and actual terminal output in each PR. Do not claim tests PASS without execution. Do not enable automatic CI just to bypass the billing issue.

## Video and submission

Record a 3–5 minute unedited screen capture of the actual application. Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md), show mock labels visibly and do not portray synthetic evidence as actual X activity. Finalize the one-page write-up from actual verification results. Deadline: 17 Nov 2026 12:00 GMT+7.
