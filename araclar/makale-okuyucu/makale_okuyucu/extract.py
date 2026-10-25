"""Parça parça Haiku çıkarımı → kod ile alıntı doğrulama + sayfa → id seçen birleştirme → kart."""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor

from makale_okuyucu import quotecheck as qc
from makale_okuyucu.config import FIELD_CAPS, FIELDS, Config
from makale_okuyucu.llm import LLMBackend, call_json
from makale_okuyucu.pdftext import Chunk

log = logging.getLogger("makale_okuyucu.extract")

ABBR = {"problem": "p", "katkilar": "k", "yontem": "y", "veri_setleri_ve_kaynaklar": "v",
        "deney_kurulumu": "d", "ana_sonuclar": "s", "sinirliliklar": "l", "gelecek_calisma": "g",
        "kapsam_disi": "x", "en_yakin_isler": "r"}

FIELD_DESC = {
    "problem": "the research problem / gap the paper addresses",
    "katkilar": "claimed contributions (one per item)",
    "yontem": "key components of the proposed method",
    "veri_setleri_ve_kaynaklar": "datasets, benchmarks, corpora, code or model resources used or released "
                                 "(name; link only if a URL is written in the text)",
    "deney_kurulumu": "experimental setup: models/baselines, hardware, scale (params, data size, compute)",
    "ana_sonuclar": "main results WITH exact numbers",
    "sinirliliklar": "limitations / weaknesses the authors state",
    "gelecek_calisma": "future work the authors state",
    "kapsam_disi": "things the authors EXPLICITLY say they do NOT do, do not address, leave out, "
                   "or assume away (out of scope)",
    "en_yakin_isler": "closest prior works they compare to or build on (name = method or paper/author-year "
                      "as written; relation = how it relates)",
}

EXTRACT_PROMPT = """TASK: extract_chunk
You read ONE part of a research paper (sections: {sections}; pages {pages}). Extract items for a paper card using ONLY this text.

Fields:
{fields}

Rules:
- "quote": copy ONE contiguous sentence or clause VERBATIM from the text (20-300 characters). Do not paraphrase, fix typos, join sentences or add words. Use "..." only to skip words inside the same sentence.
- "text": at most 25 words, English, self-contained; keep numbers exact.
- Omit a field when this part has nothing for it. At most 4 items per field. No duplicates. Do not invent.
- en_yakin_isler items mostly come from related-work / comparison text.

Return ONLY JSON of the form:
{{"problem":[{{"text":"...","quote":"..."}}], "veri_setleri_ve_kaynaklar":[{{"name":"...","link":null,"text":"...","quote":"..."}}], "en_yakin_isler":[{{"name":"...","relation":"...","text":"...","quote":"..."}}], "...other fields...":[...]}}

<text>
{text}
</text>"""

MERGE_PROMPT = """TASK: merge_card
Below are candidate items for a research-paper card, extracted part by part. Each line: [id] (V=quote verified, U=unverified) text.
For each field pick the best items: remove duplicates and near-duplicates (in en_yakin_isler and veri_setleri_ve_kaynaklar keep ONE item per named work/dataset), prefer V over U, prefer specific (numbers, names) over vague, most important first. Respect the max per field. Use only ids listed.

Max per field: {caps}

{items}

Return ONLY JSON: {{"fields": {{"<field>": ["<id>", ...], ...}}}}"""


def _fields_block() -> str:
    return "\n".join(f"- {f}: {FIELD_DESC[f]}" for f in FIELDS)


def _clip(s, n: int) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def verify_item(item: dict, chunk: Chunk) -> dict:
    quote = item.get("quote") or ""
    res = qc.check_quote(quote, chunk.text)
    if res == qc.VERIFIED:
        page = qc.locate_page(quote, chunk.page_texts())
        if page is None:
            pg = chunk.pages
            page = f"{pg[0]}-{pg[-1]}" if pg else None
        item.update(check="VERIFIED", page=page)
    else:
        item.update(check="UNVERIFIED", page=None,
                    neden={qc.UNVERIFIED: "metinde_yok", qc.TOO_SHORT: "cok_kisa", qc.NONE: "alinti_yok"}[res])
    return item


