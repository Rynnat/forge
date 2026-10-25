"""OpenAlex /works araması + atıf takibi yardımcıları.

Anahtar varsa kullanılır. Anahtarsız kullanımda iki tavan var:
  * koşu başına `openalex_nokey_per_run` istek,
  * gün başına `openalex_nokey_daily_budget` istek (data/openalex_butce.json, kalıcı).
Tavana gelince `BudgetExhausted` fırlatılır → çağıran EKSİK işaretler (sessiz kayıp yok).
"""
from __future__ import annotations

import datetime as dt
import json
import threading
from pathlib import Path

from orkestra.normalize import arxiv_from_doi, inverted_index_to_text, norm_arxiv
from orkestra.records import new_record

API = "https://api.openalex.org/works"
SELECT = ",".join(["id", "doi", "display_name", "publication_date", "publication_year",
                   "abstract_inverted_index", "primary_location", "locations", "cited_by_count",
                   "authorships"])


class BudgetExhausted(Exception):
    pass


class Budget:
    def __init__(self, cfg, path: Path | None = None):
        self.cfg = cfg
        self.keyed = bool(cfg.openalex_api_key)
        self.path = path or Path(cfg.data_dir) / "openalex_butce.json"
        self.lock = threading.Lock()
        self.run_used = 0

    def take(self) -> None:
        if self.keyed:
            return
        with self.lock:
            if self.run_used >= self.cfg.openalex_nokey_per_run:
                raise BudgetExhausted(f"koşu başı anahtarsız tavan ({self.cfg.openalex_nokey_per_run}) doldu")
            today = dt.date.today().isoformat()
            data = {}
            if self.path.exists():
                try:
                    data = json.loads(self.path.read_text(encoding="utf-8"))
                except ValueError:
                    data = {}
            used = data.get(today, 0)
            if used >= self.cfg.openalex_nokey_daily_budget:
                raise BudgetExhausted(f"günlük anahtarsız bütçe ({self.cfg.openalex_nokey_daily_budget}) doldu")
            data = {today: used + 1}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(data), encoding="utf-8")
            self.run_used += 1


def _params(cfg, extra: dict) -> dict:
    p = dict(extra)
    if cfg.openalex_api_key:
        p["api_key"] = cfg.openalex_api_key
    if cfg.openalex_mailto:
        p["mailto"] = cfg.openalex_mailto
    return p


def parse_work(w: dict) -> dict | None:
    title = w.get("display_name") or ""
    if not title:
        return {"_drop": "basliksiz"}
    doi = w.get("doi")
    arx = arxiv_from_doi(doi)
    if not arx:
        for loc in w.get("locations") or []:
            land = (loc or {}).get("landing_page_url") or ""
            if "arxiv.org/abs/" in land:
                arx = norm_arxiv(land)
                break
    d = w.get("publication_date") or w.get("publication_year")
    prim = w.get("primary_location") or {}
    return new_record(
        "openalex", title=title, doi=doi, arxiv_id=arx,
        abstract=inverted_index_to_text(w.get("abstract_inverted_index")),
        dates=[[int(x) for x in str(d).split("-")]] if d else [],
        year=w.get("publication_year"), venue=((prim.get("source") or {}) or {}).get("display_name"),
        citations=w.get("cited_by_count"), openalex_id=str(w.get("id", "")).rsplit("/", 1)[-1],
        authors=[((a or {}).get("author") or {}).get("display_name") for a in (w.get("authorships") or [])][:20],
        url=prim.get("landing_page_url") or w.get("id"),
    )


def search(http, query: str, cut: dt.date, cfg, budget: Budget) -> list[dict]:
    last = cut - dt.timedelta(days=1)
    budget.take()
    data = http.get("openalex", API, params=_params(cfg, {
        "search": query, "per-page": cfg.openalex_per_page, "select": SELECT,
        "filter": f"to_publication_date:{last:%Y-%m-%d}"})).json()
    return [parse_work(w) for w in data.get("results") or []]


def citing(http, wid: str, cut: dt.date, cfg, budget: Budget, n: int) -> list[dict]:
    """Tohumu atıf yapanlar, kesim öncesi, en çok atıf alanlar önce."""
    last = cut - dt.timedelta(days=1)
    budget.take()
    data = http.get("openalex", API, params=_params(cfg, {
        "filter": f"cites:{wid},to_publication_date:{last:%Y-%m-%d}", "sort": "cited_by_count:desc",
        "per-page": min(200, n), "select": SELECT})).json()
    return [parse_work(w) for w in data.get("results") or []]
