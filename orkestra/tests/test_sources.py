import datetime as dt
import json

import pytest

from orkestra.funnel import Funnel
from orkestra.http import BotBlocked, Http, QuotaExhausted, RequestFailed
from orkestra.sources import arxiv, crossref, dblp, openalex, s2

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:arxiv="http://arxiv.org/schemas/atom">
<opensearch:totalResults>{total}</opensearch:totalResults>
{entries}
</feed>"""
ENTRY = """<entry><id>http://arxiv.org/abs/{aid}v1</id><published>2024-01-02T00:00:00Z</published>
<title>{title}</title><summary>An abstract about {title}.</summary><author><name>A B</name></author></entry>"""


def feed(n, total=None):
    es = "".join(ENTRY.format(aid=f"2401.{i:05d}", title=f"Paper {i}") for i in range(n))
    return FEED.format(total=total if total is not None else n, entries=es).encode()


class R:
    def __init__(self, code, body=b"", headers=None):
        self.status_code, self.content, self.headers = code, body, headers or {}


class Sess:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        r = self.responses.pop(0)
        return r(kw) if callable(r) else r


def mk_http(cfg, responses):
    sleeps = []
    h = Http(cfg, session=Sess(responses), sleep=sleeps.append, cache_path=None)
    return h, sleeps


def test_underscore_kept_and_tiers():
    ts = arxiv.terms("io_uring kernel exploitation")
    assert ts == ["io_uring", "kernel", "exploitation"]
    tiers = arxiv.tier_queries("io_uring kernel exploitation")
    assert [t for t, _ in tiers] == ["AND", "MAJ", "OR"]
    assert tiers[0][1] == "all:io_uring AND all:kernel AND all:exploitation"
    assert "(all:io_uring AND all:kernel)" in tiers[1][1]
    assert arxiv.terms('"graph neural network" zero-shot')[0] == '"graph neural network"'
    assert 'all:"zero-shot"' in arxiv.tier_queries('"graph neural network" zero-shot')[0][1]


def test_date_clause():
    assert arxiv.date_clause(dt.date(2025, 6, 1)) == "submittedDate:[199101010000 TO 202505312359]"


def test_arxiv_falls_through_tiers_and_counts(cfg):
    # AND=0, MAJ=2 sonuç, OR=40 (toplam 400 → 200'de kesilir, ama 1 sayfa 100 + 2. sayfa 100)
    http, _ = mk_http(cfg, [R(200, feed(0, 0)), R(200, feed(2, 2)), R(200, feed(100, 400)), R(200, feed(100, 400))])
    f = Funnel()
    recs = arxiv.search(http, "io_uring kernel exploitation", dt.date(2025, 6, 1), cfg, f)
    assert len(recs) == 202
    assert f.info["arxiv.kademe.AND=0"] == 1 and f.info["arxiv.kademe.OR"] == 1
    assert f.info["arxiv.api_kesilen(havuza_girmedi)"] == 200
    sq = http.session.calls[0][2]["params"]["search_query"]
    assert "submittedDate" in sq and "all:io_uring" in sq


def test_arxiv_stops_when_enough(cfg):
    http, _ = mk_http(cfg, [R(200, feed(40, 40))])
    recs = arxiv.search(http, "graph neural molecule", dt.date(2025, 6, 1), cfg, Funnel())
    assert len(recs) == 40 and len(http.session.calls) == 1


def test_transient_429_is_retried_not_quota(cfg):
    http, sleeps = mk_http(cfg, [R(429), R(429), R(200, b"{}")])
    assert http.get("crossref", "u").status == 200
    assert [x for x in sleeps if x >= 5][:2] == [10.0, 30.0]  # Retry-After'sız 429: dakikalara uzanan bekleme
    assert "crossref" not in http.exhausted


def test_429_long_retry_after_is_quota(cfg):
    http, _ = mk_http(cfg, [R(429, b"", {"Retry-After": "80000"})])
    with pytest.raises(QuotaExhausted):
        http.get("openalex", "u")
    with pytest.raises(QuotaExhausted):  # sonraki çağrılar da hemen EKSİK
        http.get("openalex", "u2")


def test_429_exhausted_after_retries(cfg):
    http, _ = mk_http(cfg, [R(429)] * 10)
    with pytest.raises(QuotaExhausted):
        http.get("s2", "u")


def test_bot_wall_and_qlever_timeout(cfg):
    http, _ = mk_http(cfg, [R(200, b"<!doctype html><html><head><title>Making sure you&#39;re not a bot!</title>")])
    with pytest.raises(BotBlocked):
        http.get("dblp", "u")
    http, _ = mk_http(cfg, [R(429, b'{"exception": "Operation timed out. Last operation: Filter"}')])
    with pytest.raises(RequestFailed):
        http.get("dblp", "u")
    assert "dblp" not in http.exhausted


def test_crossref_parse_marks_drops():
    items = [{"DOI": "10.1/a", "title": ["T one"], "issued": {"date-parts": [[2020, 5]]}, "type": "journal-article",
              "is-referenced-by-count": 7},
             {"DOI": "10.1/b", "title": [], "type": "journal-article"},
             {"DOI": "10.1/c", "title": ["Dataset x"], "type": "dataset"}]
    out = [crossref.parse_item(i) for i in items]
    assert out[0]["doi"] == "10.1/a" and out[0]["dates"] == [[2020, 5]] and out[0]["citations"] == 7
    assert out[1] == {"_drop": "basliksiz"} and out[2]["_drop"].startswith("tur_disi")


def test_dblp_parse_groups_rows_and_drops_late_years():
    data = {"results": {"bindings": [
        {"p": {"value": "r1"}, "t": {"value": "Title A."}, "y": {"value": "2020"}, "ee": {"value": "https://arxiv.org/abs/2001.00001"}},
        {"p": {"value": "r1"}, "t": {"value": "Title A."}, "y": {"value": "2020"}, "ee": {"value": "https://doi.org/x"},
         "doi": {"value": "https://doi.org/10.1/A"}},
        {"p": {"value": "r2"}, "t": {"value": "Title B"}, "y": {"value": "2027"}},
    ]}}
    out = dblp.parse(data, 2025)
    assert len(out) == 2
    assert out[0]["title"] == "Title A" and out[0]["arxiv_id"] == "2001.00001" and out[0]["doi"] == "10.1/a"
    assert out[1] == {"_drop": "kesim_sonrasi(yil)"}


def test_openalex_budget_per_run_and_daily(cfg):
    cfg.openalex_nokey_per_run = 2
    b = openalex.Budget(cfg)
    b.take(); b.take()
    with pytest.raises(openalex.BudgetExhausted):
        b.take()
    cfg.openalex_nokey_per_run = 100
    cfg.openalex_nokey_daily_budget = 3
    b2 = openalex.Budget(cfg)  # yeni koşu, aynı gün: dosyadaki sayaç 2
    b2.take()
    with pytest.raises(openalex.BudgetExhausted):
        b2.take()
    cfg.openalex_api_key = "k"
    openalex.Budget(cfg).take()  # anahtar varsa tavan yok


def test_s2_parse():
    r = s2.parse_paper({"paperId": "p", "title": "X y z", "externalIds": {"ArXiv": "1704.01212", "DOI": "10.1/q"},
                        "publicationDate": "2017-04-04", "citationCount": 5, "abstract": "abs"})
    assert r["arxiv_id"] == "1704.01212" and r["doi"] == "10.1/q" and [2017, 4, 4] in r["dates"]
    assert s2.parse_paper({"title": None}) == {"_drop": "basliksiz"}
    assert s2.s2_key(r) == "ARXIV:1704.01212"


def test_concurrent_source_overlaps_serial_does_not(cfg):
    import threading, time
    from orkestra.config import SourceLimits

    def run(es):
        cfg.limits = {**getattr(cfg, "limits", {}), "oc_index": SourceLimits(min_interval_s=0.0, es_zamanli=es)}
        state = {"now": 0, "max": 0}
        lock = threading.Lock()

        def slow(kw):
            with lock:
                state["now"] += 1
                state["max"] = max(state["max"], state["now"])
            time.sleep(0.05)
            with lock:
                state["now"] -= 1
            return R(200, b"[]")

        h = Http(cfg, session=Sess([slow] * 6), sleep=lambda s: None, cache_path=None)
        ts = [threading.Thread(target=h.get, args=("oc_index", f"u{i}")) for i in range(6)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        return state["max"]

    assert run(1) == 1
    assert 1 < run(3) <= 3


def test_s2_key_header_only_when_configured(cfg):
    for key, want in (("", None), ("abc", "abc")):
        cfg.s2_api_key = key
        sess = Sess([R(200, b"[]")])
        h = Http(cfg, session=sess, sleep=lambda s: None, cache_path=None)
        s2.batch(h, ["DOI:10.1/x"])
        assert sess.calls[0][2]["headers"].get("x-api-key") == want
