"""Send races must not produce two outbound events for one recipient."""
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.main import app


def test_concurrent_mock_sends_reserve_recipient_once(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "race.sqlite3"))
    monkeypatch.setenv("AI_PROVIDER", "template")
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "false")
    monkeypatch.setenv("X_ENABLE_READ", "false")

    headers = {"X-Local-Operator": "signalbridge-local"}
    with TestClient(app) as client:
        def post(path, data):
            return client.post(path, json=data, headers=headers)

        candidate = post("/api/discover/demo", {"segment": "robotics"}).json()["prospects"][0]
        draft = post("/api/drafts", {"prospect_id": candidate["id"]}).json()
        assert post(f"/api/drafts/{draft['id']}/approve", {}).status_code == 200

        def attempt_send(_):
            return post(f"/api/drafts/{draft['id']}/send", {"transport": "mock"})

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt_send, range(2)))

        assert sorted(r.status_code for r in results) == [200, 409]
        db_state = client.get("/api/state").json()
        assert db_state["drafts"][0]["state"] == "sent"
        assert sum(a["action"] == "sent_mock" for a in db_state["activity"]) == 1
