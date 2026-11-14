"""Local-first workflow API for a candidate's GenAI Fund technical demo.

Security defaults: local binding, no CORS, required custom header for writes,
no live X calls unless enabled, explicit approval, recipient test allowlist,
recipient-level send registry, no blind retry after uncertain outbound calls.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
from . import core, x_api
from .drafter import make_draft

@asynccontextmanager
async def lifespan(app):
    core.init_db()
    yield

app = FastAPI(title="SignalBridge — FDE Outreach MVP", version="0.1.0", docs_url="/api/docs", lifespan=lifespan)
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.middleware("http")
async def prevent_cross_site_writes(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        if request.headers.get("X-Local-Operator") != "signalbridge-local":
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Only explicit local operator actions allowed"}, status_code=403)
    return await call_next(request)


class Segment(BaseModel):
    segment: str = Field(min_length=3, max_length=160)


class XDiscovery(BaseModel):
    segment: str = Field(min_length=3, max_length=160)
    x_query: str = Field(min_length=3, max_length=280)


class NewProspect(BaseModel):
    campaign_id: str
    display_name: str = Field(min_length=2, max_length=100)
    handle: str = Field(min_length=2, max_length=20)
    x_user_id: str = Field(default="", max_length=25)
    role: str = Field(min_length=2, max_length=120)
    bio: str = Field(default="", max_length=800)
    evidence_text: str = Field(min_length=8, max_length=1000)
    evidence_url: str = Field(default="", max_length=700)
    consent_confirmed: bool = False


class CreateDraft(BaseModel):
    prospect_id: str


class EditDraft(BaseModel):
    body: str = Field(min_length=15, max_length=1200)


class SendDraft(BaseModel):
    transport: Literal["mock", "x_api"] = "mock"


class SimulateReply(BaseModel):
    text: str = Field(default="Thanks for reaching out — happy to connect!", max_length=500)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "signalbridge"}


@app.get("/api/state")
def state():
    with core.connection() as db:
        data = core.snapshot(db)
    data["config"] = {"mode": "LOCAL DEMO", "x_read_enabled": x_api.enabled_read(),
                      "x_send_enabled": x_api.enabled_send(),
                      "x_test_allowlist_count": len(x_api.allowed_ids()),
                      "ai_provider": os.getenv("AI_PROVIDER", "template")}
    return data


@app.post("/api/campaigns")
def new_campaign(p: Segment):
    with core.connection() as db:
        cid = core.make_campaign(db, p.segment)
    return {"campaign_id": cid, "segment": p.segment}


@app.post("/api/discover/demo")
def discover_demo(p: Segment):
    with core.connection() as db:
        cid = core.make_campaign(db, p.segment)
        selected = []
        for candidate in core.DEMO_PEOPLE:
            score, _ = core.rank(p.segment, candidate["role"], candidate["bio"], candidate["evidence"], candidate["tags"])
            if score >= 45:
                selected.append(candidate)
        if not selected:
            selected = core.DEMO_PEOPLE[:2]
        found = []
        for person in selected[:5]:
            found.append(dict(core.store_prospect(db, cid, display_name=person["name"],
                handle=person["handle"], role=person["role"], bio=person["bio"],
                evidence_text=person["evidence"], evidence_url=person["source_url"],
                source_kind="fictional_demo", tags=person["tags"])))
    return {"campaign_id": cid, "prospects": found, "disclosure": "SYNTHETIC demonstration people, not real X users"}


@app.post("/api/discover/x")
def discover_x(p: XDiscovery):
    try:
        candidates = x_api.search_people(p.x_query)
    except (x_api.XUnavailable, ValueError) as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, "X API discovery unavailable; check X user token/scopes/credits") from e
    with core.connection() as db:
        cid = core.make_campaign(db, p.segment)
        found = [dict(core.store_prospect(db, cid, **c)) for c in candidates]
    return {"campaign_id": cid, "prospects": found,
            "disclosure": "Authors found from X recent posts; evidence comes from those posts, review manually"}


@app.post("/api/prospects")
def add_person(p: NewProspect):
    try:
        with core.connection() as db:
            result = core.store_prospect(db, p.campaign_id, display_name=p.display_name,
                    handle=p.handle, x_user_id=p.x_user_id, role=p.role,
                    bio=p.bio, evidence_text=p.evidence_text, evidence_url=p.evidence_url,
                    source_kind="manually_supplied", consent_confirmed=p.consent_confirmed)
        return dict(result)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/drafts")
def create_draft(p: CreateDraft):
    with core.connection() as db:
        prospect = db.execute("SELECT * FROM prospects WHERE id=?", (p.prospect_id,)).fetchone()
        if not prospect:
            raise HTTPException(404, "Prospect not found")
        existing = db.execute("SELECT * FROM drafts WHERE prospect_id=?", (p.prospect_id,)).fetchone()
        if existing:
            return dict(existing)
        try:
            body, method = make_draft(prospect)
        except Exception as e:
            raise HTTPException(502, "Draft provider failed; switch to AI_PROVIDER=template") from e
        did = core.new_id("dm")
        db.execute("INSERT INTO drafts(id,prospect_id,body,state,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                   (did, p.prospect_id, body, "draft", core.now(), core.now()))
        core.log_action(db, did, "draft_created", f"Drafted via {method}; unapproved")
        return dict(db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone())


@app.patch("/api/drafts/{did}")
def edit_draft(did: str, p: EditDraft):
    with core.connection() as db:
        d = db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404, "Draft not found")
        if d["state"] not in {"draft", "rejected"}:
            raise HTTPException(409, "Only unapproved drafts can be edited")
        db.execute("UPDATE drafts SET body=?,state='draft',updated_at=? WHERE id=?", (p.body, core.now(), did))
        core.log_action(db, did, "draft_edited", "Operator edited the message")
        return dict(db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone())


@app.post("/api/drafts/{did}/approve")
def approve(did: str):
    with core.connection() as db:
        d = db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404, "Draft not found")
        if d["state"] != "draft":
            raise HTTPException(409, "Draft is not awaiting approval")
        db.execute("UPDATE drafts SET state='approved',approved_at=?,updated_at=? WHERE id=?",
                   (core.now(), core.now(), did))
        core.log_action(db, did, "human_approved", "Explicit local operator approval")
        return dict(db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone())


@app.post("/api/drafts/{did}/send")
def send(did: str, request: SendDraft):
    # Atomic reservation before outbound operation prevents concurrent duplicate sends.
    with core.connection() as db:
        db.execute("BEGIN IMMEDIATE")
        d = db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
        if not d:
            db.execute("ROLLBACK")
            raise HTTPException(404, "Draft not found")
        if d["state"] != "approved":
            db.execute("ROLLBACK")
            raise HTTPException(409, "Message must be approved and not already sent")
        p = db.execute("SELECT * FROM prospects WHERE id=?", (d["prospect_id"],)).fetchone()
        key = core.recipient_key(p)
        # Lock every stable alias to prevent sending twice when one record uses
        # a numeric X ID and another only a handle (or a renamed handle).
        aliases = ["handle:" + core.normalize_handle(p["handle"])]
        if p["x_user_id"]:
            aliases.append("x:" + str(p["x_user_id"]))
        if request.transport == "x_api":
            if not x_api.enabled_send() or not os.getenv("X_USER_ACCESS_TOKEN", ""):
                db.execute("ROLLBACK")
                raise HTTPException(400, "Real X sending disabled or missing token")
            if not p["x_user_id"] or p["x_user_id"] not in x_api.allowed_ids() or not p["consent_confirmed"]:
                db.execute("ROLLBACK")
                raise HTTPException(400, "Real sending needs verified test recipient ID, explicit consent and allowlist")
        try:
            for alias in aliases:
                db.execute("INSERT INTO send_aliases(alias,draft_id) VALUES(?,?)", (alias, did))
            db.execute("INSERT INTO send_registry(recipient_key,draft_id,state,transport,created_at) VALUES(?,?,?,?,?)",
                       (key, did, "sending", request.transport, core.now()))
        except sqlite3.IntegrityError:
            db.execute("ROLLBACK")
            raise HTTPException(409, "This recipient already has an outgoing send or reserved attempt; no duplicates")
        db.execute("UPDATE drafts SET state='sending', transport=?, updated_at=? WHERE id=?",
                   (request.transport, core.now(), did))
        core.log_action(db, did, "delivery_reserved", "Recipient lock acquired before any send")
        db.execute("COMMIT")

    try:
        if request.transport == "mock":
            outcome = {"remote_event_id": core.new_id("MOCK_EVENT"), "remote_conversation_id": core.new_id("MOCK_CONV")}
        else:
            outcome = x_api.send_dm(str(p["x_user_id"]), d["body"])
    except Exception as e:
        # A timeout is AMBIGUOUS, not proof the external platform did not send.
        with core.connection() as db:
            db.execute("UPDATE drafts SET state='uncertain',last_error=?,updated_at=? WHERE id=?",
                       ("Delivery outcome unknown; review platform before any further action", core.now(), did))
            db.execute("UPDATE send_registry SET state='uncertain' WHERE draft_id=?", (did,))
            core.log_action(db, did, "send_uncertain", "No automatic retry. Check provider audit/outbox")
        raise HTTPException(502, "Delivery uncertain; NOT automatically retrying. Check account history.") from e
    with core.connection() as db:
        db.execute("UPDATE drafts SET state='sent',remote_event_id=?,remote_conversation_id=?,sent_at=?,updated_at=? WHERE id=?",
                   (outcome["remote_event_id"], outcome["remote_conversation_id"], core.now(), core.now(), did))
        db.execute("UPDATE send_registry SET state='sent',remote_event_id=? WHERE draft_id=?",
                   (outcome["remote_event_id"], did))
        core.log_action(db, did, "sent_" + request.transport, outcome["remote_event_id"])
        return dict(db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone())


@app.post("/api/drafts/{did}/simulate-reply")
def simulate_reply(did: str, p: SimulateReply):
    with core.connection() as db:
        d = db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404, "Unknown draft")
        if d["state"] != "sent" or d["transport"] != "mock":
            raise HTTPException(409, "Simulated replies are only for mock-sent messages")
        db.execute("UPDATE drafts SET state='replied',replied_at=?,updated_at=? WHERE id=?",
                   (core.now(), core.now(), did))
        core.log_action(db, did, "mock_reply_received", p.text[:500])
        return {"state": "replied", "mock": True}


@app.post("/api/drafts/{did}/sync-replies")
def sync_replies(did: str):
    with core.connection() as db:
        d = db.execute("SELECT * FROM drafts WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404, "Unknown draft")
        if d["state"] not in {"sent", "replied"} or d["transport"] != "x_api":
            raise HTTPException(409, "Only actual X-sent messages can sync actual replies")
        p = db.execute("SELECT * FROM prospects WHERE id=?", (d["prospect_id"],)).fetchone()
        recipient = p["x_user_id"]
    try:
        sync = x_api.get_replies_with_meta(recipient)
        events = sync["events"]
    except Exception as e:
        raise HTTPException(502, "Could not check X replies; verify token/access") from e
    # Ignore messages older than the send. The adapter reads at most two
    # pages; a successful lookup is not evidence of complete conversation history.
    sent_at = datetime.fromisoformat(d["sent_at"])
    actual_replies = []
    for event in events:
        try:
            event_at = datetime.fromisoformat(str(event["created_at"]).replace("Z", "+00:00"))
            if event_at > sent_at:
                actual_replies.append(event)
        except (ValueError, TypeError, KeyError):
            continue
    if actual_replies and d["state"] == "sent":
        with core.connection() as db:
            db.execute("UPDATE drafts SET state='replied',replied_at=?,updated_at=? WHERE id=?",
                       (core.now(), core.now(), did))
            core.log_action(db, did, "x_reply_detected", "Received sender-matched DM event")
    return {
        "found": len(actual_replies),
        "complete": sync["complete"],
        "has_more": sync["has_more"],
        "pages_scanned": sync["pages_scanned"],
        "note": "Only sender-matched messages AFTER send time. A limited scan is not a complete inbox history." if sync["has_more"] else "No additional page was offered by X.",
        "events": actual_replies[:10],
    }
