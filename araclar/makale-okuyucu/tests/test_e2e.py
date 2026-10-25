"""Uçtan uca: üretilmiş PDF + sahte HTTP + mock LLM."""
import json

from makale_okuyucu.cli import main
from makale_okuyucu.config import FIELDS
from makale_okuyucu.core import Reader
from makale_okuyucu.fetch import HttpResponse
from makale_okuyucu.llm import LLMError, MockBackend
from makale_okuyucu.mockllm import default_responder
from makale_okuyucu.render import est_tokens

CF_BODY = b"<html><title>Just a moment...</title></html>"


def _reader(cfg, fake_http, pdf, responder=None):
    http = fake_http({"https://arxiv.org/pdf/": HttpResponse(200, "application/pdf", pdf)})
    llm = MockBackend(cfg, responder=responder)
    return Reader(cfg, llm=llm, getter=http), http, llm


def test_read_builds_verified_card(cfg, fake_http, paper_pdf):
    r, http, llm = _reader(cfg, fake_http, paper_pdf)
    res = r.read("2501.08156")
    assert res.status == "OK" and not res.from_cache
    card = res.card
    assert set(card["fields"]) == set(FIELDS)
    for f in ("problem", "katkilar", "ana_sonuclar", "sinirliliklar", "gelecek_calisma", "kapsam_disi"):
        assert card["fields"][f], f
    res_items = {it["quote"][:20]: it for f in FIELDS for it in card["fields"][f]}
    acc = next(it for f in FIELDS for it in card["fields"][f] if "91.2" in it["quote"])
    assert acc["check"] == "VERIFIED" and acc["page"] == "3"
    oos = card["fields"]["kapsam_disi"][0]
    assert "do not address" in oos["quote"] and oos["page"] == "2"
    # references LLM'e gitmedi
    assert all("Secret reference sentence" not in p for p in llm.prompts)
    fun = card["funnel"]
    assert fun["skipped_references"]["sections"] == 1 and fun["pages"] == 4
    assert fun["llm"]["calls"] == fun["chunks"] + (1 if fun["merge_status"] == "OK" else 0)
    assert est_tokens(res.markdown) <= cfg.md_max_tokens
    d = r.store.paper_dir(res.key)
    assert (d / "card.json").exists() and (d / "card.md").exists() and (d / "doc.json").exists()
    assert res_items


def test_second_read_uses_cache_no_llm_no_http(cfg, fake_http, paper_pdf):
    r, http, llm = _reader(cfg, fake_http, paper_pdf)
    r.read("2501.08156")
    n_http, n_llm = len(http.calls), llm.stats.calls
    res2 = r.read("arXiv:2501.08156v2")
    assert res2.from_cache and len(http.calls) == n_http and llm.stats.calls == n_llm
    runs = r.store.runs(5)
    assert runs[0]["status"] == "CACHED" and runs[0]["from_cache"] == 1


def test_local_pdf_same_bytes_hits_cache_and_aliases(cfg, fake_http, paper_pdf, tmp_path):
    r, http, llm = _reader(cfg, fake_http, paper_pdf)
    r.read("2501.08156")
    f = tmp_path / "local.pdf"
    f.write_bytes(paper_pdf)
    calls = llm.stats.calls
    res = r.read(str(f))
    assert res.from_cache and res.key == "arxiv:2501.08156" and llm.stats.calls == calls
    assert r.store.resolve(res.key) == "arxiv:2501.08156"


def test_local_pdf_with_as_key(cfg, fake_http, paper_pdf, tmp_path):
    r, http, llm = _reader(cfg, fake_http, paper_pdf)
    f = tmp_path / "local.pdf"
    f.write_bytes(paper_pdf)
    res = r.read(str(f), as_key="10.1000/abc")
    assert res.status == "OK" and res.key == "doi:10.1000/abc" and not http.calls
    assert r.read("10.1000/abc").from_cache


