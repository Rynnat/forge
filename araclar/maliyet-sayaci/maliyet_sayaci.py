"""maliyet-sayaci: Claude Code transkriptlerinden gerçek token/maliyet kullanımı.

Gizlilik: yalnız usage/model/zaman/id alanları okunur; mesaj içeriği asla tutulmaz ya da yazdırılmaz.
Ayrıntı: SPEC.md.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ARAC_DIZINI = Path(__file__).resolve().parent
VARSAYILAN_FIYAT = ARAC_DIZINI / "fiyatlar.json"
VARSAYILAN_KOK = Path.home() / ".claude" / "projects"
GAPMINE_RAPORLAR = Path(r"C:\Users\LENOVO\Projeler\akademik-bosluk\gapmine\reports")
FORGE_ARACLAR = ARAC_DIZINI.parent
MAKS_SATIR = 40
VERI_SATIRI = MAKS_SATIR - 7  # baslik+cizgi+TOPLAM+gizli notu+kalite(2)+abonelik notu
AJAN_CIKTI = re.compile(r"^a[0-9a-f]{8,}\.output$")
ABONELIK_NOTU = "Not: abonelik (Pro/Max) kullanicisi icin $ teoriktir (API liste fiyati), fatura degildir."

TOKEN_ALANLARI = ("input", "output", "cw5m", "cw1h", "cache_read", "web_search")


# --------------------------------------------------------------------------- veri yapıları
@dataclass
class Mesaj:
    anahtar: str
    model: str | None
    zaman: str | None
    oturum: str
    ajan: str  # "ana" ya da ajan id
    input: int = 0
    output: int = 0
    cw5m: int = 0
    cw1h: int = 0
    cache_read: int = 0
    web_search: int = 0
    fast: bool = False
    bolge: str | None = None
    usage_var: bool = True
    kirilim_yok: bool = False  # cache_creation 5m/1h kırılımı yoktu → 5m sayıldı


@dataclass
class Kalite:
    dosya: int = 0
    satir: int = 0
    bozuk: int = 0
    bozuk_dosyalar: dict = field(default_factory=dict)
    tekrar_satir: int = 0
    usage_yok: int = 0
    id_yok: int = 0
    kirilim_yok: int = 0
    fiyatsiz_modeller: dict = field(default_factory=dict)

    def sozluk(self) -> dict:
        return {
            "dosya": self.dosya, "satir": self.satir, "bozuk_satir": self.bozuk,
            "bozuk_dosyalar": self.bozuk_dosyalar, "tekrar_satir_tekillestirildi": self.tekrar_satir,
            "usage_eksik_mesaj": self.usage_yok, "id_siz_mesaj": self.id_yok,
            "cache_kirilimi_yok_5m_sayildi": self.kirilim_yok,
            "fiyati_bilinmeyen_modeller": self.fiyatsiz_modeller,
        }


def _int(v) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else 0


# --------------------------------------------------------------------------- satır okuma
def usage_cek(d: dict, oturum: str, ajan: str) -> Mesaj | None:
    """Bir transkript satırından yalnız izinli alanları çeker. assistant değilse None."""
    if d.get("type") != "assistant":
        return None
    msg = d.get("message")
    if not isinstance(msg, dict):
        msg = {}
    anahtar = msg.get("id") or d.get("requestId")
    m = Mesaj(
        anahtar=anahtar if isinstance(anahtar, str) else "",
        model=msg.get("model") if isinstance(msg.get("model"), str) else None,
        zaman=d.get("timestamp") if isinstance(d.get("timestamp"), str) else None,
        oturum=d.get("sessionId") if isinstance(d.get("sessionId"), str) else oturum,
        ajan=(d.get("agentId") if isinstance(d.get("agentId"), str) else None) or ajan,
    )
    u = msg.get("usage")
    if not isinstance(u, dict):
        m.usage_var = False
        return m
    m.input = _int(u.get("input_tokens"))
    m.output = _int(u.get("output_tokens"))
    m.cache_read = _int(u.get("cache_read_input_tokens"))
    cw = _int(u.get("cache_creation_input_tokens"))
    cc = u.get("cache_creation")
    if isinstance(cc, dict) and ("ephemeral_5m_input_tokens" in cc or "ephemeral_1h_input_tokens" in cc):
        m.cw5m = _int(cc.get("ephemeral_5m_input_tokens"))
        m.cw1h = _int(cc.get("ephemeral_1h_input_tokens"))
        kalan = cw - m.cw5m - m.cw1h  # kırılım toplamı tutmazsa fark 5m sayılır
        if kalan > 0:
            m.cw5m += kalan
    else:
        m.cw5m = cw
        m.kirilim_yok = cw > 0
    stu = u.get("server_tool_use")
    if isinstance(stu, dict):
        m.web_search = _int(stu.get("web_search_requests"))
    m.fast = u.get("speed") == "fast"
    geo = u.get("inference_geo")
    m.bolge = geo if isinstance(geo, str) else None
    return m


class Toplayici:
    """Dosyaları okur, mesaj id'siyle küresel tekilleştirir."""

    def __init__(self) -> None:
        self.mesajlar: dict[str, Mesaj] = {}
        self.idsiz: list[Mesaj] = []
        self.kalite = Kalite()
        self.ajan_turleri: dict[str, str] = {}

    def satirlar_ekle(self, satirlar, oturum: str, ajan: str, kaynak: str = "?") -> None:
        for satir in satirlar:
            if not satir.strip():
                continue
            self.kalite.satir += 1
            try:
                d = json.loads(satir)
            except ValueError:
                d = None
            if not isinstance(d, dict):
                self.kalite.bozuk += 1
                self.kalite.bozuk_dosyalar[kaynak] = self.kalite.bozuk_dosyalar.get(kaynak, 0) + 1
                continue
            m = usage_cek(d, oturum, ajan)
            del d  # içerik tutulmaz
            if m is None:
                continue
            self._ekle(m)

    def _ekle(self, m: Mesaj) -> None:
        if not m.anahtar:
            self.kalite.id_yok += 1
            self.idsiz.append(m)
            return
        eski = self.mesajlar.get(m.anahtar)
        if eski is None:
            self.mesajlar[m.anahtar] = m
            return
        self.kalite.tekrar_satir += 1
        for a in TOKEN_ALANLARI:
            setattr(eski, a, max(getattr(eski, a), getattr(m, a)))
        eski.fast = eski.fast or m.fast
        if not eski.usage_var:
            eski.kirilim_yok, eski.bolge = m.kirilim_yok, m.bolge
        elif m.usage_var:
            eski.kirilim_yok = eski.kirilim_yok and m.kirilim_yok
        eski.usage_var = eski.usage_var or m.usage_var
        if m.zaman and (not eski.zaman or m.zaman < eski.zaman):
            eski.zaman = m.zaman
        if eski.model in (None, "<synthetic>") and m.model:
            eski.model = m.model

    def dosya_ekle(self, yol: Path, oturum: str, ajan: str) -> None:
        self.kalite.dosya += 1
        # salt okunur; gecersiz UTF-8 bayti U+FFFD olur, JSON bozuksa satir bozuk sayilir
        with open(yol, "r", encoding="utf-8", errors="replace") as f:
            self.satirlar_ekle(f, oturum, ajan, kaynak=str(yol))

    def tum_mesajlar(self) -> list[Mesaj]:
        tum = list(self.mesajlar.values()) + self.idsiz
        # usage'ı eksik olanlar tekilleştirme sonrası sayılır (birleşmiş tekrarlar bir kez)
        self.kalite.usage_yok = sum(1 for m in tum if not m.usage_var)
        self.kalite.kirilim_yok = sum(1 for m in tum if m.kirilim_yok)
        return tum


