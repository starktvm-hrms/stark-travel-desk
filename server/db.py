"""SQLite storage for Stark Travel Desk.

One database file under STARK_DATA_DIR (default /var/lib/stark-travel). All
access goes through `tx()`, which serialises writers with a process lock so the
web threads and the background sync never trip over each other.
"""
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

DATA_DIR = Path(os.environ.get("STARK_DATA_DIR", "/var/lib/stark-travel"))
DB_FILE = DATA_DIR / "travel.db"
_lock = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  pwhash   TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  username   TEXT NOT NULL,
  expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE IF NOT EXISTS travelers (
  id      TEXT PRIMARY KEY,
  name    TEXT NOT NULL,
  phone   TEXT NOT NULL DEFAULT '',
  email   TEXT NOT NULL DEFAULT '',
  aliases TEXT NOT NULL DEFAULT '',
  notify  INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS trips (
  id         TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  travelers  TEXT NOT NULL DEFAULT '[]',
  cancelled  INTEGER NOT NULL DEFAULT 0,
  notes      TEXT NOT NULL DEFAULT '',
  source     TEXT NOT NULL DEFAULT 'gmail',
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS segments (
  id          TEXT PRIMARY KEY,
  trip_id     TEXT NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
  position    INTEGER NOT NULL DEFAULT 0,
  type        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'confirmed',
  status_label TEXT NOT NULL DEFAULT '',
  origin      TEXT NOT NULL DEFAULT '',
  destination TEXT NOT NULL DEFAULT '',
  date        TEXT,
  start_time  TEXT,
  end_date    TEXT,
  end_time    TEXT,
  carrier     TEXT NOT NULL DEFAULT '',
  number      TEXT NOT NULL DEFAULT '',
  reference   TEXT NOT NULL DEFAULT '',
  details     TEXT NOT NULL DEFAULT '',
  email_id    TEXT
);
CREATE INDEX IF NOT EXISTS seg_trip ON segments(trip_id);
CREATE TABLE IF NOT EXISTS emails (
  gmail_id    TEXT PRIMARY KEY,
  subject     TEXT NOT NULL DEFAULT '',
  sender      TEXT NOT NULL DEFAULT '',
  received_at REAL,
  state       TEXT NOT NULL,           -- parsed | ignored | error
  trip_id     TEXT,
  error       TEXT NOT NULL DEFAULT '',
  processed_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS log (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id TEXT,
  at      REAL NOT NULL,
  actor   TEXT NOT NULL,
  kind    TEXT NOT NULL,
  message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS log_trip ON log(trip_id);
CREATE TABLE IF NOT EXISTS wa_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  trip_id     TEXT,
  segment_id  TEXT,
  traveler    TEXT NOT NULL DEFAULT '',
  to_phone    TEXT NOT NULL DEFAULT '',
  body        TEXT NOT NULL,
  trigger     TEXT NOT NULL,           -- new_trip | status | reminder | manual | test
  state       TEXT NOT NULL,           -- sent | failed | skipped
  provider_id TEXT NOT NULL DEFAULT '',
  error       TEXT NOT NULL DEFAULT '',
  at          REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS wa_trip ON wa_messages(trip_id);
"""


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


_con = None


def con():
    global _con
    with _lock:
        if _con is None:
            _con = connect()
            _con.executescript(SCHEMA)
            os.chmod(DB_FILE, 0o600)
        return _con


@contextmanager
def tx():
    c = con()
    with _lock:
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise


def rows(sql, args=()):
    with tx() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]


def one(sql, args=()):
    with tx() as c:
        r = c.execute(sql, args).fetchone()
        return dict(r) if r else None


def new_id():
    return uuid.uuid4().hex[:12]


def now():
    return time.time()


# ---------- settings ----------

def get_setting(key, default=None):
    r = one("SELECT value FROM settings WHERE key = ?", (key,))
    if r is None or r["value"] is None:
        return default
    return json.loads(r["value"])


def set_setting(key, value):
    with tx() as c:
        if value is None:
            c.execute("DELETE FROM settings WHERE key = ?", (key,))
        else:
            c.execute("INSERT INTO settings(key, value) VALUES(?, ?) "
                      "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, json.dumps(value)))


def add_log(trip_id, actor, kind, message, c=None):
    sql = "INSERT INTO log(trip_id, at, actor, kind, message) VALUES(?,?,?,?,?)"
    if c is not None:
        c.execute(sql, (trip_id, now(), actor, kind, message))
    else:
        with tx() as cc:
            cc.execute(sql, (trip_id, now(), actor, kind, message))
