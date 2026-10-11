"""SQLite state for F9 (WAL). Only what PRD v2 §6 allows: provider route, consent version/time, one vehicle,
status, time zone, event/outbox state and a 30-minute conversation context. No VIN, no transcripts."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS subscriber (
  route TEXT PRIMARY KEY,               -- provider space/route id exactly as Photon gives it
  status TEXT NOT NULL CHECK (status IN ('pending','active','paused','stopped')),
  consent_version TEXT, consent_at REAL,
  tz TEXT NOT NULL DEFAULT 'America/New_York',
  make TEXT, model TEXT, model_year INTEGER,
  pending_make TEXT, pending_model TEXT, pending_year INTEGER,
  last_digest_day TEXT                  -- local date of the last unsolicited digest (<= 1 per day)
);
CREATE TABLE IF NOT EXISTS tombstone (route_hash TEXT PRIMARY KEY, at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS inbound_event (id TEXT PRIMARY KEY, at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS monitor_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT, make TEXT, model TEXT, model_year INTEGER,
  fetched_at REAL NOT NULL, coverage TEXT, source_updated TEXT, odinos TEXT, campnos TEXT);
CREATE TABLE IF NOT EXISTS monitor_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT, make TEXT, model TEXT, model_year INTEGER,
  type TEXT NOT NULL CHECK (type IN ('new_complaints','new_campaign','detector_alert','corrected','removed')),
  payload TEXT NOT NULL, interval TEXT NOT NULL, catch_up INTEGER NOT NULL DEFAULT 0, at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS outbox (
  idempotency_key TEXT PRIMARY KEY, route TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued','accepted','delivered','failed','cancelled','uncertain')),
  retries INTEGER NOT NULL DEFAULT 0, provider_message_id TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS convo_ctx (
  route TEXT PRIMARY KEY, make TEXT, model TEXT, model_year INTEGER, campno TEXT, last_report TEXT,
  expires_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS worker_lock (name TEXT PRIMARY KEY, owner TEXT NOT NULL, until REAL NOT NULL);
"""


def route_hash(route: str) -> str:
    return hashlib.sha256(route.encode()).hexdigest()


def connect(path: Path | str) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), timeout=10, isolation_level=None)  # autocommit; explicit BEGIN where needed
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con


def take_lock(con: sqlite3.Connection, name: str, owner: str, ttl_s: float = 300) -> bool:
    """Single-worker advisory lock: one scheduler run at a time; a crashed owner's lock expires."""
    now = time.time()
    con.execute("BEGIN IMMEDIATE")
    try:
        row = con.execute("SELECT owner, until FROM worker_lock WHERE name = ?", [name]).fetchone()
        if row and row["until"] > now and row["owner"] != owner:
            con.execute("ROLLBACK")
            return False
        con.execute("INSERT OR REPLACE INTO worker_lock VALUES (?, ?, ?)", [name, owner, now + ttl_s])
        con.execute("COMMIT")
        return True
    except Exception:
        con.execute("ROLLBACK")
        raise


def release_lock(con: sqlite3.Connection, name: str, owner: str) -> None:
    con.execute("DELETE FROM worker_lock WHERE name = ? AND owner = ?", [name, owner])


def seen_event(con: sqlite3.Connection, event_id: str) -> bool:
    """Record an inbound event id; True if it was already processed (dedupe before any state change)."""
    try:
        con.execute("INSERT INTO inbound_event VALUES (?, ?)", [event_id, time.time()])
        return False
    except sqlite3.IntegrityError:
        return True