# --------------------------------------------------------------------------- keşif
@dataclass
class OturumDosyalari:
    oturum: str
    proje: str
    ana: Path | None
    ajanlar: list  # (ajan_id, yol, meta_yolu, workflow)


def oturumlari_bul(kok: Path, proje: str | None = None) -> list[OturumDosyalari]:
    sonuc = []
    if not kok.is_dir():
        return sonuc
    for pdir in sorted(p for p in kok.iterdir() if p.is_dir()):
        if proje and proje.lower() not in pdir.name.lower():
            continue
        idler = {p.stem for p in pdir.glob("*.jsonl")} | {p.name for p in pdir.iterdir() if p.is_dir()}
        for sid in sorted(idler):
            ana = pdir / f"{sid}.jsonl"
            sub = pdir / sid / "subagents"
            ajanlar = []
            if sub.is_dir():
                for y in sorted(sub.rglob("agent-*.jsonl")):
                    aid = y.stem[len("agent-"):]
                    wf = y.parent.name if y.parent != sub else None
                    ajanlar.append((aid, y, y.with_name(y.stem + ".meta.json"), wf))
            if not ana.is_file() and not ajanlar:
                continue
            sonuc.append(OturumDosyalari(sid, pdir.name, ana if ana.is_file() else None, ajanlar))
    return sonuc


