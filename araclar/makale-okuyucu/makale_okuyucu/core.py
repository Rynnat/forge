"""read / ask akışları."""
from __future__ import annotations

import hashlib
import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field

from makale_okuyucu import quotecheck as qc
from makale_okuyucu.config import FIELDS, VERSION, Config
from makale_okuyucu.extract import build_fields
from makale_okuyucu.fetch import MIN_CHARS, PaperInput, download, requests_getter, resolve_input
from makale_okuyucu.llm import LLMBackend, call_json, make_backend
from makale_okuyucu.pdftext import (Passage, Section, make_chunks, make_passages, pdf_pages, pdf_styled_lines,
                                    pdf_title, split_sections)
from makale_okuyucu.render import est_tokens, render
from makale_okuyucu.store import Store

log = logging.getLogger("makale_okuyucu.core")

LOCAL_PDF_HINT = ("Bu makale otomatik indirilemedi. Atlatma denenmedi. Yerel PDF ver:\n"
                  "  python -m makale_okuyucu read <dosya.pdf> --as {key}")


@dataclass
class ReadResult:
    status: str
    key: str
    card: dict | None = None
    markdown: str | None = None
    from_cache: bool = False
    attempts: list[str] = field(default_factory=list)
    message: str = ""
    run_id: int | None = None


