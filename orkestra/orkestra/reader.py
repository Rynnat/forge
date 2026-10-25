"""Okuyucu çalgıcılar (Haiku): başlık + özetten alaka puanı ve alıntı.

KURAL: ucuz katman yalnız KESİN alakasız olanı atar (rel = 0 VE kesin = true). Şüpheli,
okunamayan, JSON'u bozuk ya da cevapsız kalan aday YUKARI çıkar (rel = None).
Alıntılar kodla (quotecheck) başlık+özete karşı doğrulanır; doğrulanmayan alıntı silinir.
"""
from __future__ import annotations

import concurrent.futures as cf

from orkestra.llm import call_json
from orkestra.quotecheck import VERIFIED, check_quote

READ_PROMPT = """TASK: relevance screening.
Research question: <q>{soru}</q>
Sub-questions:
{alt}

For each item, judge relevance of the work to the research question (any sub-question):
 rel 3 = central, 2 = clearly relevant, 1 = marginal/possibly relevant, 0 = unrelated.
Set "kesin": true ONLY if you are certain it is unrelated (rel 0). If unsure, use rel 1.
"alt": list of matching sub-question ids. "alinti": the single most informative sentence fragment
(15-40 words) copied VERBATIM from the item text, or "" if none. "not": max 12 words.

{items}

Reply ONLY JSON: {{"items": [{{"id": "...", "rel": 0, "kesin": false, "alt": ["S1"], "alinti": "...", "not": "..."}}]}}"""


def item_text(r: dict, words: int) -> str:
    ab = (r.get("abstract") or "").split()
    ab_s = " ".join(ab[:words]) + (" ..." if len(ab) > words else "")
    return f"{r['title']}. {ab_s}".strip()


def screen(llm, cfg, soru: str, subs: list[dict], recs: list[dict], funnel) -> list[dict]:
    """Her kayda rel / kesin / alt / alinti / alinti_durum / not ekler. Dönüş: aynı liste."""
    alt = "\n".join(f"{s['id']}: {s['soru']}" for s in subs)
    batches = [recs[i:i + cfg.reader_batch] for i in range(0, len(recs), cfg.reader_batch)]

    def run(batch: list[dict]):
        items = "\n".join(f'<item id="{j}">{item_text(r, cfg.abstract_words_reader)}</item>'
                          for j, r in enumerate(batch))
        return batch, call_json(llm, READ_PROMPT.format(soru=soru, alt=alt, items=items),
                                model=cfg.isci_model, stage="okuyucu")

    with cf.ThreadPoolExecutor(max_workers=max(1, cfg.reader_parallel)) as ex:
        for batch, (obj, st) in ex.map(run, batches):
            got = {}
            if st == "OK" and isinstance(obj, dict):
                for it in obj.get("items") or []:
                    if isinstance(it, dict) and str(it.get("id", "")).strip().isdigit():
                        got[int(str(it["id"]).strip())] = it
            else:
                funnel.error(f"okuyucu:{st}", len(batch))
            for j, r in enumerate(batch):
                it = got.get(j)
                if it is None:
                    r.update(rel=None, kesin=False, alt=[], alinti="", alinti_durum="YOK", not_="okunamadı")
                    funnel.bump("okuyucu.cevapsiz(yukari_cikti)")
                    continue
                try:
                    rel = int(it.get("rel"))
                except (TypeError, ValueError):
                    rel = None
                q = str(it.get("alinti") or "").strip()
                src = f"{r['title']}. {r.get('abstract') or ''}"
                durum = check_quote(q, src) if q else "YOK"
                if durum != VERIFIED:
                    if q:
                        funnel.bump(f"okuyucu.alinti_{durum}")
                    q = ""
                kaynak = ("ozet" if check_quote(q, r.get("abstract") or "") == VERIFIED else "baslik") if q else ""
                r.update(rel=rel, kesin=bool(it.get("kesin")) and rel == 0, alt=[str(a) for a in it.get("alt") or []],
                         alinti=q, alinti_durum=VERIFIED if q else durum, alinti_kaynagi=kaynak,
                         not_=str(it.get("not") or "")[:120])
    return recs


def drop_certain(recs: list[dict]) -> tuple[list[dict], int]:
    keep = [r for r in recs if not (r.get("rel") == 0 and r.get("kesin"))]
    return keep, len(recs) - len(keep)
