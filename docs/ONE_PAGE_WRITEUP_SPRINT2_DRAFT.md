# SignalBridge — One-page technical write-up (working draft)

**Submission status: DRAFT — not yet submitted.** Complete the test and video evidence before sending this document.

## Problem and approach
GenAI Fund needs focused, relevant conversations with AI/robotics builders, founders and researchers. SignalBridge is a local, human-operated workflow: choose a segment, collect prospects with source evidence, review relevance, compose an evidence-grounded message, explicitly approve the exact text, send through a chosen transport, and track reply/audit state. The tool prioritizes small, explainable actions over large-scale automated outreach.

## Technical design
- **FastAPI + SQLite** keep setup short, persisted and auditable; a static web UI avoids a frontend build step.
- **Discovery:** synthetic, visibly fictional demo people; manually sourced contacts; optional official X recent-post-author search and seed-mention search (up to three handles). The latter finds authors of public posts mentioning seeds, **not** follower-graph members. X search is **not global X user search**. Sprint 2 bounds X reads to at most two pages per action.
- **Personalization:** deterministic evidence-first templates by default (no LLM involved); optional user-configured OpenAI API drafting with independent human review. Source-supplied evidence must never be portrayed as independently verified.
- **Human-in-the-loop delivery:** a DM cannot send until approved. Real X sending requires a user-authorized token, explicit opt-in, numeric recipient allowlist and consent; the default mock transport records local events **without contacting X**. Each recipient gets a durable alias-based reservation before delivery; uncertain outcomes are locked and never blindly retried.

## Trade-offs and remaining limits
This is a **single-user localhost evaluation tool**, not a hosted multitenant SaaS. Token setup remains manual: no OAuth connection wizard or encrypted customer token store. Discovery is post-author-based and keyword ranking is heuristic, so users must inspect sources and relevance. DM reply reads are bounded to two pages and expose a completeness flag; missing later pages cannot be treated as no replies. The built-in operator header is not authentication; do not deploy openly. No real X credential or consenting recipient is bundled, and **no verified live X DM has been demonstrated**.

## Costs and rules
Mock use requires no paid X or AI API. Real search/DM access requires independently obtained X authorization, appropriate endpoint permissions and any applicable paid credits; price and rate limits must be checked in the developer console for the account. Optional OpenAI drafting incurs model usage charges. Code does not scrape X or bypass its restrictions. Testing real sends is limited to owned/consenting accounts.

## AI use and validation
AI-assisted development may help draft code and messages, but each generated artifact requires source inspection, offline regression tests and human review. The deterministic baseline is **not** described as an LLM. **Before final submission:** fill in exact passing test count, GitHub CI URL, verified demo outcome, any actual API cost, and the 3–5 minute recorded video URL.

**Repository:** https://github.com/NTA1210/SignalBridge