def ajan_turu_oku(meta: Path) -> str | None:
    """meta.json'dan YALNIZ agentType alanı."""
    try:
        with open(meta, "r", encoding="utf-8") as f:
            d = json.load(f)
        t = d.get("agentType") if isinstance(d, dict) else None
        return t if isinstance(t, str) else None
    except (OSError, ValueError):
        return None


def oturumu_oku(top: Toplayici, o: OturumDosyalari) -> None:
    if o.ana:
        top.dosya_ekle(o.ana, o.oturum, "ana")
    for aid, yol, meta, wf in o.ajanlar:
        top.dosya_ekle(yol, o.oturum, aid)
        tur = ajan_turu_oku(meta) or "?"
        top.ajan_turleri[aid] = f"{tur}@{wf}" if wf else tur


# --------------------------------------------------------------------------- fiyat
class Fiyatlar:
    def __init__(self, yol: Path = VARSAYILAN_FIYAT) -> None:
        with open(yol, "r", encoding="utf-8") as f:
            self.veri = json.load(f)
        self.modeller: dict = self.veri["modeller"]
        self.web = float(self.veri.get("web_search_per_1k", 0.0))
        self.bolge = self.veri.get("bolge_carpanlari", {})
        self.kaynak = self.veri.get("_kaynak", "")
        self.tarih = self.veri.get("_tarih", "")

    def bul(self, model: str | None) -> dict | None:
        if not model:
            return None
        if model in self.modeller:
            return self.modeller[model]
        adaylar = [k for k in self.modeller if model.startswith(k + "-") or model.startswith(k + "@")]
        return self.modeller[max(adaylar, key=len)] if adaylar else None

    def maliyet(self, m: Mesaj) -> float | None:
        p = self.bul(m.model)
        if p is None:
            return None
        uzun = p.get("uzun_baglam")
        if uzun and (m.input + m.cw5m + m.cw1h + m.cache_read) > uzun["esik"]:
            p = uzun
        usd = (m.input * p["input"] + m.output * p["output"] + m.cw5m * p["cache_write_5m"]
               + m.cw1h * p["cache_write_1h"] + m.cache_read * p["cache_read"]) / 1e6
        if m.fast:
            usd *= self.bul(m.model).get("fast_carpan", 1.0)
        if m.bolge in self.bolge:
            usd *= float(self.bolge[m.bolge])
        return usd + m.web_search * self.web / 1000.0


# --------------------------------------------------------------------------- toplama
def _bos() -> dict:
    return {"mesaj": 0, "input": 0, "output": 0, "cw5m": 0, "cw1h": 0, "cache_read": 0,
            "web_search": 0, "usd": 0.0, "fiyatsiz_mesaj": 0, "modeller": set(),
            "ilk": None, "son": None}


def _topla(acc: dict, m: Mesaj, usd: float | None) -> None:
    acc["mesaj"] += 1
    for a in TOKEN_ALANLARI:
        acc[a] += getattr(m, a)
    if usd is None:
        acc["fiyatsiz_mesaj"] += 1
    else:
        acc["usd"] += usd
    if m.model:
        acc["modeller"].add(m.model)
    if m.zaman:
        acc["ilk"] = m.zaman if acc["ilk"] is None or m.zaman < acc["ilk"] else acc["ilk"]
        acc["son"] = m.zaman if acc["son"] is None or m.zaman > acc["son"] else acc["son"]


def _disa(acc: dict) -> dict:
    d = dict(acc)
    d["modeller"] = sorted(acc["modeller"])
    d["cache_write"] = acc["cw5m"] + acc["cw1h"]
    d["usd"] = round(acc["usd"], 4)
    return d


def grupla(mesajlar, fiyat: Fiyatlar, kalite: Kalite, anahtar_fn) -> dict:
    gruplar: dict = {}
    for m in mesajlar:
        usd = fiyat.maliyet(m)
        if usd is None and m.model and m.usage_var:
            kalite.fiyatsiz_modeller[m.model] = kalite.fiyatsiz_modeller.get(m.model, 0) + 1
        k = anahtar_fn(m)
        if k is None:
            continue
        _topla(gruplar.setdefault(k, _bos()), m, usd)
    return gruplar


# --------------------------------------------------------------------------- biçim
def _k(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1e6:.1f}M"
    if n >= 10_000:
        return f"{n / 1e3:.0f}k"
    return str(n)


