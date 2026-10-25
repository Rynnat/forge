"""Yerel arXiv dizinini kurar: HF `librarian-bots/arxiv-metadata-snapshot` parquet parçaları →
SQLite FTS5 (`cfg.arxiv_yerel_db`).

    python -m orkestra.arxiv_yerel_kur [--parquet DIR] [--db PATH] [--limit N]

Şema:
  kayit(rid, id, baslik, ozet_z, kategoriler, doi, v1_tarih, surumler_json, yazarlar, dergi)
    ozet_z = zlib ile sıkıştırılmış özet (UTF-8); okuma `ozet(blob)`.
    v1_tarih = versions[0].created (RFC-2822, GMT) → 'YYYY-MM-DD' (UTC). Dizinli: kesim süzgeci
    sorguda `v1_tarih < :kesim`.
  ara = FTS5(baslik, ozet), İÇERİKSİZ (content='', contentless_delete=1; rowid = kayit.rid),
    tokenizer `porter unicode61` (varsayılan ayırıcılar). Metin FTS'te tutulmaz, yalnız dizin:
    tek parçada ölçüm dış-içerikli + düz özet 794 MB/292k kayıt → 3,2 M'de ~8,7 GB (kabul ≤ 8 GB
    aşılıyordu); içeriksiz + zlib özetle aşağı iner. bm25 ve tırnaklı ifade içeriksizde çalışır;
    contentless_delete OAI-PMH artımlı güncellemede satır silip yeniden eklemeyi mümkün kılar.
  meta(k, v): kayit_sayisi, en_yeni_v1, en_yeni_update_date, kurulum_s, kaynak_dosyalar, ...

Tokenizer kararı (alt çizgi): `tokenchars '_'` ile `io_uring` tek token yapılabilirdi; YAPILMADI.
  - arXiv'in kendi araması da `io_uring`'i bölüyor (canlı `all:io_uring` metindeki "io-uring" /
    "io uring" yazımlarını da buluyor); tek token yalnız alt çizgili yazımı bulurdu (recall kaybı).
  - gapmine dersi #1'in amacı terimin `io OR uring`a dağılmamasıydı. Sorgu tarafında alt çizgi,
    tire, nokta içeren terim FTS5 tırnaklı ifadesine çevrilir (`"io uring"` = bitişik iki token),
    yani özgüllük korunur. Bkz. sources/arxiv_yerel.py `_fts_term`.
  - porter: arXiv araması da kök bulur (networks ~ network); eşdeğerlik için gerekli.

Kurulum tek iş parçacıklı, geçici dosyaya yazılır, bitince atomik olarak yerine taşınır.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import glob
import json
import os
import re
import sqlite3
import sys
import time
import zlib
from pathlib import Path

SCHEMA = """
CREATE TABLE kayit(
  rid INTEGER PRIMARY KEY,
  id TEXT NOT NULL,
  baslik TEXT NOT NULL,
  ozet_z BLOB,
  kategoriler TEXT,
  doi TEXT,
  v1_tarih TEXT,
  surumler_json TEXT,
  yazarlar TEXT,
  dergi TEXT
);
CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
CREATE VIRTUAL TABLE ara USING fts5(baslik, ozet, content='', contentless_delete=1,
                                    tokenize='porter unicode61');
