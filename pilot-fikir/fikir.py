"""Fikir pilotu (ONKAYIT-fikir-pilot.md): Claude tek elden (A) vs orkestra + fikir adımı (B).

  python pilot-fikir/fikir.py b <konu_id>     # orkestra v0 taraması + 6 aday → Haiku yenilik taraması → 3 fikir
  python pilot-fikir/fikir.py a <konu_id>     # tek Opus çağrısı, web araçlı, aynı çıktı biçimi
  python pilot-fikir/fikir.py denetle         # yenilik (Sonnet+web), dayanak (kod), kör ikili tercih (Sonnet)

Donmuş orkestra kodunu (etiket orkestra-v0-donmus) yalnız içe aktarır; değiştirmez.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import random
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent
sys.path.insert(0, str(KOK.parent / "orkestra"))

from orkestra.config import load_config  # noqa: E402
from orkestra.http import Http  # noqa: E402
from orkestra.llm import LLM, Ledger, call_json  # noqa: E402
from orkestra.normalize import norm_arxiv, norm_doi, arxiv_from_doi  # noqa: E402
from orkestra.pipeline import run as orkestra_run  # noqa: E402
from orkestra.sources import arxiv, crossref  # noqa: E402

KESIM = "2026-10-25"
SONUC = KOK / "sonuc"
TOHUM = 20261025

FIKIR_BICIMI = """{"fikirler": [{"baslik": "...", "bosluk": "what is missing in the literature (1-2 sentences)",
  "neden_simdi": "why this is timely now (1 sentence)",
  "ilk_adim": "a concrete first project a 3rd-year computer engineering student can do in 3-6 months",
  "dayanaklar": ["arXiv id or DOI of 2-5 supporting works"],
  "yenilik_notu": "closest existing work and how this idea differs"}]}"""

A_ISTEM = """Research area: {konu}

I am a 3rd-year computer engineering student. Give me the 3 research ideas with the HIGHEST potential in this
area that I could realistically start and carry out. Research the current literature on the web first (do not
answer from memory alone), find real gaps, and check on the web that each idea has not already been done.

Reply with ONLY a JSON object in this form, exactly 3 ideas:
""" + FIKIR_BICIMI.replace("{", "{{").replace("}", "}}")

URET_ISTEM = """TASK: propose research ideas from a distilled literature map.

Research area: {konu}
The user is a 3rd-year computer engineering student who wants ideas with the highest potential that they can
realistically carry out.

Below: the 30 most important works (with why they matter), then {n} candidate cards from a broad literature scan.
Card format: #<n> | <year> | cites | <title> | rel | <reader note> | Q: "<verified abstract quote>"

TOP 30:
{top}

CARDS:
{kartlar}

Propose 6 DISTINCT candidate ideas grounded in these cards: real gaps, open problems, or combinations the cards
suggest. Reply ONLY with JSON:
{{"adaylar": [{{"baslik": "...", "bosluk": "...", "neden_simdi": "...", "ilk_adim": "...",
  "dayanak_kartlar": [card numbers, 2-5], "yenilik_sorgulari": ["2-3 web search queries to check prior art"]}}]}}"""

YENILIK_ISTEM = """Check whether this research idea has ALREADY been done (published paper, preprint, or well-known
project). Search the web (use the queries below and your own).

Idea: {baslik}
Gap claimed: {bosluk}
First step: {ilk_adim}
Suggested queries: {sorgular}

Reply ONLY with JSON: {{"hukum": "YENI" | "KISMEN" | "YAPILMIS",
 "en_yakin": [{{"baslik": "...", "yil": 2024, "url": "...", "fark": "how it differs from the idea"}}],
 "not": "one sentence"}}
YENI = nothing close found; KISMEN = close work exists but the idea differs meaningfully; YAPILMIS = essentially done."""

SEC_ISTEM = """TASK: choose the final 3 research ideas.

Research area: {konu}
The user is a 3rd-year computer engineering student; they want the highest-potential ideas they can carry out.

6 candidates, each with a prior-art check done by a web worker:
{adaylar}

Pick the best 3 (potential impact, novelty given the prior-art evidence, feasibility for the student, grounding).
Drop ideas judged YAPILMIS unless you can sharpen them into something clearly different (then say how).
You may refine wording but do not invent supporting works: dayanaklar must come from the candidate's own list.

Reply ONLY with JSON, exactly 3 ideas:
""" + FIKIR_BICIMI.replace("{", "{{").replace("}", "}}")

DENETCI_ISTEM = """You are an independent reviewer. Check on the web whether this research idea has already been done.

Idea: {baslik}
Gap claimed: {bosluk}
First step: {ilk_adim}

