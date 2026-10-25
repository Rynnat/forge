import datetime as dt
import json

from conftest import mock_responder, rec

from orkestra import reader
from orkestra.funnel import Funnel
from orkestra.http import QuotaExhausted
from orkestra.llm import Ledger, MockLLM, usage_from_wrap
from orkestra.pipeline import run
from orkestra.sources.openalex import BudgetExhausted

SUBS = [{"id": "S1", "soru": "gnn molecules", "sorgular": ["gnn"]}]


def test_reader_drops_only_certain_irrelevant(cfg):
    recs = [rec("Graph networks for molecules", abstract="We study message passing networks on molecular graphs."),
            rec("A cooking recipe collection", abstract="Pasta with tomato."),
            rec("maybe related thing", abstract="Unclear text about stuff.")]
    llm = MockLLM(mock_responder)
    f = Funnel()
    reader.screen(llm, cfg, "q", SUBS, recs, f)
    keep, n = reader.drop_certain(recs)
    assert n == 1 and [r["title"] for r in keep] == ["Graph networks for molecules", "maybe related thing"]
    assert keep[0]["alinti"] and keep[0]["alinti_durum"] == "VERIFIED"
    assert keep[1]["rel"] == 0 and not keep[1]["kesin"]  # şüpheli → yukarı


def test_reader_parse_fail_keeps_everything(cfg):
    recs = [rec(f"Paper {i}", abstract="text") for i in range(5)]
    llm = MockLLM(lambda p, s: "not json at all")
    f = Funnel()
    reader.screen(llm, cfg, "q", SUBS, recs, f)
    keep, n = reader.drop_certain(recs)
    assert n == 0 and len(keep) == 5 and all(r["rel"] is None for r in keep)
    assert f.info["okuyucu.cevapsiz(yukari_cikti)"] == 5


def test_reader_rejects_fabricated_quote(cfg):
    recs = [rec("Graph networks", abstract="We study message passing networks on molecular graphs.")]
    llm = MockLLM(lambda p, s: json.dumps({"items": [{"id": "0", "rel": 3, "kesin": False, "alt": [],
                                                     "alinti": "this sentence does not appear anywhere in it", "not": ""}]}))
    f = Funnel()
    reader.screen(llm, cfg, "q", SUBS, recs, f)
    assert recs[0]["alinti"] == "" and recs[0]["alinti_durum"] == "UNVERIFIED"
    assert f.info["okuyucu.alinti_UNVERIFIED"] == 1


def test_usage_from_wrap_uses_model_usage():
    u = usage_from_wrap({"total_cost_usd": 0.0126, "usage": {"input_tokens": 4},
                         "modelUsage": {"claude-haiku-5-5": {"inputTokens": 14019, "outputTokens": 1116,
                                                             "cacheReadInputTokens": 2150, "cacheCreationInputTokens": 3385,
                                                             "webSearchRequests": 1}}})
    assert u.input_tokens == 14019 and u.web_search == 1 and abs(u.cost_usd - 0.0126) < 1e-9


# ------------------------------------------------------------------ uçtan uca (ağsız)
def _pool():
    good = [rec(f"Graph neural network molecule study {i}", abstract=f"We study graph neural networks for molecule property {i}. Results are strong.",
                dates=[[2019 + i % 5, 3, 1]], citations=i * 3) for i in range(40)]
    late = [rec(f"Graph neural network molecule late {i}", src="crossref", doi=f"10.9/late{i}", dates=[[2025, 9, 1]]) for i in range(5)]
    cook = [rec(f"Cooking with molecules {i}", abstract="A cooking recipe.", dates=[[2020, 1, 1]]) for i in range(5)]
    return good, late, cook


class FakeOC:
    """İki tohum için: ortak bir referans, biri kesim sonrası atıf yapan, biri metasız."""

    def references(self, doi):
        return ["10.7/common", f"10.7/ref-{doi[-6:]}"]

    def citations(self, doi):
        return [("10.7/citer-early", "2024-02-01"), ("10.7/citer-late", "2025-09-01")]

    def metadata(self, dois):
        out = {d: {"title": f"Linked work {d}", "pub_date": "2018-05-01"} for d in dois if d != "10.7/citer-early"}
        return out


def _inject(fail=None):
    good, late, cook = _pool()
    dup = [dict(good[0], sources=["crossref"], doi="10.5/dup")]  # preprint–yayın eşi

    def searcher(name, recs):
        def fn(q):
            if fail and name in fail:
                raise fail[name]
            return [dict(r) for r in recs]
        return fn

    return dict(
        searchers={"arxiv": searcher("arxiv", good[:30] + cook),
                   "crossref": searcher("crossref", good[25:] + late + dup + [{"_drop": "basliksiz"}]),
                   "dblp": searcher("dblp", []),
                   "openalex": searcher("openalex", [])},
        resolver=lambda items, label: ([dict(rec(it["baslik"], abstract="Seminal message passing work.", dates=[[2017, 4, 4]]),
                                             anchor=True) for it in items] if label == "sef_capa" else [], {}),
        enricher=lambda keys: [None] * len(keys),
        snowballer=FakeOC(),
        web_runner=lambda plan: [],
    )


