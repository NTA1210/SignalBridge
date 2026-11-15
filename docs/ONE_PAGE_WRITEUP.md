# SignalBridge — evidence-led AI/robotics outreach

**Problem.** GenAI Fund needs meaningful conversations with AI/robotics builders, founders and researchers—not a large, low-quality list or unsolicited automated messages. SignalBridge provides a single-operator, evidence-first workflow.

**Working prototype.** A FastAPI API, SQLite database and framework-free browser UI support: choose a segment, discover fictional examples or import sourced prospects, inspect transparent relevance signals, draft a tailored DM, edit and explicitly approve it, deliver to a local Mock transport, prevent repeat sends with atomic recipient locks, and record replies/audit events. Optional official X recent-post search can identify authors (including posts mentioning up to three seed handles). It is bounded to two requests and at most 20 distinct authors per action; seed mentions do not prove a relationship with a seed account.

**Safety and operational design.** The default experience makes **zero X/OpenAI API calls**. Mock events are never labeled real. A separate opt-in X adapter uses user-authorized credentials from a local ignored environment file and requires a numeric allowlist, manually recorded recipient consent and human approval. Unknown send outcomes are locked as `uncertain`, not retried blindly. Reply scans return an explicit completeness flag because only two pages are read. The app is localhost-only, not a publicly hosted multi-user product.

**Trade-offs.** FastAPI/SQLite/static JS keeps installation simple, the state machine auditable and cost low. Keyword scoring is explainable but misses nuanced relevance. There is no integrated OAuth connection wizard, account vault, complete X inbox backfill or verified production authorization. External data may require independent checking. The original 16 Sprint 1 offline tests were reported passing; additional Sprint 2 regression tests are committed, but **the merged integrated build has not yet been independently verified passing**.

**Cost and AI-tool disclosure.** In default synthetic/template/Mock mode, external X and LLM API spend is **$0** (excluding local compute/network installation). Live X endpoints may require platform entitlements, credits and limits checked in the operator's own developer account; optional OpenAI drafting incurs separate model charges. AI coding assistance contributed to the implementation and review; the output is not assumed correct without executing tests and human inspection. Template drafting is deterministic—not an LLM call.

**Next steps.** Run full local tests and browser acceptance, verify supported X authorization only with accounts owned or explicitly consenting to tests, and record a real 3–5 minute demo. This repository demonstrates a scoped working approach, **not verified real-world X outreach**.

Repository: https://github.com/NTA1210/SignalBridge