Search thoroughly (several queries, Google Scholar-like phrasing, arXiv, GitHub). Reply ONLY with JSON:
{{"hukum": "YENI" | "KISMEN" | "YAPILMIS", "en_yakin": {{"baslik": "...", "yil": 0, "url": "..."}},
 "gerekce": "1-2 sentences"}}
YENI = nothing close; KISMEN = close work exists but the idea differs meaningfully; YAPILMIS = essentially done."""

HAKEM_ISTEM = """You are judging two anonymous sets of research ideas for the same request.

Request: "Give me the 3 highest-potential research ideas in: {konu}. I am a 3rd-year computer engineering student
and want to actually carry them out."

SET X:
{x}

SET Y:
{y}

Judge on: potential impact, novelty, feasibility for the student, and how well grounded each idea is.
Reply ONLY with JSON: {{"daha_iyi": "X" | "Y" | "ESIT", "puan_X": 1-10, "puan_Y": 1-10, "gerekce": "2-3 sentences"}}"""


def konular() -> dict:
    return {k["id"]: k for k in json.loads((KOK / "konular.json").read_text(encoding="utf-8"))}


def yaz(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def _kart_satiri(i: int, c: dict) -> str:
    q = f' Q: "{c["alinti"]}"' if c.get("alinti") else ""
    return f"#{i} | {c.get('yil')} | cites={c.get('cites') or '?'} | {c.get('baslik')} | rel={c.get('rel')} | {c.get('not') or ''}{q}"


def b(kid: str) -> dict:
    k = konular()[kid]
    cfg = load_config()
    out = SONUC / "B" / kid
    soru = f"What are the most important works and open problems in {k['konu']}?"
    t0 = time.monotonic()
    if not (out / "orkestra" / "sonuc.json").exists():
        orkestra_run(soru, KESIM, out / "orkestra", cfg)
    ork = json.loads((out / "orkestra" / "sonuc.json").read_text(encoding="utf-8"))
    kartlar = json.loads((out / "orkestra" / "kartlar.json").read_text(encoding="utf-8"))
    ledger = Ledger(cfg.cost_log, run_id=f"fikir-B-{kid}-{time.strftime('%H%M%S')}")
    llm = LLM(cfg, ledger)
    top = "\n".join(f"- {c['baslik']} ({c.get('yil')}): {c.get('gerekce')}" for c in ork["calismalar"])
    istem = URET_ISTEM.format(konu=k["konu"], n=len(kartlar), top=top,
                              kartlar="\n".join(_kart_satiri(i + 1, c) for i, c in enumerate(kartlar)))
    obj, st = call_json(llm, istem, model=cfg.sef_model, stage="fikir_uret")
    adaylar = (obj or {}).get("adaylar") or []
    for a in adaylar:  # kart no → gerçek kimlik (kodla; şef kimlik uyduramaz)
        a["dayanaklar"] = [kartlar[n - 1]["id"] for n in a.get("dayanak_kartlar") or []
                           if isinstance(n, int) and 1 <= n <= len(kartlar)]

    def tara(a):
        return call_json(llm, YENILIK_ISTEM.format(baslik=a["baslik"], bosluk=a.get("bosluk"), ilk_adim=a.get("ilk_adim"),
                                                   sorgular=a.get("yenilik_sorgulari")),
                         model=cfg.isci_model, stage="fikir_yenilik", tools="WebSearch,WebFetch", budget=0.12)

    with cf.ThreadPoolExecutor(6) as ex:
        taramalar = list(ex.map(tara, adaylar))
    for a, (o, s) in zip(adaylar, taramalar):
        a["yenilik_taramasi"] = o if s == "OK" else {"hukum": "TARANAMADI", "durum": s}
    obj2, st2 = call_json(llm, SEC_ISTEM.format(konu=k["konu"], adaylar=json.dumps(adaylar, ensure_ascii=False, indent=1)),
                          model=cfg.sef_model, stage="fikir_sec")
    s = {"sistem": "B", "konu": k, "durum": "OK" if st == st2 == "OK" else f"{st}/{st2}",
         "fikirler": (obj2 or {}).get("fikirler") or [], "adaylar": adaylar,
         "maliyet": {"orkestra_usd": ork["maliyet_usd"], "fikir_usd": round(ledger.total, 4),
                     "toplam_usd": round(ork["maliyet_usd"] + ledger.total, 4), "fikir_asama": ledger.by_stage},
         "genislik": {"okuyucuya_giden": 1200, "kart": len(kartlar),
                      "funnel_ozet": "orkestra/funnel.json"},
         "sef_girdi_karakter": len(istem), "sure_s": round(time.monotonic() - t0, 1)}
    yaz(out / "fikirler.json", s)
    return s


def a(kid: str) -> dict:
    k = konular()[kid]
    cfg = load_config()
    ledger = Ledger(cfg.cost_log, run_id=f"fikir-A-{kid}-{time.strftime('%H%M%S')}")
    llm = LLM(cfg, ledger)
    t0 = time.monotonic()
    obj, st = call_json(llm, A_ISTEM.format(konu=k["konu"]), model="opus", stage="fikir_A",
                        tools="WebSearch,WebFetch", budget=4.0)
    s = {"sistem": "A", "konu": k, "durum": st, "fikirler": (obj or {}).get("fikirler") or [],
         "maliyet": {"toplam_usd": round(ledger.total, 4), "asama": ledger.by_stage},
         "sure_s": round(time.monotonic() - t0, 1)}
    yaz(SONUC / "A" / kid / "fikirler.json", s)
    return s


def _kimlik_coz(http, cfg, x: str) -> str:
    x = str(x or "").strip()
    ax = norm_arxiv(x.replace("arXiv:", "").replace("arxiv:", "")) or arxiv_from_doi(norm_doi(x.replace("doi:", "")))
    try:
        if ax:
            return "VAR" if arxiv.by_ids(http, [ax]) else "YOK"
        d = norm_doi(x.replace("doi:", ""))
        if d:
            return "VAR" if crossref.by_doi(http, d, cfg) else "YOK"
    except Exception as exc:  # noqa: BLE001 — kaynak hatası: bilinmiyor
        return f"BILINMIYOR:{type(exc).__name__}"
    return "KIMLIK_YOK"


def _set_metni(fs: list[dict]) -> str:
    return "\n".join(f"{i + 1}. {f.get('baslik')}\n   Gap: {f.get('bosluk')}\n   Why now: {f.get('neden_simdi')}\n"
                     f"   First step: {f.get('ilk_adim')}\n   Supporting works: {', '.join(map(str, f.get('dayanaklar') or []))}\n"
                     f"   Novelty: {f.get('yenilik_notu')}" for i, f in enumerate(fs))


def denetle() -> dict:
    cfg = load_config()
    ledger = Ledger(cfg.cost_log, run_id=f"fikir-denetim-{time.strftime('%H%M%S')}")
    llm = LLM(cfg, ledger)
    http = Http(cfg)
    rng = random.Random(TOHUM)
    rapor = {"tohum": TOHUM, "konular": {}}
    for kid, k in konular().items():
        setler = {s: json.loads((SONUC / s / kid / "fikirler.json").read_text(encoding="utf-8"))["fikirler"]
                  for s in ("A", "B")}
        kr = {}
        for s, fs in setler.items():
            def yen(f):
                return call_json(llm, DENETCI_ISTEM.format(baslik=f.get("baslik"), bosluk=f.get("bosluk"),
                                                           ilk_adim=f.get("ilk_adim")),
                                 model="sonnet", stage="fikir_denetim_yenilik", tools="WebSearch,WebFetch", budget=0.30)
            with cf.ThreadPoolExecutor(3) as ex:
                yh = list(ex.map(yen, fs))
            dayanak = [[(x, _kimlik_coz(http, cfg, x)) for x in f.get("dayanaklar") or []] for f in fs]  # sıralı
            kr[s] = {"yenilik": [o if st == "OK" else {"hukum": "DENETLENEMEDI", "durum": st} for o, st in yh],
                     "dayanak": dayanak}
        x_is_b = rng.random() < 0.5
        x, y = (setler["B"], setler["A"]) if x_is_b else (setler["A"], setler["B"])
        h, st = call_json(llm, HAKEM_ISTEM.format(konu=k["konu"], x=_set_metni(x), y=_set_metni(y)),
                          model="sonnet", stage="fikir_hakem")
        if st == "OK" and isinstance(h, dict):
            secilen = h.get("daha_iyi")
            h["kazanan_sistem"] = {"X": "B" if x_is_b else "A", "Y": "A" if x_is_b else "B"}.get(secilen, "ESIT")
        kr["hakem"] = {"X_sistemi": "B" if x_is_b else "A", "sonuc": h if st == "OK" else {"durum": st}}
        rapor["konular"][kid] = kr
    rapor["denetim_maliyet_usd"] = round(ledger.total, 4)
    yaz(SONUC / "denetim.json", rapor)
    return rapor


if __name__ == "__main__":
    cmd = sys.argv[1]
    r = {"a": lambda: a(sys.argv[2]), "b": lambda: b(sys.argv[2]), "denetle": denetle}[cmd]()
    print(json.dumps({k: v for k, v in r.items() if k in ("sistem", "durum", "maliyet", "sure_s", "denetim_maliyet_usd")},
                     ensure_ascii=False, default=str)[:800])