def tablo(basliklar, satirlar) -> str:
    gen = [len(b) for b in basliklar]
    for s in satirlar:
        gen = [max(g, len(str(h))) for g, h in zip(gen, s)]
    cizgi = lambda s: "  ".join(str(h).rjust(g) if i else str(h).ljust(g) for i, (h, g) in enumerate(zip(s, gen)))
    return "\n".join([cizgi(basliklar), "  ".join("-" * g for g in gen)] + [cizgi(s) for s in satirlar])


def _satir(ad, acc, ek=()):
    usd = f"{acc['usd']:.2f}" + ("*" if acc["fiyatsiz_mesaj"] else "")
    return [ad, *ek, acc["mesaj"], _k(acc["input"]), _k(acc["output"]), _k(acc["cw5m"] + acc["cw1h"]),
            _k(acc["cache_read"]), usd]


TOKEN_BASLIK = ["msj", "giris", "cikis", "c-yaz", "c-oku", "$"]


def kalite_satiri(k: Kalite) -> str:
    s = (f"veri: {k.dosya} dosya, {k.satir} satir, bozuk {k.bozuk}, tekrar(tekillestirildi) {k.tekrar_satir}, "
         f"usage-eksik {k.usage_yok}, id-siz {k.id_yok}")
    if k.kirilim_yok:
        s += f", 5m/1h-kirilimsiz {k.kirilim_yok}"
    if k.fiyatsiz_modeller:
        s += f"\nFIYATSIZ model (token sayildi, $ yok, '*'): {k.fiyatsiz_modeller}"
    return s


# --------------------------------------------------------------------------- komutlar
def _tarih_ok(zaman: str | None, since: str | None) -> bool:
    return since is None or (zaman is not None and zaman[:10] >= since)


def cmd_sessions(a, fiyat: Fiyatlar) -> dict:
    top = Toplayici()
    oturumlar = oturumlari_bul(Path(a.root), a.proje)
    proje_of = {}
    ajan_say = {}
    for o in oturumlar:
        oturumu_oku(top, o)
        proje_of[o.oturum] = o.proje
        ajan_say[o.oturum] = len(o.ajanlar)
    msj = [m for m in top.tum_mesajlar() if _tarih_ok(m.zaman, a.since)]
    g = grupla(msj, fiyat, top.kalite, lambda m: m.oturum)
    sirali = sorted(g.items(), key=lambda kv: kv[1]["son"] or "", reverse=True)
    toplam = _bos()
    for m in msj:
        _topla(toplam, m, fiyat.maliyet(m))
    return {
        "komut": "sessions", "since": a.since,
        "oturumlar": [{"oturum": k, "proje": proje_of.get(k, "?"), "alt_ajan": ajan_say.get(k, 0), **_disa(v)}
                      for k, v in sirali],
        "toplam": _disa(toplam), "kalite": top.kalite.sozluk(), "fiyat_kaynagi": fiyat.kaynak,
    }


def oturum_esle(kok: Path, onek: str) -> OturumDosyalari:
    adaylar = [o for o in oturumlari_bul(kok) if o.oturum.startswith(onek)]
    if not adaylar:
        raise SystemExit(f"oturum bulunamadi: {onek}")
    if len({o.oturum for o in adaylar}) > 1:
        raise SystemExit(f"belirsiz onek, eslesenler: {[o.oturum for o in adaylar][:10]}")
    return adaylar[0]


def cmd_agents(a, fiyat: Fiyatlar) -> dict:
    o = oturum_esle(Path(a.root), a.session)
    top = Toplayici()
    oturumu_oku(top, o)
    for dz in a.ek_dizin or []:
        for y in sorted(glob.glob(os.path.join(dz, "*.output"))):
            p = Path(y)
            # yalniz alt-ajan transkriptleri (a + hex id); b* dosyalari arka plan kabuk ciktisidir, okunmaz
            if AJAN_CIKTI.match(p.name):
                top.dosya_ekle(p, o.oturum, p.stem)
    msj = top.tum_mesajlar()
    g = grupla(msj, fiyat, top.kalite, lambda m: m.ajan)
    toplam = _bos()
    for m in msj:
        _topla(toplam, m, fiyat.maliyet(m))
    sirali = sorted(g.items(), key=lambda kv: (kv[0] != "ana", kv[1]["ilk"] or ""))
    return {
        "komut": "agents", "oturum": o.oturum, "proje": o.proje,
        "ajanlar": [{"ajan": k, "tur": "ana" if k == "ana" else top.ajan_turleri.get(k, "?"), **_disa(v)}
                    for k, v in sirali],
        "toplam": _disa(toplam), "kalite": top.kalite.sozluk(), "fiyat_kaynagi": fiyat.kaynak,
    }


