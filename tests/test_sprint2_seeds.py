"""Seed-account search is bounded, source-labelled and offline-testable."""
from fastapi.testclient import TestClient
import pytest
from app import x_api
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "seed-tests.sqlite3"))
    monkeypatch.setenv("AI_PROVIDER", "template")
    monkeypatch.setenv("X_ENABLE_READ", "false")
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "false")
    with TestClient(app) as c:
        yield c


def search(c, handles, segment="robotics AI"):
    return c.post(
        "/api/discover/seeds",
        json={"segment": segment, "seed_handles": handles},
        headers={"X-Local-Operator": "signalbridge-local"},
    )


def test_seed_search_requires_explicit_x_read_permission(client):
    response = search(client, ["@robotics_lab"])
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_seed_search_imports_authors_with_provenance(client, monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    queries = []

    def fake_search(q):
        queries.append(q)
        return [{
            "display_name": "Example Author", "handle": "example_author",
            "x_user_id": "12345", "role": "X account posting about the target segment",
            "bio": "Robotics developer", "evidence_text": "Published robot motion evaluation details",
            "evidence_url": "https://x.com/example_author/status/999",
            "source_kind": "x_api_recent_post",
        }]

    monkeypatch.setattr(x_api, "search_people", fake_search)
    response = search(client, ["@robotics_lab", "robotics_lab", "@ai_team"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["seed_handles"] == ["robotics_lab", "ai_team"]
    assert body["strategy"] == "recent_public_posts_mentioning_seeds"
    assert "NOT follower-network" in body["disclosure"]
    assert queries == ["(@robotics_lab OR @ai_team) (robotics OR ai) -is:retweet"]
    person = body["prospects"][0]
    assert person["source_kind"] == "x_api_recent_post"
    assert person["evidence_url"].endswith("/999")
    assert person["consent_confirmed"] == 0  # not inferred from mentions


@pytest.mark.parametrize("handles", [
    [],
    ["first", "second", "third", "fourth"],
    ["@bad-handle"],
    ["@x"],
    ["wrong or from:someone"],
])
def test_invalid_seeds_are_rejected(client, handles):
    response = search(client, handles)
    assert response.status_code in (400, 422)


def test_seed_discovery_does_not_enable_real_dms(client, monkeypatch):
    monkeypatch.setenv("X_ENABLE_READ", "true")
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "false")
    monkeypatch.setattr(x_api, "search_people", lambda q: [{
        "display_name": "Consenting status unknown", "handle": "unknown_consent",
        "x_user_id": "99", "role": "AI builder", "bio": "",
        "evidence_text": "Published interesting robotics research",
        "evidence_url": "https://x.com/unknown_consent/status/99",
        "source_kind": "x_api_recent_post",
    }])
    candidate = search(client, ["@robotics_lab"]).json()["prospects"][0]
    headers = {"X-Local-Operator": "signalbridge-local"}
    draft = client.post("/api/drafts", json={"prospect_id": candidate["id"]}, headers=headers).json()
    client.post(f"/api/drafts/{draft['id']}/approve", json={}, headers=headers)
    attempted = client.post(f"/api/drafts/{draft['id']}/send",
                            json={"transport": "x_api"}, headers=headers)
    assert attempted.status_code == 400



def test_x_enabled_flag_never_claims_unverified_config_as_delivery(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "mode.sqlite3"))
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "true")
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "")
    monkeypatch.setenv("X_TEST_ALLOWLIST_IDS", "123")
    with TestClient(app) as c:
        conf = c.get("/api/state").json()["config"]
        assert conf["x_send_requested"] is True
        assert conf["x_send_enabled"] is False
        assert conf["mode"] == "LOCAL DEMO"
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "fixture-not-real")
    with TestClient(app) as c:
        conf = c.get("/api/state").json()["config"]
        assert conf["x_send_enabled"] is True
        assert "UNVERIFIED" in conf["mode"]
        assert "NOT verified" in conf["x_status"]
        assert "fixture-not-real" not in str(conf)
