"""Orkestra hattı: şef plan → toplayıcılar (paralel) → tekilleştir + kesim → atıf takibi →
okuyucular → damıtıcı → şef final → rapor. Her aşama funnel'a girdi/çıktı/düşen yazar."""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import time
from pathlib import Path
from typing import Callable

from orkestra import chef, rank, reader, web
from orkestra.config import Config
from orkestra.funnel import EKSIK, KAPALI, OK, Funnel
from orkestra.http import BotBlocked, Http, QuotaExhausted, RequestFailed
from orkestra.llm import LLM, Ledger
from orkestra.records import cutoff_filter, dedup, earliest, fmt_date, public_id
from orkestra.report import write_outputs
from orkestra.sources import arxiv, crossref, dblp, openalex, opencitations, s2

FATAL = (QuotaExhausted, BotBlocked)


class Ctx:
    def __init__(self, cfg: Config, soru: str, kesim: str, out_dir: Path, llm=None, http=None,
                 searchers: dict[str, Callable] | None = None, resolver: Callable | None = None,
                 enricher: Callable | None = None, snowballer: Callable | None = None,
                 web_runner: Callable | None = None):
        self.cfg = cfg
        self.soru = soru
        self.kesim = kesim
        self.cut = dt.date.fromisoformat(kesim)
        self.out = Path(out_dir)
        self.run_id = time.strftime("%Y%m%d-%H%M%S-") + hashlib.sha1(f"{soru}{kesim}{time.time()}".encode()).hexdigest()[:6]
        self.ledger = getattr(llm, "ledger", None) or Ledger(cfg.cost_log, self.run_id)
        self.ledger.run_id = self.run_id
        self.llm = llm or LLM(cfg, self.ledger)
        self.http = http or Http(cfg)
        self.funnel = Funnel()
        self.times: dict[str, float] = {}
        self.budget = openalex.Budget(cfg)
        self.searchers = searchers if searchers is not None else default_searchers(self)
        self.resolver = resolver or (lambda items, label: web.resolve(self.http, cfg, items, self.funnel, label))
        self.enricher = enricher or (lambda keys: s2.batch(self.http, keys))
        self.oc = snowballer or OCClient(self.http)
        self.web_runner = web_runner or (lambda plan: web.run_workers(self.llm, cfg, soru, kesim, plan, self.funnel))


class OCClient:
    """OpenCitations erişimi (testlerde sahte nesneyle değiştirilir)."""

    def __init__(self, http):
        self.http = http

    def references(self, doi: str) -> list[str]:
        return opencitations.references(self.http, doi)

    def citations(self, doi: str) -> list[tuple[str, str]]:
        return opencitations.citations(self.http, doi)

    def metadata(self, dois: list[str]) -> dict[str, dict]:
        return opencitations.metadata(self.http, dois)


def default_searchers(ctx: Ctx) -> dict[str, Callable]:
    cfg, http = ctx.cfg, ctx.http
    return {
        "arxiv": lambda q: arxiv.search(http, q, ctx.cut, cfg, ctx.funnel),
        "crossref": lambda q: crossref.search(http, q, ctx.cut, cfg),
        "dblp": lambda q: dblp.search(http, q, ctx.cut, cfg),
        "openalex": lambda q: openalex.search(http, q, ctx.cut, cfg, ctx.budget),
    }


def _queries_for(name: str, cfg: Config, subs: list[dict]) -> list[tuple[str, str]]:
    out = []
    for s in subs:
        qs = s.get("sorgular") or [s["soru"]]
        if name == "dblp":
            qs = qs[: cfg.dblp_queries_per_subq]
        elif name == "openalex" and not cfg.openalex_api_key:
            qs = qs[:2]
        out.extend((s["id"], q) for q in qs)
    return out


def harvest_source(ctx: Ctx, name: str, subs: list[dict]) -> list[dict]:
    fn = ctx.searchers[name]
    qs = _queries_for(name, ctx.cfg, subs)
    raw: list[dict] = []
    done = 0
    t0 = time.monotonic()
    for sid, q in qs:
        try:
            got = fn(q)
        except FATAL as exc:
            ctx.funnel.source(name, EKSIK, f"{type(exc).__name__}: {exc.detail}"[:200])
            ctx.funnel.bump(f"{name}.atlanan_sorgu(kota)", len(qs) - done)
            break
        except openalex.BudgetExhausted as exc:
            ctx.funnel.source(name, EKSIK, f"bütçe: {exc}")
            ctx.funnel.bump(f"{name}.atlanan_sorgu(butce)", len(qs) - done)
            break
        except (RequestFailed, ValueError, KeyError) as exc:
            ctx.funnel.error(f"{name}:{type(exc).__name__}")
            ctx.funnel.bump(f"{name}.basarisiz_sorgu")
            got = []
        done += 1
        for r in got:
            if "_drop" not in r:
                r["hits"] = sorted(set(r.get("hits") or []) | {sid})
        raw.extend(got)
    kept = [r for r in raw if "_drop" not in r]
    drops: dict[str, int] = {}
    for r in raw:
        if "_drop" in r:
            drops[r["_drop"]] = drops.get(r["_drop"], 0) + 1
    ctx.funnel.source(name, OK, istek=done, kayit=len(kept), sorgu=len(qs))
    if done < len(qs) and ctx.funnel.sources[name]["durum"] != EKSIK:
        ctx.funnel.source(name, EKSIK, "sorguların bir kısmı koşulamadı")
    if ctx.funnel.errors.get(f"{name}:RequestFailed", 0) >= max(1, len(qs)) and not kept:
        ctx.funnel.source(name, EKSIK, "tüm sorgular başarısız")
    ctx.funnel.stage(f"toplama:{name}", len(raw), len(kept), drops)
    ctx.times[f"toplama:{name}"] = round(time.monotonic() - t0, 1)
    return kept


