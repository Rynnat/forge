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
from orkestra.records import _conflict, cutoff_filter, dedup, earliest, fmt_date, public_id
from orkestra.report import write_outputs
from orkestra.sources import arxiv, arxiv_yerel, crossref, dblp, openalex, opencitations, s2

FATAL = (QuotaExhausted, BotBlocked)


class Ctx:
    def __init__(self, cfg: Config, soru: str, kesim: str, out_dir: Path, llm=None, http=None,
                 searchers: dict[str, Callable] | None = None, resolver: Callable | None = None,
                 enricher: Callable | None = None, snowballer: Callable | None = None,
                 web_runner: Callable | None = None, preprinter: Callable | None = None,
                 arxiv_dizin=None):
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
        # Yerel arXiv dizini (v1): varsa arama + önbaskı özeti + başlık çözümleme yerel; canlı
        # arXiv yalnız by_ids için. Testler `arxiv_dizin` ile sahte/küçük dizin verebilir.
        self.arxiv_dizin = arxiv_dizin if arxiv_dizin is not None else arxiv_yerel.ac(cfg)
        if self.arxiv_dizin is not None and "arxiv" in cfg.sources:
            self.funnel.source("arxiv", OK, **arxiv_yerel.durum(self.arxiv_dizin))
            if not self.arxiv_dizin.covers(self.cut):
                self.funnel.source("arxiv", EKSIK, self.arxiv_dizin.uncovered_reason(self.cut))
        self.searchers = searchers if searchers is not None else default_searchers(self)
        titles_fn = ((lambda http, ts: arxiv_yerel.by_titles(self.arxiv_dizin, ts))
                     if self.arxiv_dizin is not None else None)
        self.resolver = resolver or (lambda items, label: web.resolve(self.http, cfg, items, self.funnel, label,
                                                                      titles_fn=titles_fn))
        self.enricher = enricher or (lambda keys: s2.batch(self.http, keys))
        self.preprint_yerel = preprinter is None and self.arxiv_dizin is not None
        if preprinter is None:
            preprinter = ((lambda titles: arxiv_yerel.by_titles(self.arxiv_dizin, titles)) if self.preprint_yerel
                          else (lambda titles: arxiv.by_titles(self.http, titles)))
        self.preprinter = preprinter
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
    dz = getattr(ctx, "arxiv_dizin", None)
    return {
        "arxiv": ((lambda q: arxiv_yerel.search(dz, q, ctx.cut, cfg, ctx.funnel)) if dz is not None
                  else (lambda q: arxiv.search(http, q, ctx.cut, cfg, ctx.funnel))),
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


def preprint_abstracts(ctx: Ctx, to_read: list[dict], pool_ids: set[str] | None = None) -> None:
    """Okuyucuya gidecek özetsiz kayıtlar için arXiv önbaskısını başlıkla bulup özetini kopyalar
    (anahtarsız yedek; S2 429 verince Crossref'siz DOI kayıtları yalnız başlıkla yargılanıyordu).
    `to_read` kesimden ve ön sıralamadan geçmiş, skora göre sıralı listedir: tavan = ilk K özetsiz.
    Kesim anlamı değişmez: yalnız zaten geçmiş kayıtlara dokunulur ve bulunan önbaskının tarihi
    `dates`e eklenir; `before_cutoff` 'en az biri kesin önce' dediğinden, kesim SONRASI tarihli
    bir önbaskı geçen çalışmayı düşüremez, kesim öncesi olan zaten geçmiştir.
    Huni bilgisi: ozet_arxiv.{aday,denendi,bulundu,bulunamadi,atlandi_*}.
    v1 yerel dizin (ctx.preprint_yerel): istek yok → tavan `arxiv_yerel_ozet_tavan` (0 = tavansız),
    canlı kota durumu bakılmaz. `arxiv_ozet_k = 0` her iki kipte de özelliği kapatır."""
    f, cfg = ctx.funnel, ctx.cfg
    need = [r for r in to_read if not (r.get("abstract") or "").strip() and r.get("title")]
    if not need:
        return
    f.bump("ozet_arxiv.aday", len(need))
    local = bool(getattr(ctx, "preprint_yerel", False))
    k = max(0, cfg.arxiv_ozet_k)
    if k == 0 or "arxiv" not in cfg.sources:
        f.bump("ozet_arxiv.atlandi_kapali", len(need))
        return
    if local:
        k = max(0, cfg.arxiv_yerel_ozet_tavan) or len(need)
    if len(need) > k:
        f.bump("ozet_arxiv.atlandi_tavan", len(need) - k)
    todo = need[:k]
    used = set(pool_ids or ())
    found = tried = 0
    skipped_quota = 0
    stop = ""
    ex = {} if local else (getattr(ctx.http, "exhausted", None) or {})
    if "arxiv" in ex:
        stop = f"arXiv bu koşuda zaten tükendi: {ex['arxiv']}"
    errors = 0
    for i in range(0, len(todo), 6):
        chunk = todo[i:i + 6]
        if stop:
            skipped_quota += len(chunk)
            continue
        try:
            cands = ctx.preprinter([r["title"] for r in chunk])
        except FATAL as exc:
            stop = f"{type(exc).__name__}: {exc.detail}"[:200]
            skipped_quota += len(chunk)
            continue
        except (RequestFailed, ValueError, KeyError) as exc:
            f.error(f"ozet_arxiv:{type(exc).__name__}")
            errors += len(chunk)
            continue
        tried += len(chunk)
        for r in chunk:
            c, s = web._best(r["title"], [x for x in cands if (x.get("abstract") or "").strip()])
            if not c or s < 0.90 or _conflict(r, c):
                continue
            found += 1
            r["abstract"] = c["abstract"]
            r["ozet_kaynagi"] = "arxiv_onbaski"
            r["onbaski_arxiv_id"] = c.get("arxiv_id")
            ds = [list(d) for d in c.get("dates") or []]
            r["dates"] = list(r.get("dates") or []) + [d for d in ds if d not in (r.get("dates") or [])]
            if ds and ctx.cut and records_before(ds, ctx.cut) is False:
                f.bump("ozet_arxiv.onbaski_kesim_sonrasi")
            if not r.get("arxiv_id") and c.get("arxiv_id") and c["arxiv_id"] not in used:
                r["arxiv_id"] = c["arxiv_id"]
                used.add(c["arxiv_id"])
    f.bump("ozet_arxiv.denendi", tried)
    f.bump("ozet_arxiv.bulundu", found)
    f.bump("ozet_arxiv.bulunamadi", tried - found)
    if errors:
        f.bump("ozet_arxiv.atlandi_hata", errors)
    if skipped_quota:
        f.bump("ozet_arxiv.atlandi_kota", skipped_quota)
        f.source("ozet_arxiv", EKSIK, stop)
    else:
        f.source("ozet_arxiv", OK, istek=0 if local else (tried + 5) // 6, kayit=found, istenen=len(todo),
                 **({"mod": "yerel"} if local else {}))


def records_before(dates: list, cut) -> bool | None:
    """Tarih listesi için 'en az biri kesin önce' kararı (kesim süzgeciyle aynı kural)."""
    from orkestra.records import before_cutoff
    return before_cutoff({"dates": dates}, cut)


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

    def fetch(sd: dict) -> tuple[str, list[str], list[tuple[str, str]], int]:
        """Bir tohumun referansları + atıf yapanları; hata olursa yükseltir (hiçbiri yarım eklenmez)."""
        rs, cs, n = [], [], 0
        for d in opencitations.seed_dois(sd):
            if not d.startswith("10.48550/"):  # arXiv DataCite DOI'lerinin kaynakçası yok
                n += 1
                rs += ctx.oc.references(d)
            n += 1
            cs += ctx.oc.citations(d)
        return public_id(sd), rs, cs, n

    with cf.ThreadPoolExecutor(max_workers=3) as ex:  # OpenCitations: es_zamanli=3
        futs = [ex.submit(fetch, sd) for sd in seeds]
        fatal = False
        for fut in futs:  # tohum sırasıyla: sonuç koşudan koşuya aynı
            try:
                sid, rs, cs, n = fut.result()
            except FATAL as exc:
                if not fatal:
                    f.source("atif", EKSIK, f"{type(exc).__name__}: {exc.detail}"[:200])
                fatal = True
                continue
            except (RequestFailed, ValueError, KeyError) as exc:
                f.error(f"atif:{type(exc).__name__}")
                continue
            calls += n
            for x in rs:
                refs.setdefault(x, set()).add(sid)
            for x, created in cs:
                if opencitations.created_before(created, ctx.cut) is False:
                    late.add(x)
                    continue
                cites.setdefault(x, set()).add(sid)
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
    preprint_abstracts(ctx, to_read, {r["arxiv_id"] for r in kept if r.get("arxiv_id")})
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
            "ozet_kaynagi": r.get("ozet_kaynagi") or "",
            "kaynaklar": r.get("sources"), "atif": r.get("citations"), "rel": r.get("rel"),
            "tohum_yakinligi": len(r.get("seed_of") or []),
        })
    return out
