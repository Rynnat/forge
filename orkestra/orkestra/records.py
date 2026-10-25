"""Kayıt modeli, tarih mantığı, tekilleştirme (preprint–yayın birleştirme) ve kesim filtresi.

Kesim kuralı (kodla, gevşetilmez): bir çalışma, bilinen sürümlerinden EN AZ BİRİNİN
yayın tarihi kesimden KESİN önceyse geçer. Hiçbir sürümün tarihi karar verecek
kesinlikte değilse (ör. yalnız yıl ve yıl = kesim yılı) düşer: sebep `tarih_belirsiz`.
"""
from __future__ import annotations

import datetime as dt
import re
from difflib import SequenceMatcher
from typing import Iterable

from orkestra.normalize import arxiv_from_doi, clean_ws, norm_arxiv, norm_doi, norm_title

DateT = tuple[int, int | None, int | None]

_NEW_ARXIV = re.compile(r"^(\d{2})(\d{2})\.\d{4,5}$")
_OLD_ARXIV = re.compile(r"^[a-z\-]+(?:\.[a-z]{2})?/(\d{2})(\d{2})\d{3}$")


def new_record(source: str, **kw) -> dict:
    r = {
        "title": "", "abstract": "", "arxiv_id": None, "doi": None, "dates": [], "year": None,
        "venue": None, "authors": [], "citations": None, "sources": [source], "hits": [],
        "url": None, "s2_id": None, "openalex_id": None, "seed_refs": 0, "seed_cites": 0,
        "anchor": False, "web": False,
    }
    r.update(kw)
    r["title"] = clean_ws(r.get("title"))
    r["abstract"] = clean_ws(r.get("abstract"))
    r["doi"] = norm_doi(r.get("doi"))
    if r["doi"] and not r.get("arxiv_id"):
        r["arxiv_id"] = arxiv_from_doi(r["doi"])
    if r["doi"] and arxiv_from_doi(r["doi"]):
        r["doi"] = None  # 10.48550 arXiv DOI'si arXiv id olarak tutulur
    r["arxiv_id"] = norm_arxiv(r.get("arxiv_id"))
    if r["arxiv_id"]:
        d = arxiv_id_date(r["arxiv_id"])
        if d:
            r["dates"] = list(r["dates"]) + [d]
    return r


def parse_date(s) -> DateT | None:
    """'2024', '2024-03', '2024-03-05', [2024,3,5], 2024 -> (y, m, d)."""
    if s is None or s == "":
        return None
    if isinstance(s, int):
        return (s, None, None) if 1000 < s < 3000 else None
    if isinstance(s, (list, tuple)):
        parts = [int(x) for x in s if x is not None and str(x).strip() != ""]
    else:
        parts = [int(x) for x in re.findall(r"\d+", str(s))[:3]]
    if not parts or not (1000 < parts[0] < 3000):
        return None
    y = parts[0]
    m = parts[1] if len(parts) > 1 and 1 <= parts[1] <= 12 else None
    d = parts[2] if m and len(parts) > 2 and 1 <= parts[2] <= 31 else None
    return (y, m, d)


def arxiv_id_date(aid: str | None) -> DateT | None:
    if not aid:
        return None
    m = _NEW_ARXIV.match(aid) or _OLD_ARXIV.match(aid)
    if not m:
        return None
    yy, mm = int(m.group(1)), int(m.group(2))
    y = 2000 + yy if yy < 90 else 1900 + yy
    return (y, mm, None) if 1 <= mm <= 12 else None


def date_before(d: DateT, cut: dt.date) -> bool | None:
    """True: kesin önce; False: kesin önce değil; None: belirsiz."""
    y, m, day = (tuple(d) + (None, None))[:3]
    if y != cut.year:
        return y < cut.year
    if m is None:
        return None
    if m != cut.month:
        return m < cut.month
    if day is None:
        return False if cut.day == 1 else None
    return day < cut.day


def before_cutoff(rec: dict, cut: dt.date) -> bool | None:
    verdicts = [date_before(tuple(d), cut) for d in rec.get("dates") or []]
    if any(v is True for v in verdicts):
        return True
    if verdicts and all(v is False for v in verdicts):
        return False
    return None