def enrich(ctx: Ctx, recs: list[dict]) -> None:
    """S2 toplu sorgusuyla eksik özet / tarih / atıf sayısını tamamlar (kayıt sayısını değiştirmez)."""
    need = [r for r in recs if s2.s2_key(r) and (not r.get("abstract") or r.get("citations") is None
                                                  or all(len(d) < 3 for d in r.get("dates") or []))]
    if not need or "atif" not in ctx.cfg.sources:
        return
    keys = [s2.s2_key(r) for r in need]
    try:
        got = ctx.enricher(keys)
    except FATAL as exc:
        ctx.funnel.source("s2_zenginlestirme", EKSIK, str(exc)[:200])
        return
    except (RequestFailed, ValueError, KeyError) as exc:
        ctx.funnel.source("s2_zenginlestirme", EKSIK, f"{type(exc).__name__}: {exc}"[:200])
        return
    n = 0
    for r, e in zip(need, got):
        if not e or "_drop" in e:
            continue
        n += 1
        if not r.get("abstract") and e.get("abstract"):
            r["abstract"] = e["abstract"]
        if r.get("citations") is None and e.get("citations") is not None:
            r["citations"] = e["citations"]
        r["dates"] = r.get("dates", []) + [d for d in e.get("dates") or [] if d not in r.get("dates", [])]
        r["s2_id"] = r.get("s2_id") or e.get("s2_id")
    ctx.funnel.source("s2_zenginlestirme", OK, istek=1, kayit=n, istenen=len(need))


def snowball(ctx: Ctx, pool: list[dict]) -> list[dict]:
    """Atıf takibi (OpenCitations): en yakın tohumların kaynakçası + onları atıf yapanlar.
    Birden çok tohuma bağlı çalışma önce gelir (ortak atıf sinyali). Atıf yapanlar
    `creation` tarihiyle kesimden önce süzülür; kalan her aday ayrıca kesim filtresinden geçer."""
    cfg, f = ctx.cfg, ctx.funnel
    rank.score(pool, ctx.soru, ctx.plan["alt_sorular"], cfg, ctx.embedder, f)
    order = sorted(pool, key=lambda r: -r["skor"])
    seeds = [r for r in order if opencitations.seed_dois(r)][: cfg.snowball_seeds]
    seeds += [r for r in order if r.get("anchor") and opencitations.seed_dois(r) and r not in seeds][:4]
    ctx.seeds = [public_id(s) for s in seeds]
    refs: dict[str, set] = {}
    cites: dict[str, set] = {}
    late: set[str] = set()
    calls = 0
    for sd in seeds:
        sid = public_id(sd)
        try:
            for d in opencitations.seed_dois(sd):
                if not d.startswith("10.48550/"):  # arXiv DataCite DOI'lerinin kaynakçası yok
                    calls += 1
                    for x in ctx.oc.references(d):
                        refs.setdefault(x, set()).add(sid)
                calls += 1
                for x, created in ctx.oc.citations(d):
                    if opencitations.created_before(created, ctx.cut) is False:
                        late.add(x)
                        continue
                    cites.setdefault(x, set()).add(sid)
        except FATAL as exc:
            f.source("atif", EKSIK, f"{type(exc).__name__}: {exc.detail}"[:200])
            break
        except (RequestFailed, ValueError, KeyError) as exc:
            f.error(f"atif:{type(exc).__name__}")
    late -= set(refs) | set(cites)
    ref_sel = sorted(refs, key=lambda d: -len(refs[d]))[: cfg.snowball_refs_max]
    cite_pool = [d for d in cites if d not in refs]
    cite_sel = sorted(cite_pool, key=lambda d: -len(cites[d]))[: cfg.snowball_cites_max]
    linked = set(refs) | set(cites) | late
    chosen = ref_sel + cite_sel
    try:
        meta = ctx.oc.metadata(chosen) if chosen else {}
    except FATAL + (RequestFailed, ValueError, KeyError) as exc:
        f.source("atif", EKSIK, f"meta: {type(exc).__name__}"[:200])
        meta = {}
    out, no_meta = [], 0
    for d in chosen:
        r = opencitations.to_record(d, meta.get(d))
        if r is None:
            no_meta += 1
            continue
        r["seed_of"] = sorted(refs.get(d, set()) | cites.get(d, set()))
        r["sources"] = ["atif"]
        out.append(r)
    f.source("atif", OK, istek=calls, kayit=len(out), tohum=len(seeds))
    f.stage("toplama:atif", len(linked), len(out),
            {"atif_yapan_kesim_sonrasi": len(late), "tavan_kesimi": len(linked) - len(late) - len(chosen),
             "meta_yok": no_meta},
            not_=f"{len(seeds)} tohum; OpenCitations referans + atıf yapan")
    return out


