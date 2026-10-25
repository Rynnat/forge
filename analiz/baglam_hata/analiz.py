"""On kayit: forge/ONKAYIT-baglam-hata.md. Salt okunur; icerik tutulmaz (yalniz bayrak + 60 karakterlik ornek, ornek dosyasi TEMP'e yazilir).

Kararlar (veri gorulmeden yazildi):
- Tur = tekil assistant message.id (bloklar birlesir), ctx = max(input+cache_read+cache_creation).
- Arac hatasi: tool_use_id eslemesiyle tool_result is_error=true, hatayi veren tura yazilir.
- Duzeltme: yalniz ana is parcacigi; gercek insan mesaji (origin.kind=human, meta/sistem/<..> degil) hemen onceki tura baglanir.
  Kalip: ek-1, mesajin ilk 40 karakteri, kucuk harf, tam sozcuk eslesmesi (Turkce I/i duzeltmeli).
- Birincil duzeltme paydasi: tum ana tur; ikincil: yalniz insan mesajiyla biten turlar.
- Tur sirasi kovalari: 1-10, 11-30, 31-100, 101-300, >300.
- Spearman: tur duzeyi (ctx ile ikili sinyal), oturum bazli bootstrap (1000). Ayarli: tur-sirasi kovasi icinde, n-agirlikli.
- Disarida: forge-orkestra-data-* (otomatik deney koşuları, insan yok).
"""
import json, re, sys, random, os, collections
from pathlib import Path
import numpy as np
from scipy.stats import rankdata, spearmanr

KOK = Path.home() / ".claude" / "projects"
CIKTI = Path(__file__).resolve().parent
SEED = 20261026
DISLA = ("forge-orkestra-data",)
KALIPLAR = ["hayır", "hayir", "yanlış", "yanlis", "olmamış", "olmadı", "olmadi", "dur", "neden böyle", "neden öyle", "niye",
            "hata var", "hatalı", "bozuk", "çalışmıyor", "calismiyor", "geri al", "istemedim", "demedim", "no,", "wrong", "stop",
            "that's not", "undo", "revert", "doesn't work"]
RE = re.compile("|".join(r"(?<!\w)" + re.escape(k) + (r"(?!\w)" if k[-1].isalnum() else "") for k in KALIPLAR))
KOVA = [50_000, 100_000, 150_000]
TURKOVA = [10, 30, 100, 300]
KADI = ["<50k", "50-100k", "100-150k", ">=150k"]
TADI = ["1-10", "11-30", "31-100", "101-300", ">300"]


