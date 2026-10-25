"""Taban A koşucusu: ağsız, sahte `claude -p`."""
import json
import subprocess
from pathlib import Path

from deney import taban
from orkestra.config import Config


def _cfg(tmp_path):
    return Config(data_dir=tmp_path / "data", log_dir=tmp_path / "logs", claude_cli_path="claude")


def _wrap(result, cost=1.25, subtype="success", is_error=False):
    return json.dumps({"type": "result", "subtype": subtype, "is_error": is_error, "result": result,
                       "total_cost_usd": cost,
                       "modelUsage": {"claude-opus": {"inputTokens": 10, "outputTokens": 500,
                                                      "cacheReadInputTokens": 100, "cacheCreationInputTokens": 5,
                                                      "webSearchRequests": 7}}})


class FakeRun:
    def __init__(self, stdout, rc=0, exc=None):
        self.stdout, self.rc, self.exc, self.calls = stdout, rc, exc, []

    def __call__(self, args, **kw):
        self.calls.append((args, kw))
        if self.exc:
            raise self.exc
        return subprocess.CompletedProcess(args, self.rc, stdout=self.stdout, stderr="")


ITEMS = [{"sira": 1, "baslik": " AFLNET: A Greybox Fuzzer ", "yil": 2020, "arxiv_id": None,
          "doi": "10.1109/ICST46399.2020.00062", "gerekce": "seminal"},
         {"sira": 2, "baslik": "ProFuzzBench", "yil": 2021, "arxiv_id": "2101.05102", "doi": "null", "gerekce": "bench"},
         {"sira": 3, "baslik": "Made up", "yil": "2019", "arxiv_id": "arXiv:9999.bad", "doi": "", "gerekce": "x"}]


def _sorular(tmp_path):
    p = tmp_path / "sorular.json"
    p.write_text(json.dumps([{"id": "D2-x", "soru": "What about fuzzing?", "kesim": "2025-06-01"}]), encoding="utf-8")
    return p


def test_batch_cikti_ve_maliyet(tmp_path):
    text = "Here is the list:\n```json\n" + json.dumps({"calismalar": ITEMS}) + "\n```"
    run = FakeRun(_wrap(text))
    cfg = _cfg(tmp_path)
    rows = taban.batch(_sorular(tmp_path), tmp_path / "out", k=2, cfg=cfg, tavan=2.5, runner=run)
    assert [r["k"] for r in rows] == [1, 2] and all(r["durum"] == "OK" for r in rows)
    d = tmp_path / "out" / "D2-x" / "k1"
    s = json.loads((d / "sonuc.json").read_text(encoding="utf-8"))
    assert (d / "ham_metin.txt").read_text(encoding="utf-8") == text
    assert json.loads((d / "ham_cikti.json").read_text(encoding="utf-8"))["result"] == text
    assert s["maliyet_usd"] == 1.25 and s["web_arama"] == 7 and s["durum"] == "OK"
    c = s["calismalar"]
    # kimlikler olduğu gibi: büyük harf DOI ve bozuk arXiv korunur, yalnız boşluk/null temizlenir
    assert c[0]["doi"] == "10.1109/ICST46399.2020.00062" and c[0]["baslik"] == "AFLNET: A Greybox Fuzzer"
    assert c[0]["id"] == "doi:10.1109/icst46399.2020.00062"
    assert c[1]["doi"] is None and c[1]["id"] == "arXiv:2101.05102"
    assert c[2]["arxiv_id"] == "arXiv:9999.bad" and c[2]["doi"] is None and c[2]["yil"] == "2019"
    assert set(c[0]) == {"sira", "id", "arxiv_id", "doi", "baslik", "yil", "gerekce"}
    assert s["gecerli_gorunen_kimlik"] == 2
    # istem: soru + kesim kuralı aynen, orkestra ipucu yok
    prompt = run.calls[0][1]["input"]
    assert "What about fuzzing?" in prompt and "Cutoff date: 2025-06-01. Only works published BEFORE this date count." in prompt
    assert "orkestra" not in prompt.lower()
    # CLI: opus, yalnız web araçları, tavan, boş cwd, ayar/MCP yok
    args, kw = run.calls[0]
    assert args[args.index("--model") + 1] == "opus"
    assert args[args.index("--tools") + 1] == "WebSearch,WebFetch"
    assert args[args.index("--allowedTools") + 1] == "WebSearch,WebFetch"
    assert args[args.index("--max-budget-usd") + 1] == "2.50"
    assert args[args.index("--setting-sources") + 1] == "" and "--strict-mcp-config" in args
    assert "--system-prompt" not in args and "CLAUDECODE" not in kw["env"]
    assert Path(kw["cwd"]).parent == cfg.data_dir / "taban_cwd"
    # maliyet logu
    logs = [json.loads(x) for x in cfg.cost_log.read_text(encoding="utf-8").splitlines()]
    assert len(logs) == 2 and all(x["asama"] == "taban" and x["llm"]["cost_usd"] == 1.25 for x in logs)
    assert json.loads((tmp_path / "out" / "batch_ozet.json").read_text(encoding="utf-8"))[1]["n"] == 3