def cmd_since(a, fiyat: Fiyatlar) -> dict:
    top = Toplayici()
    oturumlar = oturumlari_bul(Path(a.root), a.proje)
    for o in oturumlar:
        oturumu_oku(top, o)
    msj = [m for m in top.tum_mesajlar() if _tarih_ok(m.zaman, a.tarih)]
    g = grupla(msj, fiyat, top.kalite, lambda m: m.model or "?")
    gun = grupla(msj, fiyat, Kalite(), lambda m: (m.zaman or "?")[:10])
    toplam = _bos()
    for m in msj:
        _topla(toplam, m, fiyat.maliyet(m))
    oturum_say = len({m.oturum for m in msj})
    ajan_msj = sum(1 for m in msj if m.ajan != "ana")
    return {
        "komut": "since", "tarih": a.tarih, "oturum_sayisi": oturum_say, "alt_ajan_mesaji": ajan_msj,
        "modeller": {k: _disa(v) for k, v in sorted(g.items(), key=lambda kv: -kv[1]["usd"])},
        "gunler": {k: _disa(v) for k, v in sorted(gun.items())},
        "toplam": _disa(toplam), "kalite": top.kalite.sozluk(), "fiyat_kaynagi": fiyat.kaynak,
    }


LLM_ALANLARI = ("calls", "ok", "failed", "input_tokens", "output_tokens", "cache_read_tokens",
                "cache_write_tokens", "cost_usd")


def _llm_blogu(d) -> dict | None:
    if not isinstance(d, dict):
        return None
    blok = d.get("llm") if isinstance(d.get("llm"), dict) else d
    if "cost_usd" not in blok and "input_tokens" not in blok:
        return None
    out = {k: blok.get(k) for k in LLM_ALANLARI if isinstance(blok.get(k), (int, float))}
    if isinstance(blok.get("backend"), str):
        out["backend"] = blok["backend"]
    return out


def tool_loglari(gapmine: Path = GAPMINE_RAPORLAR, forge: Path = FORGE_ARACLAR) -> list[tuple[str, Path]]:
    dosyalar = [("gapmine", p) for p in sorted(gapmine.glob("*.json"))] if gapmine.is_dir() else []
    if forge.is_dir():
        for p in sorted(forge.glob("*/logs/maliyet*.json*")):
            if p.suffix in (".json", ".jsonl"):
                dosyalar.append((p.parent.parent.name, p))
    return dosyalar


def cmd_tools(a, fiyat: Fiyatlar | None = None, gapmine: Path = GAPMINE_RAPORLAR, forge: Path = FORGE_ARACLAR) -> dict:
    araclar: dict = {}
    kalite = {"dosya": 0, "kayit": 0, "bozuk": 0, "llm_blogu_yok": 0}
    for arac, p in tool_loglari(gapmine, forge):
        kalite["dosya"] += 1
        kayitlar = []
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            if p.suffix == ".jsonl":
                for satir in f:
                    if not satir.strip():
                        continue
                    try:
                        kayitlar.append(json.loads(satir))
                    except ValueError:
                        kalite["bozuk"] += 1
            else:
                try:
                    kayitlar.append(json.load(f))
                except ValueError:
                    kalite["bozuk"] += 1
        acc = araclar.setdefault(arac, {"kosu": 0, **{k: 0 for k in LLM_ALANLARI}, "backendler": set()})
        for d in kayitlar:
            b = _llm_blogu(d)
            del d
            if b is None:
                kalite["llm_blogu_yok"] += 1
                continue
            kalite["kayit"] += 1
            acc["kosu"] += 1
            for k in LLM_ALANLARI:
                acc[k] += b.get(k, 0) or 0
            if "backend" in b:
                acc["backendler"].add(b["backend"])
    for v in araclar.values():
        v["backendler"] = sorted(v["backendler"])
        v["cost_usd"] = round(v["cost_usd"], 4)
    return {"komut": "tools", "araclar": araclar, "kalite": kalite,
            "not": "cost_usd aracin kendi bildirdigidir (yeniden fiyatlanmadi)."}


