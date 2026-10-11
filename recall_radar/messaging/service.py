"""Inbound handling, provider-independent: dedupe → tombstone/echo/group checks → commands → conversation."""

from __future__ import annotations

import json
import sqlite3
import time

from . import brain, commands, conversation
from . import templates as T
from .analysis import Analysis
from .outbox import enqueue, process
from .provider import Provider
from .store import route_hash, seen_event


def handle(con: sqlite3.Connection, event: dict, a: Analysis, provider: Provider, event_id: str,
           sent_at: float | None = None) -> str | None:
    """Returns the reply text queued (None if the event is ignored)."""
    if seen_event(con, event_id):
        return None  # replayed delivery
    msg, space = event.get("message") or {}, event.get("space") or {}
    route = str(space.get("id") or "")
    sender = msg.get("sender") or {}
    if not route or msg.get("isFromMe") or sender.get("isMe") or sender.get("kind") == "agent":
        return None  # our own echo (iMessage isFromMe; Spectrum AgentSender kind "agent")
    tomb = con.execute("SELECT at FROM tombstone WHERE route_hash = ?", [route_hash(route)]).fetchone()
    if tomb and (sent_at or time.time()) <= tomb["at"]:
        return None  # late delivery from before DELETE cannot re-enroll
    text = str(((msg.get("content") or {}).get("text")) or "").strip()
    if not text:
        return None
    if is_recent_echo(con, route, text, sent_at):
        return None  # provider-independent: our own text coming back must never be answered (no reply loop)
    if space.get("type") == "group":
        reply = T.GROUP_REFUSAL
    elif commands.is_command(text):
        reply = commands.run(con, route, text, a)
    else:
        row = con.execute("SELECT * FROM convo_ctx WHERE route = ?", [route]).fetchone()
        reply, ctx = conversation.answer(text, dict(row) if row else None, a, brain=brain.from_env())
        if ctx:
            con.execute("INSERT OR REPLACE INTO convo_ctx VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [route, ctx["make"], ctx["model"], ctx["model_year"], ctx.get("campno"), None, ctx["expires_at"]])
    if reply:
        kind = "stop_ack" if text.upper().startswith("STOP") else "reply"
        enqueue(con, f"reply:{event_id}", route, kind, reply)
        process(con, provider)
    return reply


ECHO_WINDOW_S = 600


def is_recent_echo(con: sqlite3.Connection, route: str, text: str, sent_at: float | None = None) -> bool:
    """True when this exact text was sent by us on this route in the last ECHO_WINDOW_S seconds."""
    now = sent_at or time.time()
    row = con.execute(
        "SELECT 1 FROM outbox WHERE route = ? AND body = ? AND created_at >= ? LIMIT 1",
        [route, text, now - ECHO_WINDOW_S]).fetchone()
    return row is not None


def parse(body: bytes) -> dict:
    return json.loads(body.decode("utf-8"))
