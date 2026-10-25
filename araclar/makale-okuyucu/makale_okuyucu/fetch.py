"""Girdi çözümleme ve PDF indirme. LLM yok.

Bot engeli ya da ödeme duvarı ATLATILMAZ: durum işaretlenir, kullanıcıdan yerel PDF istenir.
Durumlar: OK | NO_OA | NOT_FOUND | PAYWALL | BOT_BLOCKED | NOT_PDF | PARSE_ERROR |
          EMPTY_TEXT | NETWORK_ERROR | HTTP_ERROR | BAD_INPUT
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable

log = logging.getLogger("makale_okuyucu.fetch")

BOT_MARKERS = ("just a moment", "cf-chl", "challenge-platform", "attention required",
               "verify you are human", "captcha", "cf-browser-verification", "ddos protection")
PAYWALL_MARKERS = ("access through your institution", "purchase this article", "buy article",
                   "subscribe to", "get access", "rent this article", "log in to access",
                   "sign in to access")
MIN_CHARS = 500

_ARXIV_NEW = re.compile(r"(?<![\d.])(\d{4}\.\d{4,5})(v\d+)?(?![\d])")
_ARXIV_OLD = re.compile(r"\b([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?\b")
_DOI = re.compile(r"(10\.\d{4,9}/[^\s\"<>]+)", re.I)


class InputError(ValueError):
    pass


@dataclass
class PaperInput:
    kind: str  # arxiv | doi | url | local
    key: str
    raw: str
    arxiv_id: str | None = None
    doi: str | None = None
    url: str | None = None
    path: str | None = None


def resolve_input(s: str) -> PaperInput:
    raw = s.strip()
    if not raw:
        raise InputError("boş girdi")
    if os.path.isfile(raw):
        with open(raw, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        return PaperInput("local", f"sha:{sha[:16]}", raw, path=os.path.abspath(raw))
    low = raw.lower()
    if low.startswith(("http://", "https://")):
        m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(.+?)(?:\.pdf)?/?$", raw, re.I)
        if m:
            return _arxiv(m.group(1), raw)
        if re.search(r"(?:dx\.)?doi\.org/", low):
            md = _DOI.search(raw)
            if md:
                return _doi(md.group(1), raw)
        h = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return PaperInput("url", f"url:{h}", raw, url=raw)
    s2 = raw[6:].strip() if low.startswith("arxiv:") else raw
    s2 = re.sub(r"^doi:\s*", "", s2, flags=re.I)
    if _DOI.match(s2):
        return _doi(s2, raw)
    if _ARXIV_NEW.fullmatch(s2) or _ARXIV_OLD.fullmatch(s2):
        return _arxiv(s2, raw)
    raise InputError(f"girdi tanınmadı (arXiv id / DOI / PDF URL / yerel PDF bekleniyordu): {raw!r}")


def _arxiv(s: str, raw: str) -> PaperInput:
    m = _ARXIV_NEW.search(s) or _ARXIV_OLD.search(s)
    if not m:
        raise InputError(f"arXiv id çözülemedi: {raw!r}")
    aid = m.group(1)
    return PaperInput("arxiv", f"arxiv:{aid}", raw, arxiv_id=aid)


def _doi(s: str, raw: str) -> PaperInput:
    doi = _DOI.search(s).group(1).rstrip(".,;)").lower()
    ma = re.match(r"10\.48550/arxiv\.(.+)$", doi)
    if ma:
        return _arxiv(ma.group(1), raw)
    return PaperInput("doi", f"doi:{doi}", raw, doi=doi)

# --------------------------------------------------------------------------- HTTP
@dataclass
class HttpResponse:
    status: int | None  # None = ağ hatası
    content_type: str = ""
    body: bytes = b""
    headers: dict = field(default_factory=dict)
    error: str = ""


Getter = Callable[[str], HttpResponse]


def requests_getter(user_agent: str, timeout: float) -> Getter:
    import requests

    sess = requests.Session()
    sess.headers.update({"User-Agent": user_agent, "Accept": "application/pdf,application/json,*/*"})

    def get(url: str) -> HttpResponse:
        try:
            r = sess.get(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            return HttpResponse(None, error=f"{type(exc).__name__}: {exc}"[:300])
        return HttpResponse(r.status_code, r.headers.get("Content-Type", ""), r.content,
                            {k.lower(): v for k, v in r.headers.items()})

    return get


def classify(resp: HttpResponse) -> str:
    """HTTP yanıtını duruma çevirir (gövde PDF mi bakılmaz, yalnız durum)."""
    if resp.status is None:
        return "NETWORK_ERROR"
    head = resp.body[:20000].decode("utf-8", "replace").lower()
    bot = any(m in head for m in BOT_MARKERS) or resp.headers.get("cf-mitigated") == "challenge"
    if resp.status in (404, 410):
        return "NOT_FOUND"
    if resp.status in (403, 429, 503) and bot:
        return "BOT_BLOCKED"
    if resp.status in (401, 402, 403):
        return "PAYWALL"
    if resp.status != 200:
        return "HTTP_ERROR"
    if is_pdf(resp):
        return "OK"
    if bot:
        return "BOT_BLOCKED"
    if any(m in head for m in PAYWALL_MARKERS):
        return "PAYWALL"
    return "NOT_PDF"


def is_pdf(resp: HttpResponse) -> bool:
    return resp.body[:5] == b"%PDF-" or (
        "pdf" in (resp.content_type or "").lower() and b"%PDF" in resp.body[:1024])


# --------------------------------------------------------------------------- metadata
def arxiv_title(aid: str, get: Getter) -> str:
    r = get(f"http://export.arxiv.org/api/query?id_list={aid}")
    if r.status != 200:
        return ""
    try:
        root = ET.fromstring(r.body)
    except ET.ParseError:
        return ""
    ns = {"a": "http://www.w3.org/2005/Atom"}
    t = root.find("a:entry/a:title", ns)
    return re.sub(r"\s+", " ", t.text).strip() if t is not None and t.text else ""


def openalex_work(doi: str, get: Getter) -> tuple[dict | None, str]:
    import json

    r = get(f"https://api.openalex.org/works/doi:{doi}")
    if r.status is None:
        return None, "NETWORK_ERROR"
    if r.status == 404:
        return None, "NOT_FOUND"
    if r.status != 200:
        return None, "HTTP_ERROR"
    try:
        return json.loads(r.body), "OK"
    except ValueError:
        return None, "HTTP_ERROR"


@dataclass
class FetchResult:
    status: str
    body: bytes | None = None
    source_url: str | None = None
    title: str = ""
    attempts: list[str] = field(default_factory=list)


_PRIORITY = ["OK", "BOT_BLOCKED", "PAYWALL", "NOT_PDF", "NOT_FOUND", "HTTP_ERROR", "NETWORK_ERROR", "NO_OA"]


def _worst(statuses: list[str]) -> str:
    """Başarısızlıkta en bilgilendirici durum (engel/duvar önce)."""
    for s in _PRIORITY:
        if s in statuses:
            return s
    return statuses[-1] if statuses else "NO_OA"


def candidate_urls(inp: PaperInput, get: Getter) -> tuple[list[str], str, list[str]]:
    """(url'ler, başlık, notlar)."""
    notes: list[str] = []
    if inp.kind == "arxiv":
        title = arxiv_title(inp.arxiv_id, get)
        if not title:
            notes.append("arXiv başlığı alınamadı (zararsız)")
        return [f"https://arxiv.org/pdf/{inp.arxiv_id}"], title, notes
    if inp.kind == "url":
        return [inp.url], "", notes
    if inp.kind == "doi":
        work, st = openalex_work(inp.doi, get)
        if work is None:
            notes.append(f"OpenAlex: {st}")
            return [], "", notes
        title = work.get("title") or work.get("display_name") or ""
        urls: list[str] = []
        for loc in work.get("locations") or []:
            lp = (loc or {}).get("landing_page_url") or ""
            m = re.search(r"arxiv\.org/abs/([^\s/?#]+)", lp)
            if m:
                urls.append(f"https://arxiv.org/pdf/{_ARXIV_NEW.sub(lambda x: x.group(1), m.group(1))}")
        best = work.get("best_oa_location") or {}
        if best.get("pdf_url"):
            urls.append(best["pdf_url"])
        if best.get("landing_page_url"):
            urls.append(best["landing_page_url"])
        seen, uniq = set(), []
        for u in urls:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        if not uniq:
            notes.append("OpenAlex: açık erişim konumu yok")
        return uniq, title, notes
    return [], "", notes


def download(inp: PaperInput, get: Getter) -> FetchResult:
    if inp.kind == "local":
        with open(inp.path, "rb") as fh:
            body = fh.read()
        if body[:5] != b"%PDF-":
            return FetchResult("NOT_PDF", attempts=[f"{inp.path}: NOT_PDF (yerel dosya PDF değil)"])
        return FetchResult("OK", body, inp.path)
    urls, title, notes = candidate_urls(inp, get)
    attempts = list(notes)
    if not urls:
        st = "NOT_FOUND" if any("NOT_FOUND" in n for n in notes) else (
            "NETWORK_ERROR" if any("NETWORK_ERROR" in n for n in notes) else "NO_OA")
        return FetchResult(st, title=title, attempts=attempts)
    statuses = []
    for u in urls:
        r = get(u)
        st = classify(r)
        if st == "OK":
            return FetchResult("OK", r.body, u, title, attempts)
        statuses.append(st)
        attempts.append(f"{u}: {st} (HTTP {r.status}{', ' + r.error if r.error else ''})")
    return FetchResult(_worst(statuses), title=title, attempts=attempts)