"""
POST = """
CREATE UNIQUE INDEX kayit_id ON kayit(id);
CREATE INDEX kayit_v1 ON kayit(v1_tarih);
"""
COLS = ["id", "title", "abstract", "categories", "doi", "journal-ref", "versions", "authors", "update_date"]
_MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                                    "Oct", "Nov", "Dec"], 1)}
_RFC = re.compile(r"^\w{3}, (\d{1,2}) (\w{3}) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT$")
_WS = re.compile(r"\s+")
_VER = re.compile(r"v\d+$", re.I)


def rfc2822_date(s: str | None) -> str | None:
    """'Sat, 30 Aug 2008 17:09:12 GMT' → '2008-08-30' (UTC). Hızlı yol + email.utils yedeği."""
    if not s:
        return None
    s = s.strip()
    m = _RFC.match(s)
    if m and m.group(2) in _MON:
        return f"{int(m.group(3)):04d}-{_MON[m.group(2)]:02d}-{int(m.group(1)):02d}"
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError, IndexError):
        return None
    if d.tzinfo is not None:
        d = d.astimezone(dt.timezone.utc)
    return d.strftime("%Y-%m-%d")


def _ws(s) -> str:
    return _WS.sub(" ", s).strip() if s else ""


def ozet(blob) -> str:
    return zlib.decompress(blob).decode("utf-8") if blob else ""


def _row(r: dict):
    aid = (r.get("id") or "").strip()
    title = _ws(r.get("title"))
    if not aid or not title:
        return None
    aid = _VER.sub("", aid).lower()
    vs = r.get("versions") or []
    v1 = rfc2822_date(vs[0].get("created")) if vs else None
    doi = (r.get("doi") or "").strip().lower() or None
    return (aid, title, _ws(r.get("abstract")), (r.get("categories") or "").strip(), doi, v1,
            json.dumps(vs, ensure_ascii=False, separators=(",", ":")) if vs else None,
            _ws(r.get("authors")), _ws(r.get("journal-ref")) or None)


def build(parquet_files: list[str], db_path: str | Path, limit: int | None = None,
          log=print) -> dict:
    import pyarrow.parquet as pq

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".kur")
    for p in (tmp, Path(str(tmp) + "-journal")):
        if p.exists():
            p.unlink()
    t0 = time.monotonic()
    con = sqlite3.connect(str(tmp))
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA cache_size=-262144")  # 256 MB
    con.executescript(SCHEMA)
    n = skipped = dup = 0
    max_v1 = ""
    max_upd = ""
    seen_ids: set[str] = set()
    for fp in parquet_files:
        pf = pq.ParquetFile(fp)
        cols = [c for c in COLS if c in pf.schema_arrow.names]
        for b in pf.iter_batches(batch_size=20000, columns=cols):
            rows, fts = [], []
            for r in b.to_pylist():
                x = _row(r)
                if x is None:
                    skipped += 1
                    continue
                if x[0] in seen_ids:
                    dup += 1
                    continue
                seen_ids.add(x[0])
                rid = n + len(rows) + 1
                fts.append((rid, x[1], x[2]))
                rows.append((rid, x[0], x[1], zlib.compress(x[2].encode("utf-8"), 6) if x[2] else None)
                            + x[3:])
                if x[5] and x[5] > max_v1:
                    max_v1 = x[5]
                u = r.get("update_date")
                if u is not None:
                    u = str(u)[:10]
                    if u > max_upd:
                        max_upd = u
                if limit and n + len(rows) >= limit:
                    break
            con.executemany("INSERT INTO kayit(rid,id,baslik,ozet_z,kategoriler,doi,v1_tarih,"
                            "surumler_json,yazarlar,dergi) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
            con.executemany("INSERT INTO ara(rowid,baslik,ozet) VALUES (?,?,?)", fts)
            n += len(rows)
            if limit and n >= limit:
                break
        con.commit()
        log(f"  {Path(fp).name}: toplam {n} kayıt, {time.monotonic() - t0:.0f} s")
        if limit and n >= limit:
            break
    t_rows = time.monotonic() - t0
    t_idx = time.monotonic()
    con.executescript(POST)
    t_post = time.monotonic() - t_idx
    con.execute("INSERT INTO ara(ara) VALUES('optimize')")
    con.commit()
    total = time.monotonic() - t0
    meta = {
        "kayit_sayisi": str(n), "atlanan_bos": str(skipped), "tekrar_id": str(dup),
        "en_yeni_v1": max_v1, "en_yeni_update_date": max_upd,
        "kurulum_tarihi": dt.datetime.now().isoformat(timespec="seconds"),
        "kurulum_s": f"{total:.1f}", "satir_s": f"{t_rows:.1f}", "dizin_s": f"{t_post:.1f}",
        "kaynak": "librarian-bots/arxiv-metadata-snapshot",
        "kaynak_dosyalar": json.dumps([Path(f).name for f in parquet_files]),
        "tokenizer": "porter unicode61", "sema_surum": "2",
    }
    con.executemany("INSERT INTO meta VALUES (?,?)", list(meta.items()))
    con.commit()
    con.close()
    os.replace(tmp, db_path)
    meta["boyut_mb"] = f"{db_path.stat().st_size / 1e6:.0f}"
    return meta


def main(argv=None) -> int:
    from orkestra.config import load_config

    cfg = load_config()
    ap = argparse.ArgumentParser(prog="orkestra.arxiv_yerel_kur")
    ap.add_argument("--parquet", default=str(cfg.arxiv_parquet_dir))
    ap.add_argument("--db", default=str(cfg.arxiv_yerel_db))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dosya", nargs="*", help="yalnız bu parquet dosyaları")
    a = ap.parse_args(argv)
    files = a.dosya or sorted(glob.glob(os.path.join(a.parquet, "*.parquet")))
    if not files:
        print("parquet bulunamadı:", a.parquet, file=sys.stderr)
        return 2
    part = glob.glob(os.path.join(a.parquet, "*.part"))
    if part and not a.dosya:
        print("UYARI: inen dosya var (.part); yalnız tamamlananlar kurulur:", part, file=sys.stderr)
    meta = build(files, a.db, a.limit)
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
