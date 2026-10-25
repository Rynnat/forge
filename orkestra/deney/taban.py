"""Taban çizgisi A (ONKAYIT-orkestra-v0.md): tek Opus ajanı, standart istem.

  python -m deney.taban batch --sorular sorular.json --out <dir> [--k 1] [--tavan 3.0] [--toplam-tavan 40]

`claude -p --model opus`; yalnız WebSearch + WebFetch (dosya yazma / bash yok), Claude Code'un
varsayılan sistem istemi (general-purpose ajan; özel istem verilmez), MCP / ayar kaynakları
yüklenmez, her koşu için yeni boş çalışma dizini (CLAUDE.md / hafıza yok), oturum kaydedilmez.
Soru başına sert tavan: `--max-budget-usd` (CLI tavanı turlar arasında denetler; son tur biraz
taşabilir). Tavana çarpan koşu `BUTCE` durumuyla kaydedilir, tekrar edilmez.

Çıktı `<out>/<id>/k<k>/`: `sonuc.json` (orkestra ile aynı `calismalar` alanları: sira, id,
arxiv_id, doi, baslik, yil, gerekce), `ham_cikti.json` (CLI'nin JSON sarmalı), `ham_metin.txt`
(modelin son mesajı). Kimlikler olduğu gibi tutulur (yalnız baş/son boşluk silinir); düzeltme,
tamamlama, uydurma yok — geçerliliğe skorlayıcı karar verir. Maliyet `logs/maliyet.jsonl`'a
`asama="taban"` ile yazılır.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent  # forge/orkestra
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orkestra.config import load_config  # noqa: E402
from orkestra.llm import Ledger, Usage, parse_json, usage_from_wrap  # noqa: E402

MODEL = "opus"
ARACLAR = "WebSearch,WebFetch"
N = 30

# A0: ön kayıttaki standart istem, aynen (model aramayı atlayabilir; D2 denemesinde 0 arama).
# A1 (birincil, ON KAYIT eki 2026-10-25): arama + kimlik doğrulama zorunlu; B şefinin "survey" çerçevesi de verilir.
# Soru ve kesim kuralı iki istemde de B (orkestra şefi) ile aynı metin.
PROMPT = """Research question: {soru}

Cutoff date: {kesim}. Only works published BEFORE this date count.

List the 30 most important works (papers) for this research question that were published before the cutoff date, in order of importance (most important first), each with its arXiv id and/or DOI. You may search the web.

When you are done, reply with ONLY a JSON object in this form (no other text):
{{"calismalar": [{{"sira": 1, "baslik": "exact title", "yil": 2020, "arxiv_id": "arXiv id or null", "doi": "DOI or null", "gerekce": "one sentence on why this work is important"}}]}}
with exactly 30 items. If you do not know an identifier, use null instead of guessing."""

PROMPT_A1 = """Research question: {soru}

Cutoff date: {kesim}. Only works published BEFORE this date count.

List the 30 most important works (papers) for this research question that were published before the cutoff date, in order of importance (most important first) — the kind a careful expert survey published right after the cutoff would cite. Give each with its arXiv id and/or DOI.

You MUST research this with web search rather than answer from memory: search for the important works, and verify each listed work's title, publication date and identifier on the web (e.g. arxiv.org, doi.org, the publisher or DBLP page) before including it.

