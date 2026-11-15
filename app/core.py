"""SQLite persistence, discovery ranking, and evidence-first DM drafting.

The demo catalog is intentionally fictional. Never treat its names or evidence
as actual X posts or as consent to contact real people.
"""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
DEMO_PEOPLE = [
    {
        "name": "Alex Rivera (fictional)", "handle": "demo_robot_1", "x_user_id": "",
        "role": "Robotics ML engineer", "bio": "Builds simulation-to-real robotics demos with ROS and reinforcement learning.",
        "evidence": "Built a synthetic robot-arm pick-and-place example and measured simulation-to-real transfer.",
        "tags": "robotics embodied ai reinforcement learning simulation robots", "source_url": "demo://robot-arm-example",
    },
    {
        "name": "Morgan Chen (fictional)", "handle": "demo_infra_2", "x_user_id": "",
        "role": "LLM infrastructure builder", "bio": "Develops inference serving, GPU caching, and evaluation tooling.",
        "evidence": "Published a fictional evaluation note comparing latency of LLM serving pipelines.",
        "tags": "ai models inference gpu developer tools infrastructure llm", "source_url": "demo://llm-latency-note",
    },
    {
        "name": "Taylor Singh (fictional)", "handle": "demo_vla_3", "x_user_id": "",
        "role": "Embodied AI researcher", "bio": "Investigates vision-language-action systems for household manipulation.",
        "evidence": "Shared a hypothetical write-up about vision-language-action robot evaluation.",
        "tags": "robotics embodied ai vla research vision language action", "source_url": "demo://vla-evaluation",
    },
    {
        "name": "Jordan Park (fictional)", "handle": "demo_agents_4", "x_user_id": "",
        "role": "AI application founder", "bio": "Builds agent tooling for developer workflows and product automation.",
        "evidence": "Described a fictional prototype that validates AI agent tool calls and records failed actions.",
        "tags": "ai agents applications founder developer tools software", "source_url": "demo://agent-prototype",
    },
    {
        "name": "Casey Martin (fictional)", "handle": "demo_eval_5", "x_user_id": "",
        "role": "Open-source AI tooling maintainer", "bio": "Maintains a test suite for model evaluation and transparent scoring.",
        "evidence": "Released hypothetical notes on repeatable model-evaluation benchmarks.",
        "tags": "ai research evaluation open source models developer tooling", "source_url": "demo://model-benchmarks",
    },
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:14]}"


def db_file() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(ROOT / "outreach.db"))).expanduser().resolve()


@contextmanager
def connection():
    filename = db_file()
    filename.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(filename), isolation_level=None, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 10000")
    con.execute("PRAGMA journal_mode = WAL")
    try:
        yield con
    finally:
        con.close()


