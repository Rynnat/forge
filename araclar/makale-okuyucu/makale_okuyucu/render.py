"""Kart → kompakt Markdown (token bütçeli). Token ≈ karakter / 3.5 (kaba tahmin)."""
from __future__ import annotations

from makale_okuyucu.config import FIELDS

TITLES = {
    "problem": "Problem", "katkilar": "Katkılar", "yontem": "Yöntem",
    "veri_setleri_ve_kaynaklar": "Veri setleri / kaynaklar", "deney_kurulumu": "Deney kurulumu",
    "ana_sonuclar": "Ana sonuçlar", "sinirliliklar": "Sınırlılıklar", "gelecek_calisma": "Gelecek çalışma",
    "kapsam_disi": "Kapsam dışı", "en_yakin_isler": "En yakın işler",
}
# bütçe aşılınca madde düşürme sırası (önce bunların sonundaki maddeler gider)
DROP_ORDER = ["en_yakin_isler", "veri_setleri_ve_kaynaklar", "deney_kurulumu", "yontem",
              "gelecek_calisma", "katkilar", "ana_sonuclar", "sinirliliklar", "kapsam_disi", "problem"]


def est_tokens(s: str) -> int:
    # karakter/3.5: Markdown + sayı + Türkçe karakterler İngilizce düzyazıdan pahalı
    return (len(s) * 2 + 6) // 7


def _cut(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _item_line(f: str, it: dict, qlen: int, tlen: int) -> str:
    head = _cut(it["text"], tlen)
    if f == "veri_setleri_ve_kaynaklar" and it.get("name"):
        head = (f"**{_cut(it['name'], 60)}**" + (f" <{it['link']}>" if it.get("link") else "")
                + f" — {_cut(it['text'], max(40, tlen - 40))}")
    elif f == "en_yakin_isler" and it.get("name"):
        head = f"**{_cut(it['name'], 50)}** — {_cut(it.get('relation') or it['text'], max(40, tlen // 2))}"
    tag = f"p.{it['page']}" if it.get("check") == "VERIFIED" else "UNVERIFIED"
    q = f' "{_cut(it.get("quote", ""), qlen)}"' if qlen > 0 and it.get("quote") else ""
    return f"- {head} [{tag}]{q}"


# (alıntı uzunluğu, madde metni uzunluğu) kademeleri; sığana kadar sıkılaştırılır
LEVELS = [(110, 400), (70, 300), (40, 200), (0, 200), (0, 140), (0, 100)]


def render(card: dict, max_tokens: int = 1500) -> str:
    fields = {f: list(card["fields"].get(f, [])) for f in FIELDS}
    dropped = {f: 0 for f in FIELDS}
    for qlen, tlen in LEVELS:
        md = _render(card, fields, dropped, qlen, tlen)
        if est_tokens(md) <= max_tokens:
            return md
    # en sıkı kademede de sığmadı: en kalabalık alandan madde düşür (eşitlikte DROP_ORDER)
    qlen, tlen = LEVELS[-1]
    while est_tokens(md) > max_tokens:
        cands = [f for f in DROP_ORDER if len(fields[f]) > 1]
        if not cands:
            break
        f = max(cands, key=lambda x: (len(fields[x]), -DROP_ORDER.index(x)))
        fields[f].pop()
        dropped[f] += 1
        md = _render(card, fields, dropped, qlen, tlen)
    return md


def _render(card: dict, fields: dict, dropped: dict, qlen: int, tlen: int) -> str:
    f_ = card.get("funnel", {})
    lines = [f"# {card.get('title') or card['key']}",
             f"`{card['key']}` · {card.get('pages')} s. · durum {card['status']} · "
             f"madde {f_.get('items_in_card', '?')} (UNVERIFIED {f_.get('unverified_in_card', '?')})"]
    if card.get("eksik_parcalar"):
        miss = "; ".join(f"{e['bolumler']} p.{e['sayfalar']} {e['durum']}" for e in card["eksik_parcalar"])
        lines.append(f"**EKSİK OKUNDU:** {miss}")
    for f in FIELDS:
        items = fields[f]
        if not items and not dropped[f]:
            lines.append(f"## {TITLES[f]}\n- (kartta yok)")
            continue
        lines.append(f"## {TITLES[f]}")
        lines += [_item_line(f, it, qlen, tlen) for it in items]
        if dropped[f]:
            lines.append(f"- (+{dropped[f]} madde JSON'da)")
    if qlen == 0:
        lines.append("_Alıntılar bütçe nedeniyle gizli; tam alıntı + sayfa card.json'da._")
    return "\n".join(lines) + "\n"
