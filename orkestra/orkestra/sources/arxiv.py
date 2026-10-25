"""arXiv API: kademeli sorgu (AND → çoğunluk → OR), alt çizgi korunur, tarih aralığı
sorguya gömülür (`submittedDate`), yine de kesim kodla ayrıca uygulanır.

gapmine denetim dersleri:
  #1 alt çizgi: `io_uring` tek terim kalır (`all:io_uring`).
  #2 AND/OR ikilemi: arada "çoğunluk" kademesi (terimlerin ≥ ⌈n·0.6⌉'i) var; OR yedeği 200'e kadar.
     Her sorgu için kademe sayaçları ve API'nin gönderemediği (kesilen) sonuç sayısı loglanır.
"""
from __future__ import annotations

import datetime as dt
import itertools
import math
import re
import xml.etree.ElementTree as ET

from orkestra.normalize import clean_ws, norm_arxiv, norm_doi
from orkestra.records import new_record

API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom",
      "os": "http://a9.com/-/spec/opensearch/1.1/"}
STOP = {"a", "an", "the", "of", "for", "and", "or", "in", "on", "to", "with", "by", "using", "via",
        "is", "are", "be", "from", "at", "as", "into", "its", "their", "that", "this", "what", "which",
        "how", "based", "approach", "approaches", "methods", "method", "study", "toward", "towards"}
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-\.]*[A-Za-z0-9_]|[A-Za-z0-9]")


def terms(q: str) -> list[str]:
    """Serbest metin → arXiv terimleri. Tırnaklı ifade tek terim; alt çizgi ve tire korunur."""
    phrases = [p.strip() for p in re.findall(r'"([^"]+)"', q) if p.strip()]
    rest = re.sub(r'"[^"]+"', " ", q)
    out = [f'"{p}"' for p in phrases]
    for tok in _TOKEN.findall(rest):
        if tok.lower() in STOP or tok.upper() in ("AND", "OR", "NOT") or len(tok) < 2:
            continue
        if tok not in out:
            out.append(tok)
    return out[:8]


def _t(term: str) -> str:
    if not term.startswith('"') and re.search(r"[\-\.]", term):
        return f'all:"{term}"'
    return f"all:{term}"


def date_clause(cut: dt.date) -> str:
    last = cut - dt.timedelta(days=1)
    return f"submittedDate:[199101010000 TO {last:%Y%m%d}2359]"


def tier_groups(q: str) -> list[tuple[str, list[tuple[str, ...]]]]:
    """[(kademe, [AND'lenen terim grubu, ...])] — grupların OR'u. Canlı ve yerel arama
    (sources/arxiv_yerel.py) aynı kademe/kombinasyon seçimini buradan alır."""
    ts = terms(q)
    if not ts:
        return []
    out = [("AND", [tuple(ts)])]
    n = len(ts)
    if n >= 3:
        k = max(2, math.ceil(n * 0.6))
        if k < n:
            combos = list(itertools.combinations(ts, k))
            if len(combos) > 12:  # kayan pencere: ardışık k-terim grupları + baş/son karışımı
                combos = [tuple(ts[i:i + k]) for i in range(n - k + 1)] +                          [tuple(ts[:k - 1] + [ts[-1]])]
            out.append(("MAJ", combos))
    if n >= 2:
        out.append(("OR", [(t,) for t in ts]))
    return out


def tier_queries(q: str) -> list[tuple[str, str]]:
    """[(kademe, search_query_without_date)]"""
    out = []
    for tier, groups in tier_groups(q):
        if tier == "AND":
            out.append((tier, " AND ".join(_t(t) for t in groups[0])))
        elif tier == "MAJ":
            out.append((tier, " OR ".join("(" + " AND ".join(_t(t) for t in c) + ")" for c in groups)))
        else:
            out.append((tier, " OR ".join(_t(g[0]) for g in groups)))
    return out


