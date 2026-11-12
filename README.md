# SignalBridge — GenAI Fund FDE Take-Home (Sprint 1 + Sprint 2 draft)

**Working local prototype** for researching AI/robotics prospects, scoring evidence, drafting personalized DMs, requiring human approval, sending to a safe mock transport (or an **explicitly enabled, consent-only** X API test account), and tracking sent/reply events without accidental duplicates.

**Current delivery status:** Sprint 1 local MVP + Sprint 2 improvements on a [draft PR](https://github.com/NTA1210/SignalBridge/pull/1). **Not submitted** to GenAI Fund. Real X calls have **not** been executed, and the production UX has **not** been authenticated. Sprint 1 historically reported 16/16 offline tests; Sprint 2 tests are committed but have **not yet been verified passing** because GitHub Actions jobs failed before any recorded step. See [docs/TEST_REPORT.md](docs/TEST_REPORT.md) and [docs/ACCEPTANCE_MATRIX.md](docs/ACCEPTANCE_MATRIX.md).

## 1. Run in under 15 minutes

Requires **Python 3.10+** and a network connection once to install dependencies (or Docker). From this project directory:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env              # Windows: copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Do not expose the prototype to the public internet; it is a **single-user local evaluation**, without login, encrypted token vault, multi-tenancy or public deployment hardening.

Optional Docker: `cp .env.example .env && docker compose up --build` (host port is bound to localhost only; SQLite stored in a Docker volume).

## 2. Demonstrate the entire mock workflow

1. Enter **Embodied AI robotics** and click **Discover demo**. All sample people are explicitly **fictional**. No X API requests occur.
2. Click a prospect to review the **relevance reason** and **specific evidence**.
3. Select **Create message draft**, edit the text if needed, and click **Approve message**.
4. Click **Send to mock transport**. This writes a durable send record and mock event ID to SQLite — **not an actual DM**.
5. Try sending the same DM again. The API rejects it; recipient aliases are also locked across campaigns.
6. Click **Simulate consenting reply**. The status and audit trail update to **Replied**.
7. Refresh the browser; state remains in the SQLite database `outreach.db` (which is gitignored).

The CLI smoke check repeats the same critical path:

```bash
python scripts/smoke_demo.py
```

## 3. Real sourced prospects and X adapter

The **Advanced** panel accepts a **manually supplied** prospect and source/evidence statement, an **X recent-post search query**, or up to three **seed handles** for public posts that mention those handles (seed-mention search, **not** follower-network expansion). Manual inputs are labeled as user-supplied, **not verified** by the app. X discovery uses `GET /2/tweets/search/recent` and displays post evidence URLs, not a claim to search the entire X user directory.

The application includes an X API v2 adapter using documented endpoints:

- Search recent posts: `GET /2/tweets/search/recent` (authors become prospective contacts). Search is capped at **two requests / 20 unique authors per operation**, and may consume X API credits. Seed-mention search uses the same capped official endpoint.
- Send an approved DM: `POST /2/dm_conversations/with/:participant_id/messages`.
- Check replies from one consenting recipient: `GET /2/dm_conversations/with/:participant_id/dm_events` (at most two pages, only matching senders newer than recorded send time; API response explicitly reports incomplete pagination).

**Never use X browser automation, unofficial scraping or unapproved keys.** To enable these optional features, obtain a legitimate **OAuth 2.0 PKCE user-context token**, with `dm.write`, `dm.read`, `tweet.read`, `users.read` scopes and any required credits/rate limit. Store that token **server-side only** in `.env`; never paste it into the browser, GitHub or submission.

```env
X_ENABLE_READ=true
X_ENABLE_LIVE_SEND=false
X_USER_ACCESS_TOKEN=your_authorized_user_token
X_TEST_ALLOWLIST_IDS=12345678901
```

Configuring a token is **not** proof of valid authorization or successful X delivery. The UI distinguishes MOCK from user-configured-but-unverified X mode and displays separate mock/X send totals. For read operations the UI asks for confirmation before potentially billable X API calls.

When the recipient is demonstrably yours or has explicitly consented **and** the numeric X ID is allowlisted, set `X_ENABLE_LIVE_SEND=true`. The selected prospect must have `consent_confirmed=true` in the application. The operator must still review/approve each exact message and confirm one more time before the real API call. **No batch sending / no cold outreach.** No API credentials, credits or consent have been provided for this project; the live path has not been tested with X.

**Important failure policy:** if an outbound API call times out or has an ambiguous outcome, the recipient remains locked in `uncertain`. There is **no automatic retry**. Check the authorized X account/history before deciding how to reconcile.

## 4. Optional AI drafting

Default `AI_PROVIDER=template` uses a deterministic, evidence-first message composer **without an AI API call**. This is honest and free, but should not be described as an LLM feature.

For model-assisted drafts, explicitly opt in:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

This sends the prospect's name, role, bio and evidence to OpenAI's API. Only activate with appropriate data permissions and when you're comfortable with the cost. Each generated draft still requires explicit human review. Do not represent an unverified user-provided claim as an independently verified fact.

## 5. Verify functionality

```bash
python -m pytest -q
```

The test suite includes the 16 historical Sprint 1 cases plus Sprint 2 offline regressions for X pagination, origin/host policy, seed discovery, relevance scoring and explicit sync completeness. **All real X calls are monkeypatched.** As of this draft, the new tests have not been confirmed passing: hosted CI jobs failed with no recorded steps; see [Sprint 2 plan](docs/SPRINT2_AUDIT_AND_PLAN.md). Run `python -m pytest -q` locally and share the output before claiming a pass. No tests contact real X or OpenAI.

## 6. Code layout

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI routes, state transitions, security guards |
| `app/core.py` | SQLite tables, evidence-driven prospect scoring, cross-campaign dedup |
| `app/x_api.py` | Optional official X v2 API adapter; disabled by default |
| `app/drafter.py` | Template drafting; optional model-backed drafting |
| `app/static/*` | UI (HTML/CSS/vanilla JS, deliberately no npm build step) |
| `tests/test_workflow.py` | Automated offline tests |
| `scripts/smoke_demo.py` | End-to-end HTTP verification |
| `docs/*` | Architecture, acceptance gaps, demo script, handoff and plan |

## 7. Trade-offs (important)

- **FastAPI + SQLite + no frontend framework:** the smallest maintainable first version that starts quickly on an ordinary laptop. Not a scalable SaaS production architecture.
- **Scoring is transparent keyword matching,** not an advanced semantic relevance engine; it may produce false positives/negatives and needs human review.
- **Mock transport does not prove X DM authorization or delivery.** A valid user-context token and enabled test allowlist are required to validate real delivery.
- **No built-in OAuth login flow** and no support for storing customers' encrypted credentials. User token is supplied via local environment variables only.
- **No automated conversation campaigns.** One approved outbound per recipient, by design.
- **No hosted demo/video supplied yet.** Source is runnable; submission packaging will depend on operator testing.

See [docs/ACCEPTANCE_MATRIX.md](docs/ACCEPTANCE_MATRIX.md), [docs/SPRINT2_AUDIT_AND_PLAN.md](docs/SPRINT2_AUDIT_AND_PLAN.md) and [docs/ONE_PAGE_WRITEUP_SPRINT2_DRAFT.md](docs/ONE_PAGE_WRITEUP_SPRINT2_DRAFT.md) before making any claim to HR.

## 8. Submission requirements and deadline

The original GenAI Fund brief asks for: usable source or hosted prototype with setup under 15 minutes; a 3–5 minute screen-recorded end-to-end demo; and a one-page explanation of design, trade-offs, costs, and AI use. Submission deadline in the HR message: **Tuesday, 17 November 2026, 12:00 (GMT+7)**. The user has already confirmed participation to HR; **do not re-send that confirmation**. See [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) and [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md).