def test_bot_blocked_asks_for_local_pdf(cfg, fake_http):
    import json as _j
    work = {"title": "T", "locations": [], "best_oa_location": {"pdf_url": "https://pub.example/x.pdf"}}
    http = fake_http({"https://api.openalex.org/": HttpResponse(200, "application/json", _j.dumps(work).encode()),
                      "https://pub.example/": HttpResponse(403, "text/html", CF_BODY)})
    r = Reader(cfg, llm=MockBackend(cfg), getter=http)
    res = r.read("10.1000/xyz")
    assert res.status == "BOT_BLOCKED" and res.card is None
    assert "--as doi:10.1000/xyz" in res.message and r.llm.stats.calls == 0
    assert r.store.runs(1)[0]["status"] == "BOT_BLOCKED"


def test_failed_chunk_makes_partial_card(cfg, fake_http, paper_pdf):
    def responder(p, s):
        if "TASK: extract_chunk" in p and "Conclusion" in p:
            return LLMError("down")
        return default_responder(p, s)

    r, _, _ = _reader(cfg, fake_http, paper_pdf, responder)
    res = r.read("2501.08156")
    assert res.status == "PARTIAL" and res.card["eksik_parcalar"]
    assert "EKSİK OKUNDU" in res.markdown
    assert r.store.runs(1)[0]["failed_chunks"]


def test_empty_text_pdf(cfg, fake_http):
    import pymupdf
    doc = pymupdf.open()
    doc.new_page()
    pdf = doc.tobytes()
    r, _, _ = _reader(cfg, fake_http, pdf)
    assert r.read("2501.08156").status == "EMPTY_TEXT"


def test_ask_card_section_and_notfound(cfg, fake_http, paper_pdf):
    r, _, llm = _reader(cfg, fake_http, paper_pdf)
    r.read("2501.08156")
    a1 = r.ask("2501.08156", "WidgetNet achieves percent accuracy WidgetBench")
    assert a1["kaynak"] == "kart" and a1["alintilar"][0]["check"] == "VERIFIED"
    a2 = r.ask("2501.08156", "How many transformer layers does the encoder use?")
    assert a2["kaynak"] == "bolum" and a2["dogrulanmis"] and a2["alintilar"][0]["page"] == "2"
    assert "twelve" in a2["alintilar"][0]["quote"]
    assert a2["gonderilen_karakter"] <= cfg.ask_top_k * cfg.passage_chars + 200
    a3 = r.ask("2501.08156", "quantum chromodynamics lattice?")
    assert a3["kaynak"] == "bulunamadi"
    # ask önbelleği
    calls = llm.stats.calls
    again = r.ask("2501.08156", "How many transformer layers does the encoder use?")
    assert again.get("onbellek") and llm.stats.calls == calls


def test_ask_never_sends_full_text(cfg, fake_http, paper_pdf):
    r, _, llm = _reader(cfg, fake_http, paper_pdf)
    r.read("2501.08156")
    n = len(llm.prompts)
    a = r.ask("2501.08156", "How many transformer layers does the encoder use?")
    assert a["kaynak"] == "bolum"
    sec_prompts = [p for p in llm.prompts[n:] if "TASK: ask_sections" in p]
    assert sec_prompts
    doc_chars = r.store.load_card("arxiv:2501.08156")["funnel"]["chars"]
    for p in llm.prompts[n:]:
        assert "Secret reference sentence" not in p
    for p in sec_prompts:
        body = p.split("Question:")[0]
        assert len(body) < doc_chars


def test_cli_read_and_ask_mock(cfg, paper_pdf, tmp_path, capsys):
    f = tmp_path / "p.pdf"
    f.write_bytes(paper_pdf)
    dd = str(cfg.data_dir)
    assert main(["--llm", "mock", "--data-dir", dd, "read", str(f), "--as", "2501.08156"]) == 0
    out = capsys.readouterr()
    assert out.out.startswith("# ") and "LOG: key=arxiv:2501.08156" in out.err
    assert main(["--llm", "mock", "--data-dir", dd, "card", "2501.08156", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["key"] == "arxiv:2501.08156"
    assert main(["--llm", "mock", "--data-dir", dd, "ask", "2501.08156", "Which encoder and robust loss?"]) == 0
    assert json.loads(capsys.readouterr().out)["kaynak"] in ("kart", "bolum")
    assert main(["--llm", "mock", "--data-dir", dd, "runs", "-n", "3"]) == 0
    assert main(["--llm", "mock", "--data-dir", dd, "read", "not an id"]) == 1
