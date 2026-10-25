"""Crossref /works: anahtarsız. Kesim, sunucuda `until-pub-date` ile de daraltılır."""
from __future__ import annotations

import datetime as dt
import re

from orkestra.records import new_record

API = "https://api.crossref.org/works"
SELECT = "DOI,title,issued,published,published-print,published-online,abstract,container-title,is-referenced-by-count,type,author"
SKIP_TYPES = {"component", "dataset", "peer-review", "grant", "journal-issue", "journal", "proceedings",
              "book-series", "standard", "report-series"}


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


def parse_item(it: dict) -> dict | None:
    title = " ".join(it.get("title") or [])
    if not title:
        return {"_drop": "basliksiz"}
    if it.get("type") in SKIP_TYPES:
        return {"_drop": "tur_disi:" + str(it.get("type"))}
    dates = []
    for k in ("published-print", "published-online", "issued", "published"):
        dp = ((it.get(k) or {}).get("date-parts") or [[None]])[0]
        if dp and dp[0]:
            dates.append([x for x in dp if x is not None])
    auth = [" ".join(x for x in (a.get("given"), a.get("family")) if x) for a in it.get("author") or []]
    return new_record(
        "crossref", title=title, doi=it.get("DOI"), abstract=_strip_tags(it.get("abstract") or ""),
        dates=dates, year=dates[0][0] if dates else None,
        venue=(it.get("container-title") or [None])[0], authors=auth[:20],
        citations=it.get("is-referenced-by-count"), url=f"https://doi.org/{it.get('DOI')}",
    )


def search(http, query: str, cut: dt.date, cfg) -> list[dict]:
    last = cut - dt.timedelta(days=1)
    params = {"query.bibliographic": query, "rows": cfg.crossref_rows, "select": SELECT,
              "filter": f"until-pub-date:{last:%Y-%m-%d}"}
    if cfg.crossref_mailto:
        params["mailto"] = cfg.crossref_mailto
    data = http.get("crossref", API, params=params).json()
    return [parse_item(it) for it in data["message"]["items"]]


def by_doi(http, doi: str, cfg) -> dict | None:
    data = http.get("crossref", f"{API}/{doi}").json()
    r = parse_item(data["message"])
    return None if "_drop" in r else r


def by_title(http, title: str, cfg, rows: int = 3) -> list[dict]:
    params = {"query.bibliographic": title, "rows": rows, "select": SELECT}
    data = http.get("crossref", API, params=params).json()
    return [r for r in (parse_item(it) for it in data["message"]["items"]) if "_drop" not in r]
