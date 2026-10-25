"""DBLP: anahtarsız SPARQL uç noktası (sparql.dblp.org).

Not (2026-10-25 gözlemi): dblp.org/search/publ/api REST uç noktası bot doğrulama
(Anubis) sayfası döndürüyor; aşılmaya ÇALIŞILMAZ. SPARQL uç noktası çalışıyor.
DBLP yalnız başlık + yıl verir (özet yok); başlıkta terim araması yapılır.
Kademeler: tüm terimler (AND) → yeterli değilse en az 2 terim (çoğunluk).
"""
from __future__ import annotations

import datetime as dt
import itertools
import re

from orkestra.records import new_record

API = "https://sparql.dblp.org/sparql"
STOP = {"a", "an", "the", "of", "for", "and", "or", "in", "on", "to", "with", "by", "using", "via",
        "is", "are", "from", "at", "as", "into", "based", "approach", "methods", "study", "towards"}


def title_terms(q: str) -> list[str]:
    phrases = [p.strip().lower() for p in re.findall(r'"([^"]+)"', q) if p.strip()]
    rest = re.sub(r'"[^"]+"', " ", q).lower()
    toks = [t for t in re.findall(r"[a-z0-9][a-z0-9_\-]*", rest) if t not in STOP and len(t) > 2]
    out = phrases + [t for t in toks if t not in phrases]
    return out[:5]


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_sparql(groups: list[list[str]], limit: int) -> str:
    """GROUP BY / yıl filtresi YOK: QLever'da tam tarama zaman aşımına düşüyor (gözlem);
    yıl ve tekilleştirme kodda yapılır."""
    cond = " || ".join("(" + " && ".join(f'CONTAINS(LCASE(?t), "{_esc(t)}")' for t in g) + ")" for g in groups)
    lines = [
        "PREFIX dblp: <https://dblp.org/rdf/schema#>",
        "SELECT ?p ?t ?y ?doi ?venue ?ee WHERE {",
        f"  ?p dblp:title ?t . FILTER({cond})",
        "  ?p dblp:yearOfPublication ?y .",
        "  OPTIONAL { ?p dblp:doi ?doi } OPTIONAL { ?p dblp:publishedIn ?venue }"
        " OPTIONAL { ?p dblp:primaryDocumentPage ?ee }",
        f"}} LIMIT {limit}",
    ]
    return "\n".join(lines)


def parse(data: dict, max_year: int | None = None) -> list[dict]:
    rows: dict[str, dict] = {}
    for b in data.get("results", {}).get("bindings", []):
        key = b.get("p", {}).get("value", "")
        cur = rows.setdefault(key, {"t": "", "y": "", "doi": None, "venue": None, "ees": []})
        cur["t"] = cur["t"] or b.get("t", {}).get("value", "").rstrip(".")
        cur["y"] = cur["y"] or b.get("y", {}).get("value", "")
        cur["doi"] = cur["doi"] or b.get("doi", {}).get("value")
        cur["venue"] = cur["venue"] or b.get("venue", {}).get("value")
        if b.get("ee"):
            cur["ees"].append(b["ee"]["value"])
    out = []
    for key, c in rows.items():
        y = c["y"][:4]
        if not c["t"] or not y.isdigit():
            out.append({"_drop": "basliksiz_veya_yilsiz"})
            continue
        if max_year is not None and int(y) > max_year:
            out.append({"_drop": "kesim_sonrasi(yil)"})
            continue
        m = re.search(r"arxiv\.org/abs/([^\s]+)", " ".join(c["ees"]))
        out.append(new_record("dblp", title=c["t"], doi=c["doi"], arxiv_id=m.group(1) if m else None,
                              dates=[[int(y)]], year=int(y), venue=c["venue"], url=key))
    return out


def search(http, query: str, cut: dt.date, cfg) -> list[dict]:
    ts = title_terms(query)
    if not ts:
        return []
    tiers = [[ts]]
    if len(ts) >= 3:
        tiers.append([list(c) for c in itertools.combinations(ts, 2)][:10])
    out: list[dict] = []
    for groups in tiers:
        q = build_sparql(groups, cfg.dblp_limit)
        r = http.request("dblp", API, data={"query": q}, method="POST",
                         headers={"Accept": "application/sparql-results+json"})
        got = parse(r.json(), cut.year)
        out.extend(got)
        if sum(1 for x in out if "_drop" not in x) >= 20:
            break
    return out