def test_pipeline_end_to_end_funnel_balanced(cfg, tmp_path):
    llm = MockLLM(mock_responder, Ledger(cfg.cost_log))
    s = run("Which GNN methods predict molecular properties?", "2025-06-01", tmp_path / "out", cfg, llm=llm, **_inject())
    assert s["funnel_dengeli"] is True
    fd = json.loads((tmp_path / "out" / "funnel.json").read_text(encoding="utf-8"))
    for st in fd["asamalar"]:
        assert st["giren"] == st["cikan"] + sum(st["dusen"].values()), st
    names = [st["asama"] for st in fd["asamalar"]]
    for n in ("toplama:arxiv", "toplama:crossref", "tekillestirme_1", "kesim_1", "toplama:atif", "kesim_2",
              "okuyucu_kesimi", "okuyucu", "damitma", "sef_final"):
        assert n in names
    kesim = next(st for st in fd["asamalar"] if st["asama"] == "kesim_1")
    assert kesim["dusen"]["kesim_sonrasi"] == 5
    okuyucu = next(st for st in fd["asamalar"] if st["asama"] == "okuyucu")
    assert okuyucu["dusen"].get("kesin_alakasiz") == 5
    top = next(st for st in fd["asamalar"] if st["asama"] == "toplama:crossref")
    assert top["dusen"] == {"basliksiz": 3}  # 3 sorgu × 1 başlıksız kayıt
    assert len(s["calismalar"]) == cfg.final_n
    cut = dt.date(2025, 6, 1)
    for x in s["calismalar"]:
        assert x["tarih"] < "2025-06" and x["gerekce"]
        assert x["alinti_durum"] in ("VERIFIED", "OZET_YOK", "YOK")
    assert all(x["alinti_durum"] == "VERIFIED" for x in s["calismalar"])
    assert s["durum"] == "OK" and s["ozet_token_tahmini"] <= cfg.ozet_token_cap
    assert (tmp_path / "out" / "ozet.md").exists()
    log = (cfg.cost_log).read_text(encoding="utf-8").splitlines()
    assert log and all("llm" in json.loads(x) for x in log)
    assert {json.loads(x)["asama"] for x in log} >= {"sef_plan", "okuyucu", "sef_final"}


def test_pipeline_eksik_on_quota_and_budget(cfg, tmp_path):
    llm = MockLLM(mock_responder)
    inj = _inject(fail={"arxiv": QuotaExhausted("arxiv", 429, "Retry-After=80000s"),
                        "openalex": BudgetExhausted("günlük anahtarsız bütçe doldu")})
    s = run("q about gnn molecules", "2025-06-01", tmp_path / "o", cfg, llm=llm, **inj)
    assert s["durum"] == "EKSİK"
    assert set(s["eksik_kaynaklar"]) >= {"arxiv", "openalex"}
    assert s["funnel_dengeli"]
    assert "EKSİK" in (tmp_path / "o" / "ozet.md").read_text(encoding="utf-8")


def test_pipeline_chef_failure_falls_back_and_flags(cfg, tmp_path):
    def resp(p, stage):
        if stage == "sef_final":
            return "garbage"
        return mock_responder(p, stage)
    s = run("q about gnn molecules", "2025-06-01", tmp_path / "o", cfg, llm=MockLLM(resp), **_inject())
    assert "sef_final" in s["eksik_kaynaklar"]
    assert len(s["calismalar"]) == cfg.final_n
    assert all(x["gerekce_kokeni"] == "damitici" for x in s["calismalar"])


def test_pipeline_plan_failure_uses_question(cfg, tmp_path):
    def resp(p, stage):
        if stage == "sef_plan":
            return Exception("boom")
        return mock_responder(p, stage)
    s = run("graph neural network molecule", "2025-06-01", tmp_path / "o", cfg, llm=MockLLM(resp), **_inject())
    assert "sef_plan" in s["eksik_kaynaklar"] and s["funnel_dengeli"]


def test_ozet_token_cap_enforced(cfg, tmp_path):
    cfg.ozet_token_cap = 900
    s = run("q about gnn molecules", "2025-06-01", tmp_path / "o", cfg, llm=MockLLM(mock_responder), **_inject())
    assert s["ozet_token_tahmini"] <= 900


def test_snowball_stage_accounting(cfg, tmp_path):
    s = run("q about gnn molecules", "2025-06-01", tmp_path / "o", cfg, llm=MockLLM(mock_responder), **_inject())
    fd = json.loads((tmp_path / "o" / "funnel.json").read_text(encoding="utf-8"))
    st = next(x for x in fd["asamalar"] if x["asama"] == "toplama:atif")
    assert st["dusen"]["atif_yapan_kesim_sonrasi"] == 1  # 2025-09 atıf yapan
    assert st["dusen"]["meta_yok"] == 1
    assert st["giren"] == st["cikan"] + sum(st["dusen"].values())
    assert s["tohumlar"]
