"""Verify the real local ASGI workflow without network calls or persistent test data.

Usage (after pip install -r requirements-dev.txt):
    python scripts/verify_offline.py

This is a MOCK-ONLY verification. It does not prove X API authorization,
real DM delivery, hosted security or live reply fetching.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Set safe env before importing app.main, whose module reads .env.
os.environ["X_ENABLE_READ"] = "false"
os.environ["X_ENABLE_LIVE_SEND"] = "false"
os.environ["AI_PROVIDER"] = "template"
os.environ.pop("X_USER_ACCESS_TOKEN", None)
os.environ.pop("OPENAI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

HEADERS = {"X-Local-Operator": "signalbridge-local"}


def check() -> None:
    with tempfile.TemporaryDirectory(prefix="signalbridge-offline-") as temp:
        os.environ["DATABASE_PATH"] = str(Path(temp) / "verify.sqlite3")
        with TestClient(app) as client:
            def post(path: str, payload: dict) -> dict:
                response = client.post(path, json=payload, headers=HEADERS)
                assert response.status_code == 200, (
                    f"{path}: {response.status_code} {response.text}"
                )
                return response.json()

            assert client.get("/healthz").json()["ok"] is True
            assert client.get("/api/state").json()["config"]["x_send_enabled"] is False

            result = post("/api/discover/demo", {"segment": "robotics embodied AI"})
            assert result["prospects"] and result["disclosure"].startswith("SYNTHETIC")
            person = result["prospects"][0]
            assert person["source_kind"] == "fictional_demo"

            draft = post("/api/drafts", {"prospect_id": person["id"]})
            assert draft["state"] == "draft"
            blocked = client.post(
                f"/api/drafts/{draft['id']}/send",
                json={"transport": "mock"}, headers=HEADERS,
            )
            assert blocked.status_code == 409, "Sending before approval must fail"

            approved = post(f"/api/drafts/{draft['id']}/approve", {})
            assert approved["state"] == "approved"

            sent = post(f"/api/drafts/{draft['id']}/send", {"transport": "mock"})
            assert sent["state"] == "sent" and sent["transport"] == "mock"
            assert sent["remote_event_id"].startswith("MOCK_EVENT")

            duplicate = client.post(
                f"/api/drafts/{draft['id']}/send",
                json={"transport": "mock"}, headers=HEADERS,
            )
            assert duplicate.status_code == 409, "Duplicate send must be blocked"

            reply = post(
                f"/api/drafts/{draft['id']}/simulate-reply",
                {"text": "Synthetic consenting response"},
            )
            assert reply["state"] == "replied"
            state = client.get("/api/state").json()
            assert state["drafts"][0]["state"] == "replied"
            assert state["activity"][0]["action"] == "mock_reply_received"

    print("PASS: offline mock workflow; no real X/OpenAI calls, no persistent test DB")


if __name__ == "__main__":
    check()
