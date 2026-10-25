from makale_okuyucu.config import FIELDS
from makale_okuyucu.render import est_tokens, render


def _card(n_items=8, qlen=250):
    fields = {f: [{"id": f"{f}{i}", "text": f"Item {i} of {f} with a reasonably long claim text about things",
                   "quote": "q" * qlen, "page": str(i + 1), "check": "VERIFIED" if i else "UNVERIFIED"}
                  for i in range(n_items)] for f in FIELDS}
    fields["veri_setleri_ve_kaynaklar"][0].update(name="WidgetBench", link="https://x.org")
    return {"key": "arxiv:1", "title": "T", "pages": 9, "status": "OK", "fields": fields,
            "eksik_parcalar": [{"bolumler": ["results"], "sayfalar": "5-6", "durum": "LLM_ERROR"}],
            "funnel": {"items_in_card": 80, "unverified_in_card": 10}}


def test_small_card_keeps_quotes_and_flags():
    md = render(_card(n_items=1, qlen=60), 1500)
    assert '"qqqq' in md and "[UNVERIFIED]" in md and "EKSİK OKUNDU" in md
    assert "**WidgetBench** <https://x.org>" in md


def test_big_card_within_budget_and_reports_drops():
    md = render(_card(), 1500)
    assert est_tokens(md) <= 1500
    assert "JSON'da" in md


def test_empty_field_marked():
    c = _card(n_items=1)
    c["fields"]["kapsam_disi"] = []
    assert "## Kapsam dışı\n- (kartta yok)" in render(c, 1500)