def kucult(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def insan_mi(d):
    if d.get("isMeta"):
        return None
    m = (d.get("message") or {}).get("content")
    if not isinstance(m, str):
        return None
    o = d.get("origin")
    if isinstance(o, dict):
        if o.get("kind") != "human":
            return None
    elif d.get("turnOrigin") not in (None, "human"):
        return None
    t = m.lstrip()
    if (not t or t.startswith("<") or t.startswith("[Request interrupted") or t.startswith("This session is being continued")
            or t.startswith("Another Claude") or t.startswith("Caveat:")):
        return None
    return t


def dosya_isle(yol, ana, oturum, turlar, olaylar, kalite):
    tmap, toolmap, sira, son = {}, {}, 0, None
    with open(yol, "r", encoding="utf-8", errors="replace") as f:
        for l in f:
            if not ('"type":"assistant"' in l or '"type":"user"' in l or '"type": "assistant"' in l or '"type": "user"' in l):
                continue
            try:
                d = json.loads(l)
            except ValueError:
                kalite["bozuk"] += 1
                continue
            t = d.get("type")
            if t == "assistant":
                msg = d.get("message") or {}
                u = msg.get("usage")
                mid = msg.get("id") or d.get("requestId")
                if not isinstance(u, dict) or not mid or msg.get("model") == "<synthetic>":
                    kalite["usage_yok"] += 1
                    continue
                ctx = sum(v for v in (u.get("input_tokens"), u.get("cache_read_input_tokens"), u.get("cache_creation_input_tokens"))
                          if isinstance(v, int))
                tr = tmap.get(mid)
                if tr is None:
                    sira += 1
                    tr = {"oturum": oturum, "ana": ana, "idx": sira, "ctx": ctx, "err": False, "corr": False, "insan_sonra": False}
                    tmap[mid] = tr
                    turlar.append(tr)
                else:
                    kalite["tekrar"] += 1
                    tr["ctx"] = max(tr["ctx"], ctx)
                c = msg.get("content")
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
                            toolmap[b["id"]] = tr
                son = tr
            elif t == "user":
                c = (d.get("message") or {}).get("content")
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            tr = toolmap.get(b.get("tool_use_id"))
                            if tr is None:
                                kalite["tool_eslesmedi"] += 1
                            elif b.get("is_error") is True:
                                tr["err"] = True
                elif ana and son is not None:
                    h = insan_mi(d)
                    if h is not None:
                        mm = RE.search(kucult(h[:40]))
                        son["insan_sonra"] = True
                        son["corr"] = bool(mm)
                        kalite["insan_mesaj"] += 1
                        if mm:
                            olaylar.append((oturum, son["idx"], h[:60], mm.group(0), son["ctx"]))
                        son = None


def topla():
    turlar, olaylar, kalite = [], [], collections.Counter()
    for pdir in sorted(p for p in KOK.iterdir() if p.is_dir()):
        if any(x in pdir.name for x in DISLA):
            kalite["disla_proje"] += 1
            continue
        for ana in sorted(pdir.glob("*.jsonl")):
            kalite["ana_dosya"] += 1
            dosya_isle(ana, True, ana.stem, turlar, olaylar, kalite)
        for sub in sorted(pdir.glob("*/subagents/**/agent-*.jsonl")):
            kalite["ajan_dosya"] += 1
            dosya_isle(sub, False, sub.relative_to(pdir).parts[0], turlar, olaylar, kalite)
    return turlar, olaylar, kalite


def kova(c):
    return int(np.searchsorted(KOVA, c, side="right"))


def turkova(i):
    return int(np.searchsorted(TURKOVA, i, side="left"))


def oranlar(cb, y, nb=4):
    r = []
    for b in range(nb):
        m = cb == b
        n = int(m.sum())
        k = int(y[m].sum())
        r.append((n, k, k / n if n else float("nan")))
    return r


def spearman_boot(ctx, y, oturum, strat=None, B=1000, rng=None):
    sidx = {s: i for i, s in enumerate(sorted(set(oturum)))}
    si = np.array([sidx[s] for s in oturum])
    S = len(sidx)
    gruplar = [np.arange(len(ctx))] if strat is None else [np.where(strat == s)[0] for s in np.unique(strat)]
    yy_all = y.astype(float)
    tablolar = []
    for g in gruplar:
        if len(g) < 30:
            continue
        rx = rankdata(ctx[g])
        yy = yy_all[g]
        a = np.zeros((S, 6))
        np.add.at(a[:, 0], si[g], 1)
        np.add.at(a[:, 1], si[g], rx)
        np.add.at(a[:, 2], si[g], rx * rx)
        np.add.at(a[:, 3], si[g], yy)
        np.add.at(a[:, 4], si[g], yy * yy)
        np.add.at(a[:, 5], si[g], rx * yy)
        tablolar.append(a)

    def rho(w):
        top = ag = 0.0
        for a in tablolar:
            t = (a * w[:, None]).sum(0)
            N = t[0]
            if N < 30:
                continue
            cov = t[5] / N - (t[1] / N) * (t[3] / N)
            vx = t[2] / N - (t[1] / N) ** 2
            vy = t[4] / N - (t[3] / N) ** 2
            if vx <= 0 or vy <= 0:
                continue
            top += N * cov / np.sqrt(vx * vy)
            ag += N
        return top / ag if ag else float("nan")

    ham = rho(np.ones(S))
    bs = np.array([rho(np.bincount(rng.integers(0, S, S), minlength=S).astype(float)) for _ in range(B)])
    return float(ham), float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


def oran_boot(cb, y, oturum, B=1000, rng=None):
    sidx = {s: i for i, s in enumerate(sorted(set(oturum)))}
    si = np.array([sidx[s] for s in oturum])
    S = len(sidx)
    a = np.zeros((S, 4, 2))
    np.add.at(a, (si, cb, 0), 1)
    np.add.at(a, (si, cb, 1), y.astype(float))

    def r(w):
        t = (a * w[:, None, None]).sum(0)
        if t[0, 0] == 0 or t[3, 0] == 0 or t[0, 1] == 0:
            return np.nan
        return (t[3, 1] / t[3, 0]) / (t[0, 1] / t[0, 0])

    h = r(np.ones(S))
    bs = np.array([r(np.bincount(rng.integers(0, S, S), minlength=S).astype(float)) for _ in range(B)])
    return float(h), float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


def sinyal(ad, sel, anahtar, rng):
    ctx = np.array([t["ctx"] for t in sel])
    y = np.array([bool(t[anahtar]) for t in sel]).astype(int)
    ti = np.array([t["idx"] for t in sel])
    osn = np.array([t["oturum"] for t in sel])
    cb = np.array([kova(c) for c in ctx])
    tb = np.array([turkova(i) for i in ti])
    o = {"ad": ad, "n": len(y), "olay": int(y.sum()), "oturum": len(set(osn))}
    o["kovalar"] = oranlar(cb, y)
    o["rho"] = spearman_boot(ctx, y, osn, None, rng=rng)
    o["oran"] = oran_boot(cb, y, osn, rng=rng)
    r4 = [x[2] for x in o["kovalar"]]
    o["rho_kova4"] = float(spearmanr(range(4), r4)[0]) if not any(x != x for x in r4) else None
    o["tekduze"] = all(r4[i] <= r4[i + 1] for i in range(3)) if not any(x != x for x in r4) else None
    o["turkova"] = oranlar(tb, y, 5)
    o["strata"] = []
    for s in range(5):
        m = tb == s
        if m.sum() < 30:
            o["strata"].append((TADI[s], int(m.sum()), None, None))
            continue
        oo = oranlar(cb[m], y[m])
        oo_rho = spearman_boot(ctx[m], y[m], osn[m], None, B=1, rng=rng)[0]
        o["strata"].append((TADI[s], int(m.sum()), oo, oo_rho))
    o["rho_ayarli"] = spearman_boot(ctx, y, osn, tb, rng=rng)
    return o


def main():
    rng = np.random.default_rng(SEED)
    turlar, olaylar, kalite = topla()
    ana = [t for t in turlar if t["ana"]]
    ajan = [t for t in turlar if not t["ana"]]
    sonuc = {
        "arac_hatasi_tum": sinyal("arac_hatasi_tum", turlar, "err", rng),
        "arac_hatasi_ana": sinyal("arac_hatasi_ana", ana, "err", rng),
        "arac_hatasi_ajan": sinyal("arac_hatasi_ajan", ajan, "err", rng),
        "duzeltme_birincil": sinyal("duzeltme_birincil", ana, "corr", rng),
        "duzeltme_ikincil": sinyal("duzeltme_ikincil", [t for t in ana if t["insan_sonra"]], "corr", rng),
    }
    r2 = random.Random(SEED)
    ornek = r2.sample(olaylar, min(40, len(olaylar)))
    with open(Path(os.environ.get("TEMP", ".")) / "baglam_hata_ornek.txt", "w", encoding="utf-8") as f:
        for i, (_, _, snip, kal, _) in enumerate(ornek):
            f.write(f"{i + 1}\t{kal}\t{snip!r}\n")
    ozet = {"kalite": dict(kalite), "tur_toplam": len(turlar), "ana_tur": len(ana), "ajan_tur": len(ajan),
            "oturum": len({t["oturum"] for t in turlar}), "olay": len(olaylar), "seed": SEED,
            "ctx_tur_rho": float(spearmanr([t["ctx"] for t in turlar], [t["idx"] for t in turlar])[0]),
            "kalip_dagilimi": collections.Counter(k for _, _, _, k, _ in olaylar).most_common(12), "sonuc": sonuc}
    with open(CIKTI / "sonuc.json", "w", encoding="utf-8") as f:
        json.dump(ozet, f, ensure_ascii=False, indent=1)
    print(json.dumps(ozet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
