"""maliyet-sayaci testleri — yalnız sentetik veri. Dosyalar araç klasöründeki tests/_calisma altına yazılır."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ARAC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ARAC))
import maliyet_sayaci as ms  # noqa: E402

CALISMA = Path(__file__).resolve().parent / "_calisma"
GIZLI = "GIZLI-ICERIK-ASLA-CIKMAMALI"


def asst(mid, model="claude-opus-5-5", ts="2026-10-24T10:00:00Z", sid="S1", agent=None, usage="var",
         inp=10, out=100, cw5=0, cw1=0, cr=0, ws=0, speed="standard", geo="global", req=None, kirilim=True):
    msg = {"id": mid, "model": model, "role": "assistant",
           "content": [{"type": "text", "text": GIZLI}]}
    if usage == "var":
        u = {"input_tokens": inp, "output_tokens": out, "cache_creation_input_tokens": cw5 + cw1,
             "cache_read_input_tokens": cr, "speed": speed, "inference_geo": geo,
             "server_tool_use": {"web_search_requests": ws}}
        if kirilim:
            u["cache_creation"] = {"ephemeral_5m_input_tokens": cw5, "ephemeral_1h_input_tokens": cw1}
        msg["usage"] = u
    d = {"type": "assistant", "timestamp": ts, "sessionId": sid, "message": msg}
    if mid is None:
        del msg["id"]
    if req:
        d["requestId"] = req
    if agent:
        d["agentId"] = agent
    return json.dumps(d)


def user(sid="S1"):
    return json.dumps({"type": "user", "sessionId": sid, "message": {"role": "user", "content": GIZLI}})


@pytest.fixture
def fiyat():
    return ms.Fiyatlar()


@pytest.fixture
def calisma():
    shutil.rmtree(CALISMA, ignore_errors=True)
    CALISMA.mkdir(parents=True)
    yield CALISMA
    shutil.rmtree(CALISMA, ignore_errors=True)


def topla(satirlar):
    t = ms.Toplayici()
    t.satirlar_ekle(satirlar, "S1", "ana", "test")
    return t, t.tum_mesajlar()


# ------------------------------------------------------------------ tekilleştirme
def test_ayni_id_streaming_parcalari_bir_kez_sayilir():
    satir = asst("msg_1", inp=5, out=200, cw5=1000, cr=5000)
    t, m = topla([satir, satir, satir, user()])
    assert len(m) == 1
    assert (m[0].input, m[0].output, m[0].cw5m, m[0].cache_read) == (5, 200, 1000, 5000)
    assert t.kalite.tekrar_satir == 2


def test_buyuyen_parcada_en_buyuk_deger_alinir():
    t, m = topla([asst("msg_1", out=3), asst("msg_1", out=250), asst("msg_1", out=40)])
    assert len(m) == 1 and m[0].output == 250


def test_farkli_idler_ayri_sayilir():
    _, m = topla([asst("msg_1"), asst("msg_2"), asst("msg_1")])
    assert len(m) == 2


def test_id_yoksa_requestid_kullanilir_ikisi_de_yoksa_sayilir_ve_raporlanir():
    t, m = topla([asst(None, req="req_1"), asst(None, req="req_1"), asst(None), asst(None)])
    assert len(m) == 3  # req_1 bir kez + id'siz iki satır
    assert t.kalite.id_yok == 2


def test_dosyalar_arasi_tekillestirme(calisma):
    a = calisma / "a.jsonl"
    b = calisma / "b.jsonl"
    a.write_text(asst("msg_1") + "\n" + asst("msg_2") + "\n", encoding="utf-8")
    b.write_text(asst("msg_2") + "\n", encoding="utf-8")  # hard link / kopya benzetimi
    t = ms.Toplayici()
    t.dosya_ekle(a, "S1", "ana")
    t.dosya_ekle(b, "S1", "x")
    assert len(t.tum_mesajlar()) == 2 and t.kalite.tekrar_satir == 1


# ------------------------------------------------------------------ eksik / bozuk
def test_eksik_usage_mesaj_sayilir_token_sifir(fiyat):
    t, m = topla([asst("msg_1", usage=None), asst("msg_2", out=7)])
    assert len(m) == 2
    assert t.kalite.usage_yok == 1
    eksik = [x for x in m if x.anahtar == "msg_1"][0]
    assert eksik.output == 0 and fiyat.maliyet(eksik) == 0.0


def test_eksik_usage_tekrarinda_usageli_parca_kazanir():
    t, m = topla([asst("msg_1", usage=None), asst("msg_1", out=99)])
    assert len(m) == 1 and m[0].output == 99 and t.kalite.usage_yok == 0


def test_bozuk_satir_atlanmaz_sayilir():
    t, m = topla(['{"type":"assistant",', "null", "[1,2]", "", asst("msg_1"), "çöp"])
    assert t.kalite.bozuk == 4  # yarım JSON, null, liste, çöp; boş satır sayılmaz
    assert t.kalite.satir == 5
    assert t.kalite.bozuk_dosyalar == {"test": 4}
    assert len(m) == 1


def test_kirilimsiz_cache_yazimi_5m_sayilir_ve_raporlanir():
    t, m = topla([asst("msg_1", cw5=500, kirilim=False)])
    assert m[0].cw5m == 500 and m[0].cw1h == 0 and t.kalite.kirilim_yok == 1


# ------------------------------------------------------------------ fiyat
def test_model_bazli_fiyat(fiyat):
    m = ms.Mesaj("k", "claude-opus-5-5", None, "S", "ana", input=1_000_000, output=1_000_000,
                 cw5m=1_000_000, cw1h=1_000_000, cache_read=1_000_000)
    assert fiyat.maliyet(m) == pytest.approx(4 + 20 + 5 + 8 + 0.20)
    m.model = "claude-sonnet-5-5"
    assert fiyat.maliyet(m) == pytest.approx(2 + 10 + 2.5 + 4 + 0.10)
    m.model = "claude-opus-5"
    assert fiyat.maliyet(m) == pytest.approx(5 + 25 + 6.25 + 10 + 0.50)


def test_haiku_uzun_baglam_esigi(fiyat):
    kisa = ms.Mesaj("k", "claude-haiku-5-5", None, "S", "ana", input=100_000, output=1_000_000)
    uzun = ms.Mesaj("k", "claude-haiku-5-5", None, "S", "ana", input=50_000, cache_read=50_001, output=1_000_000)
    assert fiyat.maliyet(kisa) == pytest.approx(0.10 * 0.1 + 0.50)
    assert fiyat.maliyet(uzun) == pytest.approx((50_000 * 0.50 + 50_001 * 0.05) / 1e6 + 2.50)


def test_fast_bolge_ve_web_arama(fiyat):
    m = ms.Mesaj("k", "claude-opus-5-5", None, "S", "ana", output=1_000_000, fast=True, bolge="us", web_search=3)
    assert fiyat.maliyet(m) == pytest.approx(20 * 2 * 1.1 + 0.03)


def test_bilinmeyen_model_fiyatsiz_ama_token_sayilir(fiyat):
    t, m = topla([asst("msg_1", model="claude-gizemli-9", out=500), asst("msg_2", out=100)])
    g = ms.grupla(m, fiyat, t.kalite, lambda x: "hepsi")["hepsi"]
    assert g["output"] == 600 and g["fiyatsiz_mesaj"] == 1
    assert t.kalite.fiyatsiz_modeller == {"claude-gizemli-9": 1}


def test_tarihli_model_adi_onekle_eslesir_synthetic_sifir(fiyat):
    assert fiyat.bul("claude-opus-5-5-20261001") is fiyat.modeller["claude-opus-5-5"]
    m = ms.Mesaj("k", "<synthetic>", None, "S", "ana", output=10)
    assert fiyat.maliyet(m) == 0.0


# ------------------------------------------------------------------ uçtan uca: keşif + gizlilik
def kur_oturum(kok: Path):
    p = kok / "proj-A"
    sub = p / "S1" / "subagents"
    (sub / "workflows" / "wf_1").mkdir(parents=True)
    (p / "S1.jsonl").write_text("\n".join([user(), asst("m1", out=100), asst("m1", out=100), "bozuk{"]) + "\n",
                                encoding="utf-8")
    (sub / "agent-aaa111.jsonl").write_text(asst("m2", agent="aaa111", out=50) + "\n", encoding="utf-8")
    (sub / "agent-aaa111.meta.json").write_text(json.dumps({"agentType": "Explore", "description": GIZLI}),
                                                encoding="utf-8")
    (sub / "workflows" / "wf_1" / "agent-bbb222.jsonl").write_text(
        asst("m3", agent="bbb222", out=25, ts="2026-10-25T01:00:00Z") + "\n", encoding="utf-8")
    return p


def test_uctan_uca_agents_sessions_since(calisma, capsys):
    kur_oturum(calisma)
    ms.ana(["--root", str(calisma), "--json", "agents", "--session", "S1"])
    out = capsys.readouterr().out
    assert GIZLI not in out
    d = json.loads(out)
    ajanlar = {a["ajan"]: a for a in d["ajanlar"]}
    assert ajanlar["ana"]["output"] == 100
    assert ajanlar["aaa111"]["tur"] == "Explore" and ajanlar["aaa111"]["output"] == 50
    assert ajanlar["bbb222"]["tur"] == "?@wf_1"
    assert d["toplam"]["output"] == 175 and d["kalite"]["bozuk_satir"] == 1

    ms.ana(["--root", str(calisma), "sessions"])
    out = capsys.readouterr().out
    assert GIZLI not in out and "S1" in out and "bozuk 1" in out and "teoriktir" in out

    ms.ana(["--root", str(calisma), "--json", "since", "2026-10-25"])
    d = json.loads(capsys.readouterr().out)
    assert d["toplam"]["output"] == 25 and d["toplam"]["mesaj"] == 1


def test_ek_dizin_yalniz_ajan_ciktilarini_okur(calisma, capsys):
    kur_oturum(calisma)
    tasks = calisma / "tasks"
    tasks.mkdir()
    (tasks / "aaa111ff00.output").write_text(asst("m2", agent="aaa111", out=50) + "\n", encoding="utf-8")
    (tasks / "b1x2y3z4.output").write_text("kabuk ciktisi " + GIZLI + "\n", encoding="utf-8")
    ms.ana(["--root", str(calisma), "--json", "agents", "--session", "S1", "--ek-dizin", str(tasks)])
    d = json.loads(capsys.readouterr().out)
    assert d["toplam"]["output"] == 175  # hard-link kopyası çift sayılmadı
    assert d["kalite"]["bozuk_satir"] == 1  # kabuk çıktısı okunmadı


def test_tablo_en_fazla_40_satir(calisma, capsys):
    p = calisma / "proj"
    p.mkdir()
    for i in range(60):
        (p / f"S{i:03d}.jsonl").write_text(asst(f"m{i}", sid=f"S{i:03d}") + "\n", encoding="utf-8")
    ms.ana(["--root", str(calisma), "sessions"])
    out = capsys.readouterr().out.splitlines()
    assert len(out) <= 40  # tablo + gizli satır notu + kalite + abonelik notu dahil
    assert any("gosterilmedi" in s for s in out)


def test_transkript_dosyasi_degismez(calisma, capsys):
    p = kur_oturum(calisma)
    once = {f: f.read_bytes() for f in p.rglob("*") if f.is_file()}
    ms.ana(["--root", str(calisma), "sessions"])
    capsys.readouterr()
    assert once == {f: f.read_bytes() for f in p.rglob("*") if f.is_file()}


# ------------------------------------------------------------------ tools modu
def test_tools_yalniz_llm_blogunu_toplar(calisma):
    gm = calisma / "gapmine_reports"
    gm.mkdir()
    (gm / "r1.json").write_text(json.dumps({"claim": GIZLI, "llm": {
        "backend": "claude_cli", "calls": 3, "ok": 3, "failed": 0, "input_tokens": 6, "output_tokens": 900,
        "cache_read_tokens": 0, "cache_write_tokens": 100, "cost_usd": 0.01}}), encoding="utf-8")
    (gm / "r2.json").write_text("{bozuk", encoding="utf-8")
    fg = calisma / "forge"
    (fg / "makale-okuyucu" / "logs").mkdir(parents=True)
    (fg / "makale-okuyucu" / "logs" / "maliyet.jsonl").write_text(
        json.dumps({"calls": 1, "input_tokens": 10, "output_tokens": 20, "cost_usd": 0.5}) + "\n{x\n",
        encoding="utf-8")
    (fg / "makale-okuyucu" / "logs" / "baska.json").write_text(json.dumps({"cost_usd": 99}), encoding="utf-8")
    d = ms.cmd_tools(None, None, gapmine=gm, forge=fg)
    assert GIZLI not in json.dumps(d)
    assert d["araclar"]["gapmine"]["cost_usd"] == 0.01 and d["araclar"]["gapmine"]["calls"] == 3
    assert d["araclar"]["makale-okuyucu"]["cost_usd"] == 0.5
    assert d["kalite"]["bozuk"] == 2 and d["kalite"]["dosya"] == 3