class Reader:
    def __init__(self, cfg: Config, store: Store | None = None, llm: LLMBackend | None = None, getter=None):
        self.cfg = cfg
        self.store = store or Store(cfg.data_dir)
        self.llm = llm or make_backend(cfg, recorder=self.store.record_llm)
        if self.llm.recorder is None:
            self.llm.recorder = self.store.record_llm
        self.get = getter or requests_getter(cfg.user_agent, cfg.http_timeout_s)

    # ------------------------------------------------------------------ read
    def _target_key(self, inp: PaperInput, as_key: str | None) -> str:
        if as_key:
            return resolve_input(as_key).key
        return inp.key

    def _cached(self, keys: list[str]) -> str | None:
        for k in keys:
            hit = self.store.resolve(k)
            if hit:
                return hit
        return None

    def _llm_cols(self) -> dict:
        s = self.llm.stats
        return dict(llm_calls=s.calls, llm_failed=s.failed, input_tokens=s.input_tokens,
                    output_tokens=s.output_tokens, cache_read_tokens=s.cache_read_tokens,
                    cache_write_tokens=s.cache_write_tokens, cost_usd=round(s.cost_usd, 6),
                    llm_duration_s=round(s.duration_s, 2))

    def read(self, raw: str, as_key: str | None = None, force: bool = False) -> ReadResult:
        t0 = time.monotonic()
        inp = resolve_input(raw)
        key = self._target_key(inp, as_key)
        if not force:
            hit = self._cached([key, inp.key])
            if hit:
                for k in (key, inp.key):
                    self.store.add_alias(k, hit)
                rid = self.store.start_run("read", hit)
                card = self.store.load_card(hit)
                self.store.finish_run(rid, status="CACHED", from_cache=1, pages=card.get("pages"),
                                      duration_s=round(time.monotonic() - t0, 3))
                return ReadResult("OK", hit, card, self._md(hit, card), True, run_id=rid)

        rid = self.store.start_run("read", key)
        fr = download(inp, self.get)
        if fr.status != "OK":
            msg = LOCAL_PDF_HINT.format(key=key) if inp.kind != "local" else "Yerel dosya PDF değil."
            self.store.finish_run(rid, status=fr.status, from_cache=0, detail="\n".join(fr.attempts)[:4000],
                                  duration_s=round(time.monotonic() - t0, 3))
            return ReadResult(fr.status, key, attempts=fr.attempts, message=msg, run_id=rid)
        body = fr.body
        sha = hashlib.sha256(body).hexdigest()
        if not force:
            hit = self.store.by_sha(sha)
            if hit:
                for k in (key, inp.key):
                    self.store.add_alias(k, hit)
                card = self.store.load_card(hit)
                self.store.finish_run(rid, status="CACHED_SHA", from_cache=1, pages=card.get("pages"),
                                      duration_s=round(time.monotonic() - t0, 3))
                return ReadResult("OK", hit, card, self._md(hit, card), True, run_id=rid)
        try:
            pages = pdf_pages(body)
            meta_title = pdf_title(body)
        except Exception as exc:  # pymupdf çeşitli türler fırlatır; durum olarak raporlanır
            self.store.finish_run(rid, status="PARSE_ERROR", detail=f"{type(exc).__name__}: {exc}"[:2000],
                                  duration_s=round(time.monotonic() - t0, 3))
            return ReadResult("PARSE_ERROR", key, message=f"PDF ayrıştırılamadı: {exc}", run_id=rid)
        chars = sum(len(t) for _, t in pages)
        if sum(len(t.strip()) for _, t in pages) < MIN_CHARS:
            self.store.finish_run(rid, status="EMPTY_TEXT", pages=len(pages),
                                  detail=f"{chars} karakter; taranmış PDF olası (OCR yok)",
                                  duration_s=round(time.monotonic() - t0, 3))
            return ReadResult("EMPTY_TEXT", key, message="Metin çıkmadı (taranmış PDF? OCR yok).", run_id=rid)

        d = self.store.paper_dir(key)
        (d / "paper.pdf").write_bytes(body)
        try:
            styled = pdf_styled_lines(body)
        except Exception as exc:  # biçim bilgisi isteğe bağlı; yoksa yalnız metin sezgisi
            log.warning("biçim bilgisi okunamadı: %s", exc)
            styled = None
        sections = split_sections(pages, styled)
        chunks, skipped = make_chunks(sections, self.cfg.chunk_chars)
        self.store.write_json(key, "doc.json", {"pages": [list(p) for p in pages],
                                                "sections": [s.to_dict() for s in sections]})
        title = fr.title or meta_title or _first_line(pages)
        self.llm.reset_stats()
        fields, failed, fun = build_fields(self.llm, self.cfg, chunks)

        funnel = {
            "pages": len(pages), "chars": chars,
            "sections": [f"{s.name}:{s.title[:40]}@p{s.pages[0]}" for s in sections if s.pages],
            "sections_found": sorted({s.name for s in sections}),
            "chunks": len(chunks), "chunk_chars": self.cfg.chunk_chars,
            "skipped_references": {"sections": len(skipped), "chars": sum(len(s.text) for s in skipped),
                                   "pages": sorted({p for s in skipped for p in s.pages})},
            **fun,
        }
        status = "PARTIAL" if failed else ("EMPTY" if fun["items_in_card"] == 0 else "OK")
        card = {"key": key, "aliases": [], "title": title, "source_url": fr.source_url, "pages": len(pages),
                "status": status, "fields": fields, "eksik_parcalar": failed, "funnel": funnel,
                "version": VERSION}
        funnel["llm"] = self.llm.stats.as_dict()
        funnel["duration_s"] = round(time.monotonic() - t0, 2)
        md = render(card, self.cfg.md_max_tokens)
        funnel["md_tokens_est"] = est_tokens(md)
        funnel["md_chars"] = len(md)
        self.store.save_card(card, sha, chars, VERSION)
        self.store.add_alias(inp.key, key)
        card["aliases"] = self.store.aliases(key)
        self.store.write_json(key, "card.json", card)
        (d / "card.md").write_text(md, encoding="utf-8")
        self.store.finish_run(
            rid, status=status, from_cache=0, pages=len(pages), chunks=len(chunks),
            duration_s=round(time.monotonic() - t0, 2), unverified=fun["unverified_in_card"],
            failed_chunks=", ".join(f"#{e['parca']}:{e['durum']}" for e in failed) or None,
            detail=f"items_raw={fun['items_raw']} raw_unverified={fun['items_raw_unverified']} "
                   f"merge={fun.get('merge_status')}", **self._llm_cols())
        return ReadResult(status, key, card, md, False, fr.attempts, run_id=rid)

    def _md(self, key: str, card: dict) -> str:
        p = self.store.paper_dir(key) / "card.md"
        return p.read_text(encoding="utf-8") if p.exists() else render(card, self.cfg.md_max_tokens)

    # ------------------------------------------------------------------ ask
    def ask(self, raw: str, question: str, refresh: bool = False) -> dict:
        t0 = time.monotonic()
        rr = self.read(raw)
        if rr.status not in ("OK", "PARTIAL", "EMPTY"):
            return {"kaynak": "aranamadi", "durum": rr.status, "mesaj": rr.message, "key": rr.key}
        key, card = rr.key, rr.card
        q = question.strip()
        if not refresh:
            hit = self.store.get_ask(key, q)
            if hit:
                hit["onbellek"] = True
                return hit
        rid = self.store.start_run("ask", key)
        self.llm.reset_stats()
        out = self._ask_card(card, q)
        if out is None or out.get("kaynak") != "kart":
            terms = (out or {}).get("_terms") or []
            out = self._ask_sections(key, q, terms, card_note=(out or {}).get("_note"))
        out.pop("_terms", None)
        out.pop("_note", None)
        out.update(key=key, soru=q, llm=self.llm.stats.as_dict(), sure_s=round(time.monotonic() - t0, 2))
        self.store.put_ask(key, q, out)
        self.store.finish_run(rid, status=out["kaynak"], from_cache=0,
                              duration_s=out["sure_s"], **self._llm_cols())
        return out

    def _ask_card(self, card: dict, q: str) -> dict | None:
        by_id = {}
        lines = []
        for f in FIELDS:
            for it in card["fields"].get(f, []):
                by_id[it["id"]] = it
                nm = f"{it['name']}: " if it.get("name") else ""
                lines.append(f"[{it['id']}] {f}: {nm}{it['text']}")
        prompt = ASK_CARD_PROMPT.format(title=card.get("title") or card["key"], items="\n".join(lines), q=q)
        obj, status, err = call_json(self.llm, prompt, purpose="ask_card")
        if status != "OK" or not isinstance(obj, dict):
            return {"kaynak": None, "_note": f"kart adımı {status}", "_terms": []}
        terms = [t for t in (obj.get("search_terms") or []) if isinstance(t, str)][:12]
        ids = [i for i in (obj.get("item_ids") or []) if i in by_id]
        if obj.get("answerable") and ids and obj.get("answer"):
            cites = [{"id": i, "text": by_id[i]["text"], "quote": by_id[i].get("quote"),
                      "page": by_id[i].get("page"), "check": by_id[i]["check"]} for i in ids]
            return {"kaynak": "kart", "cevap": str(obj["answer"]), "alintilar": cites,
                    "dogrulanmis": any(c["check"] == "VERIFIED" for c in cites)}
        return {"kaynak": None, "_terms": terms}

    def _ask_sections(self, key: str, q: str, terms: list[str], card_note: str | None = None) -> dict:
        doc = self.store.read_json(key, "doc.json")
        if not doc:
            return {"kaynak": "bulunamadi", "cevap": None, "alintilar": [], "not": "doc.json yok"}
        sections = [Section.from_dict(s) for s in doc["sections"]]
        passages = make_passages(sections, self.cfg.passage_chars)
        query = q + " " + " ".join(terms)
        top = bm25_top(passages, query, self.cfg.ask_top_k)
        if not top:
            return {"kaynak": "bulunamadi", "cevap": None, "alintilar": [], "not": "BM25 eşleşme yok"}
        blocks = "\n\n".join(f'<passage id="P{p.idx}" section="{p.section}">\n{p.text}\n</passage>' for p in top)
        prompt = ASK_SECTIONS_PROMPT.format(passages=blocks, q=q)
        obj, status, err = call_json(self.llm, prompt, purpose="ask_sections")
        info = {"pasajlar": [f"P{p.idx}:{p.section}" for p in top], "gonderilen_karakter": sum(len(p.text) for p in top)}
        if card_note:
            info["not"] = card_note
        if status != "OK" or not isinstance(obj, dict):
            return {"kaynak": "aranamadi", "durum": status, "cevap": None, "alintilar": [], **info}
        if not obj.get("found"):
            return {"kaynak": "bulunamadi", "cevap": None, "alintilar": [], **info}
        pmap = {f"P{p.idx}": p for p in top}
        cites = []
        for qd in (obj.get("quotes") or [])[:5]:
            if not isinstance(qd, dict):
                continue
            quote = str(qd.get("quote") or "")
            p = pmap.get(str(qd.get("passage")))
            cands = [p] if p else top
            check, page = "UNVERIFIED", None
            for c in cands:
                if qc.check_quote(quote, c.text) == qc.VERIFIED:
                    check = "VERIFIED"
                    page = qc.locate_page(quote, c.page_texts())
                    break
            cites.append({"quote": quote, "page": page, "check": check})
        ok = any(c["check"] == "VERIFIED" for c in cites)
        return {"kaynak": "bolum", "cevap": str(obj.get("answer") or ""), "alintilar": cites,
                "dogrulanmis": ok, **info}