def search(http, query: str, cut: dt.date, cfg, funnel=None) -> list[dict]:
    """Kademeli arama. Yeterli toplam (cfg.arxiv_enough) gelince sonraki kademe koşulmaz."""
    recs: list[dict] = []
    total_seen = 0
    for tier, sq in tier_queries(query):
        cap = {"AND": cfg.arxiv_and_max, "MAJ": cfg.arxiv_majority_max, "OR": cfg.arxiv_or_max}[tier]
        full = f"({sq}) AND {date_clause(cut)}"
        got, total = _paged(http, full, cap)
        recs.extend(got)
        if funnel is not None:
            funnel.bump(f"arxiv.kademe.{tier}")
            if total == 0:
                funnel.bump(f"arxiv.kademe.{tier}=0")
            if total and total > len(got):
                funnel.bump("arxiv.api_kesilen(havuza_girmedi)", total - len(got))
        total_seen += total or 0
        if total_seen >= cfg.arxiv_enough:
            break
    return recs


def _paged(http, sq: str, cap: int) -> tuple[list[dict], int]:
    out, start, total = [], 0, None
    while start < cap:
        n = min(100, cap - start)
        r = http.get("arxiv", API, params={"search_query": sq, "start": start, "max_results": n,
                                           "sortBy": "relevance", "sortOrder": "descending"})
        recs, tot = parse_feed(r.body)
        total = tot if tot is not None else total
        out.extend(recs)
        start += n
        if not recs or (total is not None and start >= total):
            break
    return out, (total or 0)


def by_ids(http, ids: list[str]) -> list[dict]:
    out = []
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        r = http.get("arxiv", API, params={"id_list": ",".join(chunk), "max_results": len(chunk)})
        out.extend(x for x in parse_feed(r.body)[0] if "_drop" not in x)
    return out


def by_titles(http, titles: list[str]) -> list[dict]:
    """Başlık listesini birkaç başlıklık OR'lu `ti:"..."` sorgularıyla arar (aday döner;
    eşleştirme çağıranda başlık benzerliğiyle yapılır)."""
    out = []
    clean = [re.sub(r'["\\:()]', " ", t).strip() for t in titles if t and t.strip()]
    for i in range(0, len(clean), 6):
        chunk = clean[i:i + 6]
        sq = " OR ".join(f'ti:"{re.sub(r"\s+", " ", t)}"' for t in chunk)
        r = http.get("arxiv", API, params={"search_query": sq, "max_results": 30})
        out.extend(x for x in parse_feed(r.body)[0] if "_drop" not in x)
    return out


def parse_feed(body: bytes) -> tuple[list[dict], int | None]:
    root = ET.fromstring(body)
    tel = root.find("os:totalResults", NS)
    total = int(tel.text) if tel is not None and (tel.text or "").strip().isdigit() else None
    out = []
    for e in root.findall("a:entry", NS):
        eid = (e.findtext("a:id", default="", namespaces=NS) or "").strip()
        if "/api/errors" in eid:
            raise ValueError("arXiv hata: " + clean_ws(e.findtext("a:summary", "", NS)))
        title = clean_ws(e.findtext("a:title", default="", namespaces=NS))
        if not title:
            out.append({"_drop": "basliksiz"})
            continue
        aid = norm_arxiv(eid)
        pub = (e.findtext("a:published", default="", namespaces=NS) or "")[:10]
        out.append(new_record(
            "arxiv", title=title, arxiv_id=aid,
            abstract=e.findtext("a:summary", default="", namespaces=NS),
            doi=norm_doi(e.findtext("arxiv:doi", default=None, namespaces=NS)),
            dates=[list(map(int, pub.split("-")))] if len(pub) == 10 else [],
            year=int(pub[:4]) if pub[:4].isdigit() else None,
            venue=clean_ws(e.findtext("arxiv:journal_ref", default="", namespaces=NS)) or "arXiv",
            authors=[clean_ws(a.findtext("a:name", default="", namespaces=NS)) for a in e.findall("a:author", NS)],
            url=f"https://arxiv.org/abs/{aid}" if aid else eid,
        ))
    return out, total
