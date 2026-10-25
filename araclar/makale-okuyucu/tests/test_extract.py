import json

from makale_okuyucu.config import FIELD_CAPS, FIELDS
from makale_okuyucu.extract import build_fields, extract_chunk, fallback_merge, merge, verify_item
from makale_okuyucu.llm import LLMError, MockBackend
from makale_okuyucu.pdftext import Chunk

CHUNK = Chunk(1, ["method"], [(5, "We propose WidgetNet, a model for widget learning."),
                              (6, "It achieves 91.2 percent accuracy on WidgetBench.")])


def test_verify_item_page_and_unverified():
    it = verify_item({"id": "a", "text": "t", "quote": "achieves 91.2 percent accuracy on WidgetBench"}, CHUNK)
    assert it["check"] == "VERIFIED" and it["page"] == "6"
    it2 = verify_item({"id": "b", "text": "t", "quote": "achieves 95 percent accuracy on WidgetBench"}, CHUNK)
    assert it2["check"] == "UNVERIFIED" and it2["page"] is None and it2["neden"] == "metinde_yok"
    it3 = verify_item({"id": "c", "text": "t", "quote": "WidgetNet"}, CHUNK)
    assert it3["check"] == "UNVERIFIED" and it3["neden"] == "cok_kisa"
    it4 = verify_item({"id": "d", "text": "t", "quote": "widget learning. It achieves 91.2"}, CHUNK)
    assert it4["check"] == "VERIFIED" and it4["page"] == "5-6"


def test_extract_chunk_schema_and_malformed(cfg):
    resp = json.dumps({
        "katkilar": [{"text": "WidgetNet model", "quote": "We propose WidgetNet, a model for widget learning."},
                     "not a dict", {"quote": "no text"}],
        "veri_setleri_ve_kaynaklar": [{"name": "WidgetBench", "link": "not-a-url", "text": "bench",
                                       "quote": "91.2 percent accuracy on WidgetBench"}],
        "ana_sonuclar": {"text": "91.2%", "quote": "It achieves 91.2 percent accuracy on WidgetBench."},
        "bogus": [],
    })
    r = extract_chunk(MockBackend(cfg, responder=[resp]), CHUNK)
    assert r["status"] == "OK" and r["dropped_malformed"] == 2 and r["unknown_fields"] == ["bogus"]
    assert r["items"]["katkilar"][0]["id"] == "c1k1" and r["items"]["katkilar"][0]["page"] == "5"
    assert r["items"]["veri_setleri_ve_kaynaklar"][0]["link"] is None
    assert r["items"]["ana_sonuclar"][0]["check"] == "VERIFIED"


def test_extract_chunk_non_dict_is_schema(cfg):
    r = extract_chunk(MockBackend(cfg, responder=["[1,2]"]), CHUNK)
    assert r["status"] == "SCHEMA"


def _pool(n_per_field=8):
    pool = {}
    for f in FIELDS:
        pool[f] = [{"id": f"{f}{i}", "text": f"{f} alpha{i} beta{i} gamma{i} delta{i}", "quote": "q",
                    "check": "VERIFIED" if i % 2 else "UNVERIFIED"} for i in range(n_per_field)]
    return pool


def test_fallback_merge_caps_and_dedup():
    pool = {f: [] for f in FIELDS}
    pool["katkilar"] = [
        {"id": "u", "text": "WidgetNet model for widgets", "check": "UNVERIFIED"},
        {"id": "v", "text": "WidgetNet model for widgets", "check": "VERIFIED"},
        {"id": "w", "text": "completely different contribution here", "check": "VERIFIED"},
    ]
    out = fallback_merge(pool)
    assert out["katkilar"] == ["v", "w"]


def test_merge_skips_llm_when_small(cfg):
    be = MockBackend(cfg, responder=lambda p, s: LLMError("should not be called"))
    pool = {f: [] for f in FIELDS}
    pool["problem"] = [{"id": "x", "text": "a", "check": "VERIFIED"}]
    out, info = merge(be, pool)
    assert out["problem"] == ["x"] and info["merge_status"] == "SKIPPED_SMALL" and be.stats.calls == 0


def test_merge_unknown_ids_and_caps(cfg):
    pool = _pool()
    resp = {"fields": {"katkilar": ["katkilar1", "nope", "katkilar1"] + [f"katkilar{i}" for i in range(8)],
                       "problem": []}}
    out, info = merge(MockBackend(cfg, responder=[json.dumps(resp)]), pool)
    assert info["merge_status"] == "OK" and info["unknown_ids"] >= 2
    assert len(out["katkilar"]) == FIELD_CAPS["katkilar"] and out["katkilar"][0] == "katkilar1"
    # LLM alanı boş bıraktı ama aday var -> yedekten doldurulur, sessiz kayıp yok
    assert out["problem"] and "problem" in info["fields_from_fallback"]


def test_merge_llm_failure_falls_back(cfg):
    out, info = merge(MockBackend(cfg, responder=lambda p, s: LLMError("x")), _pool())
    assert info["merge_status"].startswith("FALLBACK") and all(len(out[f]) == FIELD_CAPS[f] for f in FIELDS)


def test_build_fields_records_failed_chunk(cfg):
    chunks = [CHUNK, Chunk(2, ["results"], [(7, "Some other text that is long enough to read.")])]

    def responder(p, s):
        if "pages 7-7" in p:
            return LLMError("down")
        return json.dumps({"katkilar": [{"text": "x", "quote": "We propose WidgetNet, a model for widget learning."}]})

    fields, failed, fun = build_fields(MockBackend(cfg, responder=responder), cfg, chunks)
    assert len(failed) == 1 and failed[0]["parca"] == 2 and failed[0]["durum"] == "LLM_ERROR"
    assert failed[0]["sayfalar"] == "7-7"
    assert fun["chunks_ok"] == 1 and fun["chunks_failed"] == 1 and fields["katkilar"]

def test_merge_dedups_same_named_work(cfg):
    pool = _pool()
    for i, it in enumerate(pool["en_yakin_isler"]):
        it["name"] = "Turpin et al. (2023)" if i < 3 else f"Other{i} et al."
    pool["en_yakin_isler"][1]["name"] = "Turpin et al., 2023"
    resp = {"fields": {"en_yakin_isler": [it["id"] for it in pool["en_yakin_isler"]]}}
    out, info = merge(MockBackend(cfg, responder=[json.dumps(resp)]), pool)
    names = [next(it["name"] for it in pool["en_yakin_isler"] if it["id"] == i) for i in out["en_yakin_isler"]]
    assert sum("Turpin" in n for n in names) == 1 and info["name_duplicates"] == 2
    fb = fallback_merge(pool)["en_yakin_isler"]
    assert sum(1 for i in fb if i in {"en_yakin_isler0", "en_yakin_isler1", "en_yakin_isler2"}) == 1
