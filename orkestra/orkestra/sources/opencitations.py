"""OpenCitations (anahtarsız): atıf takibi.

  Index v2  /references/doi:X  → tohumun kaynakçası (DOI'ler)
            /citations/doi:X   → tohumu atıf yapanlar (DOI + `creation` tarihi)
  Meta v1   /metadata/doi:A__doi:B__...  → başlık + yayın tarihi (özet YOK)

Gözlem (2026-10-25): arXiv DataCite DOI'lerinin (10.48550) kaynakçası yok (0 referans), ama
atıf yapanları var. Bu yüzden tohumun dergi/konferans DOI'si varsa referanslar ondan alınır.
"""
from __future__ import annotations

import datetime as dt
import re

from orkestra.normalize import norm_doi
from orkestra.records import new_record, parse_date

INDEX = "https://api.opencitations.net/index/v2"
META = "https://api.opencitations.net/meta/v1/metadata"
_DOI = re.compile(r"doi:(\S+)")


def _doi_of(field: str) -> str | None:
    m = _DOI.search(field or "")
    return norm_doi(m.group(1)) if m else None


def seed_dois(r: dict) -> list[str]:
    out = []
    if r.get("doi"):
        out.append(r["doi"])
    if r.get("arxiv_id"):
        out.append(f"10.48550/arxiv.{r['arxiv_id']}")
    return out


def references(http, doi: str) -> list[str]:
    data = http.get("oc_index", f"{INDEX}/references/doi:{doi}").json()
    return [d for d in (_doi_of(x.get("cited", "")) for x in data) if d]


def citations(http, doi: str) -> list[tuple[str, str]]:
    """[(atıf yapan DOI, creation)]"""
    data = http.get("oc_index", f"{INDEX}/citations/doi:{doi}").json()
    return [(d, x.get("creation") or "") for x in data if (d := _doi_of(x.get("citing", "")))]


def created_before(creation: str, cut: dt.date) -> bool | None:
    d = parse_date(creation)
    if not d:
        return None
    y, m, day = d
    if y != cut.year:
        return y < cut.year
    if m is None:
        return None
    if m != cut.month:
        return m < cut.month
    if day is None:
        return False if cut.day == 1 else None
    return day < cut.day


def metadata(http, dois: list[str], batch: int = 40) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(dois), batch):
        chunk = dois[i:i + batch]
        data = http.get("oc_meta", f"{META}/" + "__".join(f"doi:{d}" for d in chunk)).json()
        for x in data:
            ids = x.get("id", "")
            title = (x.get("title") or "").strip().strip('"').strip()
            for d in re.findall(r"doi:(\S+)", ids):
                out[norm_doi(d)] = {"title": title, "pub_date": x.get("pub_date") or "",
                                    "venue": re.sub(r"\s*\[.*?\]", "", x.get("venue") or "") or None}
    return out


def to_record(doi: str, meta: dict) -> dict | None:
    if not meta or not meta.get("title"):
        return None
    d = parse_date(meta.get("pub_date"))
    return new_record("atif", title=meta["title"], doi=doi, dates=[list(d)] if d else [],
                      year=d[0] if d else None, venue=meta.get("venue"))