# --------------------------------------------------------------------------- yazdırma
def yazdir(s: dict, limit: int = VERI_SATIRI) -> str:
    out = []
    k = s["komut"]
    if k == "sessions":
        satirlar = [_satir(o["oturum"][:8], o, (o["proje"][-18:], o["alt_ajan"], (o["son"] or "?")[:10]))
                    for o in s["oturumlar"]]
        gizli = max(0, len(satirlar) - limit)
        out.append(tablo(["oturum", "proje", "ajan", "son"] + TOKEN_BASLIK,
                         satirlar[:limit] + [_satir("TOPLAM", s["toplam"], ("", "", ""))]))
        if gizli:
            out.append(f"({gizli} oturum gosterilmedi; --json ile tamami)")
    elif k == "agents":
        satirlar = [_satir(x["ajan"][:17], x, (x["tur"][:22], ",".join(m.replace("claude-", "") for m in x["modeller"])))
                    for x in s["ajanlar"]]
        gizli = max(0, len(satirlar) - limit)
        out.append(f"oturum {s['oturum']} ({s['proje']})")
        out.append(tablo(["ajan", "tur", "model"] + TOKEN_BASLIK,
                         satirlar[:limit] + [_satir("TOPLAM", s["toplam"], ("", ""))]))
        if gizli:
            out.append(f"({gizli} ajan gosterilmedi; --json ile tamami)")
    elif k == "since":
        out.append(f"{s['tarih']} itibariyle: {s['oturum_sayisi']} oturum, alt-ajan mesaji {s['alt_ajan_mesaji']}")
        satirlar = [_satir(m, v) for m, v in s["modeller"].items()]
        out.append(tablo(["model"] + TOKEN_BASLIK, satirlar[:limit - 2] + [_satir("TOPLAM", s["toplam"])]))
    elif k == "tools":
        satirlar = [[a, ",".join(v["backendler"]), v["kosu"], v["calls"], _k(v["input_tokens"]), _k(v["output_tokens"]),
                     _k(v["cache_write_tokens"]), _k(v["cache_read_tokens"]), f"{v['cost_usd']:.4f}"]
                    for a, v in s["araclar"].items()]
        out.append(tablo(["arac", "backend", "kosu", "cagri", "giris", "cikis", "c-yaz", "c-oku", "$"], satirlar[:limit]))
        kq = s["kalite"]
        out.append(f"veri: {kq['dosya']} dosya, {kq['kayit']} kayit, bozuk {kq['bozuk']}, llm-blogu-yok {kq['llm_blogu_yok']}")
        out.append(s["not"])
        return "\n".join(out)
    q = s["kalite"]
    kq = Kalite(dosya=q["dosya"], satir=q["satir"], bozuk=q["bozuk_satir"], tekrar_satir=q["tekrar_satir_tekillestirildi"],
                usage_yok=q["usage_eksik_mesaj"], id_yok=q["id_siz_mesaj"], kirilim_yok=q["cache_kirilimi_yok_5m_sayildi"],
                fiyatsiz_modeller=q["fiyati_bilinmeyen_modeller"])
    out.append(kalite_satiri(kq))
    out.append(ABONELIK_NOTU)
    return "\n".join(out)


def ana(argv=None) -> int:
    p = argparse.ArgumentParser(prog="maliyet_sayaci", description="Claude Code token/maliyet sayaci")
    p.add_argument("--root", default=str(VARSAYILAN_KOK))
    p.add_argument("--fiyat", default=str(VARSAYILAN_FIYAT))
    p.add_argument("--json", action="store_true")
    alt = p.add_subparsers(dest="komut", required=True)
    s = alt.add_parser("sessions")
    s.add_argument("--proje")
    s.add_argument("--since")
    s.add_argument("--limit", type=int, default=VERI_SATIRI)
    g = alt.add_parser("agents")
    g.add_argument("--session", required=True)
    g.add_argument("--ek-dizin", action="append", help="*.output dosyalari (orn. Temp/.../tasks); tekillestirilir")
    n = alt.add_parser("since")
    n.add_argument("tarih")
    n.add_argument("--proje")
    alt.add_parser("tools")
    for sp in alt.choices.values():
        sp.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    a = p.parse_args(argv)
    fiyat = Fiyatlar(Path(a.fiyat))
    sonuc = {"sessions": cmd_sessions, "agents": cmd_agents, "since": cmd_since, "tools": cmd_tools}[a.komut](a, fiyat)
    if a.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=1, default=sorted))
    else:
        print(yazdir(sonuc, min(getattr(a, "limit", VERI_SATIRI), VERI_SATIRI)))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(ana())
