"""Nazik HTTP istemcisi: kaynak başına hız sınırı, SQLite önbellek, 429/5xx bekleme.

gapmine denetim dersi #3: Retry-After'sız geçici 429 kota DEĞİLDİR. Önce dakikalara
uzanan bekleme (`backoff_s`) denenir; ancak tekrarlar tükenince ya da Retry-After
`max_wait_s`'i aşınca `QuotaExhausted` fırlatılır ve çağıran kaynağı EKSİK işaretler.
"""
from __future__ import annotations

import email.utils
import hashlib
import json
import sqlite3
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests

from orkestra import __version__
from orkestra.config import Config

USER_AGENT = f"forge-orkestra/{__version__} (literature survey tool; python-requests)"


class HttpError(Exception):
    def __init__(self, source: str, status: int | None, detail: str):
        super().__init__(f"{source}: HTTP {status}: {detail}")
        self.source, self.status, self.detail = source, status, detail


class RequestFailed(HttpError):
    pass


class QuotaExhausted(HttpError):
    pass


class BotBlocked(HttpError):
    """Sunucu bot doğrulaması (ör. Anubis) döndürdü; aşmaya çalışılmaz."""


@dataclass
class Resp:
    status: int
    body: bytes
    from_cache: bool

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class Cache:
    def __init__(self, path: Path | None):
        self.lock = threading.Lock()
        self.conn = None
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(path), check_same_thread=False)
            self.conn.execute("CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY, body BLOB, ts REAL)")
            self.conn.commit()

    def get(self, k: str) -> bytes | None:
        if self.conn is None:
            return None
        with self.lock:
            row = self.conn.execute("SELECT body FROM cache WHERE k=?", (k,)).fetchone()
        return bytes(row[0]) if row else None

    def put(self, k: str, body: bytes) -> None:
        if self.conn is None:
            return
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (k, body, time.time()))
            self.conn.commit()


def parse_retry_after(v: str | None) -> float | None:
    if not v:
        return None
    v = v.strip()
    try:
        return float(v)
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(v)
        return max(0.0, dt.timestamp() - time.time())
    except (TypeError, ValueError, IndexError):
        return None


class Http:
    def __init__(self, cfg: Config, session: Any = None, sleep: Callable[[float], None] = time.sleep,
                 cache_path: Path | None | bool = True):
        self.cfg = cfg
        self.session = session or requests.Session()
        self.sleep = sleep
        if cache_path is True:
            cache_path = Path(cfg.data_dir) / "http_cache.sqlite"
        self.cache = Cache(cache_path or None)
        self.locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
        self.last: dict[str, float] = {}
        self.sems: dict[str, threading.BoundedSemaphore] = {}
        self.stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.exhausted: dict[str, str] = {}

    def _key(self, source: str, method: str, url: str, params: Any, data: Any) -> str:
        raw = json.dumps([source, method, url, params, data], sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def request(self, source: str, url: str, params: dict | None = None, data: Any = None,
                method: str = "GET", headers: dict | None = None, cache: bool = True,
                json_body: Any = None) -> Resp:
        if source in self.exhausted:
            raise QuotaExhausted(source, 429, "bu koşuda zaten tükendi: " + self.exhausted[source])
        key = self._key(source, method, url, params, data if json_body is None else json_body)
        st = self.stats[source]
        if cache:
            body = self.cache.get(key)
            if body is not None:
                st["cache"] += 1
                return Resp(200, body, True)
        lim = self.cfg.limits_for(source)
        hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
        last = ""
        for attempt in range(lim.max_retries + 1):
            r, err = self._send(source, lim, method, url, params, data, json_body, hdrs)
            if err:
                last = err
            st["istek"] += 1
            if r is None:
                st["ag_hatasi"] += 1
                if attempt < lim.max_retries:
                    self.sleep(min(lim.backoff_s[min(attempt, len(lim.backoff_s) - 1)], 30.0))
                continue
            code = int(r.status_code)
            body = r.content if isinstance(r.content, (bytes, bytearray)) else str(r.content).encode()
            if code in (200, 202) and _is_bot_wall(body, r):
                st["bot"] += 1
                raise BotBlocked(source, code, "bot doğrulama sayfası (aşılmaz)")
            if code == 200:
                if cache:
                    self.cache.put(key, bytes(body))
                return Resp(200, bytes(body), False)
            last = body[:200].decode("utf-8", errors="replace")
            if code == 429 and b"timed out" in body[:400].lower():
                # QLever (DBLP SPARQL) sorgu zaman aşımını 429 ile döndürür: kota değil
                st["sorgu_zaman_asimi"] += 1
                raise RequestFailed(source, 429, "sorgu zaman aşımı: " + last)
            if code == 429:
                st["429"] += 1
                ra = parse_retry_after((r.headers or {}).get("Retry-After"))
                if ra is not None and ra > lim.max_wait_s:
                    self.exhausted[source] = f"Retry-After={ra:.0f}s"
                    raise QuotaExhausted(source, 429, self.exhausted[source])
                if attempt < lim.max_retries:
                    self.sleep(max(ra or 0.0, lim.backoff_s[min(attempt, len(lim.backoff_s) - 1)]))
                    continue
                self.exhausted[source] = f"{lim.max_retries + 1} denemede 429"
                raise QuotaExhausted(source, 429, self.exhausted[source])
            if 500 <= code < 600:
                st["5xx"] += 1
                if attempt < lim.max_retries:
                    self.sleep(min(lim.backoff_s[min(attempt, len(lim.backoff_s) - 1)], 60.0))
                continue
            raise RequestFailed(source, code, last)
        raise RequestFailed(source, None, f"tekrarlar tükendi: {last}")

    def _send(self, source, lim, method, url, params, data, json_body, hdrs):
        """Tek istek. es_zamanli=1: kaynak başına sıralı + aralıklı (kilit istek boyunca tutulur).
        es_zamanli>1: başlangıçlar yine min_interval aralıklı, ama en çok N istek aynı anda uçuşta."""
        def call():
            try:
                return self.session.request(method, url, params=params, data=data, json=json_body,
                                            headers=hdrs, timeout=self.cfg.http_timeout_s), ""
            except (requests.RequestException, OSError) as exc:
                return None, f"{type(exc).__name__}: {exc}"

        def wait_gap():
            gap = time.monotonic() - self.last.get(source, -1e9)
            if gap < lim.min_interval_s:
                self.sleep(lim.min_interval_s - gap)

        if lim.es_zamanli <= 1:
            with self.locks[source]:
                wait_gap()
                res = call()
                self.last[source] = time.monotonic()
            return res
        with self.locks["_sem"]:
            sem = self.sems.setdefault(source, threading.BoundedSemaphore(lim.es_zamanli))
        with sem:
            with self.locks[source]:
                wait_gap()
                self.last[source] = time.monotonic()
            return call()

    def get(self, source: str, url: str, params: dict | None = None, **kw) -> Resp:
        return self.request(source, url, params=params, **kw)


def _is_bot_wall(body: bytes, r: Any) -> bool:
    head = body[:600].lower()
    return b"making sure you&#39;re not a bot" in head or b"anubis" in head and b"<html" in head
