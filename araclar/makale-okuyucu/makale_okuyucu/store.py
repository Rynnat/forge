"""Önbellek: SQLite (data/cache.db) + JSON dosyaları (data/papers/<anahtar>/)."""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers(
  key TEXT PRIMARY KEY, status TEXT, title TEXT, source_url TEXT, sha256 TEXT,
  pages INTEGER, chars INTEGER, card_json TEXT, created_at TEXT, version TEXT);
CREATE INDEX IF NOT EXISTS papers_sha ON papers(sha256);
CREATE TABLE IF NOT EXISTS aliases(alias TEXT PRIMARY KEY, key TEXT);
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, op TEXT, key TEXT, status TEXT, from_cache INTEGER,
  pages INTEGER, chunks INTEGER, llm_calls INTEGER, llm_failed INTEGER,
  input_tokens INTEGER, output_tokens INTEGER, cache_read_tokens INTEGER, cache_write_tokens INTEGER,
  cost_usd REAL, duration_s REAL, llm_duration_s REAL, unverified INTEGER, failed_chunks TEXT,
  detail TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS llm_calls(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, backend TEXT, purpose TEXT, ok INTEGER,
  attempts INTEGER, duration_s REAL, input_tokens INTEGER, output_tokens INTEGER,
  cache_read_tokens INTEGER, cache_write_tokens INTEGER, cost_usd REAL, error TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS asks(
  key TEXT, question TEXT, answer_json TEXT, ts TEXT, PRIMARY KEY(key, question));
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_dir(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", key)


class Store:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.data_dir / "cache.db"), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.lock = threading.Lock()
        self.run_id: int | None = None

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ papers
    def paper_dir(self, key: str) -> Path:
        d = self.data_dir / "papers" / safe_dir(key)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def resolve(self, key: str) -> str | None:
        """Anahtar ya da takma ad → kayıtlı ve kartı olan anahtar."""
        row = self.conn.execute("SELECT key FROM aliases WHERE alias=?", (key,)).fetchone()
        k = row["key"] if row else key
        row = self.conn.execute("SELECT key FROM papers WHERE key=? AND card_json IS NOT NULL", (k,)).fetchone()
        return row["key"] if row else None

    def by_sha(self, sha: str) -> str | None:
        row = self.conn.execute(
            "SELECT key FROM papers WHERE sha256=? AND card_json IS NOT NULL", (sha,)).fetchone()
        return row["key"] if row else None

    def add_alias(self, alias: str, key: str) -> None:
        if alias != key:
            with self.lock:
                self.conn.execute("INSERT OR REPLACE INTO aliases(alias, key) VALUES (?,?)", (alias, key))
                self.conn.commit()

    def aliases(self, key: str) -> list[str]:
        return [r["alias"] for r in self.conn.execute("SELECT alias FROM aliases WHERE key=?", (key,))]

    def save_card(self, card: dict, sha: str, chars: int, version: str) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO papers(key,status,title,source_url,sha256,pages,chars,card_json,created_at,version)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (card["key"], card["status"], card.get("title"), card.get("source_url"), sha,
                 card.get("pages"), chars, json.dumps(card, ensure_ascii=False), now(), version))
            self.conn.commit()

    def load_card(self, key: str) -> dict | None:
        row = self.conn.execute("SELECT card_json FROM papers WHERE key=?", (key,)).fetchone()
        return json.loads(row["card_json"]) if row and row["card_json"] else None

    def write_json(self, key: str, name: str, obj) -> Path:
        p = self.paper_dir(key) / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        return p

    def read_json(self, key: str, name: str):
        p = self.paper_dir(key) / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    # ------------------------------------------------------------------ runs / llm
    def start_run(self, op: str, key: str) -> int:
        with self.lock:
            cur = self.conn.execute("INSERT INTO runs(op, key, status, ts) VALUES (?,?,?,?)", (op, key, "RUNNING", now()))
            self.conn.commit()
            self.run_id = cur.lastrowid
        return self.run_id

    def finish_run(self, run_id: int, **kw) -> None:
        cols = ", ".join(f"{k}=?" for k in kw)
        with self.lock:
            self.conn.execute(f"UPDATE runs SET {cols} WHERE id=?", (*kw.values(), run_id))
            self.conn.commit()

    def record_llm(self, backend, purpose, ok, attempts, dur, res, error) -> None:
        with self.lock:
            self.conn.execute(
                "INSERT INTO llm_calls(run_id, backend, purpose, ok, attempts, duration_s, input_tokens,"
                " output_tokens, cache_read_tokens, cache_write_tokens, cost_usd, error, ts)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (self.run_id, backend, purpose, int(ok), attempts, dur,
                 res.input_tokens if res else 0, res.output_tokens if res else 0,
                 res.cache_read_tokens if res else 0, res.cache_write_tokens if res else 0,
                 res.cost_usd if res else 0.0, (error or None) and str(error)[:2000], now()))
            self.conn.commit()

    def runs(self, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

    # ------------------------------------------------------------------ asks
    def get_ask(self, key: str, q: str) -> dict | None:
        row = self.conn.execute("SELECT answer_json FROM asks WHERE key=? AND question=?", (key, q)).fetchone()
        return json.loads(row["answer_json"]) if row else None

    def put_ask(self, key: str, q: str, ans: dict) -> None:
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO asks(key, question, answer_json, ts) VALUES (?,?,?,?)",
                              (key, q, json.dumps(ans, ensure_ascii=False), now()))
            self.conn.commit()
