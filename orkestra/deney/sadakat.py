"""Sadakat denetçisi (ONKAYIT-orkestra-v0, Sadakat + Eşik 3).

Sistemin listelediği çalışmalardan rastgele N iddia (çalışma + gerekçe cümlesi) örneklenir; şefin
(opus) DIŞINDA bir model (sonnet, yalnız WebSearch/WebFetch) her birini kaynağa karşı denetler.
Önce koda uygun varlık kontrolü yapılır (arXiv API / Crossref) ve sonuç denetçiye ipucu olarak verilir.

Karar: KONTROL_EDILEMEDI = DESTEKLENMİYOR sayılır (muhafazakâr). Eşik 3: n=30'da >=28 destekleniyor,
Wilson alt sınır >=0,79 ve uydurma=0. n<30 ise yalnız pilot; KABUL/RED verilmez.

Kullanım (forge/orkestra içinde):
  python -m deney.sadakat sonuc1.json [sonuc2.json ...] --out DIR [--n 30] [--seed S]
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from orkestra.config import load_config  # noqa: E402
from orkestra.http import Http, HttpError  # noqa: E402
from orkestra.llm import LLM, Ledger, call_json  # noqa: E402
from orkestra.normalize import norm_arxiv, norm_doi, norm_title  # noqa: E402

VERDICTS = ("DESTEKLENIYOR", "DESTEKLENMIYOR", "UYDURMA", "KONTROL_EDILEMEDI")
AUDIT_MODEL = "sonnet"
DEFAULT_SEED = 20261025
TOOLS = "WebSearch,WebFetch"
STAGE = "sadakat"
SYSTEM = ("You are a strict, skeptical citation auditor. Use the web tools to check claims about scholarly "
          "works. Answer ONLY with valid JSON. Never guess: if you cannot reach the source, say so.")


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n <= 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d


def load_claims(paths: list[Path]) -> list[dict]:
    out = []
    for p in paths:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
        for w in d.get("calismalar", []):
            out.append({"kaynak_dosya": str(p), "run_id": d.get("run_id", ""), "sira": w.get("sira"),
                        "id": w.get("id"), "arxiv_id": w.get("arxiv_id"), "doi": w.get("doi"),
                        "baslik": w.get("baslik", ""), "yil": w.get("yil"), "gerekce": w.get("gerekce", "")})
    return out


def sample(claims: list[dict], n: int, seed: int) -> list[dict]:
    return random.Random(seed).sample(claims, min(n, len(claims)))


def _sim(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()


def exist_check(http, c: dict) -> dict:
    """Koda uygun varlık kontrolü. durum: ESLESTI | BASLIK_UYUSMUYOR | YOK | BILINMIYOR | KIMLIK_YOK."""
    aid, doi = norm_arxiv(c.get("arxiv_id")), norm_doi(c.get("doi"))
    try:
        if aid:
            r = http.request("arxiv", "https://export.arxiv.org/api/query", params={"id_list": aid, "max_results": 1})
            ns = {"a": "http://www.w3.org/2005/Atom"}
            ents = ET.fromstring(r.body).findall("a:entry", ns)
            t = ents[0].findtext("a:title", "", ns) if ents else ""
            if not ents or not t.strip() or t.strip().lower() == "error":
                return {"durum": "YOK", "kimlik": f"arXiv:{aid}", "url": f"https://arxiv.org/abs/{aid}"}
            t = re.sub(r"\s+", " ", t).strip()
            s = _sim(t, c["baslik"])
            return {"durum": "ESLESTI" if s >= 0.8 else "BASLIK_UYUSMUYOR", "kimlik": f"arXiv:{aid}",
                    "bulunan_baslik": t, "benzerlik": round(s, 2), "url": f"https://arxiv.org/abs/{aid}"}
        if doi:
            r = http.request("crossref", f"https://api.crossref.org/works/{doi}")
            t = " ".join(((r.json().get("message") or {}).get("title")) or [])
            s = _sim(t, c["baslik"]) if t else 0.0
            return {"durum": "ESLESTI" if s >= 0.8 else "BASLIK_UYUSMUYOR", "kimlik": f"doi:{doi}",
                    "bulunan_baslik": t, "benzerlik": round(s, 2), "url": f"https://doi.org/{doi}"}
    except HttpError as e:
        # Crossref 404 = DOI başka ajansta (DataCite vb.) olabilir; kesin YOK denmez
        return {"durum": "BILINMIYOR", "kimlik": aid or doi, "not": str(e)[:120]}
    except Exception as e:  # ağ/parse
        return {"durum": "BILINMIYOR", "kimlik": aid or doi, "not": f"{type(e).__name__}: {e}"[:120]}
    return {"durum": "KIMLIK_YOK"}


def make_prompt(c: dict, ex: dict) -> str:
    return f"""Audit ONE claim made by a literature-survey tool.

Work: "{c['baslik']}" ({c.get('yil')})
Identifiers: arXiv={c.get('arxiv_id')} DOI={c.get('doi')}
Tool's justification sentence (the claim): "{c['gerekce']}"

