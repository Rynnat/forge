"""Çıktılar: sonuc.json (tam), ozet.md (şefe dönen, ≤ ozet_token_cap token), funnel.json.

Token sayımı tahmindir ve TEMKİNLİ yapılır: ceil(karakter / 3.0) (İngilizce metinde gerçek
token sayısı genelde karakter/4 civarıdır; tahmin yukarı yuvarlar). Tavan aşılırsa önce
alıntılar, sonra gerekçeler kısaltılır.
"""
from __future__ import annotations

import json
import math


def est_tokens(s: str) -> int:
    return math.ceil(len(s) / 3.0)


def _short(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: max(0, n - 1)].rstrip() + "…"


def render_ozet(ctx, final: list[dict], qlen: int = 220, glen: int = 200) -> str:
    f = ctx.funnel
    fd = f.as_dict()
    L = [f"# Orkestra özeti", f"Soru: {ctx.soru}", f"Kesim: {ctx.kesim} | koşu: {ctx.run_id}",
         f"Durum: {fd['durum']}" + (f" (eksik: {', '.join(fd['eksik_kaynaklar'])})" if fd["eksik_kaynaklar"] else ""),
         f"Maliyet (teorik, liste fiyatı): ${ctx.ledger.total:.3f} | süre: {ctx.times.get('toplam', 0):.0f} s",
         "", "## Funnel"]
    for s in f.stages:
        d = ", ".join(f"{k} {v}" for k, v in s.dusen.items()) or "–"
        L.append(f"- {s.name}: {s.giren} → {s.cikan} (düşen: {d})")
    src = "; ".join(f"{k} {v['durum']}" + (f" [{_short(v.get('sebep', ''), 60)}]" if v.get("sebep") else "")
                    for k, v in f.sources.items())
    L += [f"Kaynaklar: {src}", "", f"## {len(final)} çalışma (önem sırasıyla)"]
    for x in final:
        q = f' «{_short(x["alinti"], qlen)}»' if x["alinti"] and qlen > 0 else (" «alıntı yok: özet erişilemedi»" if x["alinti_durum"] == "OZET_YOK" else "")
        L.append(f"{x['sira']}. {x['id']} — {_short(x['baslik'], 140)} ({x['tarih']}). {_short(x['gerekce'], glen)}{q}")
    return "\n".join(L) + "\n"


def fit_ozet(ctx, final: list[dict]) -> str:
    cap = ctx.cfg.ozet_token_cap
    for qlen, glen in ((220, 200), (160, 180), (110, 160), (70, 140), (0, 120), (0, 80)):
        txt = render_ozet(ctx, final, qlen, glen)
        if est_tokens(txt) <= cap:
            return txt
    return txt[: cap * 3]


def write_outputs(ctx, final: list[dict], cards: list[dict]) -> dict:
    ctx.out.mkdir(parents=True, exist_ok=True)
    ozet = fit_ozet(ctx, final)
    (ctx.out / "ozet.md").write_text(ozet, encoding="utf-8")
    fd = ctx.funnel.as_dict()
    summary = {
        "run_id": ctx.run_id, "soru": ctx.soru, "kesim": ctx.kesim, "durum": fd["durum"],
        "eksik_kaynaklar": fd["eksik_kaynaklar"], "funnel_dengeli": fd["dengeli"],
        "maliyet_usd": round(ctx.ledger.total, 4), "maliyet_asama": ctx.ledger.by_stage,
        "sureler_s": ctx.times, "ozet_token_tahmini": est_tokens(ozet),
        "plan": ctx.plan, "tohumlar": getattr(ctx, "seeds", []),
        "calismalar": final,
    }
    (ctx.out / "sonuc.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (ctx.out / "funnel.json").write_text(json.dumps(fd, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (ctx.out / "kartlar.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary
