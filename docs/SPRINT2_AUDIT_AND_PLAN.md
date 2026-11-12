# SignalBridge Sprint 2 — Audit & implementation plan
Date: 12 November 2026 | Deadline: 17 November 2026, 12:00 Asia/Ho_Chi_Minh

## Baseline
- Sprint 1 is local FastAPI + SQLite + static HTML/JS, Docker optional.
- Its historical 16 offline tests passed on 12 Nov. **Do not claim that real X DMs were sent.**
- Source is not a production-grade multi-user app. Do not publicly expose the development server.
- Delivery is only valid with an authorized user-context X token, explicit tester consent, allowlisted numeric user ID, a human-approved exact message, and permission/credits from X.
- X API use must obey the applicable X developer policies. No unofficial scraping or browser login automation.
- The operator has not supplied an X user token, test-recipient consent, or X credits in this repository.

## Findings and prioritization
| Priority | Finding | Evidence | Planned action |
|---|---|---|---|
| P0 | No CI evidence for the imported Sprint 1 | No Actions workflows in original tree | Add Python 3.10 and 3.12 offline CI, preserve existing tests |
| P0 | X recent-post discovery was single-page only | `app/x_api.py` used `max_results=10` without `next_token` | Bounded search pagination (max 2 API requests / 20 authors) and tests |
| P0 | X reply scan was first-page only | `get_replies` read one page | Bounded next-token traversal; do not claim a complete sync |
| P0 | No verified real-X end-to-end | No auth credentials or platform evidence | Keep live sends disabled; only test with authorized consenting account; disclose limits |
| P0 | No final recorded demo or submission | Script and write-up drafts only | Record 3–5m genuine demo; produce final one-page write-up |
| P1 | Seed-account expansion is absent | Only segment/mock/manual/X query input | Add bounded seed-account workflow using supported X APIs |
| P1 | Relevance scores uncalibrated | Substring keyword matching in `core.rank` | Word-boundary matching and a compact quality benchmark |
| P1 | Local write guard is not authentication | Static `X-Local-Operator` value in frontend | Clarify local-only threat model; add origin/host checks without breaking browser workflow |
| P1 | Identity dedup may miss combined handle + ID changes | Send aliases lock observed IDs and handles only | Explicit reconciliation/identity checks, tests |
| P1 | Limited X reply/event semantics | Current local draft state and first-event audit | Sync cursors and conservative completeness reporting; no auto DM |
| P2 | `/api/state` returns unbounded data | `snapshot()` lists all campaigns/prospects/drafts | Apply limits/pagination after critical path is stable |

## Batch A (implemented on feature branch)
- [x] Create isolated feature branch.
- [x] Add bounded X discovery/reply read pagination.
- [x] Add offline tests for pagination, author dedup, sender filter, partial failures, disabled reads.
- [x] Add offline GitHub Actions matrix (Python 3.10/3.12).
- [ ] Confirm GitHub Actions jobs finish successfully. On 12 Nov, run https://github.com/NTA1210/SignalBridge/actions/runs/43185101371 reported failure **before any recorded job step** (both Python versions): no pytest output is available; root cause is not established. Inspect Actions account/runner configuration and rerun. Do not claim tests passed.

## Batch B (next)
- [ ] Investigate X permissions and actual user-context access via an operator-owned account; **do not enable live mode by default**. Operator has not provided test-account consent/credentials. Runtime UI now labels configured-but-unverified X mode.
- [x] Implement up to 3 seed-handle **mention-based recent-post search**, explicitly *not* follower expansion, with a 2-request cap and UI cost confirmation. Tests added; run remains unverified.
- [x] Improve exact-word relevance scoring (including `AI`) to avoid substring false positives; add regression tests. Drafting still needs manual evidence review.
- [x] Show `pages_scanned`, `has_more` and `complete` for X reply scanning; UI warns of incomplete results. Tests added; live read unverified.
- [x] Add local trusted-host and cross-origin write restrictions with offline security tests. This is still **not user authentication**.
- [ ] Add concurrency stress tests and handle/ID identity reconciliation; existing Sprint 1 alias/ambiguous-timeout tests remain in place. New stubbed real-transport partial reply sync test added.

## Batch C (submission)
- [ ] Clean clone + setup within 15 minutes on candidate hardware.
- [ ] Record actual 3–5 minute screen demo (synthetic vs real clearly labeled).
- [ ] Finalize one-page write-up: workflow, system design, tradeoffs, costs, AI assistance and verification.
- [ ] Review repository for credentials, user data and documentation truthfulness.
- [ ] Candidate explicitly authorizes submission; then submit in existing HR thread no later than 17 Nov 12:00 GMT+7.

## Exit gates
1. All existing 16 tests **and** new regression tests pass.
2. Mock mode is genuinely executable end-to-end, creates persistent records, refuses repeat sends.
3. Live mode is opt-in, restricted, never used on strangers, and no action is represented as live unless confirmed by real API response.
4. Setup instructions include missing permissions/keys, constraints and cost caveats.
5. Video and one-page write-up match what was actually demonstrated.