def earliest(rec: dict) -> DateT | None:
    ds = [tuple(d) for d in rec.get("dates") or []]
    if not ds:
        return None
    ds = [(tuple(d) + (None, None))[:3] for d in ds]
    return min(ds, key=lambda d: (d[0], d[1] or 13, d[2] or 32))


def fmt_date(d: DateT | None) -> str:
    if not d:
        return "?"
    y, m, day = d
    return f"{y}" + (f"-{m:02d}" if m else "") + (f"-{day:02d}" if m and day else "")


def cutoff_filter(recs: list[dict], cut: dt.date) -> tuple[list[dict], dict[str, int]]:
    keep, drop = [], {"kesim_sonrasi": 0, "tarih_belirsiz": 0, "tarih_yok": 0}
    for r in recs:
        if not r.get("dates"):
            drop["tarih_yok"] += 1
            continue
        v = before_cutoff(r, cut)
        if v is True:
            keep.append(r)
        elif v is False:
            drop["kesim_sonrasi"] += 1
        else:
            drop["tarih_belirsiz"] += 1
    return keep, drop


# ------------------------------------------------------------------ tekilleştirme
def _title_key_tokens(nt: str) -> list[str]:
    toks = [t for t in nt.split() if len(t) > 3]
    return sorted(toks, key=lambda t: (-len(t), t))[:3]


def title_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _tok_set(s: str) -> frozenset[str]:
    return frozenset(t[:-1] if len(t) > 3 and t.endswith("s") else t for t in s.split())


def _jac(ta: frozenset, tb: frozenset) -> float:
    return len(ta & tb) / max(1, len(ta | tb))


def _tok_jaccard(a: str, b: str) -> float:
    """Kelime kümesi benzerliği (sondaki 's' atılarak): tek kelimesi farklı kısa başlıkların
    karakter benzerliğiyle yanlışlıkla birleşmesini önler."""
    return _jac(_tok_set(a), _tok_set(b))


class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def dedup(recs: list[dict], fuzzy: float = 0.90) -> tuple[list[dict], int]:
    """Kayıtları arXiv id / DOI / normalize başlık (≥ fuzzy benzerlik) ile birleştirir.
    Dönüş: (birleşmiş kayıtlar, birleşerek düşen kayıt sayısı)."""
    n = len(recs)
    uf = _UF(n)
    by: dict[tuple[str, str], int] = {}
    nts = [norm_title(r.get("title")) for r in recs]
    for i, r in enumerate(recs):
        keys = []
        if r.get("arxiv_id"):
            keys.append(("a", r["arxiv_id"]))
        for d in _dois(r):
            keys.append(("d", d))
        if len(nts[i]) >= 12:
            keys.append(("t", nts[i]))
        for k in keys:
            if k in by:
                uf.union(by[k], i)
            else:
                by[k] = i
    # bulanık başlık: anahtar-kelime bloklaması + SequenceMatcher.
    # Ucuz süzgeçler önce (uzunluk, kelime kümesi, çakışma), pahalı oran en son; her çift bir kez.
    blocks: dict[str, list[int]] = {}
    for i, nt in enumerate(nts):
        if len(nt) < 20:
            continue
        for tok in _title_key_tokens(nt):
            blocks.setdefault(tok, []).append(i)
    toks: dict[int, frozenset] = {}
    seen: set[tuple[int, int]] = set()
    for idx in blocks.values():
        if len(idx) > 400:  # aşırı yaygın kelime: bloklama işe yaramaz
            continue
        for a_i in range(len(idx)):
            for b_i in range(a_i + 1, len(idx)):
                a, b = idx[a_i], idx[b_i]
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                if uf.find(a) == uf.find(b):
                    continue
                na, nb = nts[a], nts[b]
                la, lb = len(na), len(nb)
                if min(la, lb) / max(la, lb) < fuzzy - 0.05:
                    continue
                ta = toks.get(a) or toks.setdefault(a, _tok_set(na))
                tb = toks.get(b) or toks.setdefault(b, _tok_set(nb))
                if _jac(ta, tb) < 0.75:
                    continue
                if _conflict(recs[a], recs[b], na, nb):
                    continue
                sm = SequenceMatcher(None, na, nb, autojunk=False)
                if sm.real_quick_ratio() >= fuzzy and sm.quick_ratio() >= fuzzy and sm.ratio() >= fuzzy:
                    uf.union(a, b)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(i)
    out = [merge([recs[i] for i in g]) for g in sorted(groups.values(), key=lambda g: g[0])]
    return out, n - len(out)