def extract_chunk(llm: LLMBackend, chunk: Chunk) -> dict:
    """{'chunk':idx, 'status':OK|PARSE_FAIL|LLM_ERROR|SCHEMA, 'items':{field:[...]}, 'error':...}"""
    pg = chunk.pages
    prompt = EXTRACT_PROMPT.format(sections=", ".join(dict.fromkeys(chunk.sections)),
                                   pages=f"{pg[0]}-{pg[-1]}" if pg else "?",
                                   fields=_fields_block(), text=chunk.text)
    obj, status, err = call_json(llm, prompt, purpose=f"extract#{chunk.idx}")
    out = {"chunk": chunk.idx, "label": chunk.label(), "status": status, "items": {}, "error": err,
           "dropped_malformed": 0}
    if status != "OK":
        return out
    if not isinstance(obj, dict):
        out.update(status="SCHEMA", error=f"JSON nesne değil: {type(obj).__name__}")
        return out
    unknown = [k for k in obj if k not in FIELDS]
    if unknown:
        out["unknown_fields"] = unknown
    for f in FIELDS:
        vals = obj.get(f) or []
        if isinstance(vals, dict):
            vals = [vals]
        if not isinstance(vals, list):
            out["dropped_malformed"] += 1
            continue
        items = []
        for n, v in enumerate(vals[:6], 1):
            if not isinstance(v, dict) or not (v.get("text") or v.get("name")):
                out["dropped_malformed"] += 1
                continue
            it = {"id": f"c{chunk.idx}{ABBR[f]}{n}", "text": _clip(v.get("text") or v.get("name"), 300),
                  "quote": str(v.get("quote") or "").strip()}
            if f == "veri_setleri_ve_kaynaklar":
                it["name"] = _clip(v.get("name") or "", 120)
                link = v.get("link")
                it["link"] = link if isinstance(link, str) and link.strip().lower().startswith(("http", "www")) else None
            if f == "en_yakin_isler":
                it["name"] = _clip(v.get("name") or "", 150)
                it["relation"] = _clip(v.get("relation") or "", 200)
            items.append(verify_item(it, chunk))
        if len(vals) > 6:
            out["dropped_malformed"] += len(vals) - 6
        if items:
            out["items"][f] = items
    return out


NAMED_FIELDS = ("en_yakin_isler", "veri_setleri_ve_kaynaklar")


def _name_key(name: str) -> str:
    """'Turpin et al. (2023)' ve 'Turpin et al., 2023' aynı anahtar."""
    return " ".join(re.findall(r"[a-z0-9]+", (name or "").lower()))


def _toks(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (s or "").lower()) if len(t) > 2}


def fallback_merge(pool: dict[str, list[dict]]) -> dict[str, list[str]]:
    """Deterministik: doğrulanmışlar önce, Jaccard ≥ 0.6 tekrarı at, üst sınır."""
    out = {}
    for f in FIELDS:
        items = sorted(pool.get(f, []), key=lambda it: it["check"] != "VERIFIED")
        kept: list[dict] = []
        for it in items:
            if f in NAMED_FIELDS and _name_key(it.get("name", "")) and any(
                    _name_key(it.get("name", "")) == _name_key(k.get("name", "")) for k in kept):
                continue
            t = _toks(it.get("name", "") + " " + it["text"])
            if any(len(t & _toks(k.get("name", "") + " " + k["text"])) / max(1, len(t | _toks(k.get("name", "") + " " + k["text"]))) >= 0.6 for k in kept):
                continue
            kept.append(it)
        out[f] = [it["id"] for it in kept[: FIELD_CAPS[f]]]
    return out