Automated existence pre-check (code, may be incomplete): {json.dumps(ex, ensure_ascii=False)}

Do two checks using WebSearch/WebFetch (open the arXiv abstract page / DOI landing page / publisher page):
1. EXISTENCE: does a work with this title/ID exist (title substantially matches the ID)?
2. SUPPORT: is the justification sentence supported by the source (abstract or paper text)? If a part of the
   sentence is an unverifiable popularity/impact judgement ("highly cited", "foundational") but the descriptive
   part is right, judge the descriptive part and mention the unverifiable part in "not".

Verdict (exactly one):
- DESTEKLENIYOR: work exists AND the sentence is supported by the source.
- DESTEKLENMIYOR: work exists but the sentence is not supported / contradicted / materially overstated.
- UYDURMA: no such work exists (fabricated, or the ID/title point to different works so the cited work does not exist).
- KONTROL_EDILEMEDI: you could not reach enough of the source to decide.

Reply ONLY with JSON: {{"karar": "...", "var_mi": true|false|null, "kanit_alinti": "short verbatim quote from the source (<=300 chars) or empty", "url": "the URL you relied on", "not": "one short sentence"}}"""


def audit_one(llm, http, c: dict, budget: float, ex: dict | None = None) -> dict:
    ex = ex if ex is not None else exist_check(http, c)
    row = {k: c[k] for k in ("kaynak_dosya", "sira", "id", "arxiv_id", "doi", "baslik", "yil", "gerekce")}
    row["varlik_kodu"] = ex
    t0 = time.monotonic()
    obj, st = call_json(llm, make_prompt(c, ex), model=AUDIT_MODEL, stage=STAGE, system=SYSTEM,
                        tools=TOOLS, budget=budget)
    row["sure_s"] = round(time.monotonic() - t0, 1)
    if not isinstance(obj, dict) or obj.get("karar") not in VERDICTS:
        row.update(karar="KONTROL_EDILEMEDI", kanit_alinti="", url=ex.get("url", ""),
                   **{"not": f"denetçi yanıtı kullanılamadı ({st})"})
    else:
        row.update(karar=obj["karar"], var_mi=obj.get("var_mi"), kanit_alinti=str(obj.get("kanit_alinti", ""))[:400],
                   url=str(obj.get("url", "")), **{"not": str(obj.get("not", ""))[:300]})
    return row


def summarize(rows: list[dict], n_req: int, seed: int, pool: int) -> dict:
    n = len(rows)
    cnt = {v: sum(r["karar"] == v for r in rows) for v in VERDICTS}
    k = cnt["DESTEKLENIYOR"]  # KONTROL_EDILEMEDI destekli sayılmaz (muhafazakâr)
    wl = wilson_lower(k, n)
    full = n >= 30
    ok = cnt["UYDURMA"] == 0 and k >= 28  # ON KAYIT eki: sayı bağlayıcı, Wilson betimsel
    return {"seed": seed, "n_istenen": n_req, "n": n, "havuz": pool, "sayim": cnt,
            "destekleniyor": f"{k}/{n}", "wilson_alt_95": round(wl, 3), "uydurma": cnt["UYDURMA"],
            "muhafazakar_kural": "KONTROL_EDILEMEDI ve DESTEKLENMIYOR 'desteklenmiyor' sayilir; payda n'dir.",
            "esik3": "n=30'da >=28 destekleniyor ve uydurma=0 (Wilson alt betimsel; ON KAYIT eki 2026-10-25)",
            "sonuc": ("GECTI" if ok else "KALDI") if full else "PILOT (n<30; esik hukmu yok)"}


def run(cfg, inputs: list[Path], out: Path, n: int = 30, seed: int = DEFAULT_SEED, budget: float = 0.15,
        llm=None, http=None, workers: int = 3) -> dict:
    claims = load_claims(inputs)
    pick = sample(claims, n, seed)
    ledger = Ledger(cfg.cost_log, run_id=f"sadakat-{time.strftime('%Y%m%d-%H%M%S')}")
    llm = llm or LLM(cfg, ledger)
    http = http or Http(cfg)
    exs = [exist_check(http, c) for c in pick]  # arXiv'e sıralı (paralelde 429 alıyordu); denetim paralel
    with ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(lambda ce: audit_one(llm, http, ce[0], budget, ce[1]), zip(pick, exs)))
    s = summarize(rows, n, seed, len(claims))
    s["maliyet_usd"] = round(llm.ledger.by_stage.get(STAGE, {}).get("cost_usd", 0.0), 4)
    s["denetci_model"] = AUDIT_MODEL
    out.mkdir(parents=True, exist_ok=True)
    (out / "sadakat.json").write_text(json.dumps({"ozet": s, "girdiler": [str(p) for p in inputs], "iddialar": rows},
                                                 ensure_ascii=False, indent=2), encoding="utf-8")
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--budget-per-claim", type=float, default=0.15)
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    s = run(load_config(a.config), a.inputs, a.out, a.n, a.seed, a.budget_per_claim)
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
