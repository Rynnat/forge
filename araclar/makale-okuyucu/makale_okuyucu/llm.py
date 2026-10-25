"""Takılabilir LLM arka uçları: claude_cli (varsayılan), anthropic_api, mock.

gapmine/llm.py'den kopyalandı (ClaudeCLIBackend, AnthropicAPIBackend, parse_json_response,
call_json aynı); gapmine DB'si yerine `recorder` geri çağrısı ve iş parçacığı kilidi eklendi.

claude_cli: `claude -p --model haiku --output-format json`; prompt STDIN'den verilir
(Windows komut satırı ~32K karakter sınırı). Bağlamı küçültmek için --system-prompt ile
Claude Code'un varsayılan sistem istemi değiştirilir, araçlar kapatılır (--tools ""),
MCP/ayar kaynakları yüklenmez, oturum kaydedilmez; cwd boş bir proje-içi dizin.
Böylece kullanıcının CLAUDE.md / bellek dosyaları modele GİTMEZ ve çağrı ~20 kat ucuzlar.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from makale_okuyucu.config import Config

log = logging.getLogger("makale_okuyucu.llm")

DEFAULT_SYSTEM = (
    "You are a careful research assistant that answers ONLY with valid JSON matching the "
    "requested schema. Quotes must be copied verbatim from the provided text."
)


class LLMError(Exception):
    pass


class JSONParseError(ValueError):
    pass


@dataclass
class LLMResult:
    text: str
    duration_s: float = 0.0
    attempts: int = 1
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class LLMStats:
    calls: int = 0
    ok: int = 0
    failed: int = 0
    attempts: int = 0
    duration_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    by_purpose: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        d = dict(self.__dict__)
        d["by_purpose"] = dict(self.by_purpose)
        d["cost_usd"] = round(self.cost_usd, 6)
        d["duration_s"] = round(self.duration_s, 2)
        return d


Recorder = Callable[[str, str, bool, int, float, "LLMResult | None", "str | None"], None]


class LLMBackend:
    name = "base"

    def __init__(self, cfg: Config, recorder: Recorder | None = None):
        self.cfg = cfg
        self.recorder = recorder
        self.stats = LLMStats()
        self._lock = threading.Lock()

    def reset_stats(self) -> None:
        with self._lock:
            self.stats = LLMStats()

    def _complete(self, prompt: str, system: str) -> LLMResult:
        raise NotImplementedError

    def complete(self, prompt: str, system: str = DEFAULT_SYSTEM, purpose: str = "") -> LLMResult:
        with self._lock:
            self.stats.calls += 1
            self.stats.by_purpose[purpose] = self.stats.by_purpose.get(purpose, 0) + 1
        t0 = time.monotonic()
        try:
            res = self._complete(prompt, system)
        except LLMError as exc:
            dur = time.monotonic() - t0
            with self._lock:
                self.stats.failed += 1
                self.stats.duration_s += dur
            self._record(purpose, False, getattr(exc, "attempts", 1), dur, None, str(exc))
            raise
        with self._lock:
            s = self.stats
            s.ok += 1
            s.attempts += res.attempts
            s.duration_s += res.duration_s
            s.input_tokens += res.input_tokens
            s.output_tokens += res.output_tokens
            s.cache_read_tokens += res.cache_read_tokens
            s.cache_write_tokens += res.cache_write_tokens
            s.cost_usd += res.cost_usd
        self._record(purpose, True, res.attempts, res.duration_s, res, None)
        return res

    def _record(self, purpose, ok, attempts, dur, res, error) -> None:
        if self.recorder is not None:
            self.recorder(self.name, purpose, ok, attempts, dur, res, error)


# --------------------------------------------------------------------------- claude CLI
class ClaudeCLIBackend(LLMBackend):
    name = "claude_cli"

    def __init__(self, cfg: Config, recorder: Recorder | None = None,
                 runner: Callable[..., Any] = subprocess.run, sleep: Callable[[float], None] = time.sleep):
        super().__init__(cfg, recorder)
        self.runner = runner
        self.sleep = sleep
        self.exe = cfg.claude_cli_path or shutil.which("claude") or "claude"
        self.cwd = Path(cfg.data_dir) / "llm_cwd"  # boş dizin: proje CLAUDE.md'si yüklenmesin

    def build_args(self, system: str) -> list[str]:
        return [
            self.exe, "-p",
            "--model", self.cfg.llm_model,
            "--output-format", "json",
            "--system-prompt", system,
            "--tools", "",
            "--strict-mcp-config",
            "--setting-sources", "",
            "--no-session-persistence",
        ]

    def _complete(self, prompt: str, system: str) -> LLMResult:
        self.cwd.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k not in ("CLAUDECODE",)}
        args = self.build_args(system)
        last_err = ""
        t0 = time.monotonic()
        attempts = 0
        for attempt in range(self.cfg.llm_max_retries + 1):
            attempts = attempt + 1
            try:
                proc = self.runner(
                    args, input=prompt, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=self.cfg.llm_timeout_s, cwd=str(self.cwd), env=env,
                )
            except subprocess.TimeoutExpired:
                last_err = f"zaman aşımı ({self.cfg.llm_timeout_s:.0f}s)"
                log.warning("claude -p %s (deneme %d)", last_err, attempts)
                self._backoff(attempt)
                continue
            except OSError as exc:  # exe yok vb. — tekrar denemek anlamsız
                err = LLMError(f"claude çalıştırılamadı: {exc}")
                err.attempts = attempts  # type: ignore[attr-defined]
                raise err from exc
            if proc.returncode != 0:
                last_err = f"çıkış kodu {proc.returncode}: {(proc.stderr or proc.stdout or '')[:400]}"
                log.warning("claude -p hata (deneme %d): %s", attempts, last_err)
                self._backoff(attempt)
                continue
            try:
                wrap = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                last_err = f"CLI çıktısı JSON değil: {exc}: {proc.stdout[:200]!r}"
                log.warning("claude -p (deneme %d): %s", attempts, last_err)
                self._backoff(attempt)
                continue
            if wrap.get("is_error") or wrap.get("subtype") not in (None, "success"):
                last_err = f"CLI hata bildirdi: subtype={wrap.get('subtype')} result={str(wrap.get('result'))[:300]}"
                log.warning("claude -p (deneme %d): %s", attempts, last_err)
                self._backoff(attempt)
                continue
            usage = wrap.get("usage") or {}
            return LLMResult(
                text=str(wrap.get("result") or ""),
                duration_s=time.monotonic() - t0,
                attempts=attempts,
                input_tokens=int(usage.get("input_tokens") or 0),
                output_tokens=int(usage.get("output_tokens") or 0),
                cache_read_tokens=int(usage.get("cache_read_input_tokens") or 0),
                cache_write_tokens=int(usage.get("cache_creation_input_tokens") or 0),
                cost_usd=float(wrap.get("total_cost_usd") or 0.0),
            )
        err = LLMError(f"claude -p {attempts} denemede başarısız: {last_err}")
        err.attempts = attempts  # type: ignore[attr-defined]
        raise err

    def _backoff(self, attempt: int) -> None:
        if attempt < self.cfg.llm_max_retries:
            self.sleep(5.0 * (2 ** attempt))


# --------------------------------------------------------------------------- Anthropic API
class AnthropicAPIBackend(LLMBackend):
    name = "anthropic_api"

    def __init__(self, cfg: Config, recorder: Recorder | None = None, client: Any = None):
        super().__init__(cfg, recorder)
        if client is None:
            import anthropic  # isteğe bağlı bağımlılık (requirements'ta yok)

            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise LLMError("anthropic_api arka ucu için ANTHROPIC_API_KEY gerekli")
            client = anthropic.Anthropic(max_retries=cfg.llm_max_retries, timeout=cfg.llm_timeout_s)
        self.client = client

    def _complete(self, prompt: str, system: str) -> LLMResult:
        t0 = time.monotonic()
        try:
            msg = self.client.messages.create(
                model=self.cfg.api_model, max_tokens=8192, system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # SDK hata hiyerarşisi geniş; LLMError'a çevrilip sayılır
            raise LLMError(f"Anthropic API hatası: {type(exc).__name__}: {exc}") from exc
        text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text")
        u = msg.usage
        return LLMResult(
            text=text, duration_s=time.monotonic() - t0, attempts=1,
            input_tokens=getattr(u, "input_tokens", 0) or 0,
            output_tokens=getattr(u, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
        )


# --------------------------------------------------------------------------- mock
class MockBackend(LLMBackend):
    """Testler ve çevrimdışı deneme için. `responder(prompt, system) -> str | Exception`
    ya da sırayla tüketilecek yanıt listesi. Varsayılan: mockllm.default_responder."""

    name = "mock"

    def __init__(self, cfg: Config, recorder: Recorder | None = None,
                 responder: Callable[[str, str], Any] | list | None = None):
        super().__init__(cfg, recorder)
        self.prompts: list[str] = []
        if isinstance(responder, list):
            queue = list(responder)
            self.responder = lambda p, s: queue.pop(0) if queue else ""
        elif responder is None:
            from makale_okuyucu.mockllm import default_responder

            self.responder = default_responder
        else:
            self.responder = responder

    def _complete(self, prompt: str, system: str) -> LLMResult:
        with self._lock:
            self.prompts.append(prompt)
        out = self.responder(prompt, system)
        if isinstance(out, Exception):
            raise out
        return LLMResult(text=out, input_tokens=len(prompt) // 4, output_tokens=len(out) // 4)


def make_backend(cfg: Config, recorder: Recorder | None = None, **kw) -> LLMBackend:
    name = cfg.llm_backend
    if name == "claude_cli":
        return ClaudeCLIBackend(cfg, recorder, **kw)
    if name == "anthropic_api":
        return AnthropicAPIBackend(cfg, recorder, **kw)
    if name == "mock":
        return MockBackend(cfg, recorder, **kw)
    raise ValueError(f"Bilinmeyen LLM arka ucu: {name}")


def parse_json_response(text: str) -> Any:
    """LLM metninden JSON çıkar: kod çiti soy, ilk {..} / [..] bloğunu çöz."""
    if text is None:
        raise JSONParseError("boş yanıt")
    t = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    if fence:
        t = fence.group(1).strip()
    dec = json.JSONDecoder()
    if t[:1] in "{[":
        try:
            obj, end = dec.raw_decode(t)
            if not t[end:].strip():
                return obj
        except json.JSONDecodeError as exc:  # aşağıdaki taramaya devam; sonunda yine başarısızsa fırlatılır
            log.debug("doğrudan JSON çözülemedi, taranıyor: %s", exc)
    for i, ch in enumerate(t):
        if ch in "{[":
            try:
                obj, _ = dec.raw_decode(t[i:])
                return obj
            except json.JSONDecodeError:
                continue
    raise JSONParseError(f"JSON bulunamadı: {text[:200]!r}")


RETRY_SUFFIX = (
    "\n\nIMPORTANT: Your previous reply could not be parsed as JSON. Reply again with ONLY "
    "the JSON object, no prose, no code fences."
)


def call_json(llm: LLMBackend, prompt: str, purpose: str,
              system: str = DEFAULT_SYSTEM) -> tuple[Any | None, str, str | None]:
    """(nesne, durum, hata). durum: OK | PARSE_FAIL | LLM_ERROR.
    JSON değilse bir kez tekrar denenir; yine olmazsa PARSE_FAIL."""
    last = None
    for attempt in range(2):
        p = prompt if attempt == 0 else prompt + RETRY_SUFFIX
        try:
            res = llm.complete(p, system=system, purpose=purpose)
        except LLMError as exc:
            return None, "LLM_ERROR", str(exc)[:500]
        try:
            return parse_json_response(res.text), "OK", None
        except JSONParseError as exc:
            last = str(exc)[:500]
            log.warning("%s: JSON ayrıştırılamadı (deneme %d): %s", purpose, attempt + 1, last)
    return None, "PARSE_FAIL", last