def merge(llm: LLMBackend, pool: dict[str, list[dict]]) -> tuple[dict[str, list[str]], dict]:
    """(alan→id listesi, bilgi). Toplam aday sınırın altındaysa LLM çağrılmaz."""
    info = {"merge_status": "SKIPPED_SMALL", "unknown_ids": 0, "over_cap_trimmed": 0}
    total = sum(len(v) for v in pool.values())
    if all(len(pool.get(f, [])) <= FIELD_CAPS[f] for f in FIELDS):
        # tekrar yine de olabilir -> deterministik tekilleştirme yeterli
        return fallback_merge(pool), info
    lines = []
    for f in FIELDS:
        if not pool.get(f):
            continue
        lines.append(f"## {f}")
        for it in pool[f]:
            nm = f"{it['name']}: " if it.get("name") else ""
            lines.append(f"[{it['id']}] ({'V' if it['check'] == 'VERIFIED' else 'U'}) {nm}{_clip(it['text'], 200)}")
    prompt = MERGE_PROMPT.format(caps=json.dumps(FIELD_CAPS), items="\n".join(lines))
    obj, status, err = call_json(llm, prompt, purpose="merge")
    if status != "OK" or not isinstance(obj, dict) or not isinstance(obj.get("fields"), dict):
        info.update(merge_status=f"FALLBACK({status if status != 'OK' else 'SCHEMA'})", error=err)
        return fallback_merge(pool), info
    ids_by_field = {f: {it["id"] for it in pool.get(f, [])} for f in FIELDS}
    name_of = {it["id"]: _name_key(it.get("name", "")) for f in FIELDS for it in pool.get(f, [])}
    info["name_duplicates"] = 0
    out: dict[str, list[str]] = {}
    for f in FIELDS:
        chosen = obj["fields"].get(f) or []
        good = []
        seen_names: set[str] = set()
        for i in chosen if isinstance(chosen, list) else []:
            if i not in ids_by_field[f] or i in good:
                info["unknown_ids"] += 1
                continue
            nk = name_of.get(i, "")
            if f in NAMED_FIELDS and nk and nk in seen_names:
                info["name_duplicates"] += 1
                continue
            seen_names.add(nk)
            good.append(i)
        if len(good) > FIELD_CAPS[f]:
            info["over_cap_trimmed"] += len(good) - FIELD_CAPS[f]
            good = good[: FIELD_CAPS[f]]
        if not good and pool.get(f):
            # LLM alanı boş bıraktı ama aday var -> sessiz kayıp olmasın, yedekten al
            good = fallback_merge({f: pool[f]})[f]
            info.setdefault("fields_from_fallback", []).append(f)
        out[f] = good
    info["merge_status"] = "OK"
    info["candidates"] = total
    return out, info


def build_fields(llm: LLMBackend, cfg: Config, chunks: list[Chunk]) -> tuple[dict, list[dict], dict]:
    """(alanlar, eksik_parcalar, funnel-parçası)."""
    with ThreadPoolExecutor(max_workers=max(1, cfg.llm_workers)) as ex:
        results = list(ex.map(lambda c: extract_chunk(llm, c), chunks))
    pool: dict[str, list[dict]] = {f: [] for f in FIELDS}
    failed = []
    fun = {"chunks_ok": 0, "chunks_failed": 0, "items_raw": 0, "items_raw_verified": 0,
           "items_raw_unverified": 0, "dropped_malformed": 0}
    for r in results:
        fun["dropped_malformed"] += r["dropped_malformed"]
        if r["status"] != "OK":
            fun["chunks_failed"] += 1
            ch = chunks[r["chunk"] - 1]
            failed.append({"parca": r["chunk"], "bolumler": list(dict.fromkeys(ch.sections)),
                           "sayfalar": f"{ch.pages[0]}-{ch.pages[-1]}" if ch.pages else "?",
                           "durum": r["status"], "hata": (r.get("error") or "")[:300]})
            continue
        fun["chunks_ok"] += 1
        for f, items in r["items"].items():
            pool[f].extend(items)
            for it in items:
                fun["items_raw"] += 1
                fun["items_raw_verified" if it["check"] == "VERIFIED" else "items_raw_unverified"] += 1
    chosen, minfo = merge(llm, pool)
    by_id = {it["id"]: it for f in FIELDS for it in pool[f]}
    fields = {f: [by_id[i] for i in chosen.get(f, [])] for f in FIELDS}
    fun.update(minfo)
    fun["items_in_card"] = sum(len(v) for v in fields.values())
    fun["unverified_in_card"] = sum(1 for v in fields.values() for it in v if it["check"] != "VERIFIED")
    fun["dropped_by_merge"] = fun["items_raw"] - fun["items_in_card"]
    return fields, failed, fun
