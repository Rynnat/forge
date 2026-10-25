"""Canlı sözleşme testleri: her kaynağa 1 küçük gerçek sorgu. Koşmak için:
    python -m pytest -m live
Kota/bot durumu sözleşme ihlali değil, dürüst durumdur: o zaman test `skip` eder ve sebebi yazar
(sessizce geçmez)."""
import datetime as dt

import pytest

from orkestra.http import BotBlocked, Http, QuotaExhausted
from orkestra.sources import arxiv, crossref, dblp, openalex, s2

pytestmark = pytest.mark.live
CUT = dt.date(2025, 6, 1)


@pytest.fixture
def http(cfg):
    return Http(cfg, cache_path=None)


def _guard(fn):
    try:
        return fn()
    except (QuotaExhausted, BotBlocked, openalex.BudgetExhausted) as exc:
        pytest.skip(f"EKSİK (kota/bot/bütçe): {exc}")


def test_live_arxiv_underscore(http, cfg):
    recs = _guard(lambda: arxiv.search(http, "io_uring", CUT, cfg))
    assert recs and all("_drop" not in r for r in recs)
    assert any("io_uring" in (r["title"] + r["abstract"]).lower() for r in recs)
    assert all(r["dates"] and tuple(r["dates"][0][:2]) < (2025, 6) for r in recs)


def test_live_crossref(http, cfg):
    recs = [r for r in _guard(lambda: crossref.search(http, "message passing quantum chemistry", CUT, cfg)) if "_drop" not in r]
    assert recs and all(r["doi"] for r in recs)


def test_live_dblp_sparql(http, cfg):
    recs = [r for r in _guard(lambda: dblp.search(http, "io_uring", CUT, cfg)) if "_drop" not in r]
    assert recs and all(r["year"] <= 2025 for r in recs)


def test_live_openalex(http, cfg):
    b = openalex.Budget(cfg)
    recs = [r for r in _guard(lambda: openalex.search(http, "graph neural network molecular property", CUT, cfg, b))
            if "_drop" not in r]
    assert recs and all(r["dates"] for r in recs)


def test_live_s2_batch_and_refs(http, cfg):
    got = _guard(lambda: s2.batch(http, ["ARXIV:1704.01212"]))
    assert got[0] and "message passing" in got[0]["title"].lower()
    refs = _guard(lambda: s2.references(http, "ARXIV:1704.01212", 20))
    assert len([r for r in refs if "_drop" not in r]) >= 5


def test_live_claude_haiku_json(cfg):
    from orkestra.llm import LLM, Ledger, call_json
    ledger = Ledger(cfg.cost_log)
    obj, st = call_json(LLM(cfg, ledger), 'Reply with {"ok": true}', model=cfg.isci_model, stage="canli_test")
    assert st == "OK" and obj.get("ok") is True
    assert ledger.total > 0


def test_live_opencitations(http, cfg):
    from orkestra.sources import opencitations as oc
    refs = _guard(lambda: oc.references(http, "10.1145/3292500.3330675"))
    assert len(refs) >= 5
    meta = _guard(lambda: oc.metadata(http, ["10.1038/nature14539"]))
    assert meta["10.1038/nature14539"]["title"].lower() == "deep learning"
