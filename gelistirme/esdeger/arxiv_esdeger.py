"""Eşdeğerlik denetimi (ağsız): v0 duman koşularının önbellekteki canlı arXiv yanıtları ↔ yerel dizin.

Girdi: http_cache_kopya.sqlite (forge/orkestra/data/http_cache.sqlite'ın sqlite3 backup API ile
salt-okunur alınmış kopyası; asıl dosyaya yazılmaz). Her arXiv Atom yanıtının <title>'ında
search_query yazılıdır; oradan kademe ifadesi + kesim çıkarılır, ifade FTS5'e birebir çevrilir
(all:X → "X"; AND/OR/parantez aynen), aynı kesimle yerelde koşulur.

    python gelistirme/esdeger/arxiv_esdeger.py [--db ...] [--cache ...] [--json out.json]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "orkestra"))

from orkestra.normalize import norm_arxiv, norm_title  # noqa: E402
from orkestra.records import title_sim  # noqa: E402
from orkestra.sources import arxiv_yerel  # noqa: E402

NS = {"a": "http://www.w3.org/2005/Atom", "os": "http://a9.com/-/spec/opensearch/1.1/"}
_Q = re.compile(r"search_query=(.*?)&id_list=(.*?)&start=(\d+)&max_results=(\d+)", re.S)
_DATE = re.compile(r'\s*AND submittedDate:"199101010000 TO (\d{8})2359"\s*$')


def feeds(cache: Path):
    con = sqlite3.connect(f"file:{cache.as_posix()}?mode=ro", uri=True)
    for (body,) in con.execute("SELECT body FROM cache"):
        b = bytes(body)
        if b"arXiv Query" not in b[:3000] and b"ArXiv Query" not in b[:3000]:
            continue
        root = ET.fromstring(b)
        title = html.unescape(root.findtext("a:title", "", NS))
        m = _Q.search(title)
        if not m:
            continue
        tot = root.findtext("os:totalResults", None, NS)
        entries = []
        for e in root.findall("a:entry", NS):
            eid = (e.findtext("a:id", "", NS) or "").strip()
            entries.append({"id": norm_arxiv(eid), "title": " ".join((e.findtext("a:title", "", NS) or "").split()),
                            "published": (e.findtext("a:published", "", NS) or "")[:10]})
        yield {"sq": m.group(1), "ids": m.group(2), "start": int(m.group(3)), "max": int(m.group(4)),
               "total": int(tot) if tot and tot.isdigit() else None, "entries": entries}


def to_fts(expr: str) -> str:
    out = re.sub(r'all:"([^"]+)"', lambda m: '"' + m.group(1) + '"', expr)
    out = re.sub(r"all:([^\s()\"]+)", lambda m: '"' + m.group(1) + '"', out)
    return out


def tier_of(expr: str) -> str:
    if " OR " not in expr:
        return "AND"
    return "MAJ" if " AND " in expr else "OR"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=r"C:\Users\LENOVO\Projeler\forge-veri\arxiv_yerel.sqlite")
    ap.add_argument("--cache", default=str(HERE / "http_cache_kopya.sqlite"))
    ap.add_argument("--json", default=str(HERE / "esdeger_sonuc.json"))
    a = ap.parse_args(argv)
    dz = arxiv_yerel.Dizin(a.db)
    caps = {"AND": 100, "MAJ": 100, "OR": 200}

    # sorgu → sayfalar (start 0, 100, ...) birleştir; aynı sorgu birden çok koşuda önbellekte tek
    searches: dict[str, dict] = {}
    titles: list[dict] = []
    for f in feeds(Path(a.cache)):
        if f["ids"]:
            continue  # id_list (by_ids): canlı kalır, karşılaştırılmaz
        if f["sq"].startswith("ti:"):
            titles.append(f)
            continue
        m = _DATE.search(f["sq"])
        if not m:
            continue
        expr = f["sq"][: m.start()].strip()
        if expr.startswith("(") and expr.endswith(")"):
            expr = expr[1:-1]
        cut = dt.datetime.strptime(m.group(1), "%Y%m%d").date() + dt.timedelta(days=1)
        s = searches.setdefault(f"{expr}|{cut}", {"expr": expr, "cut": cut, "pages": {}, "total": f["total"]})
        s["pages"][f["start"]] = f["entries"]

    per_q = []
    miss_reasons = collections.Counter()
    miss_examples = collections.defaultdict(list)
    date_cmp = collections.Counter()
    pub_vs_v1_days = []
    agg = collections.Counter()
    for key, s in searches.items():
        live = [e for st in sorted(s["pages"]) for e in s["pages"][st] if e["id"]]
        if not live:
            agg["bos_canli_sorgu"] += 1
            continue
        tier = tier_of(s["expr"])
        fts = to_fts(s["expr"])
        try:
            ids_full = [r[0] for r in dz.query(
                "WITH m AS MATERIALIZED (SELECT rowid AS rid, " + arxiv_yerel.BM25 + " AS s FROM ara WHERE ara MATCH ?) "
                "SELECT k.id FROM m JOIN kayit k ON k.rid = m.rid WHERE k.v1_tarih < ? ORDER BY m.s",
                (fts, s["cut"].isoformat()))]
            total_local = len(ids_full)
        except sqlite3.OperationalError as exc:
            agg["fts_hata"] += 1
            print("FTS hata:", fts[:120], exc, file=sys.stderr)
            continue
        set_full = set(ids_full)
        set_cap = set(ids_full[: caps[tier]])
        n = len(live)
        in_full = sum(e["id"] in set_full for e in live)
        in_cap = sum(e["id"] in set_cap for e in live)
        top10 = live[:10]
        in10_full = sum(e["id"] in set_full for e in top10)
        agg["sorgu"] += 1
        agg[f"sorgu.{tier}"] += 1
        agg["canli_id"] += n
        agg["yerel_tum_eslesmede"] += in_full
        agg["yerel_tavan_icinde"] += in_cap
        agg["canli_top10"] += len(top10)
        agg["top10_yerelde"] += in10_full
        per_q.append({"tier": tier, "cut": str(s["cut"]), "expr": s["expr"][:200], "canli_n": n,
                      "canli_toplam": s["total"], "yerel_toplam": total_local,
                      "yerelde": in_full, "tavan_icinde": in_cap, "oran": round(in_full / n, 3)})
        # kaçanlar: neden?
        missing = [e for e in live if e["id"] not in set_full]
        if missing:
            have = {r["arxiv_id"]: r for r in arxiv_yerel.by_ids(dz, [e["id"] for e in missing])}
            raw = {row[0]: row for row in dz.query(
                "SELECT id, v1_tarih, kategoriler FROM kayit WHERE id IN (%s)" % ",".join("?" * len(missing)),
                tuple(e["id"] for e in missing))}
            for e in missing:
                if e["id"] not in have:
                    v = "dizinde_yok"
                else:
                    v1 = raw[e["id"]][1]
                    if v1 and v1 >= str(s["cut"]):
                        v = "v1_kesim_sonrasi(yerel)"
                    else:
                        # aynı ifade kesimsiz ve tek kayıtla: metin eşleşmesi var mı?
                        rid = dz.query("SELECT rid FROM kayit WHERE id=?", (e["id"],))[0][0]
                        hit = dz.query("SELECT count(*) FROM ara WHERE ara MATCH ? AND rowid=?", (fts, rid))[0][0]
                        v = "metin_eslesmiyor(baslik+ozet)" if not hit else "baska"
                miss_reasons[v] += 1
                if len(miss_examples[v]) < 6:
                    miss_examples[v].append({"id": e["id"], "baslik": e["title"][:90], "expr": s["expr"][:90],
                                             "kesim": str(s["cut"]), "published": e["published"]})
        # tarih anlamı: canlı published (v1 gönderim) ↔ yerel v1_tarih
        rows = {r[0]: r[1] for r in dz.query(
            "SELECT id, v1_tarih FROM kayit WHERE id IN (%s)" % ",".join("?" * len(live)), tuple(e["id"] for e in live))}
        for e in live:
            if e["id"] in rows and e["published"] and rows[e["id"]]:
                d = (dt.date.fromisoformat(rows[e["id"]]) - dt.date.fromisoformat(e["published"])).days
                date_cmp["ayni_gun" if d == 0 else ("1_gun" if abs(d) == 1 else "farkli")] += 1
                if d:
                    pub_vs_v1_days.append(d)

    # başlık araması (preprint_abstracts / çapa çözümleme): canlı ti: yanıtındaki, sorulan başlıkla
    # eşleşen (benzerlik ≥ 0.90) kayıtlar yerel by_titles'ta da var mı?
    t_agg = collections.Counter()
    t_miss = []
    for f in titles:
        asked = [html.unescape(x) for x in re.findall(r'ti:"([^"]*)"', f["sq"])]
        cands = arxiv_yerel.by_titles(dz, asked)
        loc_ids = {c["arxiv_id"] for c in cands}
        for t in asked:
            nt = norm_title(t)
            live_m = [e for e in f["entries"] if e["id"] and title_sim(nt, norm_title(e["title"])) >= 0.90]
            if not live_m:
                continue
            t_agg["canli_eslesen_baslik"] += 1
            if any(e["id"] in loc_ids for e in live_m):
                t_agg["yerelde_bulundu"] += 1
            else:
                loc_best = max((title_sim(nt, norm_title(c["title"])) for c in cands), default=0)
                if loc_best >= 0.90:
                    t_agg["yerelde_baska_id_ayni_baslik"] += 1
                elif len(t_miss) < 10:
                    t_miss.append({"baslik": t[:100], "canli_id": live_m[0]["id"]})

    res = {
        "dizin": {"kayit": dz.n, "en_yeni_v1": str(dz.max_v1)},
        "ozet": dict(agg), "kacan_sebep": dict(miss_reasons), "kacan_ornek": miss_examples,
        "tarih_karsilastirma": dict(date_cmp),
        "published_v1_fark_gun_ornek": sorted(collections.Counter(pub_vs_v1_days).items())[:20],
        "baslik": dict(t_agg), "baslik_kacan_ornek": t_miss, "sorgular": per_q,
    }
    Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    o = agg
    if o["canli_id"]:
        print(f"sorgu {o['sorgu']} | canlı id {o['canli_id']} | yerel tüm eşleşmede {o['yerel_tum_eslesmede'] / o['canli_id']:.3f}"
              f" | tavan içinde {o['yerel_tavan_icinde'] / o['canli_id']:.3f} | top10 {o['top10_yerelde'] / max(1, o['canli_top10']):.3f}")
    print("kaçan sebep:", dict(miss_reasons))
    print("tarih:", dict(date_cmp))
    print("başlık:", dict(t_agg))


if __name__ == "__main__":
    main()
