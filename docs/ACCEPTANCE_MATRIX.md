# GenAI Fund acceptance matrix — integrated Sprint 2 (15 Nov 2026)

Source of requirements: [official FDE brief](https://docs.google.com/document/d/1SLHdAz1NNmxZ7OOkEKKsWkEMV48oDTxtbQjv-MiXdj0/edit).

**Verification levels:** Implemented = merged code exists; historical PASS = earlier Sprint 1 run only; **unverified** = no independent integrated run/real platform evidence yet. Never equate a GitHub merge with a passed test.

| Brief requirement | Integrated implementation | Evidence and remaining gap |
|---|---|---|
| Target segment or seed accounts | Segment input; up to three seed handles searched via recent public posts mentioning seeds; manual import | Implemented; no follower-graph expansion; actual X search remains unverified |
| Find relevant AI/robotics people | Fictional local catalog, manual source, authorized X recent-post authors; max 2 read calls / up to 20 authors | Demo historically tested; live source unverified, ranking is simple |
| Evidence-backed relevance | Full-token keyword matches and explicit reasons; source URLs for X posts | Added offline regression tests; needs quality benchmark and human verification |
| Personalized DM | Evidence-only template by default; optional user-provided OpenAI key | Template historically tested; LLM provider unverified; do not imply template is LLM |
| Human review | Editable draft and explicit approval state transition | Sprint 1 historically tested |
| Send from own X account | Opt-in official X adapter, numeric allowlist and consent record; Mock transport is separate | **No live send performed**; no built-in OAuth connection/credentials provided |
| Never duplicate sends | SQLite atomic reservation and alias locks across campaigns; uncertain outcome never blindly retried | Historically tested; concurrency test added but integrated run unverified; identity changes can still evade alias linkage |
| Track sends and replies | Durable transport-labelled mock records, simulated replies, optional X DM scan with pages/has_more/complete | Mock historically tested; X reply read unverified and may be incomplete |
| Usable independently | FastAPI/SQLite browser UI, Docker option, CLI smoke, local runbook | Clean-install under 15 minutes and final browser smoke **not yet verified** |
| Costs and platform rules | No paid API in default mock mode; authorized official API only; bounded read calls and operator confirmation | Account-specific X credits, scopes and rate limit require independent validation |
| Demo video 3–5 minutes | Step-by-step recording script | **Not recorded** |
| One-page technical write-up | [Prepared](ONE_PAGE_WRITEUP.md) with disclosure of unknown tests/costs | Fill actual verification findings before submission |

**Status:** all seven focused Sprint 2 PRs (#2–#8) merged. No automatic PR CI, by user request. Historical test counts do not prove this merged version is green. Source is available; final HR submission has **not** been sent.
