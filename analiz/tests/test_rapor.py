"""analiz.rapor testleri: yalnız sentetik fixture (altın set / canlı çıktı okunmaz). Ağsız."""
from __future__ import annotations

import json
from pathlib import Path

from analiz import rapor as R


def _w(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _gold(q):
    return [{"arxiv_id": f"2001.{q * 100 + j:05d}", "doi": None, "baslik": f"Gold {q} {j}"} for j in range(30)]


def _liste(q, hits):
    out = [{"sira": j + 1, "arxiv_id": f"2001.{q * 100 + j:05d}", "doi": None, "baslik": f"Gold {q} {j}"}
           for j in range(hits)]
    out += [{"sira": hits + j + 1, "arxiv_id": f"2999.{q * 100 + j:05d}", "doi": None, "baslik": f"Junk {q} {j}"}
            for j in range(30 - hits)]
    return out


def _kosu(kok: Path, qid, q, hits, usd, durum="OK", sure=100.0, k=1, **ekstra):
    d = {"durum": durum, "maliyet_usd": usd, "sure_s": sure, "calismalar": _liste(q, hits) if durum in ("OK", "EKSİK") else []}
    d.update(ekstra)
    _w(kok / qid / f"k{k}" / "sonuc.json", d)


def kur(tmp: Path, n=30, hb=lambda q: 20, h1=lambda q: 10, h0=lambda q: 8, ub=0.3, u1=1.0, alan=True,
        b_ok=lambda q: True, tok=3500, sadakat=(29, 0), sad_n=30):
    ad = tmp / "altin"
    qs = []
    for q in range(n):
        qid = f"q{q:02d}"
        it = {"id": qid, "soru": "?", "kesim": "2025-06-01"}
        if alan:
            it["alan"] = f"alan{q % 6}"
        qs.append(it)
        _w(ad / f"{qid}.json", _gold(q))
        if b_ok(q):
            _kosu(tmp / "B", qid, q, hb(q), ub, ozet_token_tahmini=tok, eksik_kaynaklar=["openalex"] if q == 0 else [],
                  )
            _w(tmp / "B" / qid / "k1" / "funnel.json", {"bilgi": {"ozet_arxiv.bulundu": 2, "ozet_arxiv.denendi": 3}})
        _kosu(tmp / "A1", qid, q, h1(q), u1, web_arama=7)
        _kosu(tmp / "A0", qid, q, h0(q), 0.16, web_arama=0)
    _w(ad / "sorular.json", qs)
    sad = None
    if sadakat is not None:
        sad = tmp / "sadakat.json"
        _w(sad, {"ozet": {"n": sad_n, "sayim": {"DESTEKLENIYOR": sadakat[0], "UYDURMA": sadakat[1]},
                          "uydurma": sadakat[1]}})
    return dict(b_dir=tmp / "B", a1_dir=tmp / "A1", a0_dir=tmp / "A0", altin_dizin=ad, sadakat=sad)


def test_kabul(tmp_path):
    r = R.hesapla(**kur(tmp_path))
    assert r["hukum"] == "KABUL"
    assert r["b_a1"]["n"] == 30 and abs(r["b_a1"]["ortalama"] - 100 / 3) < 1e-6
    assert r["b_a1"]["isaret"]["p"] < 0.05
    assert all(t["gecti"] for t in r["esikler"])
    md = R.markdown(r)
    assert md.splitlines()[0].startswith("# HÜKÜM: KABUL")
    assert "recall 0" in md and "OpenAlex" in md  # kural + sınırlamalar
    assert "alan0" in md  # alan kırılımı
    assert "bulundu=60" in md  # ozet_arxiv toplamı


def test_red_maliyet(tmp_path):
    r = R.hesapla(**kur(tmp_path, ub=0.8))  # recall iyi ama $B > %50 $A1, ama $B < $A1 -> ARŞİV değil
    assert r["hukum"] == "RED" and not r["arsiv_kosulu"]
    assert [t["gecti"] for t in r["esikler"]] == [True, False, True, True]


def test_red_sadakat_uydurma_ve_token(tmp_path):
    r = R.hesapla(**kur(tmp_path, sadakat=(30, 1), tok=4001))
    assert r["hukum"] == "RED"
    assert [t["gecti"] for t in r["esikler"]] == [True, True, False, False]
    r = R.hesapla(**kur(tmp_path / "x", sadakat=(27, 0)))
    assert r["hukum"] == "RED"


def test_isaret_testi_p_yetmez(tmp_path):
    # ortalama fark >= +10 ama yalnız 4 soruda pozitif (diğerleri beraber): p = 0,0625 -> RED
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 30 if q < 4 else 5, h1=lambda q: 5))
    assert r["b_a1"]["ortalama"] >= 10 and r["b_a1"]["isaret"]["p"] > 0.05
    assert r["hukum"] == "RED" and r["esikler"][0]["gecti"] is False