def run(soru: str, kesim: str, out_dir: str | Path, cfg: Config | None = None, **inject) -> dict:
    cfg = cfg or Config()
    ctx = Ctx(cfg, soru, kesim, Path(out_dir), **inject)
    ctx.embedder = rank.Embedder(cfg)
    ctx.seeds = []
    T0 = time.monotonic()
    f = ctx.funnel

    # 1. şef plan
    t = time.monotonic()
    plan, st = chef.plan(ctx.llm, cfg, soru, kesim)
    if plan is None or not plan["alt_sorular"]:
        f.source("sef_plan", EKSIK, f"plan alınamadı ({st}); soru metniyle devam")
        plan = chef.fallback_plan(soru)
    else:
        f.source("sef_plan", OK, kayit=len(plan["alt_sorular"]))
    ctx.plan = plan
    subs = plan["alt_sorular"]
    ctx.times["sef_plan"] = round(time.monotonic() - t, 1)

    # 2. toplayıcılar (paralel)
    t = time.monotonic()
    for name in ("arxiv", "crossref", "dblp", "openalex", "web", "atif"):
        if name not in cfg.sources:
            f.source(name, KAPALI, "yapılandırmada kapalı")
    jobs = {}
    pool: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for name in ("arxiv", "crossref", "dblp", "openalex"):
            if name in cfg.sources and name in ctx.searchers:
                jobs[ex.submit(harvest_source, ctx, name, subs)] = name
        anchors = [{"baslik": a["baslik"], "yil": a.get("yil"), "koken": "sef"} for a in plan["capa_calismalar"]]
        if anchors:
            jobs[ex.submit(ctx.resolver, anchors, "sef_capa")] = "sef_capa"
        if "web" in cfg.sources:
            def _web():
                t1 = time.monotonic()
                items = ctx.web_runner(plan)
                ctx.times["web_isci"] = round(time.monotonic() - t1, 1)
                return ctx.resolver(items, "web") if items else ([], {})
            jobs[ex.submit(_web)] = "web"
        for fut in cf.as_completed(jobs):
            name = jobs[fut]
            try:
                res = fut.result()
            except Exception as exc:  # beklenmeyen hata: kaynak EKSİK, koşu sürer
                f.source(name, EKSIK, f"beklenmeyen hata: {type(exc).__name__}: {exc}"[:200])
                continue
            recs = res[0] if isinstance(res, tuple) else res
            pool.extend(recs)
    ctx.times["toplama"] = round(time.monotonic() - t, 1)

    # 3. tekilleştir + zenginleştir + kesim
    t = time.monotonic()
    merged, n_merged = dedup(pool)
    f.stage("tekillestirme_1", len(pool), len(merged), {"birlesti": n_merged})
    enrich(ctx, merged)
    kept, drops = cutoff_filter(merged, ctx.cut)
    f.stage("kesim_1", len(merged), len(kept), drops)
    ctx.times["tekil+kesim_1"] = round(time.monotonic() - t, 1)

    # 4. atıf takibi
    t = time.monotonic()
    if "atif" in cfg.sources and kept:
        new = snowball(ctx, kept)
        pool2 = kept + new
        merged2, n2 = dedup(pool2)
        f.stage("tekillestirme_2", len(pool2), len(merged2), {"birlesti": n2})
        kept, drops2 = cutoff_filter(merged2, ctx.cut)
        f.stage("kesim_2", len(merged2), len(kept), drops2)
    ctx.times["atif"] = round(time.monotonic() - t, 1)

    # 5. okuyucu kesimi (ön sıralama) + okuyucu
    t = time.monotonic()
    rank.score(kept, soru, subs, cfg, ctx.embedder, f)
    order = sorted(kept, key=lambda r: -r["skor"])
    to_read, cut_off = order[: cfg.reader_max], order[cfg.reader_max:]
    f.stage("okuyucu_kesimi", len(order), len(to_read), {"on_siralama_kesimi": len(cut_off)},
            not_=f"en çok {cfg.reader_max} aday okunur; düşenler dusenler_on_siralama.jsonl")
    ctx.out.mkdir(parents=True, exist_ok=True)
    with open(ctx.out / "dusenler_on_siralama.jsonl", "w", encoding="utf-8") as fh:
        for r in cut_off:
            fh.write(json.dumps({"id": public_id(r), "baslik": r["title"], "skor": round(r["skor"], 4)},
                                ensure_ascii=False) + "\n")
    reader.screen(ctx.llm, cfg, soru, subs, to_read, f)
    read_kept, n_irrel = reader.drop_certain(to_read)
    f.stage("okuyucu", len(to_read), len(read_kept), {"kesin_alakasiz": n_irrel})
    ctx.times["okuyucu"] = round(time.monotonic() - t, 1)

    # 6. damıtıcı
    t = time.monotonic()
    rank.score(read_kept, soru, subs, cfg, ctx.embedder, f, use_rel=True)
    rank.cluster(read_kept, max(2, len(subs)))
    cards_recs = rank.top_with_cap(read_kept, cfg.chef_cards, cfg.cluster_cap_frac)
    f.stage("damitma", len(read_kept), len(cards_recs), {"ilk_kart_disi": len(read_kept) - len(cards_recs)},
            not_=f"hibrit skor + küme tavanı %{int(cfg.cluster_cap_frac * 100)}")
    cards = [card(r) for r in cards_recs]
    ctx.times["damitma"] = round(time.monotonic() - t, 1)

    # 7. şef final
    t = time.monotonic()
    final = finalize(ctx, cards_recs, cards)
    ctx.times["sef_final"] = round(time.monotonic() - t, 1)
    ctx.times["toplam"] = round(time.monotonic() - T0, 1)
    return write_outputs(ctx, final, cards)


