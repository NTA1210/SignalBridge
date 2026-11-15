# SignalBridge — 3–5 minute genuine demo recording script

Record the actual local application (not slides or a fake X session). Aim for **4:30–4:55** total. No X credentials or real outbound messages are required for the default safe demonstration.

**Before recording:** run `python scripts/verify_offline.py` and `python -m pytest -q` and capture genuine output if tests pass. Start `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Ensure `X_ENABLE_LIVE_SEND=false` and `X_ENABLE_READ=false`; use a clean local SQLite demo database, not a database with real outbound history.

| Time | Actual app interaction | Narration |
|---|---|---|
| 00:00–00:30 | Home dashboard, mode banner | “SignalBridge is a local, consent-conscious outreach prototype. Default discovery and delivery are explicitly synthetic; no stranger is contacted.” |
| 00:30–01:00 | Target `Embodied AI robotics` → Discover demo | “The demo loads fictional candidates, scored by transparent keyword evidence. Real X discovery is a separate opt-in API path.” |
| 01:00–01:35 | Select candidate and inspect evidence and reason | “Each suggestion includes a traceable reason. The demo evidence is fictional; source-supplied or X material requires validation.” |
| 01:35–02:25 | Create draft → edit → approve | “The deterministic template cites evidence without inventing familiarity, and humans approve the exact message.” |
| 02:25–03:05 | Mock send and duplicate attempt | “The event is mock-only, persisted locally. A second send is rejected to protect recipients.” |
| 03:05–03:40 | Simulate reply → audit log → refresh | “Simulated replies change the status and are tracked in SQLite. Refreshing retains the audit record.” |
| 03:40–04:15 | Open Advanced UI and X test mode documentation | “There is bounded official X recent-post and seed-mention search, plus a consent/allowlist-gated DM adapter. Real X authorization and delivery have not been verified.” |
| 04:15–04:50 | Show test output (only if really run), README and write-up | “The prototype is designed for quick local setup. We disclose limits, API access requirements, costs, and where human judgment is still needed.” |

**Recording checklist:** captured from a running app; visible Mock labels; no exposed secrets/recipient private data; 3–5 min duration; clear audio or subtitles; hosted viewable link shared in HR submission. If setup/tests fail, fix or state failures instead of fabricating PASS. **A real video has not yet been recorded.**
