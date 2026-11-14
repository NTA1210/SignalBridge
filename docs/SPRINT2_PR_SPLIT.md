# Sprint 2 PR split (replacement for monolithic PR #1)

## Why this exists
The original [PR #1](https://github.com/NTA1210/SignalBridge/pull/1) accumulated **40 commits across 19 files** covering unrelated concerns. That made review and merge safety difficult. Its original head `4ee6d87bb397522c5555b9d43579052d5dbf9750` is preserved for traceability. New independent branches start from Sprint 1 `main` commit `43f7518aaef4bf0b29e2f444e4ed97166f4441a7` and do not rewrite PR #1's history.

## Independent replacement PRs
| PR | Single purpose | Branch | Focused files |
|---|---|---|---|
| [#2](https://github.com/NTA1210/SignalBridge/pull/2) | Offline CI and repeatable regression verification | `ci/offline-regression-checks` | 4 |
| [#3](https://github.com/NTA1210/SignalBridge/pull/3) | Correct exact-token relevance ranking | `fix/relevance-token-scoring` | 2 |
| [#4](https://github.com/NTA1210/SignalBridge/pull/4) | Protect localhost operator boundary and numeric X allowlist | `security/local-operator-boundary` | 3 |
| [#5](https://github.com/NTA1210/SignalBridge/pull/5) | Present Mock vs unverified X transport accurately | `feat/mock-vs-x-transport-status` | 3 |
| [#6](https://github.com/NTA1210/SignalBridge/pull/6) | Bounded X post/seed-mention discovery | `feat/x-prospect-discovery` | 6 |
| [#7](https://github.com/NTA1210/SignalBridge/pull/7) | Bounded reply sync and honest completeness indicator | `feat/x-reply-sync-completeness` | 4 |

All are **Draft** until tests and review are verified. No PR sends real X DMs. Independent PRs may overlap files but change separate functions; re-evaluate mergeability/rebase later PRs after each merge.

## Recommended review order
1. #2 — establish reproducible offline verification (hosted GitHub Actions are blocked by a separate account billing lock, not a Python traceback).
2. #4 — local and X recipient safety controls.
3. #3 — ranking correction.
4. #6 — sourced discovery, subject to verified X search/query behavior.
5. #7 — reply sync accuracy, conditional on allowed X API access.
6. #5 — honest transport labels before recording the demo.

This is a **review order, not authorization to merge**. Resolve merge conflicts, verify full tests and make the merge decision for each PR separately.

## Final documentation
After the needed code PRs are merged, open one separate `docs/*` PR to update README/architecture/acceptance matrix and finish the one-page write-up and 3–5-minute screen recording guidance. Base claims on actual test results and openly state if Real X remained untested. **Do not copy stale assertions from #1 as if all changes were merged.**

## PR lifecycle
- Original PR #1 is superseded; preserve the old feature branch and all commits for audit.
- Close #1 rather than force-pushing/rebasing its 40-commit history into one more large PR.
- When shipping a feature, update this matrix if a split PR has been merged or replaced.