def init_db() -> None:
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY, segment TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prospects (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL REFERENCES campaigns(id),
            display_name TEXT NOT NULL, handle TEXT NOT NULL,
            x_user_id TEXT NOT NULL DEFAULT '', role TEXT NOT NULL,
            bio TEXT NOT NULL, evidence_text TEXT NOT NULL,
            evidence_url TEXT NOT NULL, source_kind TEXT NOT NULL,
            score INTEGER NOT NULL, reason TEXT NOT NULL,
            consent_confirmed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(campaign_id, handle)
        );
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY, prospect_id TEXT NOT NULL UNIQUE REFERENCES prospects(id),
            body TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'draft',
            transport TEXT NOT NULL DEFAULT '', remote_event_id TEXT NOT NULL DEFAULT '',
            remote_conversation_id TEXT NOT NULL DEFAULT '',
            last_error TEXT NOT NULL DEFAULT '', approved_at TEXT NOT NULL DEFAULT '',
            sent_at TEXT NOT NULL DEFAULT '', replied_at TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS send_registry (
            recipient_key TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL UNIQUE REFERENCES drafts(id),
            state TEXT NOT NULL, transport TEXT NOT NULL,
            remote_event_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS send_aliases (
            alias TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL REFERENCES drafts(id)
        );
        CREATE TABLE IF NOT EXISTS activity (
            id TEXT PRIMARY KEY, draft_id TEXT NOT NULL REFERENCES drafts(id),
            action TEXT NOT NULL, detail TEXT NOT NULL, at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_prospects_campaign ON prospects(campaign_id);
        CREATE INDEX IF NOT EXISTS idx_drafts_state ON drafts(state);
        """)


def log_action(db: sqlite3.Connection, draft_id: str, action: str, detail: str = ""):
    db.execute("INSERT INTO activity(id,draft_id,action,detail,at) VALUES(?,?,?,?,?)",
               (new_id("evt"), draft_id, action, detail[:500], now()))


def normalize_handle(handle: str) -> str:
    handle = handle.strip().lstrip("@").lower()
    if not re.fullmatch(r"[a-zA-Z0-9_]{2,15}", handle):
        raise ValueError("X handle must contain 2–15 letters, digits or underscores")
    return handle


def recipient_key(prospect: sqlite3.Row) -> str:
    x_id = prospect["x_user_id"].strip()
    return "x:" + x_id if x_id else "handle:" + normalize_handle(prospect["handle"])


def make_campaign(db: sqlite3.Connection, segment: str) -> str:
    campaign_id = new_id("camp")
    db.execute("INSERT INTO campaigns(id,segment,created_at) VALUES(?,?,?)", (campaign_id, segment[:160], now()))
    return campaign_id


def rank(segment: str, role: str, bio: str, evidence: str, tags: str = "") -> tuple[int, str]:
    # Match complete words, not substrings ("mouths" != "souths").
    # Allow short domain tokens such as "AI", which the earlier 3+ regex lost.
    stopwords = {"and", "for", "the", "with", "people", "from", "using", "who", "work"}
    tokens = set(re.findall(r"[a-z0-9]{2,}", segment.lower())) - stopwords
    corpus_words = set(re.findall(
        r"[a-z0-9]{2,}", " ".join((role, bio, evidence, tags)).lower()
    ))
    matched = sorted(tokens & corpus_words)
    score = min(95, 28 + 17 * len(matched) + (8 if len(matched) > 1 else 0))
    if not tokens:
        score = 40
    reason = "Matching signals: " + ", ".join(matched[:6]) if matched else "No direct term match; review manually"
    return score, reason


def store_prospect(db: sqlite3.Connection, campaign_id: str, *, display_name: str, handle: str,
                   x_user_id: str = "", role: str, bio: str, evidence_text: str, evidence_url: str,
                   source_kind: str = "manual", consent_confirmed: bool = False,
                   tags: str = "") -> sqlite3.Row:
    handle = normalize_handle(handle)
    if x_user_id and not re.fullmatch(r"[0-9]{1,25}", x_user_id):
        raise ValueError("X user ID must be numeric")
    segment = db.execute("SELECT segment FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    if not segment:
        raise ValueError("Unknown campaign")
    if not evidence_text.strip():
        raise ValueError("Evidence is required; do not invent personalization")
    score, reason = rank(segment["segment"], role, bio, evidence_text, tags)
    db.execute("""INSERT OR IGNORE INTO prospects
        (id,campaign_id,display_name,handle,x_user_id,role,bio,evidence_text,evidence_url,
         source_kind,score,reason,consent_confirmed,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (new_id("person"), campaign_id, display_name[:100], handle, x_user_id, role[:120],
         bio[:800], evidence_text[:1000], evidence_url[:700], source_kind,
         score, reason, int(consent_confirmed), now()))
    return db.execute("SELECT * FROM prospects WHERE campaign_id=? AND handle=?", (campaign_id, handle)).fetchone()


def draft_from_evidence(person: sqlite3.Row) -> str:
    """Deterministic, auditable baseline; not labeled as AI generation."""
    first = person["display_name"].split()[0].strip("(,.")
    first = "there" if not first.isalpha() else first
    evidence = person["evidence_text"].strip().rstrip(".")
    if len(evidence) > 145:
        evidence = evidence[:142].rsplit(" ", 1)[0] + "…"
    return (
        f"Hi {first}, I noticed this detail in your work: \"{evidence}\". "
        "I'm exploring conversations with builders working in AI and robotics. "
        "Would you be open to a brief exchange about what you're building?"
    )


def snapshot(db: sqlite3.Connection) -> dict:
    camps = [dict(c) for c in db.execute("SELECT * FROM campaigns ORDER BY created_at DESC")]
    people = [dict(p) for p in db.execute("SELECT * FROM prospects ORDER BY score DESC, created_at DESC")]
    drafts = [dict(d) for d in db.execute("SELECT * FROM drafts ORDER BY created_at DESC")]
    events = [dict(v) for v in db.execute("SELECT * FROM activity ORDER BY rowid DESC LIMIT 80")]
    for p in people:
        p["consent_confirmed"] = bool(p["consent_confirmed"])
    return {"campaigns": camps, "prospects": people, "drafts": drafts, "activity": events}