When you are done, reply with ONLY a JSON object in this form (no other text):
{{"calismalar": [{{"sira": 1, "baslik": "exact title", "yil": 2020, "arxiv_id": "arXiv id or null", "doi": "DOI or null", "gerekce": "one sentence on why this work is important"}}]}}
with exactly 30 items. If you do not know an identifier, use null instead of guessing."""

ISTEMLER = {"a0": PROMPT, "a1": PROMPT_A1}

ARXIV_RE = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$", re.I)
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def _s(v: Any) -> Any:
    """Metni olduğu gibi tut; yalnız boşluk kırp, boş/'null' → None. Sayı vb. dokunulmaz."""
    if isinstance(v, str):
        v = v.strip()
        return None if v == "" or v.lower() in ("null", "none") else v
    return v


def calismalar_coz(text: str) -> tuple[list[dict], str, int]:
    """(çalışmalar, durum, ham_sayi). durum: OK | PARSE_FAIL. İlk N tutulur, sira yeniden yazılmaz
    ama yoksa liste sırası verilir."""
    try:
        obj = parse_json(text)
    except ValueError:
        return [], "PARSE_FAIL", 0
    items = obj.get("calismalar") if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        return [], "PARSE_FAIL", 0
    out = []
    for i, x in enumerate(items, 1):
        if not isinstance(x, dict):
            continue
        ax, doi = _s(x.get("arxiv_id")), _s(x.get("doi"))
        kid = f"arXiv:{ax}" if ax else (f"doi:{str(doi).lower()}" if doi else None)
        out.append({"sira": x.get("sira", i), "id": kid, "arxiv_id": ax, "doi": doi,
                    "baslik": _s(x.get("baslik")), "yil": _s(x.get("yil")), "gerekce": _s(x.get("gerekce"))})
    return out[:N], "OK", len(out)


def kimlik_gecerli_mi(c: dict) -> bool:
    """Yalnız biçim denetimi (rapor için); çözümleme skorlayıcının işi."""
    ax, doi = c.get("arxiv_id"), c.get("doi")
    return bool((isinstance(ax, str) and ARXIV_RE.match(ax)) or (isinstance(doi, str) and DOI_RE.match(doi)))


def cli_args(exe: str, tavan: float) -> list[str]:
    return [exe, "-p", "--model", MODEL, "--output-format", "json", "--tools", ARACLAR,
            "--allowedTools", ARACLAR, "--strict-mcp-config", "--setting-sources", "",
            "--no-session-persistence", "--max-budget-usd", f"{tavan:.2f}"]


def kos(soru: str, kesim: str, out: Path, *, cfg, ledger: Ledger, tavan: float, run_id: str,
        runner: Callable[..., Any] = subprocess.run, timeout_s: float = 2400.0, mod: str = "a1") -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cwd = Path(cfg.data_dir) / "taban_cwd" / run_id  # her koşu yeni, boş
    cwd.mkdir(parents=True, exist_ok=True)
    exe = cfg.claude_cli_path or shutil.which("claude") or "claude"
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    prompt = ISTEMLER[mod].format(soru=soru, kesim=kesim)
    t0 = time.monotonic()
    u, durum, hata, wrap, text = Usage(), "OK", "", None, ""
    try:
        p = runner(cli_args(exe, tavan), input=prompt, capture_output=True, text=True, encoding="utf-8",
                   errors="replace", timeout=timeout_s, cwd=str(cwd), env=env)
        stdout = p.stdout or ""
        try:
            wrap = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            durum, hata = "HATA", f"çıkış {p.returncode}: {(p.stderr or stdout)[:300]}"
            (out / "ham_cikti.json").write_text(stdout, encoding="utf-8")
    except subprocess.TimeoutExpired:
        durum, hata = "HATA", f"zaman aşımı ({timeout_s:.0f} s; maliyet bilinmiyor)"
    dur = time.monotonic() - t0
    if wrap is not None:
        (out / "ham_cikti.json").write_text(json.dumps(wrap, ensure_ascii=False, indent=1), encoding="utf-8")
        u = usage_from_wrap(wrap)
        text = str(wrap.get("result") or "")
        if wrap.get("is_error") or wrap.get("subtype") not in (None, "success"):
            st = str(wrap.get("subtype"))
            durum = "BUTCE" if "budget" in st else "HATA"
            hata = f"CLI: {st}: {text[:200]}"
    (out / "ham_metin.txt").write_text(text, encoding="utf-8")
    ledger.add("taban", MODEL, durum == "OK", u, dur, hata)
    cal, pdurum, ham_n = calismalar_coz(text) if text else ([], "PARSE_FAIL", 0)
    if durum == "OK" and pdurum != "OK":
        durum = "PARSE_FAIL"
    s = {"run_id": run_id, "sistem": f"A-taban-{mod}", "mod": mod, "soru": soru, "kesim": kesim, "durum": durum, "hata": hata,
         "model": MODEL, "araclar": ARACLAR, "tavan_usd": tavan, "maliyet_usd": round(u.cost_usd, 4),
         "sure_s": round(dur, 1), "web_arama": u.web_search,
         "token": {"in": u.input_tokens, "out": u.output_tokens, "cache_read": u.cache_read_tokens,
                   "cache_write": u.cache_write_tokens},
         "son_rapor_token_tahmini": -(-len(text) // 3), "ham_sayi": ham_n,
         "gecerli_gorunen_kimlik": sum(map(kimlik_gecerli_mi, cal)),
         "istem": prompt, "calismalar": cal}
    (out / "sonuc.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        cwd.rmdir()  # boş kaldıysa sil (araçlar dosya yazamaz)
    except OSError:
        pass
    return s


def batch(sorular: str | Path, out: str | Path, k: int = 1, *, cfg=None, tavan: float = 3.0,
          toplam_tavan: float | None = None, runner: Callable[..., Any] = subprocess.run,
          mod: str = "a1") -> list[dict]:
    cfg = cfg or load_config()
    items = json.loads(Path(sorular).read_text(encoding="utf-8"))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(cfg.cost_log)
    rows: list[dict] = []
    for it in items:
        for kk in range(1, k + 1):
            if toplam_tavan is not None and ledger.total + tavan > toplam_tavan:
                rows.append({"id": it["id"], "k": kk, "durum": "ATLANDI", "hata": "toplam tavan"})
                continue
            ledger.run_id = f"taban-{mod}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
            dt.date.fromisoformat(it["kesim"])
            s = kos(it["soru"], it["kesim"], out / str(it["id"]) / f"k{kk}", cfg=cfg, ledger=ledger,
                    tavan=tavan, run_id=ledger.run_id, runner=runner, mod=mod)
            rows.append({"id": it["id"], "k": kk, "durum": s["durum"], "maliyet_usd": s["maliyet_usd"],
                         "sure_s": s["sure_s"], "n": len(s["calismalar"]),
                         "gecerli_gorunen_kimlik": s["gecerli_gorunen_kimlik"], "hata": s["hata"]})
            print(f"[{s['durum']}] {it['id']} k{kk} | ${s['maliyet_usd']:.3f} | {s['sure_s']:.0f} s | "
                  f"{len(s['calismalar'])} çalışma, {s['gecerli_gorunen_kimlik']} geçerli görünen kimlik")
            (out / "batch_ozet.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="deney.taban")
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--sorular", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--k", type=int, default=1)
    b.add_argument("--id", action="append", help="yalnız bu id(ler) (önek eşleşmesi)")
    b.add_argument("--tavan", type=float, default=3.0, help="soru başına $ tavanı (--max-budget-usd)")
    b.add_argument("--toplam-tavan", type=float, default=None, help="batch toplam $ tavanı")
    b.add_argument("--mod", choices=sorted(ISTEMLER), default="a1", help="a1 = birincil (arama zorunlu), a0 = ön kayıt aynen")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sorular = Path(a.sorular)
    if a.id:  # filtreli geçici liste
        items = [x for x in json.loads(sorular.read_text(encoding="utf-8"))
                 if any(str(x["id"]).startswith(p) for p in a.id)]
        Path(a.out).mkdir(parents=True, exist_ok=True)
        sorular = Path(a.out) / "sorular_secili.json"
        sorular.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = batch(sorular, a.out, a.k, cfg=load_config(a.config), tavan=a.tavan, toplam_tavan=a.toplam_tavan, mod=a.mod)
    print(f"bitti: {len(rows)} koşu, toplam ${sum(r.get('maliyet_usd') or 0 for r in rows):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
