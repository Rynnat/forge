import json

from deney import sadakat as S
from orkestra.http import HttpError
from orkestra.llm import Ledger, MockLLM


class FakeHttp:
    def __init__(self, fn):
        self.fn = fn

    def request(self, source, url, params=None, **kw):
        return self.fn(source, url, params)


class R:
    def __init__(self, body):
        self.body = body if isinstance(body, bytes) else body.encode()

    def json(self):
        return json.loads(self.body)


def atom(title):
    return f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>{title}</title></entry></feed>'


def mk(tmp, n=6):
    cs = [{"sira": i, "id": f"arXiv:2101.0000{i}", "arxiv_id": f"2101.0000{i}", "doi": None,
           "baslik": f"Paper {i} on graphs", "yil": 2021, "gerekce": f"claim {i}"} for i in range(n)]
    p = tmp / "s.json"
    p.write_text(json.dumps({"run_id": "r", "calismalar": cs}), encoding="utf-8")
    return p


def test_wilson():
    assert abs(S.wilson_lower(28, 30) - 0.79) < 0.01
    assert S.wilson_lower(0, 0) == 0.0


def test_sample_fixed_seed(tmp_path):
    cl = S.load_claims([mk(tmp_path)])
    a = [c["sira"] for c in S.sample(cl, 3, 1)]
    assert a == [c["sira"] for c in S.sample(cl, 3, 1)] and len(a) == 3
    assert len(S.sample(cl, 99, 1)) == 6


def test_exist_check():
    c = {"arxiv_id": "2101.00001", "doi": None, "baslik": "Paper 1 on graphs"}
    assert S.exist_check(FakeHttp(lambda s, u, p: R(atom("Paper 1 on graphs"))), c)["durum"] == "ESLESTI"
    assert S.exist_check(FakeHttp(lambda s, u, p: R(atom("Totally other"))), c)["durum"] == "BASLIK_UYUSMUYOR"
    assert S.exist_check(FakeHttp(lambda s, u, p: R('<feed xmlns="http://www.w3.org/2005/Atom"/>')), c)["durum"] == "YOK"

    def boom(s, u, p):
        raise HttpError("crossref", 404, "nf")
    assert S.exist_check(FakeHttp(boom), {"arxiv_id": None, "doi": "10.1/x", "baslik": "t"})["durum"] == "BILINMIYOR"
    assert S.exist_check(FakeHttp(boom), {"baslik": "t"})["durum"] == "KIMLIK_YOK"


def test_run_conservative(tmp_path, cfg):
    p = mk(tmp_path)
    seen = []

    def resp(prompt, stage):
        seen.append((stage, prompt))
        if '"claim 0"' in prompt:
            return json.dumps({"karar": "UYDURMA", "var_mi": False, "kanit_alinti": "", "url": "u", "not": "n"})
        if '"claim 1"' in prompt:
            return "not json"
        if '"claim 2"' in prompt:
            return json.dumps({"karar": "KONTROL_EDILEMEDI", "url": ""})
        if '"claim 3"' in prompt:
            return json.dumps({"karar": "BOGUS"})
        return json.dumps({"karar": "DESTEKLENIYOR", "var_mi": True, "kanit_alinti": "q", "url": "u", "not": "ok"})
    llm = MockLLM(resp, Ledger(cfg.cost_log, "t"))
    http = FakeHttp(lambda s, u, pr: R(atom("Paper %s on graphs" % pr["id_list"][-1])))
    s = S.run(cfg, [p], tmp_path / "o", n=6, seed=3, llm=llm, http=http)
    assert s["n"] == 6 and s["uydurma"] == 1
    assert s["destekleniyor"] == "2/6" and s["sayim"]["KONTROL_EDILEMEDI"] == 3
    assert s["sonuc"].startswith("PILOT")
    assert all(st == "sadakat" for st, _ in seen)
    assert any("ESLESTI" in pr for _, pr in seen)
    d = json.loads((tmp_path / "o" / "sadakat.json").read_text(encoding="utf-8"))
    assert len(d["iddialar"]) == 6 and d["ozet"]["seed"] == 3
    assert "sadakat" in cfg.cost_log.read_text(encoding="utf-8")


def test_full_pass_fail():
    ok = [{"karar": "DESTEKLENIYOR"}] * 30
    assert S.summarize(ok, 30, 1, 30)["sonuc"] == "GECTI"
    assert S.summarize([{"karar": "DESTEKLENIYOR"}] * 29 + [{"karar": "UYDURMA"}], 30, 1, 30)["sonuc"] == "KALDI"
    assert S.summarize([{"karar": "DESTEKLENIYOR"}] * 27 + [{"karar": "KONTROL_EDILEMEDI"}] * 3, 30, 1, 30)["sonuc"] == "KALDI"
