"""Komut satırı: read / ask / card / runs."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from makale_okuyucu.config import Config, pin_caches
from makale_okuyucu.core import Reader
from makale_okuyucu.fetch import InputError, resolve_input
from makale_okuyucu.store import Store


def _summary(card: dict, from_cache: bool) -> str:
    f = card.get("funnel", {})
    llm = f.get("llm", {})
    return (f"LOG: key={card['key']} durum={card['status']} önbellek={'evet' if from_cache else 'hayır'} "
            f"sayfa={f.get('pages')} parça={f.get('chunks')} haiku={llm.get('calls')} "
            f"(başarısız {llm.get('failed')}) token_in={llm.get('input_tokens', 0) + llm.get('cache_write_tokens', 0) + llm.get('cache_read_tokens', 0)} "
            f"token_out={llm.get('output_tokens')} maliyet=${llm.get('cost_usd')} süre={f.get('duration_s')}s "
            f"UNVERIFIED={f.get('unverified_in_card')}/{f.get('items_in_card')} "
            f"başarısız_parça={len(card.get('eksik_parcalar') or [])} md≈{f.get('md_tokens_est')} token")


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="makale_okuyucu", description="Makaleyi bir kez oku, kanıtlı kart üret.")
    ap.add_argument("--llm", choices=["claude_cli", "anthropic_api", "mock"], default=None)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read", help="makaleyi oku, kart üret (önbellekli)")
    r.add_argument("input")
    r.add_argument("--as", dest="as_key", default=None, help="yerel PDF'i bu arXiv id / DOI anahtarına bağla")
    r.add_argument("--force", action="store_true", help="önbelleği yok say, yeniden oku")
    r.add_argument("--json", action="store_true", help="Markdown yerine kart JSON'u bas")
    a = sub.add_parser("ask", help="makaleye soru sor (önce kart, sonra ilgili bölümler)")
    a.add_argument("input")
    a.add_argument("question")
    a.add_argument("--refresh", action="store_true")
    c = sub.add_parser("card", help="önbellekteki kartı bas")
    c.add_argument("input")
    c.add_argument("--json", action="store_true")
    ru = sub.add_parser("runs", help="son çalıştırmaların maliyet/funnel logu")
    ru.add_argument("-n", type=int, default=10)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    over = {}
    if args.llm:
        over["llm_backend"] = args.llm
    if args.data_dir:
        over["data_dir"] = Path(args.data_dir)
    cfg = Config.from_env(**over)
    pin_caches(cfg.data_dir)

    if args.cmd == "runs":
        st = Store(cfg.data_dir)
        for row in st.runs(args.n):
            print(json.dumps(row, ensure_ascii=False))
        return 0
    if args.cmd == "card":
        st = Store(cfg.data_dir)
        try:
            key = st.resolve(resolve_input(args.input).key)
        except InputError as exc:
            print(f"HATA: {exc}", file=sys.stderr)
            return 1
        if not key:
            print("Önbellekte yok; önce `read`.", file=sys.stderr)
            return 3
        d = st.paper_dir(key)
        print((d / ("card.json" if args.json else "card.md")).read_text(encoding="utf-8"))
        return 0

    reader = Reader(cfg)
    try:
        if args.cmd == "read":
            res = reader.read(args.input, as_key=args.as_key, force=args.force)
            if res.card is None:
                print(f"DURUM: {res.status} ({res.key})")
                for at in res.attempts:
                    print(f"  - {at}")
                print(res.message)
                return 2 if res.status in ("BOT_BLOCKED", "PAYWALL", "NO_OA", "NOT_FOUND", "NOT_PDF",
                                           "NETWORK_ERROR", "HTTP_ERROR") else 1
            if args.json:
                print(json.dumps(res.card, ensure_ascii=False, indent=1))
            else:
                print(res.markdown, end="")
            print(_summary(res.card, res.from_cache), file=sys.stderr)
            print(f"dosyalar: {reader.store.paper_dir(res.key)}", file=sys.stderr)
            return 0
        if args.cmd == "ask":
            out = reader.ask(args.input, args.question, refresh=args.refresh)
            print(json.dumps(out, ensure_ascii=False, indent=1))
            return 0 if out["kaynak"] in ("kart", "bolum", "bulunamadi") else 2
    except InputError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1
    return 1
