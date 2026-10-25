"""Semantic Scholar Graph API (anahtarsız): toplu zenginleştirme (özet, tarih, atıf sayısı)
ve atıf takibi (referanslar + atıf yapanlar). 429'da dakikalara uzanan bekleme; sonra EKSİK."""
from __future__ import annotations

from orkestra.records import new_record

API = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,externalIds,publicationDate,year,abstract,citationCount,venue"


def s2_key(r: dict) -> str | None:
    if r.get("arxiv_id"):
        return f"ARXIV:{r['arxiv_id']}"
    if r.get("doi"):
        return f"DOI:{r['doi']}"
    return None


def parse_paper(p: dict | None) -> dict | None:
    if not p:
        return None
    if not p.get("title"):
        return {"_drop": "basliksiz"}
    ext = p.get("externalIds") or {}
    d = p.get("publicationDate")
    dates = [[int(x) for x in d.split("-")]] if d else ([[int(p["year"])]] if p.get("year") else [])
    return new_record("s2", title=p["title"], arxiv_id=ext.get("ArXiv"), doi=ext.get("DOI"),
                      abstract=p.get("abstract") or "", dates=dates, year=p.get("year"),
                      citations=p.get("citationCount"), venue=p.get("venue") or None,
                      s2_id=p.get("paperId"))


def _hdrs(http) -> dict | None:
    key = getattr(getattr(http, "cfg", None), "s2_api_key", "")
    return {"x-api-key": key} if key else None


def batch(http, keys: list[str]) -> list[dict | None]:
    """keys ile aynı sırada kayıt (bulunamayan → None)."""
    out: list[dict | None] = []
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        r = http.request("s2", f"{API}/paper/batch", method="POST", params={"fields": FIELDS},
                         json_body={"ids": chunk}, headers=_hdrs(http))
        data = r.json()
        out.extend(parse_paper(p) for p in data)
    return out


def references(http, key: str, n: int) -> list[dict]:
    r = http.get("s2", f"{API}/paper/{key}/references", params={"fields": FIELDS, "limit": min(n, 1000)},
                 headers=_hdrs(http))
    return [parse_paper(e.get("citedPaper")) or {"_drop": "bos_kayit"} for e in r.json().get("data") or []]


def citations(http, key: str, n: int) -> list[dict]:
    r = http.get("s2", f"{API}/paper/{key}/citations", params={"fields": FIELDS, "limit": min(n, 1000)},
                 headers=_hdrs(http))
    return [parse_paper(e.get("citingPaper")) or {"_drop": "bos_kayit"} for e in r.json().get("data") or []]
