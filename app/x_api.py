"""Official X API v2 adapter. No scraping, no browser automation, no token persistence."""
from __future__ import annotations
import os
import re
import httpx

BASE = "https://api.x.com/2"


class XUnavailable(Exception):
    pass


def token() -> str:
    value = os.environ.get("X_USER_ACCESS_TOKEN", "").strip()
    if not value:
        raise XUnavailable("X_USER_ACCESS_TOKEN is missing. Use Mock mode or configure an authorized user token.")
    return value


def enabled_read() -> bool:
    return os.environ.get("X_ENABLE_READ", "false").lower() == "true"


def enabled_send() -> bool:
    return os.environ.get("X_ENABLE_LIVE_SEND", "false").lower() == "true"


def allowed_ids() -> set[str]:
    return {p.strip() for p in os.environ.get("X_TEST_ALLOWLIST_IDS", "").split(",") if p.strip()}


def _headers() -> dict:
    return {"Authorization": "Bearer " + token(), "Content-Type": "application/json"}


def _request(method: str, url: str, **kwargs) -> dict:
    with httpx.Client(timeout=15.0, follow_redirects=False) as client:
        response = client.request(method, url, headers=_headers(), **kwargs)
        response.raise_for_status()
        return response.json()


def search_people(query: str) -> list[dict]:
    """Recent-post author discovery; not a global X user-search claim.

    Converts actual post text to auditable evidence and account handles to people.
    """
    if not enabled_read():
        raise XUnavailable("X reads are disabled; set X_ENABLE_READ=true after authorizing API access.")
    if not query or len(query) > 280:
        raise ValueError("Search query must be 1–280 characters")
    payload = _request("GET", BASE + "/tweets/search/recent", params={
        "query": query,
        "expansions": "author_id",
        "tweet.fields": "created_at,author_id",
        "user.fields": "name,username,description",
        "max_results": "10",
    })
    users = {u["id"]: u for u in payload.get("includes", {}).get("users", [])}
    candidates: dict[str, dict] = {}
    for post in payload.get("data", []):
        author = users.get(post.get("author_id"))
        if not author or not author.get("username"):
            continue
        handle = author["username"]
        pid = author["id"]
        if pid in candidates:
            continue
        candidates[pid] = {
            "display_name": author.get("name") or handle,
            "handle": handle, "x_user_id": pid,
            "role": "X account posting about the target segment",
            "bio": author.get("description", ""),
            "evidence_text": (post.get("text") or "")[:900],
            "evidence_url": f"https://x.com/{handle}/status/{post['id']}",
            "source_kind": "x_api_recent_post",
        }
    return list(candidates.values())


def send_dm(recipient_id: str, text: str) -> dict:
    if not enabled_send():
        raise XUnavailable("Live sending disabled; set X_ENABLE_LIVE_SEND=true deliberately.")
    if not re.fullmatch(r"\d{1,25}", recipient_id):
        raise XUnavailable("A numeric X user ID is required for live sending")
    if recipient_id not in allowed_ids():
        raise XUnavailable("Recipient not in X_TEST_ALLOWLIST_IDS. No unsolicited sending.")
    if not text.strip() or len(text) > 10000:
        raise ValueError("DM body is invalid")
    data = _request("POST", BASE + f"/dm_conversations/with/{recipient_id}/messages", json={"text": text})
    event = data.get("data", {})
    if not event.get("dm_event_id"):
        raise XUnavailable("X did not provide a DM event ID; delivery is uncertain")
    return {"remote_event_id": str(event["dm_event_id"]),
            "remote_conversation_id": str(event.get("dm_conversation_id", ""))}


def get_replies(recipient_id: str) -> list[dict]:
    """Compatibility wrapper: only matched DM events, without sync metadata."""
    return get_replies_with_meta(recipient_id)["events"]


def get_replies_with_meta(recipient_id: str) -> dict:
    """Bounded DM history; expose whether pagination was exhausted."""
    if not enabled_read():
        raise XUnavailable("X reads disabled")
    if not re.fullmatch(r"\d{1,25}", recipient_id):
        raise XUnavailable("Numeric X user ID required")
    # Bounded at 2 API calls to prevent uncontrolled cost. Callers must not
    # claim a complete inbox sync beyond the pages actually retrieved.
    events: list[dict] = []
    next_token = None
    seen_tokens: set[str] = set()
    pages_scanned = 0
    has_more = False
    for _ in range(2):
        params = {"dm_event.fields": "created_at,sender_id,text", "max_results": "20"}
        if next_token:
            params["pagination_token"] = next_token
        data = _request("GET", BASE + f"/dm_conversations/with/{recipient_id}/dm_events", params=params)
        pages_scanned += 1
        if not isinstance(data, dict):
            raise XUnavailable("Malformed X DM response")
        if data.get("errors"):
            raise XUnavailable("X returned incomplete DM data; sync not confirmed")
        events.extend(e for e in data.get("data", [])
                      if isinstance(e, dict) and str(e.get("sender_id")) == recipient_id
                      and e.get("event_type", "MessageCreate") == "MessageCreate")
        next_token = data.get("meta", {}).get("next_token")
        if not isinstance(next_token, str) or not next_token:
            has_more = False
            break
        if next_token in seen_tokens:
            # A token cycle means we cannot claim complete results.
            has_more = True
            break
        has_more = True
        seen_tokens.add(next_token)
    return {"events": events, "pages_scanned": pages_scanned,
            "has_more": has_more, "complete": not has_more}
