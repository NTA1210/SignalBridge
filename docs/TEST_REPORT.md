# Sprint 1 test report

Run with:

```bash
python -m pytest -q
```

Automated unit and API integration coverage:

- FastAPI health and local write-request guard.
- Synthetic seed ranking and explicit fictional labels.
- Message text grounded in the stored evidence.
- Approval required before sending.
- Full mock send and reply event flow.
- Duplicate drafts and duplicate sent messages rejected.
- Same recipient blocked across campaigns via normalized handle.
- Same numeric X ID blocked even when handle changes.
- No editing a message after approval.
- Live send disabled when X credentials/flag are missing.
- Consent and allowlist gate for real sending.
- Mock reply cannot mark an unsent message as replied.
- X discovery disabled by default.
- Ambiguous API error sets a permanent `uncertain` state, with no blind retry.
- Evidence required to import real prospects.
- Official X DM endpoint and DM-read parser tested with fake HTTP transport.

**Actual network calls to X:** 0. **Actual network calls to OpenAI:** 0. **Actual live DM sends:** 0. **Real employer/user acceptance:** not established. UI browser smoke and clean-machine verification: see next completed results.

## Verified Sprint 1 execution — 12 Nov 2026

```text
................                                                         [100%]
16 passed in 0.73s
```

The local HTTP smoke script also completed:

```text
PASS mock E2E: discover -> draft -> approve -> send -> duplicate blocked -> reply
```

**UI check:** Chromium executed the real HTML/CSS/JS against a TestClient bridge to the actual FastAPI backend, exercising discover → draft → approve → mock send → mock reply with **zero JavaScript page errors** at **desktop (1440 px)** and **mobile (390 px)** widths. PNGs are saved as `docs/ui-workflow-preview.png` and `docs/ui-mobile-preview.png`. The sandbox blocked direct Chromium navigation to localhost, so this is not a clean-network deployment browser test. The local Uvicorn server itself answered `GET /healthz` and served both static assets with HTTP 200.

**Remaining QA:** Run the included code on the candidate's own machine with a fresh install; review keyboard navigation, cross-browser styling, failure states, and optionally authorized X test-account delivery. Do not claim actual X DM delivery or a production OAuth connection.
