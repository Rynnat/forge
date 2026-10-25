"""CLI:
  python -m orkestra run --soru "<...>" --kesim YYYY-MM-DD --out <dir>
  python -m orkestra batch --sorular sorular.json --out <dir> [--k 3]
sorular.json: [{"id": ..., "soru": ..., "kesim": "YYYY-MM-DD"}]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import time
import traceback
from pathlib import Path

from orkestra.config import load_config
from orkestra.pipeline import run


def _date(s: str) -> str:
    dt.date.fromisoformat(s)
    return s


def _print(summary: dict) -> None:
    print(f"[{summary['durum']}] {summary['soru'][:80]} | kesim {summary['kesim']} | "
          f"${summary['maliyet_usd']:.3f} | {summary['sureler_s'].get('toplam', 0):.0f} s | "
          f"özet ~{summary['ozet_token_tahmini']} token | funnel dengeli: {summary['funnel_dengeli']}")
    if summary["eksik_kaynaklar"]:
        print("  EKSİK:", ", ".join(summary["eksik_kaynaklar"]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="orkestra")
    ap.add_argument("--config", default=None)
    ap.add_argument("-v", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--soru", required=True)
    r.add_argument("--kesim", required=True, type=_date)
    r.add_argument("--out", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--sorular", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--k", type=int, default=1)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if a.v else logging.WARNING, format="%(asctime)s %(name)s %(message)s")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    cfg = load_config(a.config)
    if a.cmd == "run":
        s = run(a.soru, a.kesim, a.out, cfg)
        _print(s)
        print(f"  çıktı: {Path(a.out).resolve()}")
        return 0
    items = json.loads(Path(a.sorular).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for it in items:
        for k in range(1, a.k + 1):
            d = out / str(it["id"]) / f"k{k}"
            t0 = time.monotonic()
            try:
                s = run(it["soru"], _date(it["kesim"]), d, cfg)
                _print(s)
                rows.append({"id": it["id"], "k": k, "durum": s["durum"], "eksik": s["eksik_kaynaklar"],
                             "maliyet_usd": s["maliyet_usd"], "sure_s": s["sureler_s"].get("toplam"),
                             "ozet_token": s["ozet_token_tahmini"], "n": len(s["calismalar"])})
            except Exception as exc:  # bir soru düşerse diğerleri sürer; hata kaydedilir
                rows.append({"id": it["id"], "k": k, "durum": "HATA", "hata": f"{type(exc).__name__}: {exc}",
                             "sure_s": round(time.monotonic() - t0, 1)})
                traceback.print_exc()
            (out / "batch_ozet.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"batch bitti: {len(rows)} koşu, {sum(1 for x in rows if x['durum'] == 'HATA')} hata → {out / 'batch_ozet.json'}")
    return 0
