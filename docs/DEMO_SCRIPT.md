# 3–5 minute demo script (candidate-operated)

**Before recording:** use the actual checkout being submitted, start the server and run the test suite; ensure `X_ENABLE_READ=false` / `X_ENABLE_LIVE_SEND=false`. Set up a fresh local database for a clean demo if desired; do **not** delete prior real-send audit history. Open the app in the browser.

| Time | Action on screen | What to say |
|---|---|---|
| 00:00–00:25 | Dashboard and safety notice | “This is SignalBridge, a narrow, working prototype. Synthetic records are labeled and persist in local SQLite. Sending real X DMs is disabled in this evaluation.” |
| 00:25–01:00 | Enter `Embodied AI robotics`, click Discover demo | “Target segments are matched against known evidence. Each fictional candidate has a transparent relevance reason; for actual X data there is an optional authorized recent-post search adapter.” |
| 01:00–01:40 | Select a profile, inspect role/evidence | “Personalization uses a source-specific statement rather than inventing familiarity. For this demo the source is deliberately fictitious.” |
| 01:40–02:20 | Create a draft, edit, Approve | “An operator must see and approve the exact message; no unattended sending.” |
| 02:20–02:55 | Send mock, inspect mock event ID, try duplicate | “The send is mocked and explicitly labeled. SQLite reserves the recipient before delivery, so repeat sends are rejected even across campaigns.” |
| 02:55–03:30 | Simulate reply, inspect dashboard and audit | “Replies update the status and need-attention count. This event is simulated, not a real reply from X.” |
| 03:30–04:25 | Show `.env.example`, X adapter and test log | “For a real authorized account we use X's official DM endpoint with an OAuth user token, approved-recipient allowlist, explicit consent, and a no-retry policy for ambiguous failures. We did not enable or claim live delivery without credentials.” |
| 04:25–04:50 | Show test report and known gaps | “The tests cover core reliability. The next increment is real account verification and better semantic targeting while staying within API terms.” |

**Do not fabricate a recorded X send or suggest demo profiles are real.** If you later obtain valid access, record a separate real test to your own/consenting account and add authenticated proof to the final report.