def test_esik_sinir_tam_10_puan(tmp_path):
    # her soruda +3 isabet = tam +10 puan, p çok küçük -> geçer
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 13, h1=lambda q: 10))
    assert abs(r["b_a1"]["ortalama"] - 10.0) < 1e-9 and r["esikler"][0]["gecti"]


def test_arsiv_ortalama_negatif(tmp_path):
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 9, h1=lambda q: 10))  # -3,3 puan; ilk 10'da ara durdurma değil
    assert r["hukum"].startswith("ARŞİV") and not r["ara"]["tetik"]


def test_arsiv_maliyet_asimi(tmp_path):
    r = R.hesapla(**kur(tmp_path, ub=1.5))
    assert r["hukum"].startswith("ARŞİV") and "$(B) > $(A1)" in r["hukum_not"]


def test_pilot_n_kucuk(tmp_path):
    r = R.hesapla(**kur(tmp_path, n=12, sadakat=(10, 0), sad_n=10))
    assert r["pilot"] and r["hukum"].startswith("PİLOT")
    md = R.markdown(r)
    assert "pilot, karar yok" in md and "PİLOT" in md.split("## Ayrıntı")[0]
    assert "değerlendirilemedi" not in md  # n=12 >= 10, ara kontrol yapılabilir


def test_ara_durdurma_tetik(tmp_path):
    # ilk 10 soruda B 4 isabet eksik (-13,3 puan) ve 11. sorudan sonra koşu yok
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 6, h1=lambda q: 10, b_ok=lambda q: q < 10))
    assert r["ara"]["tetik"] and r["hukum"] == "RED"
    md = R.markdown(r)
    assert "TETİKLENDİ" in md and "ara durdurma sonrası yapılmadı" in md
    assert "20 koşu YOK" not in md  # beklenen eksik, "gerçek eksik" olarak sayılmaz


def test_ara_durdurma_tetiklenmez_sinirin_altinda(tmp_path):
    # ilk 10 ort. -6,7 puan (> -10)
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 8 if q < 10 else 20, h1=lambda q: 10))
    assert not r["ara"]["tetik"] and abs(r["ara"]["ortalama"] + 6.6667) < 1e-3


def test_ara_durdurma_tam_sinir(tmp_path):
    r = R.hesapla(**kur(tmp_path, hb=lambda q: 7 if q < 10 else 20, h1=lambda q: 10))  # tam -10,0
    assert r["ara"]["tetik"]


def test_basarisiz_kosu_recall_sifir(tmp_path):
    kw = kur(tmp_path)
    _w(tmp_path / "B" / "q05" / "k1" / "sonuc.json", {"durum": "HATA", "maliyet_usd": 0.1, "calismalar": []})
    (tmp_path / "A1" / "q06" / "k1" / "sonuc.json").unlink()  # eksik koşu
    r = R.hesapla(**kw)
    assert r["sb"]["q05"]["recall"] == 0.0 and r["s1"]["q06"]["recall"] == 0.0
    assert r["sayim"]["B"]["basarisiz"] == [("q05", "HATA")] and r["sayim"]["A1"]["yok"] == ["q06"]
    md = R.markdown(r)
    assert "UYARI" in md and "q05:HATA" in md and "1 koşu YOK" in md


def test_eksik_kaynakli_b_basarisiz_sayilmaz(tmp_path):
    kw = kur(tmp_path)
    _kosu(tmp_path / "B", "q01", 1, 20, 0.3, durum="EKSİK", ozet_token_tahmini=3000, eksik_kaynaklar=["arxiv"])
    r = R.hesapla(**kw)
    assert r["sayim"]["B"]["basarisiz"] == [] and r["sb"]["q01"]["recall"] > 0
    assert "arxiv" in R.markdown(r)


def test_alan_yok_ve_sadakat_yok(tmp_path):
    r = R.hesapla(**kur(tmp_path, alan=False, sadakat=None))
    assert r["hukum"].startswith("KARAR YOK")
    assert "alan bilgisi yok" in R.markdown(r)


def test_kararlilik_std(tmp_path):
    kw = kur(tmp_path)
    kd = tmp_path / "K"
    for k, h in ((1, 10), (2, 13), (3, 16)):  # recall 33,3 / 43,3 / 53,3 -> std 10
        _kosu(kd, "q00", 0, h, 0.3, k=k)
    kw["kararlilik_dir"] = kd
    r = R.hesapla(**kw)
    assert abs(r["kararlilik"]["satir"][0]["std"] - 10.0) < 1e-6
    assert "std 10.00" in R.markdown(r)


def test_cli(tmp_path):
    kw = kur(tmp_path)
    out = tmp_path / "out" / "RAPOR.md"
    rc = R.main(["--b", str(kw["b_dir"]), "--a1", str(kw["a1_dir"]), "--a0", str(kw["a0_dir"]),
                 "--altin-dizin", str(kw["altin_dizin"]), "--sadakat", str(kw["sadakat"]), "--out", str(out)])
    assert rc == 0 and out.read_text(encoding="utf-8").startswith("# HÜKÜM: KABUL")
