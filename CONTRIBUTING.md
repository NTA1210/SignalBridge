# Contributing to SignalBridge

## One task, one pull request

A PR represents **one independently reviewable outcome**. Implement only the minimal backend/frontend/tests/documentation needed to prove that outcome. Avoid accumulating unrelated bug fixes, refactors, UX changes and report edits.

### Workflow
1. Start from up-to-date `main`, on a fresh branch (e.g. `feat/x-prospect-discovery`, `fix/relevance-token-scoring`, `security/local-operator-boundary`, `ci/offline-regression-checks`).
2. State **goal**, **out of scope**, and **acceptance criteria** before coding. Add a narrowly scoped test that fails before the fix where applicable.
3. Keep patches focused. Prefer 1–3 deliberate commits; avoid unrelated code formatting and churn. Treat ~300 changed lines as a review checkpoint, not an absolute quota (a vertical slice may require UI + API + tests).
4. Run affected tests and the complete test suite before requesting review. Distinguish `not run`, `blocked`, `failed`, and `passed` explicitly.
5. Open a **Draft** PR while implementation/test evidence is incomplete. In the PR body include what changed, why, how it was verified, risks and known limitations.
6. If separate features touch the same file, keep different branches based on `main`; merge in a defined order and rebase/update later PRs as needed. Do not sneak unrelated changes into a shared branch.
7. Merge only after review + verified test evidence. Prefer **squash** for a concise main history. Never force-push the default branch or merge solely because GitHub labels a PR mergeable.
8. Close abandoned/superseded PRs with links to their replacements; preserve their branch/history until the replacement changes are verified.

### Core safety invariants
- Mock delivery is local **only**. Never describe its events as real X DMs.
- Real X reads/sends require legitimate authorization and rate/cost limits; real sends additionally require a controlled/consenting test recipient, allowlisted numeric X ID, and explicit human review.
- Keep credentials in local ignored environment variables, never GitHub or browser UI.
- No prohibited scraping, no unattended cold DMs, and no blind retries for ambiguous delivery.
- A failing or blocked hosted CI is **not** a passing test. If hosted CI cannot start, capture a local terminal transcript with branch, commit SHA, Python version and complete passing output.

### PR classification
| Scope | Example | Do not include |
|---|---|---|
| `ci/*` | Offline verifier, pytest workflow | New application features |
| `fix/*` | Ranking correction | UI redesign or X integration |
| `security/*` | Localhost/allowlist guards | Prospect discovery |
| `feat/*` | One user-facing workflow slice | Unrelated business workflows |
| `docs/*` | Technical write-up / final submission pack | Code behavior changes |

### No silent scope expansion
If a new problem is found during a PR, file it as a separate follow-up unless the bug blocks the exact PR's acceptance criteria or introduces immediate security risk. Explain any unavoidable scope addition in the PR description.