def _dois(r: dict) -> list[str]:
    ds = list(r.get("alt_dois") or [])
    if r.get("doi"):
        ds.append(r["doi"])
    return [d for d in ds if d]


_DIGITS = re.compile(r"\d+")
_ROMAN = re.compile(r"\b(?:i{1,3}|iv|v|vi{0,3}|ix|x)\b")


def _conflict(a: dict, b: dict, na: str | None = None, nb: str | None = None) -> bool:
    """Başlık benzer olsa da birleşmeyecek çiftler: farklı arXiv id'leri; başlıktaki sayılar ya da
    roma rakamları farklı ('Part I/II', 'v2/v3', '... 2019/2020')."""
    if a.get("arxiv_id") and b.get("arxiv_id") and a["arxiv_id"] != b["arxiv_id"]:
        return True
    if na is None:
        na = norm_title(a.get("title"))
    if nb is None:
        nb = norm_title(b.get("title"))
    if _DIGITS.findall(na) != _DIGITS.findall(nb):
        return True
    return _ROMAN.findall(na) != _ROMAN.findall(nb)


_SRC_PRIO = {"arxiv": 0, "crossref": 1, "openalex": 2, "s2": 3, "dblp": 4}


def merge(group: list[dict]) -> dict:
    if len(group) == 1:
        r = dict(group[0])
        r["dates"] = _uniq_dates(r.get("dates") or [])
        return r
    g = sorted(group, key=lambda r: min(_SRC_PRIO.get(s, 9) for s in r.get("sources") or ["?"]))
    out = dict(g[0])
    out["sources"] = sorted({s for r in g for s in r.get("sources") or []})
    out["hits"] = sorted({h for r in g for h in r.get("hits") or []})
    out["dates"] = _uniq_dates([d for r in g for d in r.get("dates") or []])
    out["arxiv_id"] = next((r["arxiv_id"] for r in g if r.get("arxiv_id")), None)
    dois = [d for r in g for d in _dois(r)]
    out["doi"] = next((d for d in dois if not d.startswith("10.48550")), None)
    out["alt_dois"] = sorted(set(dois) - {out["doi"]})
    out["abstract"] = max((r.get("abstract") or "" for r in g), key=len)
    out["title"] = max((r.get("title") or "" for r in g if r.get("title")), key=lambda t: (len(t) < 300, len(t)), default="")
    cits = [r["citations"] for r in g if isinstance(r.get("citations"), int)]
    out["citations"] = max(cits) if cits else None
    for k in ("venue", "url", "s2_id", "openalex_id", "year"):
        if not out.get(k):
            out[k] = next((r[k] for r in g if r.get(k)), None)
    venues = [r.get("venue") for r in g if r.get("venue") and r.get("venue") not in ("arXiv", "CoRR")]
    if venues:
        out["venue"] = venues[0]
    for k in ("seed_refs", "seed_cites"):
        out[k] = max(int(r.get(k) or 0) for r in g)
    out["seed_of"] = sorted({s for r in g for s in r.get("seed_of") or []})
    out["anchor"] = any(r.get("anchor") for r in g)
    out["web"] = any(r.get("web") for r in g)
    out["authors"] = max((r.get("authors") or [] for r in g), key=len)
    return out


def _uniq_dates(ds: Iterable) -> list[list]:
    seen, out = set(), []
    for d in ds:
        t = tuple(d)
        if t not in seen:
            seen.add(t)
            out.append(list(t))
    return out


def public_id(r: dict) -> str:
    if r.get("arxiv_id"):
        return f"arXiv:{r['arxiv_id']}"
    if r.get("doi"):
        return f"doi:{r['doi']}"
    return f"title:{norm_title(r.get('title'))[:60]}"
