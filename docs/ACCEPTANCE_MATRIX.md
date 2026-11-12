# Acceptance matrix — GenAI Fund FDE take-home vs current build

**Source:** [GenAI Fund FDE Take-Home Assignment](https://docs.google.com/document/d/1SLHdAz1NNmxZ7OOkEKKsWkEMV48oDTxtbQjv-MiXdj0/edit), read 12 November 2026. This matrix separates implemented/tested behavior from external platform integration that has **not** been validated.

| Brief criterion | Sprint 1 implementation | Evidence level | Remaining gap |
|---|---|---|---|
| Input segment or seed accounts | Segment input, manual sourced prospect, X recent-post search when token supplied | Segment and manual: **implemented / tested**; X: **implemented not live-tested** | Seed-account *mention-based* search is available in the Sprint 2 branch (not follower-graph expansion) |
| Discover relevant AI/robotics people | Synthetic catalog, X recent-post authors with bounded pagination (Sprint 2 branch: at most 2 requests / 20 distinct authors), evidence URLs; keyword score | Sprint 1 demo **tested**; Sprint 2 offline tests **added but CI unverified**; actual X **not live-tested** | Small heuristic; no full account graph expansion; tune against real accounts |
| Explain why a person fits | Per-person matched keyword rationale and source evidence | **tested** | Scores not calibrated; no relevance benchmark |
| Draft personalized DMs from real evidence | Deterministic template by default, optional OpenAI API | Template **tested**; OpenAI **not live-tested** | Review for accuracy and helpful tone before send |
| Human review and explicit approval | Editable draft, state gate and append-only approval audit | **tested** | No multi-user RBAC |
| Send approved DMs from connected X account | Official user-context endpoint with opt-in token, allowlist, consent; mock provider default | Mock **tested**; X HTTP contract unit-tested with fake transport, **not real X tested** | OAuth2 PKCE session connect and live platform authorization need real account |
| Never double-message anyone | Atomic alias reservation for handle and X ID, across campaigns; no blind retries | **tested** | User changing both handle and X ID may circumvent alias; full identity resolution needed |
| Track sent and replied | Durable `mock` states; X event sync with max 2 pages in Sprint 2 branch | Sprint 1 mock **tested**; Sprint 2 test **added, CI pending**; X **not live-tested** | Still bounded/incomplete; no webhook/backfill or real reply test |
| Usable without developer beside them | Local UI + commands + `.env.example`; Docker alternative | **manual browser smoke pending** | Dependency installation required; verify clean-machine setup |
| Clear costs, limits, failures | Documented provider selection and no-auto-retry policy | **tested** for ambiguous failures | Real X credit prices/rate limits must be verified in developer console |
| 3–5 minute video | Suggested script | **not recorded** | Operator records genuine session |
| One-page write-up | Editable draft | **draft only** | Fill actual test outcomes/costs and check assertions |

**Do not claim this version fully passes the employer's requirement to operate an actual X account.** The employer allows mock data, but a good final submission should explicitly show what can and cannot be used by a recruiter today.
