"""Haiku web işçileri (yalnız WebSearch/WebFetch açık) + başlık çözümleme.

İşçiler blog / survey / awesome-list sayfalarından makale ADI toplar. Hiçbir başlık
doğrudan güvenilmez: arXiv / Crossref'te başlık benzerliği ≥ 0.90 (ya da verilen
id'nin başlığı ≥ 0.75) ile gerçek bir kayda çözülemeyen ad düşer (`cozulemedi`).
Şefin "çapa çalışmaları" da aynı çözümleyiciden geçer (uydurma çalışma girmez).
"""
from __future__ import annotations

import concurrent.futures as cf
import re

from orkestra.http import BotBlocked, QuotaExhausted, RequestFailed
from orkestra.llm import call_json
from orkestra.normalize import norm_arxiv, norm_doi, norm_title
from orkestra.records import title_sim
from orkestra.sources import arxiv, crossref

WEB_SYSTEM = ("You are a literature scout. You may use WebSearch and WebFetch. You collect paper "
              "titles that literally appear on the pages you read. Final answer: ONLY JSON.")

WEB_PROMPT = """Research question: {soru}
Your focus: {odak}
Cutoff: only papers published before {kesim} matter (older classics are welcome).

Find pages that list important papers on this topic: GitHub "awesome" lists, reading lists,
survey/tutorial pages, well-known blog posts. Use at most {ns} WebSearch calls and at most {nf}
WebFetch calls. From the pages you actually read, collect up to 60 paper titles relevant to the
question (seminal works, main methods, benchmarks). Copy titles as written; add arXiv id / DOI
only if shown on the page.

Reply ONLY with JSON: {{"makaleler": [{{"baslik": "...", "yil": 2020, "arxiv": "", "doi": "", "kaynak_url": "..."}}]}}"""


def run_workers(llm, cfg, soru: str, kesim: str, plan: dict, funnel) -> list[dict]:
    subs = plan.get("alt_sorular") or []
    foci = list(plan.get("web_odaklari") or [])
    n = max(0, cfg.web_workers)
    if n == 0:
        return []
    groups = [[] for _ in range(n)]
    for i, s in enumerate(subs):
        groups[i % n].append(s["soru"])
    tasks = []
    for i in range(n):
        odak = "; ".join(([foci[i]] if i < len(foci) else []) + groups[i][:3]) or soru
        tasks.append(WEB_PROMPT.format(soru=soru, odak=odak, kesim=kesim, ns=4, nf=4))
    found: list[dict] = []

    def one(p: str):
        return call_json(llm, p, model=cfg.isci_model, stage="web_isci", system=WEB_SYSTEM,
                         tools="WebSearch,WebFetch", budget=cfg.web_max_budget_usd)

    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        for obj, st in ex.map(one, tasks):
            if st != "OK" or not isinstance(obj, dict):
                funnel.error(f"web_isci:{st}")
                continue
            for m in obj.get("makaleler") or []:
                if isinstance(m, dict) and str(m.get("baslik") or "").strip():
                    found.append({"baslik": str(m["baslik"]).strip(), "yil": m.get("yil"),
                                  "arxiv": m.get("arxiv") or "", "doi": m.get("doi") or "", "koken": "web"})
    funnel.source("web", "OK" if found or not tasks else "EKSİK",
                  "" if found else "işçiler başlık döndürmedi", kayit=len(found))
    return found


def _best(title: str, cands: list[dict]) -> tuple[dict | None, float]:
    nt = norm_title(title)
    best, bs = None, 0.0
    for c in cands:
        s = title_sim(nt, norm_title(c.get("title")))
        if s > bs:
            best, bs = c, s
    return best, bs


def resolve(http, cfg, items: list[dict], funnel, label: str) -> tuple[list[dict], dict[str, int]]:
    """items: [{baslik, yil, arxiv, doi, koken}] → (kayıtlar, düşen sayaçları)."""
    out: list[dict] = []
    drop = {"cozulemedi": 0, "kaynak_hatasi": 0}
    seen: set[str] = set()
    uniq = []
    for it in items:
        k = norm_title(it["baslik"])
        if k and k not in seen:
            seen.add(k)
            uniq.append(it)
    drop["tekrar_baslik"] = len(items) - len(uniq)
    pending = []

    def tag(rec: dict, it: dict) -> dict:
        rec = dict(rec)
        if it.get("koken") == "sef":
            rec["anchor"] = True
        else:
            rec["web"] = True
        rec["sources"] = sorted(set(rec.get("sources") or []) | {it.get("koken") or "web"})
        return rec

    # 1) verilen arXiv id'leri
    with_id = [(it, norm_arxiv(str(it.get("arxiv")))) for it in uniq if it.get("arxiv")]
    id_recs = {}
    try:
        ids = [a for _, a in with_id if a and re.match(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[a-z]{2})?/\d{7})$", a)]
        for r in arxiv.by_ids(http, ids) if ids else []:
            id_recs[r["arxiv_id"]] = r
    except (QuotaExhausted, RequestFailed, BotBlocked, ValueError):
        funnel.error(f"{label}:arxiv_id")
    for it in uniq:
        a = norm_arxiv(str(it.get("arxiv"))) if it.get("arxiv") else None
        r = id_recs.get(a) if a else None
        if r and title_sim(norm_title(it["baslik"]), norm_title(r["title"])) >= 0.75:
            out.append(tag(r, it))
        else:
            pending.append(it)
    # 2) arXiv başlık araması
    still = []
    try:
        cands = arxiv.by_titles(http, [it["baslik"] for it in pending]) if pending else []
    except (QuotaExhausted, RequestFailed, BotBlocked, ValueError):
        funnel.error(f"{label}:arxiv_title")
        cands = []
    for it in pending:
        r, s = _best(it["baslik"], cands)
        if r and s >= 0.90:
            out.append(tag(r, it))
        else:
            still.append(it)
    # 3) Crossref (DOI varsa önce DOI, sonra başlık)
    for it in still:
        try:
            r = None
            d = norm_doi(it.get("doi"))
            if d:
                try:
                    r = crossref.by_doi(http, d, cfg)
                except RequestFailed:
                    r = None
                if r and title_sim(norm_title(it["baslik"]), norm_title(r["title"])) < 0.75:
                    r = None
            if r is None:
                r, s = _best(it["baslik"], crossref.by_title(http, it["baslik"], cfg))
                if s < 0.90:
                    r = None
        except (QuotaExhausted, RequestFailed, BotBlocked, ValueError, KeyError):
            drop["kaynak_hatasi"] += 1
            continue
        if r:
            out.append(tag(r, it))
        else:
            drop["cozulemedi"] += 1
    funnel.stage(f"cozumleme:{label}", len(items), len(out), drop)
    return out, drop
