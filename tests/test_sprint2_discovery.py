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

def test_x_read_defaults_off(monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "false")
    invoked = []
    monkeypatch.setattr(x_api, "_request", lambda *a, **k: invoked.append(True))
    with pytest.raises(x_api.XUnavailable):
        x_api.search_people("robotics")
    with pytest.raises(x_api.XUnavailable):
        x_api.get_replies("123")
    assert invoked == []

