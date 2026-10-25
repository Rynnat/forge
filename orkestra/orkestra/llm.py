"""LLM çağrıları: `claude -p` (şef: opus, işçi: haiku) + test için mock.

Her çağrı `logs/maliyet.jsonl`'a bir satır yazar (maliyet-sayaci `tools` sözleşmesi:
`llm` bloğunda backend, calls, ok, failed, *_tokens, cost_usd). `cost_usd`, CLI'nin
bildirdiği `total_cost_usd`'dur (liste fiyatı, teorik).

Bağlam küçük tutulur: özel sistem istemi, varsayılan araçlar kapalı (web işçisi hariç),
MCP/ayar kaynakları yüklenmez, boş çalışma dizini (CLAUDE.md yüklenmez), oturum kaydedilmez.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

SYSTEM_JSON = ("You are a careful research assistant. Answer ONLY with valid JSON matching the "
               "requested schema. Quotes must be copied verbatim from the provided text.")


class LLMError(Exception):
    pass


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    web_search: int = 0


@dataclass
class Result:
    text: str
    usage: Usage
    duration_s: float


@dataclass
class Ledger:
    """Koşu içi toplam + jsonl log."""
    path: Path | None
    run_id: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)
    by_stage: dict[str, dict] = field(default_factory=dict)

    def add(self, stage: str, model: str, ok: bool, u: Usage, dur: float, error: str = "") -> None:
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "arac": "orkestra", "run_id": self.run_id,
               "asama": stage, "model": model, "sure_s": round(dur, 2), "hata": error[:200],
               "llm": {"backend": "claude_cli", "calls": 1, "ok": int(ok), "failed": int(not ok),
                       "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                       "cache_read_tokens": u.cache_read_tokens, "cache_write_tokens": u.cache_write_tokens,
                       "cost_usd": round(u.cost_usd, 6)}}
        with self.lock:
            s = self.by_stage.setdefault(stage, {"calls": 0, "failed": 0, "cost_usd": 0.0, "in": 0, "out": 0,
                                                 "web_search": 0})
            s["calls"] += 1
            s["failed"] += int(not ok)
            s["cost_usd"] += u.cost_usd
            s["in"] += u.input_tokens + u.cache_read_tokens + u.cache_write_tokens
            s["out"] += u.output_tokens
            s["web_search"] += u.web_search
            if self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    @property
    def total(self) -> float:
        return sum(s["cost_usd"] for s in self.by_stage.values())


def usage_from_wrap(wrap: dict) -> Usage:
    u = Usage(cost_usd=float(wrap.get("total_cost_usd") or 0.0))
    mu = wrap.get("modelUsage") or {}
    if mu:  # çok turlu (araçlı) çağrılarda üst düzey `usage` yalnız son turu gösterir
        for m in mu.values():
            u.input_tokens += int(m.get("inputTokens") or 0)
            u.output_tokens += int(m.get("outputTokens") or 0)
            u.cache_read_tokens += int(m.get("cacheReadInputTokens") or 0)
            u.cache_write_tokens += int(m.get("cacheCreationInputTokens") or 0)
            u.web_search += int(m.get("webSearchRequests") or 0)
    else:
        us = wrap.get("usage") or {}
        u.input_tokens = int(us.get("input_tokens") or 0)
        u.output_tokens = int(us.get("output_tokens") or 0)
        u.cache_read_tokens = int(us.get("cache_read_input_tokens") or 0)
        u.cache_write_tokens = int(us.get("cache_creation_input_tokens") or 0)
    return u


class LLM:
    def __init__(self, cfg, ledger: Ledger, runner: Callable[..., Any] = subprocess.run):
        self.cfg = cfg
        self.ledger = ledger
        self.runner = runner
        self.exe = cfg.claude_cli_path or shutil.which("claude") or "claude"
        self.cwd = Path(cfg.data_dir) / "llm_cwd"

    def args(self, model: str, system: str, tools: str = "", budget: float | None = None) -> list[str]:
        a = [self.exe, "-p", "--model", model, "--output-format", "json", "--system-prompt", system,
             "--tools", tools, "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence"]
        if tools:
            a += ["--allowedTools", tools]
        if budget:
            a += ["--max-budget-usd", f"{budget:.2f}"]
        return a

    def complete(self, prompt: str, *, model: str, stage: str, system: str = SYSTEM_JSON,
                 tools: str = "", budget: float | None = None) -> Result:
        self.cwd.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        last = ""
        for attempt in range(self.cfg.llm_max_retries + 1):
            t0 = time.monotonic()
            try:
                p = self.runner(self.args(model, system, tools, budget), input=prompt, capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=self.cfg.llm_timeout_s, cwd=str(self.cwd), env=env)
            except subprocess.TimeoutExpired:
                last = "zaman aşımı"
                self.ledger.add(stage, model, False, Usage(), time.monotonic() - t0, last)
                continue
            dur = time.monotonic() - t0
            try:
                wrap = json.loads(p.stdout)
            except (json.JSONDecodeError, TypeError):
                last = f"çıkış {p.returncode}: {(p.stderr or p.stdout or '')[:300]}"
                self.ledger.add(stage, model, False, Usage(), dur, last)
                continue
            u = usage_from_wrap(wrap)
            if wrap.get("is_error") or wrap.get("subtype") not in (None, "success"):
                last = f"CLI hata: {wrap.get('subtype')}: {str(wrap.get('result'))[:200]}"
                self.ledger.add(stage, model, False, u, dur, last)
                # bütçe tavanı: tekrar etmek yine aynı tavana çarpar
                if "budget" in str(wrap.get("subtype")):
                    break
                continue
            self.ledger.add(stage, model, True, u, dur)
            return Result(str(wrap.get("result") or ""), u, dur)
        raise LLMError(f"{stage}: {last}")


class MockLLM:
    """Testler için: responder(prompt, stage) -> str."""

    def __init__(self, responder: Callable[[str, str], str], ledger: Ledger | None = None):
        self.responder = responder
        self.ledger = ledger or Ledger(None)
        self.calls: list[tuple[str, str]] = []

    def complete(self, prompt: str, *, model: str, stage: str, **kw) -> Result:
        self.calls.append((stage, prompt))
        out = self.responder(prompt, stage)
        if isinstance(out, Exception):
            self.ledger.add(stage, model, False, Usage(), 0.0, str(out))
            raise LLMError(str(out))
        u = Usage(input_tokens=len(prompt) // 4, output_tokens=len(out) // 4, cost_usd=0.0)
        self.ledger.add(stage, model, True, u, 0.0)
        return Result(out, u, 0.0)


def parse_json(text: str) -> Any:
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if m:
        t = m.group(1).strip()
    dec = json.JSONDecoder()
    for i, ch in enumerate(t):
        if ch in "{[":
            try:
                return dec.raw_decode(t[i:])[0]
            except json.JSONDecodeError:
                continue
    raise ValueError(f"JSON yok: {text[:200]!r}")


def call_json(llm, prompt: str, **kw) -> tuple[Any | None, str]:
    """(nesne, durum) — durum: OK | PARSE_FAIL | LLM_ERROR. JSON değilse bir kez tekrar."""
    for attempt in range(2):
        p = prompt if attempt == 0 else prompt + "\n\nIMPORTANT: reply with ONLY the JSON object."
        try:
            r = llm.complete(p, **kw)
        except LLMError:
            return None, "LLM_ERROR"
        try:
            return parse_json(r.text), "OK"
        except ValueError:
            continue
    return None, "PARSE_FAIL"
