"""Sprint 2: bounded, deterministic X API behavior with no external calls."""
import pytest
from app import x_api


def test_recent_search_paginates_with_a_strict_two_request_budget(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs["params"].copy()))
        page = len(calls)
        return {
            "includes": {"users": [{
                "id": str(page), "name": "Researcher",
                "username": f"builder_{page}", "description": "AI robotics",
            }]},
            "data": [{
                "id": str(100 + page), "author_id": str(page),
                "text": "Published robot motion planning benchmarks",
            }],
            "meta": {"next_token": f"page-{page}"},
        }

    monkeypatch.setattr(x_api, "_request", fake_request)
    result = x_api.search_people("robotics")
    assert len(calls) == 2
    assert len(result) == 2
    assert calls[0][2].get("pagination_token") is None
    assert calls[1][2]["pagination_token"] == "page-1"
    assert all(p["source_kind"] == "x_api_recent_post" for p in result)
    assert result[0]["evidence_url"] == "https://x.com/builder_1/status/101"


def test_x_search_deduplicates_authors_across_pages(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")

    def fake_request(method, url, **kwargs):
        repeated = "pagination_token" in kwargs["params"]
        return {
            "includes": {"users": [{"id": "19", "name": "Researcher", "username": "builder19"}]},
            "data": [{"id": "102" if repeated else "101",
                      "author_id": "19", "text": "AI builder evidence"}],
            "meta": {} if repeated else {"next_token": "more"},
        }

    monkeypatch.setattr(x_api, "_request", fake_request)
    result = x_api.search_people("AI robotics")
    assert len(result) == 1
    assert result[0]["evidence_url"].endswith("/101")


def test_x_search_stops_on_partial_errors(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    monkeypatch.setattr(x_api, "_request", lambda *a, **k: {
        "errors": [{"title": "Partial results"}], "data": []})
    with pytest.raises(x_api.XUnavailable, match="incomplete"):
        x_api.search_people("robotics")


def test_dm_reply_pagination_is_bounded_and_sender_filtered(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(kwargs["params"].copy())
        page = len(calls)
        return {
            "data": [
                {"id": str(page), "sender_id": "123", "text": "A reply",
                 "event_type": "MessageCreate", "created_at": "2026-11-12T10:00:00Z"},
                {"id": "other", "sender_id": "999", "text": "Our own DM",
                 "event_type": "MessageCreate"},
            ],
            "meta": {"next_token": f"next-{page}"},
        }

    monkeypatch.setattr(x_api, "_request", fake_request)
    events = x_api.get_replies("123")
    assert len(calls) == 2
    assert calls[1]["pagination_token"] == "next-1"
    assert len(events) == 2
    assert all(event["sender_id"] == "123" for event in events)


def test_dm_reply_errors_are_not_treated_as_complete_sync(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    monkeypatch.setattr(x_api, "_request",
                        lambda *a, **k: {"errors": [{"detail": "rate limited"}]})
    with pytest.raises(x_api.XUnavailable, match="incomplete"):
        x_api.get_replies("123")


def test_x_read_defaults_off(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "false")
    invoked = []
    monkeypatch.setattr(x_api, "_request", lambda *a, **k: invoked.append(True))
    with pytest.raises(x_api.XUnavailable):
        x_api.search_people("robotics")
    with pytest.raises(x_api.XUnavailable):
        x_api.get_replies("123")
    assert invoked == []



def test_cross_origin_writes_are_rejected(tmp_path, monkeypatch):
    """A known public header does not give untrusted web origins write access."""
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "origin.sqlite3"))
    with TestClient(app) as c:
        headers = {
            "X-Local-Operator": "signalbridge-local",
            "Origin": "https://untrusted.example",
        }
        response = c.post("/api/discover/demo",
                          json={"segment": "robotics"}, headers=headers)
        assert response.status_code == 403
        assert "Cross-origin" in response.json()["detail"]
        good = c.post("/api/discover/demo",
                      json={"segment": "robotics"},
                      headers={"X-Local-Operator": "signalbridge-local",
                               "Origin": "http://testserver"})
        assert good.status_code == 200


def test_untrusted_host_is_rejected():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        response = c.get("/healthz", headers={"Host": "untrusted.example"})
        assert response.status_code == 400



def test_reply_meta_marks_bounded_result_incomplete(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    calls = []

    def paginated(method, url, **kwargs):
        calls.append(kwargs["params"])
        return {
            "data": [{"id": str(len(calls)), "sender_id": "123",
                      "event_type": "MessageCreate", "text": "Hello"}],
            "meta": {"next_token": f"next-{len(calls)}"},
        }

    monkeypatch.setattr(x_api, "_request", paginated)
    result = x_api.get_replies_with_meta("123")
    assert result["pages_scanned"] == 2
    assert result["has_more"] is True
    assert result["complete"] is False
    assert len(result["events"]) == 2


def test_reply_meta_marks_exhausted_page_complete(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    monkeypatch.setattr(x_api, "_request", lambda *a, **k: {
        "data": [{"id": "1", "sender_id": "123", "event_type": "MessageCreate"}],
        "meta": {},
    })
    result = x_api.get_replies_with_meta("123")
    assert result["pages_scanned"] == 1
    assert result["complete"] is True
    assert result["has_more"] is False


def test_real_transport_stub_reports_partial_reply_sync(tmp_path, monkeypatch):
    """No outgoing network: transport and reply scan are both monkeypatched."""
    from datetime import datetime, timedelta, timezone
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "sync.sqlite3"))
    monkeypatch.setenv("AI_PROVIDER", "template")
    monkeypatch.setenv("X_ENABLE_READ", "true")
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "true")
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "fake-not-live")
    monkeypatch.setenv("X_TEST_ALLOWLIST_IDS", "123")
    monkeypatch.setattr(x_api, "send_dm", lambda *a: {
        "remote_event_id": "fixture_event", "remote_conversation_id": "fixture_conv",
    })
    def mock_sync(*a):
        after = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
        return {
            "events": [{"created_at": after, "text": "Yes", "sender_id": "123"}],
            "pages_scanned": 2, "complete": False, "has_more": True,
        }
    monkeypatch.setattr(x_api, "get_replies_with_meta", mock_sync)
    headers = {"X-Local-Operator": "signalbridge-local"}
    with TestClient(app) as c:
        def post(path, data):
            return c.post(path, json=data, headers=headers)
        campaign = post("/api/campaigns", {"segment": "robotics"}).json()
        person = post("/api/prospects", {
            "campaign_id": campaign["campaign_id"], "display_name": "Test Participant",
            "handle": "consentedtest", "x_user_id": "123",
            "role": "Robotics builder",
            "evidence_text": "Builds test robots with consent.", "consent_confirmed": True,
        }).json()
        dm = post("/api/drafts", {"prospect_id": person["id"]}).json()
        assert post(f"/api/drafts/{dm['id']}/approve", {}).status_code == 200
        sent = post(f"/api/drafts/{dm['id']}/send", {"transport": "x_api"})
        assert sent.status_code == 200
        assert sent.json()["transport"] == "x_api"
        sync = post(f"/api/drafts/{dm['id']}/sync-replies", {})
        assert sync.status_code == 200, sync.text
        assert sync.json()["found"] == 1
        assert sync.json()["has_more"] is True
        assert sync.json()["complete"] is False
        assert c.get("/api/state").json()["drafts"][0]["state"] == "replied"
