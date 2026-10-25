"""recall@30 puanlayıcı (ONKAYIT-orkestra-v0 "Metrikler"). Ağsız, yalnız stdlib.

  python -m orkestra.deney.puanla tek  --sistem sonuc.json --altin altin.json
  python -m orkestra.deney.puanla esli --manifest manifest.json

Manifest: {"sorular": [{"id": "q1", "A": "a/sonuc.json", "B": "b/sonuc.json", "altin": "q1.json"}, ...]}
(yollar manifest dosyasına göre). Altın biçimi: [{"arxiv_id","doi","baslik"}] (her alan eksik olabilir);
başka biçim gelirse yalnız `altin_yukle` değişir.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .. import normalize as N
from ..records import _conflict, title_sim

K = 30
ESIK = 0.90  # başlık benzerliği (ONKAYIT)


def _oku(yol) -> object:
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def altin_yukle(yol) -> list[dict]:
    """Altın dosyası -> [{"arxiv_id","doi","baslik"}]. Biçim değişirse yalnız burayı uyarla."""
    veri = _oku(yol)
    if isinstance(veri, dict):  # {"calismalar": [...]} gibi sarmalayıcıyı da kabul et
        veri = veri.get("calismalar") or veri.get("altin") or []
    return [{"arxiv_id": g.get("arxiv_id"), "doi": g.get("doi"), "baslik": g.get("baslik") or g.get("title")}
            for g in veri]


def sistem_yukle(yol) -> list[dict]:
    """orkestra sonuc.json -> sıralı liste (dosya sırası esas)."""
    return [{"arxiv_id": c.get("arxiv_id"), "doi": c.get("doi"), "baslik": c.get("baslik")}
            for c in _oku(yol).get("calismalar", [])]


def _anahtar(c: dict) -> dict:
    ax = N.norm_arxiv(c.get("arxiv_id")) or N.arxiv_from_doi(c.get("doi"))
    doi = N.norm_doi(c.get("doi"))
    return {"arxiv_id": ax, "doi": None if N.arxiv_from_doi(doi) else doi,  # arXiv-DOI arxiv kuralına gider
            "baslik": c.get("baslik") or "", "nt": N.norm_title(c.get("baslik"))}


def esle(liste: list[dict], altin: list[dict], k: int = K) -> list[dict]:
    """liste[:k] öğelerini altınla eşler. Kural önceliği: arxiv > doi > başlık (her kural tüm liste
    üzerinde sırayla); bir altın en çok bir kez, bir liste öğesi en çok bir kez eşleşir.
    Dönüş: [{"sira": i, "altin": j, "kural": "arxiv"|"doi"|"baslik", "sim": f|None}]."""
    L = [_anahtar(c) for c in liste[:k]]
    G = [_anahtar(c) for c in altin]
    li, gi, out = set(), set(), []

    def ekle(i, j, kural, sim=None):
        li.add(i)
        gi.add(j)
        out.append({"sira": i + 1, "altin": j, "kural": kural, "sim": sim})

    for kural, alan in (("arxiv", "arxiv_id"), ("doi", "doi")):
        for i, l in enumerate(L):
            if i in li or not l[alan]:
                continue
            for j, g in enumerate(G):
                if j not in gi and g[alan] == l[alan]:
                    ekle(i, j, kural)
                    break
    adaylar = []  # başlık: en iyi çiftten başlayarak açgözlü
    for i, l in enumerate(L):
        for j, g in enumerate(G):
            if i in li or j in gi or not l["nt"] or not g["nt"]:
                continue
            s = title_sim(l["nt"], g["nt"])
            if s >= ESIK and not _conflict({"arxiv_id": l["arxiv_id"], "title": l["baslik"]},
                                           {"arxiv_id": g["arxiv_id"], "title": g["baslik"]}, l["nt"], g["nt"]):
                adaylar.append((-s, i, j))
    for ns, i, j in sorted(adaylar):
        if i not in li and j not in gi:
            ekle(i, j, "baslik", round(-ns, 4))
    return sorted(out, key=lambda m: m["sira"])


def recall_at_k(liste: list[dict], altin: list[dict], k: int = K) -> dict:
    m = esle(liste, altin, k)
    payda = min(k, len(altin))
    return {"recall": (len(m) / payda) if payda else None, "eslesen": len(m), "payda": payda,
            "altin_n": len(altin), "liste_n": min(k, len(liste)), "eslesmeler": m}


def isaret_testi(farklar: list[float]) -> dict:
    """Tek yönlü işaret testi (H1: B>A). Beraberlikler atılır. p = P(X>=pozitif | n, 0.5), kesin binom."""
    poz = sum(1 for d in farklar if d > 0)
    neg = sum(1 for d in farklar if d < 0)
    n = poz + neg
    p = sum(math.comb(n, i) for i in range(poz, n + 1)) / 2 ** n if n else 1.0
    return {"pozitif": poz, "negatif": neg, "beraber": len(farklar) - n, "n": n, "p": p}


def wilson_alt(x: int, n: int, z: float = 1.96) -> float:
    """Wilson skor aralığı alt sınırı (varsayılan z=1.96; 28/30 -> 0.787, z=1.645 -> 0.817; ONKAYIT "0.79" z belirtmiyor)."""
    if n == 0:
        return 0.0
    ph = x / n
    d = 1 + z * z / n
    mer = ph + z * z / (2 * n)
    sp = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return (mer - sp) / d


def esli(sorular: list[dict]) -> dict:
    """sorular: [{"id","A": liste,"B": liste,"altin": liste}] -> soru başına B-A, ortalama, işaret testi."""
    satir = []
    for q in sorular:
        a, b = recall_at_k(q["A"], q["altin"]), recall_at_k(q["B"], q["altin"])
        satir.append({"id": q.get("id"), "A": a["recall"], "B": b["recall"],
                      "fark": (b["recall"] - a["recall"]) if a["recall"] is not None else None})
    f = [s["fark"] for s in satir if s["fark"] is not None]
    return {"n": len(f), "ortalama_fark": sum(f) / len(f) if f else None, "sorular": satir,
            "isaret": isaret_testi(f)}


def _cli(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m orkestra.deney.puanla")
    sp = ap.add_subparsers(dest="komut", required=True)
    t = sp.add_parser("tek")
    t.add_argument("--sistem", required=True)
    t.add_argument("--altin", required=True)
    e = sp.add_parser("esli")
    e.add_argument("--manifest", required=True)
    a = ap.parse_args(argv)
    if a.komut == "tek":
        r = recall_at_k(sistem_yukle(a.sistem), altin_yukle(a.altin))
    else:
        mp = Path(a.manifest)
        kok = mp.parent
        qs = [{"id": q.get("id"), "A": sistem_yukle(kok / q["A"]), "B": sistem_yukle(kok / q["B"]),
               "altin": altin_yukle(kok / q["altin"])} for q in _oku(mp)["sorular"]]
        r = esli(qs)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