def test_otuzdan_fazla_kesilir_liste_bicimi_de_olur():
    cal, st, n = taban.calismalar_coz(json.dumps([{"baslik": f"t{i}"} for i in range(35)]))
    assert st == "OK" and n == 35 and len(cal) == 30 and cal[29]["sira"] == 30 and cal[0]["id"] is None


def test_parse_fail_ve_butce(tmp_path):
    cfg = _cfg(tmp_path)
    s = taban.kos("q", "2025-06-01", tmp_path / "a", cfg=cfg, ledger=taban.Ledger(cfg.cost_log), tavan=1,
                  run_id="r1", runner=FakeRun(_wrap("Sorry, no JSON here.")))
    assert s["durum"] == "PARSE_FAIL" and s["calismalar"] == [] and s["maliyet_usd"] == 1.25
    s = taban.kos("q", "2025-06-01", tmp_path / "b", cfg=cfg, ledger=taban.Ledger(cfg.cost_log), tavan=1,
                  run_id="r2", runner=FakeRun(_wrap("", cost=1.02, subtype="error_max_budget_usd", is_error=True)))
    assert s["durum"] == "BUTCE" and s["maliyet_usd"] == 1.02
    logs = [json.loads(x) for x in cfg.cost_log.read_text(encoding="utf-8").splitlines()]
    assert logs[-1]["llm"]["failed"] == 1 and logs[-1]["llm"]["cost_usd"] == 1.02


def test_cli_cokmesi_ve_zaman_asimi(tmp_path):
    cfg = _cfg(tmp_path)
    led = taban.Ledger(cfg.cost_log)
    s = taban.kos("q", "2025-06-01", tmp_path / "a", cfg=cfg, ledger=led, tavan=1, run_id="r1",
                  runner=FakeRun("not json", rc=1))
    assert s["durum"] == "HATA" and "çıkış 1" in s["hata"]
    s = taban.kos("q", "2025-06-01", tmp_path / "b", cfg=cfg, ledger=led, tavan=1, run_id="r2",
                  runner=FakeRun("", exc=subprocess.TimeoutExpired("claude", 5)))
    assert s["durum"] == "HATA" and "zaman aşımı" in s["hata"]


def test_toplam_tavan_atlar(tmp_path):
    p = tmp_path / "s.json"
    p.write_text(json.dumps([{"id": i, "soru": "q", "kesim": "2025-06-01"} for i in ("a", "b", "c")]), encoding="utf-8")
    run = FakeRun(_wrap(json.dumps({"calismalar": ITEMS}), cost=1.25))
    rows = taban.batch(p, tmp_path / "o", cfg=_cfg(tmp_path), tavan=1.0, toplam_tavan=2.6, runner=run)
    assert [r["durum"] for r in rows] == ["OK", "OK", "ATLANDI"] and len(run.calls) == 2