ASK_CARD_PROMPT = """TASK: ask_card
Paper: {title}
Card items (id, field, text):
{items}

Question: {q}

Answer ONLY if the card items clearly answer the question. Otherwise answerable=false and give 3-8 English search_terms (keywords likely to appear in the paper's text) to find the answer in the full text.
Return ONLY JSON: {{"answerable": true|false, "answer": "<short answer, same language as the question>", "item_ids": ["..."], "search_terms": ["..."]}}"""

ASK_SECTIONS_PROMPT = """TASK: ask_sections
Passages from a research paper:
{passages}

Question: {q}

Answer using ONLY these passages. If they do not contain the answer, found=false.
Quotes must be copied VERBATIM (20-300 characters, one contiguous sentence or clause) from a passage; give the passage id.
Return ONLY JSON: {{"found": true|false, "answer": "<short answer, same language as the question>", "quotes": [{{"passage": "P<n>", "quote": "..."}}]}}"""


def _first_line(pages) -> str:
    for _, t in pages[:1]:
        for ln in t.splitlines():
            if len(ln.strip()) > 10:
                return ln.strip()[:200]
    return ""


_STOP = set("the a an of and or to in on for with by is are was were be been this that these those it its "
            "as at from what which how does do did why who whom when where can could would should paper "
            "they their there than then into about over under".split())


def _bm_tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 1 and t not in _STOP]


def bm25_top(passages: list[Passage], query: str, k: int, k1: float = 1.5, b: float = 0.75) -> list[Passage]:
    docs = [_bm_tokens(p.text + " " + p.title) for p in passages]
    if not docs:
        return []
    n = len(docs)
    avg = sum(len(d) for d in docs) / n or 1.0
    df = Counter(t for d in docs for t in set(d))
    qt = set(_bm_tokens(query))
    scores = []
    for p, d in zip(passages, docs):
        tf = Counter(d)
        s = 0.0
        for t in qt:
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avg))
        scores.append((s, p))
    ranked = [p for s, p in sorted(scores, key=lambda x: -x[0]) if s > 0]
    return ranked[:k]
