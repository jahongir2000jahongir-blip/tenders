"""SQLite storage. One connection per call; WAL mode; schema created on first use."""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from . import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS tenders (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  source       TEXT NOT NULL,
  external_id  TEXT NOT NULL,
  country      TEXT NOT NULL,
  title        TEXT NOT NULL,
  description  TEXT,
  customer     TEXT,
  region       TEXT,
  category     TEXT NOT NULL DEFAULT 'other',
  method       TEXT,
  amount       REAL,
  currency     TEXT,
  amount_usd   REAL,
  published_at TEXT,
  deadline_at  TEXT,
  url          TEXT,
  status       TEXT NOT NULL DEFAULT 'open',
  fingerprint  TEXT NOT NULL,
  lang         TEXT,
  raw          TEXT,
  first_seen_at TEXT NOT NULL,
  updated_at   TEXT NOT NULL,
  UNIQUE (source, external_id)
);
CREATE INDEX IF NOT EXISTS ix_tenders_fp ON tenders (fingerprint);
CREATE INDEX IF NOT EXISTS ix_tenders_country ON tenders (country);
CREATE INDEX IF NOT EXISTS ix_tenders_deadline ON tenders (deadline_at);
CREATE INDEX IF NOT EXISTS ix_tenders_published ON tenders (published_at);
CREATE INDEX IF NOT EXISTS ix_tenders_category ON tenders (category);

CREATE TABLE IF NOT EXISTS sources (
  code         TEXT PRIMARY KEY,
  country      TEXT NOT NULL,
  enabled      INTEGER NOT NULL DEFAULT 1,
  last_run_at  TEXT,
  last_status  TEXT,
  last_error   TEXT,
  last_fetched INTEGER DEFAULT 0,
  last_added   INTEGER DEFAULT 0,
  last_updated INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS runs (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  source      TEXT NOT NULL,
  started_at  TEXT NOT NULL,
  finished_at TEXT,
  status      TEXT NOT NULL,
  fetched     INTEGER DEFAULT 0,
  added       INTEGER DEFAULT 0,
  updated     INTEGER DEFAULT 0,
  duplicates  INTEGER DEFAULT 0,
  error       TEXT
);
CREATE INDEX IF NOT EXISTS ix_runs_started ON runs (started_at);

CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'admin',
  created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token      TEXT PRIMARY KEY,
  user_id    INTEGER NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  email      TEXT NOT NULL,
  countries  TEXT NOT NULL,
  keywords   TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_PATH, timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """Serialised write transaction."""
    with _lock:
        con = connect()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def init() -> None:
    from .countries import SOURCES
    with tx() as con:
        con.executescript(SCHEMA)
        for s in SOURCES:
            con.execute(
                "INSERT OR IGNORE INTO sources (code, country) VALUES (?, ?)",
                (s["code"], s["country"]),
            )


def get_setting(key: str, default: Any = None) -> Any:
    con = connect()
    try:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default
    finally:
        con.close()


def set_setting(key: str, value: Any) -> None:
    with tx() as con:
        con.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )


def rows(sql: str, params: tuple = ()) -> list[dict]:
    con = connect()
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def one(sql: str, params: tuple = ()) -> dict | None:
    con = connect()
    try:
        r = con.execute(sql, params).fetchone()
        return dict(r) if r else None
    finally:
        con.close()
