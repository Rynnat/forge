"""Orkestra v0 ön kayıt sonuç raporu üretici (ağsız, yalnız stdlib + puanla.py).

  python -m analiz.rapor --b DIR --a1 DIR --a0 DIR --altin-dizin DIR [--sorular FILE]
         [--sadakat FILE] [--kararlilik DIR] --out RAPOR.md      (forge/ dizininden)

Dizin düzeni (orkestra batch / deney.taban batch çıktısı): DIR/<soru_id>/k<k>/sonuc.json (+ funnel.json).
Birincil koşu k1'dir. Altın dizini: sorular.json (id, soru, kesim, isteğe bağlı alan/field) ve altın için
ya <id>.json (soru başına) ya da altin.json ({id: [...]} | {"sorular": [{id, calismalar|altin}]} | [{id, ...}]).
Puanlama orkestra.deney.puanla'dır (yeniden yazılmadı). ONKAYIT-orkestra-v0.md + iki ek: eşikler aynen.

KURAL: eksik / başarısız koşu o sistem için recall 0 sayılır (raporun başında yazılır, yüksek sesle işaretlenir).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

_ORK = Path(__file__).resolve().parent.parent / "orkestra"
if str(_ORK) not in sys.path:
    sys.path.insert(0, str(_ORK))

from orkestra.deney import puanla as P  # noqa: E402

N_TAM = 30
FARK_ESIK = 10.0      # puan
P_ESIK = 0.05
MALIYET_ORAN = 0.50
SADAKAT_MIN = 28
TOKEN_MAX = 4000
ARA_N = 10
ARA_ESIK = -10.0      # puan
EPS = 1e-9
TAMAM_DURUM = {"OK", "EKSİK", "EKSIK"}  # B'de EKSİK = kaynak eksik ama liste üretildi; koşu başarısız değil

SINIRLAMALAR = [
    "Anahtarsız koşu: OpenAlex ve Semantic Scholar anahtarı yoktu; B bu kaynaklar olmadan ölçüldü (B için haksız zayıflık olabilir).",
    "Sorular Türkçe yazıldı; iki sistem de aynı soruyu aldı, ama şef planı/sorguları İngilizce üretir; dil etkisi ölçülmedi.",
    "Altın set kalite kontrolü 2/30 hata buldu (kesik DOI); sistematik süzgeçle 26 kayıt atıldı, süzgeç sonrası yeni örneklem çekilmedi.",
    "Sadakat denetçisi (Sonnet) B ile aynı model ailesinden; bağımsız bir aile değil.",
    "Altın = survey kaynakçası; survey'in atıf yapmadığı ama önemli çalışmalar 'yanlış' sayılır (recall tavanı < 1).",
    "Özet token sayısı tahminidir: ceil(karakter/3), gerçek tokenizer değil.",
]


def _oku(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def _pts(x):
    return None if x is None else x * 100.0


def ortalama(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


# ---------------------------------------------------------------- yükleme
def sorulari_yukle(altin_dizin: Path, sorular_dosya: Path | None = None) -> list[dict]:
    d = _oku(sorular_dosya or Path(altin_dizin) / "sorular.json")
    if isinstance(d, dict):
        d = d.get("sorular") or []
    alanlar = {}  # forge-altin: alan bilgisi altin.json'da
    toplu = Path(altin_dizin) / "altin.json"
    if toplu.exists():
        t = _oku(toplu)
        if isinstance(t, list):
            alanlar = {str(it.get("id")): it.get("alan") for it in t if isinstance(it, dict)}
    return [{"id": str(it["id"]),
             "alan": it.get("alan") or it.get("field") or it.get("domain") or alanlar.get(str(it["id"]))}
            for it in d or []]


def _altin_listesi(veri) -> list[dict]:
    if isinstance(veri, dict):
        veri = veri.get("calismalar") or veri.get("altin") or veri.get("kaynakca") or []
    return [P.altin_kayit(g) for g in veri]


def altin_yukle(altin_dizin: Path, qid: str):
    """Soru altını; bulunamazsa None (rapora 'altın yok' olarak yazılır)."""
    f = Path(altin_dizin) / f"{qid}.json"
    if f.exists():
        return P.altin_yukle(f)
    toplu = _oku(Path(altin_dizin) / "altin.json")
    if isinstance(toplu, dict) and "sorular" in toplu:
        toplu = toplu["sorular"]
    if isinstance(toplu, dict) and qid in toplu:
        return _altin_listesi(toplu[qid])
    if isinstance(toplu, list):
        for it in toplu:
            if isinstance(it, dict) and str(it.get("id")) == qid:
                return _altin_listesi(it)
    return None


def kosu_yukle(kok: Path, qid: str, k: int = 1) -> dict:
    """{"var","durum","tamam","sonuc","funnel","dizin"}; sonuc.json yoksa var=False."""
    dizin = Path(kok) / qid / f"k{k}"
    s = _oku(dizin / "sonuc.json") if dizin.exists() else None
    if not isinstance(s, dict):
        return {"var": False, "durum": "KOSU_YOK", "tamam": False, "sonuc": None, "funnel": None, "dizin": dizin}
    durum = str(s.get("durum", "OK"))
    return {"var": True, "durum": durum, "tamam": durum in TAMAM_DURUM, "sonuc": s,
            "funnel": _oku(dizin / "funnel.json"), "dizin": dizin}


def liste_of(kosu: dict) -> list[dict]:
    if not kosu["tamam"]:
        return []  # başarısız koşu: boş liste -> recall 0
    return [{"arxiv_id": c.get("arxiv_id"), "doi": c.get("doi"), "baslik": c.get("baslik")}
            for c in kosu["sonuc"].get("calismalar", [])]


# ---------------------------------------------------------------- istatistik
def sistem_puanla(kok: Path | None, sorular: list[dict], altinlar: dict) -> dict:
    yok = {"var": False, "durum": "KOSU_YOK", "tamam": False, "sonuc": None, "funnel": None, "dizin": None}
    sat = {}
    for q in sorular:
        kos = kosu_yukle(kok, q["id"]) if kok else yok
        alt = altinlar.get(q["id"])
        r = P.recall_at_k(liste_of(kos), alt) if alt else {"recall": None, "eslesen": 0, "payda": 0}
        s = kos["sonuc"] or {}
        sat[q["id"]] = {"kosu": kos, "recall": r["recall"], "eslesen": r["eslesen"], "payda": r["payda"],
                        "usd": s.get("maliyet_usd"), "sure": s.get("sure_s")}
    return sat


def eslestir(sa: dict, sb: dict, ids: list[str]) -> dict:
    """B − A (puan). Altını boş soru (recall None) dışarıda."""
    f = {}
    for i in ids:
        if sa[i]["recall"] is not None and sb[i]["recall"] is not None:
            f[i] = (sb[i]["recall"] - sa[i]["recall"]) * 100.0
    return {"farklar": f, "n": len(f), "ortalama": ortalama(list(f.values())),
            "isaret": P.isaret_testi(list(f.values()))}


def kosu_sayimlari(sat: dict, ids: list[str]) -> dict:
    yok = [i for i in ids if not sat[i]["kosu"]["var"]]
    basarisiz = [(i, sat[i]["kosu"]["durum"]) for i in ids if sat[i]["kosu"]["var"] and not sat[i]["kosu"]["tamam"]]
    bos = [i for i in ids if sat[i]["kosu"]["tamam"] and not liste_of(sat[i]["kosu"])]
    return {"yok": yok, "basarisiz": basarisiz, "bos": bos}


def kararlilik(kdir: Path | None, bdir: Path | None, sorular: list[dict], altinlar: dict) -> dict | None:
    if not kdir or not Path(kdir).exists():
        return None
    satir = []
    for q in sorular:
        alt = altinlar.get(q["id"])
        qd = Path(kdir) / q["id"]
        if not alt or not qd.exists():
            continue
        ks = sorted(int(p.name[1:]) for p in qd.iterdir() if p.is_dir() and p.name[0] == "k" and p.name[1:].isdigit())
        kosular = [kosu_yukle(kdir, q["id"], k) for k in ks]
        if 1 not in ks and bdir:
            k1 = kosu_yukle(bdir, q["id"], 1)
            if k1["var"]:
                kosular.insert(0, k1)
        if len(kosular) < 2:
            continue
        rs = [(P.recall_at_k(liste_of(k), alt)["recall"] or 0.0) * 100.0 for k in kosular]
        satir.append({"id": q["id"], "k": len(rs), "recall": rs, "std": statistics.stdev(rs),
                      "basarisiz": sum(1 for k in kosular if not k["tamam"])})
    if not satir:
        return {"satir": [], "ort_std": None, "maks_std": None}
    return {"satir": satir, "ort_std": ortalama([s["std"] for s in satir]), "maks_std": max(s["std"] for s in satir)}


def sadakat_degerlendir(yol: Path | None) -> dict:
    d = _oku(yol) if yol else None
    if not isinstance(d, dict):
        return {"var": False}
    o = d.get("ozet") or {}
    sayim = o.get("sayim") or {}
    n = int(o.get("n", 0))
    k = int(sayim.get("DESTEKLENIYOR", 0))
    uyd = int(o.get("uydurma", sayim.get("UYDURMA", 0)))
    return {"var": True, "n": n, "k": k, "uydurma": uyd, "wilson": P.wilson_alt(k, n), "sayim": sayim,
            "tam": n >= N_TAM, "gecti": n >= N_TAM and k >= SADAKAT_MIN and uyd == 0}


def b_kaynak_durumu(sb: dict, ids: list[str]) -> dict:
    eksik, ozet_yok, toplam, ozet_ark = {}, 0, 0, {}
    for i in ids:
        k = sb[i]["kosu"]
        if not k["var"]:
            continue
        e = k["sonuc"].get("eksik_kaynaklar") or []
        if e:
            eksik[i] = list(e)
        cal = k["sonuc"].get("calismalar", [])
        toplam += len(cal)
        ozet_yok += sum(1 for c in cal if c.get("alinti_durum") == "OZET_YOK")
        for ad, v in ((k["funnel"] or {}).get("bilgi") or {}).items():
            if ad.startswith("ozet_arxiv."):
                ozet_ark[ad] = ozet_ark.get(ad, 0) + (v if isinstance(v, (int, float)) else 0)
    return {"eksik": eksik, "ozet_yok": ozet_yok, "calisma_toplam": toplam, "ozet_arxiv": ozet_ark}


def b_token(sb: dict, ids: list[str]) -> list[float]:
    out = []
    for i in ids:
        k = sb[i]["kosu"]
        if not k["tamam"]:
            continue
        t = k["sonuc"].get("ozet_token_tahmini")
        if t is None:
            oz = k["dizin"] / "ozet.md"
            if oz.exists():
                t = -(-len(oz.read_text(encoding="utf-8")) // 3)
        if t is not None:
            out.append(float(t))
    return out


# ---------------------------------------------------------------- hüküm
def hesapla(b_dir, a1_dir, a0_dir, altin_dizin, sadakat=None, kararlilik_dir=None, sorular_dosya=None) -> dict:
    sorular = sorulari_yukle(Path(altin_dizin), Path(sorular_dosya) if sorular_dosya else None)
    ids = [q["id"] for q in sorular]
    altinlar = {i: altin_yukle(Path(altin_dizin), i) for i in ids}
    sb = sistem_puanla(Path(b_dir) if b_dir else None, sorular, altinlar)
    s1 = sistem_puanla(Path(a1_dir) if a1_dir else None, sorular, altinlar)
    s0 = sistem_puanla(Path(a0_dir) if a0_dir else None, sorular, altinlar)
    r = {"sorular": sorular, "ids": ids, "altinsiz": [i for i in ids if not altinlar[i]],
         "sb": sb, "s1": s1, "s0": s0}
    r["b_a1"] = eslestir(s1, sb, ids)
    r["b_a0"] = eslestir(s0, sb, ids)
    r["a1_a0"] = eslestir(s0, s1, ids)

    # ara durdurma: ilk 10 soru (soru dosyası sırası), B−A1
    f10 = [r["b_a1"]["farklar"][i] for i in ids[:ARA_N] if i in r["b_a1"]["farklar"]]
    r["ara"] = {"n": len(f10), "ortalama": ortalama(f10), "degerlendirilebilir": len(f10) >= ARA_N,
                "tetik": len(f10) >= ARA_N and ortalama(f10) <= ARA_ESIK + EPS}

    r["sayim"] = {}
    for ad, s in (("B", sb), ("A1", s1), ("A0", s0)):
        c = kosu_sayimlari(s, ids)
        # ara durdurma tetiklendiyse 11. sorudan sonrası yapılmaz: beklenen eksik
        c["beklenen_yok"] = [i for i in c["yok"] if r["ara"]["tetik"] and ids.index(i) >= ARA_N]
        r["sayim"][ad] = c

    mB = ortalama([sb[i]["usd"] or 0.0 for i in ids])
    mA1 = ortalama([s1[i]["usd"] or 0.0 for i in ids])
    r["maliyet"] = {"B": mB, "A1": mA1, "A0": ortalama([s0[i]["usd"] or 0.0 for i in ids]),
                    "oran": (mB / mA1) if mA1 else None}
    toks = b_token(sb, ids)
    r["token"] = {"n": len(toks), "ort": ortalama(toks)}
    r["sadakat"] = sadakat_degerlendir(Path(sadakat) if sadakat else None)
    r["sure"] = {ad: ortalama([s[i]["sure"] for i in ids if s[i]["sure"] is not None])
                 for ad, s in (("B", sb), ("A1", s1), ("A0", s0))}
    r["kararlilik"] = kararlilik(Path(kararlilik_dir) if kararlilik_dir else None,
                                 Path(b_dir) if b_dir else None, sorular, altinlar)
    r["b_kaynak"] = b_kaynak_durumu(sb, ids)

    # eşikler
    e = r["b_a1"]
    n = e["n"]
    pilot = n < N_TAM
    m, p = e["ortalama"], e["isaret"]["p"]
    t1 = {"ad": "Eşli recall farkı B−A1",
          "deger": f"{m:+.1f} puan, p={p:.4f}" if m is not None else "yok",
          "esik": f"≥ +{FARK_ESIK:.0f} puan VE p < {P_ESIK}",
          "gecti": (m is not None and m >= FARK_ESIK - EPS and p < P_ESIK), "pilot": pilot}
    mo = r["maliyet"]["oran"]
    t2 = {"ad": "Maliyet B/A1",
          "deger": (f"${mB:.3f} / ${mA1:.3f} = %{mo * 100:.0f}" if mo is not None else "A1 maliyeti yok"),
          "esik": f"≤ %{MALIYET_ORAN * 100:.0f}", "gecti": mo is not None and mo <= MALIYET_ORAN + EPS}
    sd = r["sadakat"]
    if sd["var"]:
        t3 = {"ad": "Sadakat",
              "deger": f"{sd['k']}/{sd['n']} destekli, uydurma={sd['uydurma']}, Wilson alt={sd['wilson']:.3f} (betimsel)",
              "esik": f"≥ {SADAKAT_MIN}/30 VE uydurma = 0", "gecti": sd["gecti"], "pilot": not sd["tam"]}
    else:
        t3 = {"ad": "Sadakat", "deger": "sadakat.json yok", "esik": f"≥ {SADAKAT_MIN}/30 VE uydurma = 0",
              "gecti": False, "eksik": True}
    tk = r["token"]["ort"]
    t4 = {"ad": "Bağlam (B son rapor)",
          "deger": (f"{tk:.0f} token ort. ({r['token']['n']} koşu)" if tk is not None else "veri yok"),
          "esik": f"≤ {TOKEN_MAX} token", "gecti": tk is not None and tk <= TOKEN_MAX}
    r["esikler"] = [t1, t2, t3, t4]

    arsiv = (m is not None and m < 0) or (mB is not None and mA1 is not None and mB > mA1)
    r["arsiv_kosulu"] = bool(arsiv)
    ek = []
    diger_ok = all(t["gecti"] for t in (t1, t2, t4))
    if r["ara"]["tetik"]:
        v = "RED"
        ek.append(f"ara durdurma tetiklendi: ilk {ARA_N} soruda ort. B−A1 = {r['ara']['ortalama']:+.1f} ≤ {ARA_ESIK:.0f}")
    elif pilot:
        v = "PİLOT — KARAR YOK"
        ek.append(f"n={n} < {N_TAM}")
    elif arsiv:
        v = "ARŞİV (RED)"
        ek.append("ort(B−A1) < 0" if (m is not None and m < 0) else "$(B) > $(A1)")
    elif all(t["gecti"] for t in r["esikler"]):
        v = "KABUL"
    elif diger_ok and t3.get("eksik"):
        v = "KARAR YOK — sadakat verisi eksik"
    elif diger_ok and t3.get("pilot"):
        v = "KARAR YOK — sadakat pilot (n<30)"
    else:
        v = "RED"
        ek.append("tutmayan eşik: " + ", ".join(t["ad"] for t in r["esikler"] if not t["gecti"]))
    r["hukum"], r["hukum_not"], r["pilot"] = v, "; ".join(ek), pilot
    return r


# ---------------------------------------------------------------- Markdown
def _f(x, nd=1, sfx=""):
    return "yok" if x is None else f"{x:.{nd}f}{sfx}"


def _gecti(t, pilot_genel):
    if t.get("eksik"):
        return "YOK"
    if t.get("pilot"):
        return "PİLOT"
    return "evet" if t["gecti"] else "HAYIR"


def markdown(r: dict) -> str:
    L = []
    v = r["hukum"] + (f" ({r['hukum_not']})" if r["hukum_not"] else "")
    L.append(f"# HÜKÜM: {v}")
    L.append("")
    L.append("> Kural: eksik veya başarısız koşu o sistem için **recall 0** sayılır; eşikler ön kayıttaki gibi uygulanır. "
             "Birincil karşılaştırma B−A1; A0 yalnız betimsel.")
    uy = []
    for ad in ("B", "A1", "A0"):
        c = r["sayim"][ad]
        ger_yok = [i for i in c["yok"] if i not in c["beklenen_yok"]]
        if ger_yok or c["basarisiz"] or c["bos"]:
            uy.append(f"**{ad}**: {len(ger_yok)} koşu YOK, {len(c['basarisiz'])} koşu BAŞARISIZ "
                      f"({', '.join(f'{i}:{d}' for i, d in c['basarisiz']) or '-'}), "
                      f"{len(c['bos'])} koşu boş liste. Hepsi recall 0 sayıldı.")
        if c["beklenen_yok"]:
            uy.append(f"{ad}: {len(c['beklenen_yok'])} koşu ara durdurma sonrası yapılmadı (beklenen; recall 0 sayıldı).")
    if r["altinsiz"]:
        uy.append(f"**{len(r['altinsiz'])} soruda altın bulunamadı/boş** (istatistik dışı): {', '.join(r['altinsiz'])}")
    if uy:
        L.append("")
        L.append("## UYARI: eksik / başarısız koşular")
        L += [f"- {u}" for u in uy]
    L.append("")
    L.append("## Eşikler")
    L.append("")
    L.append("| eşik | değer | eşik değeri | geçti? |")
    L.append("|---|---|---|---|")
    for t in r["esikler"]:
        L.append(f"| {t['ad']} | {t['deger']} | {t['esik']} | {_gecti(t, r['pilot'])} |")
    e = r["b_a1"]
    L.append("")
    L.append(f"- n = {e['n']} eşli soru" + (" (**pilot, karar yok**: n < 30)" if r["pilot"] else ""))
    L.append(f"- İşaret testi (tek yönlü, eşitlik atılır): +{e['isaret']['pozitif']} / −{e['isaret']['negatif']} "
             f"/ ={e['isaret']['beraber']}, p = {e['isaret']['p']:.4f}")
    a = r["ara"]
    if a["degerlendirilebilir"]:
        L.append(f"- Ara durdurma (ilk {ARA_N} soru, ort. B−A1 ≤ {ARA_ESIK:.0f}): ort = {a['ortalama']:+.1f} → "
                 + ("**TETİKLENDİ → RED**" if a["tetik"] else "tetiklenmedi"))
    else:
        L.append(f"- Ara durdurma: değerlendirilemedi (ilk {ARA_N} soruda yalnız {a['n']} eşli fark var)")
    L.append("- ARŞİV koşulu (ort(B−A1) < 0 ya da $(B) > $(A1)): " + ("**VAR**" if r["arsiv_kosulu"] else "yok"))

    L.append("")
    L.append("## Ayrıntı")
    L.append("")
    L.append(f"### Sistemler ({len(r['ids'])} soru)")
    L.append("")
    L.append("| sistem | ort. recall@30 (puan) | ort. $ | ort. süre (s) | web arama ort. |")
    L.append("|---|---|---|---|---|")
    for ad, s in (("B", r["sb"]), ("A1", r["s1"]), ("A0", r["s0"])):
        rc = ortalama([_pts(s[i]["recall"]) for i in r["ids"]])
        ws = ortalama([s[i]["kosu"]["sonuc"].get("web_arama") for i in r["ids"]
                       if s[i]["kosu"]["sonuc"] and s[i]["kosu"]["sonuc"].get("web_arama") is not None])
        L.append(f"| {ad} | {_f(rc)} | {_f(r['maliyet'].get(ad), 3)} | {_f(r['sure'][ad], 0)} | {_f(ws, 1)} |")
    L.append("")
    L.append("### A0 karşılaştırmaları (betimsel)")
    for ad, k in (("B−A0", "b_a0"), ("A1−A0", "a1_a0")):
        x = r[k]
        L.append(f"- {ad}: n={x['n']}, ort = {_f(x['ortalama'], 1, ' puan')}, işaret +{x['isaret']['pozitif']}/"
                 f"−{x['isaret']['negatif']}, p = {x['isaret']['p']:.4f}")
    L.append("")
    L.append("### Alan kırılımı")
    alanlar = {}
    for q in r["sorular"]:
        if q["alan"]:
            alanlar.setdefault(q["alan"], []).append(q["id"])
    if not alanlar:
        L.append("Soru dosyasında alan bilgisi yok; kırılım yapılmadı.")
    else:
        L.append("")
        L.append("| alan | n | B | A1 | A0 | B−A1 |")
        L.append("|---|---|---|---|---|---|")
        for al, qs in sorted(alanlar.items()):
            def m(s, qs=qs):
                return ortalama([_pts(s[i]["recall"]) for i in qs])
            d = [r["b_a1"]["farklar"][i] for i in qs if i in r["b_a1"]["farklar"]]
            L.append(f"| {al} | {len(qs)} | {_f(m(r['sb']))} | {_f(m(r['s1']))} | {_f(m(r['s0']))} | {_f(ortalama(d))} |")
    L.append("")
    L.append("### Soru başına recall@30 (puan)")
    L.append("")
    L.append("| soru | B | A1 | A0 | B−A1 | durum B/A1/A0 |")
    L.append("|---|---|---|---|---|---|")
    for i in r["ids"]:
        d = r["b_a1"]["farklar"].get(i)
        L.append(f"| {i} | {_f(_pts(r['sb'][i]['recall']))} | {_f(_pts(r['s1'][i]['recall']))} | "
                 f"{_f(_pts(r['s0'][i]['recall']))} | {_f(d)} | "
                 f"{r['sb'][i]['kosu']['durum']}/{r['s1'][i]['kosu']['durum']}/{r['s0'][i]['kosu']['durum']} |")
    L.append("")
    L.append("### B kaynak durumu")
    bk = r["b_kaynak"]
    if bk["eksik"]:
        L.append(f"- EKSİK kaynaklı koşu: {len(bk['eksik'])}/{len(r['ids'])}")
        for i, e2 in bk["eksik"].items():
            L.append(f"  - {i}: {', '.join(e2)}")
    else:
        L.append("- EKSİK kaynak yok (ya da B verisi yok).")
    L.append(f"- OZET_YOK alıntı durumu: {bk['ozet_yok']}/{bk['calisma_toplam']} çalışma")
    if bk["ozet_arxiv"]:
        L.append("- ozet_arxiv sayaçları (toplam): "
                 + ", ".join(f"{k.split('.', 1)[1]}={int(v)}" for k, v in sorted(bk["ozet_arxiv"].items())))
    else:
        L.append("- ozet_arxiv sayaçları: yok")
    L.append("")
    L.append("### Kararlılık (B, k koşu, soru içi örnek std. sapması, n−1)")
    kr = r["kararlilik"]
    if kr is None:
        L.append("Kararlılık koşusu verilmedi.")
    elif not kr["satir"]:
        L.append("Kararlılık dizininde kullanılabilir soru yok.")
    else:
        L.append(f"- {len(kr['satir'])} soru; ort. std = {kr['ort_std']:.2f} puan, en büyük = {kr['maks_std']:.2f}")
        for s in kr["satir"]:
            L.append(f"  - {s['id']}: k={s['k']}, recall {', '.join(f'{x:.1f}' for x in s['recall'])}, std {s['std']:.2f}"
                     + (f", {s['basarisiz']} başarısız (=0)" if s["basarisiz"] else ""))
        if len(kr["satir"]) != 10:
            L.append(f"  - NOT: beklenen 10 soru, bulunan {len(kr['satir'])}.")
    L.append("")
    L.append("### Sadakat")
    sd = r["sadakat"]
    if sd["var"]:
        L.append(f"- n={sd['n']}, sayım: {sd['sayim']}; Wilson alt (z=1,96) = {sd['wilson']:.3f} "
                 "(betimsel; bağlayıcı olan sayıdır)")
        if not sd["tam"]:
            L.append("- n < 30: sadakat için pilot, eşik hükmü yok.")
    else:
        L.append("- Sadakat dosyası verilmedi.")
    L.append("")
    L.append("## Bilinen sınırlamalar")
    L += [f"- {s}" for s in SINIRLAMALAR]
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="analiz.rapor")
    ap.add_argument("--b", required=True)
    ap.add_argument("--a1", required=True)
    ap.add_argument("--a0", required=True)
    ap.add_argument("--altin-dizin", required=True)
    ap.add_argument("--sorular", help="varsayılan: <altin-dizin>/sorular.json")
    ap.add_argument("--sadakat")
    ap.add_argument("--kararlilik")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    r = hesapla(a.b, a.a1, a.a0, a.altin_dizin, a.sadakat, a.kararlilik, a.sorular)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown(r), encoding="utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    print(f"{r['hukum']} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