def card(r: dict) -> dict:
    return {"id": public_id(r), "baslik": r["title"], "yil": (earliest(r) or [None])[0],
            "cites": r.get("citations"), "kaynaklar": [s for s in r.get("sources") or []],
            "rel": r.get("rel"), "not": r.get("not_") or "", "alinti": r.get("alinti") or ""}


def finalize(ctx: Ctx, recs: list[dict], cards: list[dict]) -> list[dict]:
    cfg, f = ctx.cfg, ctx.funnel
    k = min(cfg.final_n, len(recs))
    sel, st = (chef.final(ctx.llm, cfg, ctx.soru, ctx.kesim, ctx.plan["alt_sorular"], cards)
               if recs else ([], "BOS"))
    chosen: list[tuple[int, str, str]] = []  # (indeks, gerekçe, köken)
    invalid = 0
    if sel is None:
        f.source("sef_final", EKSIK, f"şef sıralaması alınamadı ({st}); damıtıcı sırası kullanıldı")
    else:
        f.source("sef_final", OK, kayit=len(sel))
        seen = set()
        for x in sel:
            try:
                i = int(x.get("kart")) - 1
            except (TypeError, ValueError):
                invalid += 1
                continue
            if not (0 <= i < len(recs)) or i in seen:
                invalid += 1
                continue
            seen.add(i)
            chosen.append((i, str(x.get("gerekce") or "").strip(), "sef"))
            if len(chosen) >= k:
                break
    if invalid:
        f.bump("sef_final.gecersiz_kart", invalid)
    if len(chosen) < k:
        used = {i for i, _, _ in chosen}
        fill = [i for i in range(len(recs)) if i not in used][: k - len(chosen)]
        f.bump("sef_final.damitici_ile_dolduruldu", len(fill))
        chosen += [(i, recs[i].get("not_") or "", "damitici") for i in fill]
    f.stage("sef_final", len(recs), len(chosen), {"secilmedi": len(recs) - len(chosen)})
    out = []
    for rank_i, (i, why, origin) in enumerate(chosen, 1):
        r = recs[i]
        d = earliest(r)
        out.append({
            "sira": rank_i, "id": public_id(r), "arxiv_id": r.get("arxiv_id"), "doi": r.get("doi"),
            "baslik": r["title"], "yil": d[0] if d else r.get("year"), "tarih": fmt_date(d),
            "gerekce": why, "gerekce_kokeni": origin,
            "alinti": r.get("alinti") or "",
            "alinti_durum": "VERIFIED" if r.get("alinti") else ("OZET_YOK" if not r.get("abstract") else "YOK"),
            "alinti_kaynagi": r.get("alinti_kaynagi") or "",
            "kaynaklar": r.get("sources"), "atif": r.get("citations"), "rel": r.get("rel"),
            "tohum_yakinligi": len(r.get("seed_of") or []),
        })
    return out
