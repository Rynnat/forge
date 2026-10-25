"""Yerel arXiv dizini (SQLite FTS5) üzerinden arama — canlı `sources/arxiv.py` ile aynı arayüz,
aynı kademeler (AND → çoğunluk ⌈0,6n⌉ → OR), aynı terim çıkarımı (`arxiv.terms`) ve aynı
huni sayaç adları:
  arxiv.kademe.{AND,MAJ,OR}, arxiv.kademe.{..}=0, arxiv.api_kesilen(havuza_girmedi)
(son sayaç yerelde "kademe tavanı yüzünden havuza girmeyen eşleşme" demektir; ad, huni ve
raporlar değişmesin diye korunur).

Farklar (bilerek):
  - Kesim süzgeci SQL'de: `v1_tarih < :kesim` (v1 = versions[0].created, UTC gün). Canlıdaki
    `submittedDate:[.. TO kesim-1 23:59]` ile aynı anlam; kayıt tarihi de v1'dir (canlıda
    `published` = v1 gönderim zamanı).
  - Arama alanı başlık + özet. Canlı `all:` yazar, yorum, dergi künyesi alanlarını da tarar.
  - Sıralama bm25 (başlık ağırlığı 2). arXiv'in sıralaması farklı; birebir sıra beklenmez.
  - Terimlerin hepsi FTS5 tırnaklı ifadesi olur: `io_uring` → "io_uring" → tokenizer'da
    bitişik (io, uring) ifadesi; `zero-shot`, `"graph neural network"` aynı şekilde. Tek
    kelimeli terim tırnakla da tek token'dır; tırnak FTS5 sözdizimi tuzaklarını (AND/OR/NOT/NEAR
    kelimeleri, özel karakterler) da kapatır.
Dürüst durum: kesim, anlık görüntünün en yeni v1 gününden sonraysa dizin kesimi kapsamaz →
kaynak EKSİK (sebep yazılır); sonuçlar yine döner (kısmi).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import threading
from pathlib import Path

from orkestra.arxiv_yerel_kur import ozet
from orkestra.funnel import EKSIK
from orkestra.records import new_record
from orkestra.sources.arxiv import terms, tier_groups  # noqa: F401  (terms: dışa açık)

BM25 = "bm25(ara, 2.0, 1.0)"
_AUTH_SPLIT = re.compile(r",\s*|\s+and\s+")
_WORD = re.compile(r"\w+", re.U)


class Dizin:
    """Salt okunur bağlantı + kilit (toplayıcı iş parçacığı ve ana iş parçacığı paylaşır)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        uri = self.path.resolve().as_uri() + "?mode=ro"
        self.con = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self.lock = threading.Lock()
        self.meta = dict(self.con.execute("SELECT k, v FROM meta").fetchall())
        self.max_v1 = dt.date.fromisoformat(self.meta["en_yeni_v1"]) if self.meta.get("en_yeni_v1") else None
        self.n = int(self.meta.get("kayit_sayisi") or 0)
        self.istek = 0

    def query(self, sql: str, args: tuple) -> list[tuple]:
        with self.lock:
            self.istek += 1
            return self.con.execute(sql, args).fetchall()

    def covers(self, cut: dt.date) -> bool:
        """`v1 < cut` için gereken tüm günler (cut-1'e kadar) anlık görüntüde tam mı."""
        return self.max_v1 is not None and cut <= self.max_v1

    def uncovered_reason(self, cut: dt.date) -> str:
        return (f"yerel dizin kesimi kapsamıyor: anlık görüntü en yeni v1 {self.max_v1}, "
                f"kesim {cut} (aradaki günler dizinde yok)")

    def close(self) -> None:
        self.con.close()


def ac(cfg) -> Dizin | None:
    """Yapılandırmaya göre dizini açar; canlı zorlanmışsa ya da dosya yoksa/bozuksa None."""
    if getattr(cfg, "arxiv_canli_zorla", False):
        return None
    p = getattr(cfg, "arxiv_yerel_db", None)
    if not p or not Path(p).exists():
        return None
    try:
        return Dizin(p)
    except (sqlite3.Error, KeyError, ValueError):
        return None


def _fts_term(t: str) -> str:
    return '"' + t.strip('"').replace('"', '""') + '"'


def tier_matches(q: str) -> list[tuple[str, str]]:
    """Canlı `tier_queries` ile aynı kademe/kombinasyon yapısı (`arxiv.tier_groups`), FTS5
    MATCH ifadesi olarak."""
    out = []
    for tier, groups in tier_groups(q):
        if tier == "MAJ":
            out.append((tier, " OR ".join("(" + " AND ".join(_fts_term(t) for t in g) + ")" for g in groups)))
        else:
            op = " AND " if tier == "AND" else " OR "
            out.append((tier, op.join(_fts_term(t) for g in groups for t in g)))
    return out


# bm25 pencere fonksiyonuyla aynı seviyede kullanılamıyor → önce FTS eşleşmeleri + skor (CTE),
# sonra kayit ile birleşim, tarih süzgeci, toplam (COUNT OVER) ve sıralı kesim.
_SEL = ("WITH m AS MATERIALIZED (SELECT rowid AS rid, " + BM25 + " AS s FROM ara WHERE ara MATCH ?) "
        "SELECT k.id, k.baslik, k.ozet_z, k.doi, k.v1_tarih, k.yazarlar, k.dergi{extra} "
        "FROM m JOIN kayit k ON k.rid = m.rid{date} ORDER BY m.s LIMIT ?")


def _match(dz: Dizin, expr: str, cut: dt.date | None, cap: int, count: bool = True) -> tuple[list[dict], int]:
    sql = _SEL.format(extra=", COUNT(*) OVER ()" if count else "",
                      date=" WHERE k.v1_tarih < ?" if cut else "")
    args = (expr,) + ((cut.isoformat(),) if cut else ()) + (cap,)
    rows = dz.query(sql, args)
    total = rows[0][7] if rows and count else len(rows)
    return [to_record(r) for r in rows], total


def to_record(r: tuple) -> dict:
    aid, title, oz, doi, v1, auth, jref = r[:7]
    d = [int(x) for x in v1.split("-")] if v1 else None
    return new_record(
        "arxiv", title=title, arxiv_id=aid, abstract=ozet(oz), doi=doi,
        dates=[d] if d else [], year=d[0] if d else None, venue=jref or "arXiv",
        authors=[a for a in _AUTH_SPLIT.split(auth or "") if a.strip()],
        url=f"https://arxiv.org/abs/{aid}",
    )


def search(dz: Dizin, query: str, cut: dt.date, cfg, funnel=None) -> list[dict]:
    """Kademeli arama (canlı `arxiv.search` ile aynı durdurma kuralı: kademe toplamları
    cfg.arxiv_enough'a ulaşınca sonraki kademe koşulmaz)."""
    if funnel is not None and not dz.covers(cut):
        funnel.source("arxiv", EKSIK, dz.uncovered_reason(cut))
        funnel.bump("arxiv.yerel_kesim_kapsanmiyor")
    recs: list[dict] = []
    total_seen = 0
    for tier, expr in tier_matches(query):
        cap = {"AND": cfg.arxiv_and_max, "MAJ": cfg.arxiv_majority_max, "OR": cfg.arxiv_or_max}[tier]
        got, total = _match(dz, expr, cut, cap)
        recs.extend(got)
        if funnel is not None:
            funnel.bump(f"arxiv.kademe.{tier}")
            if total == 0:
                funnel.bump(f"arxiv.kademe.{tier}=0")
            if total and total > len(got):
                funnel.bump("arxiv.api_kesilen(havuza_girmedi)", total - len(got))
        total_seen += total or 0
        if total_seen >= cfg.arxiv_enough:
            break
    return recs


def by_titles(dz: Dizin, titles: list[str], per_title: int = 5) -> list[dict]:
    """Canlı `by_titles` karşılığı: her başlık için başlık sütununda tüm kelimeler (AND), hiç
    yoksa uzun kelimelerin OR'u; aday döner, eşleştirme çağıranda başlık benzerliğiyle."""
    out, seen = [], set()
    for t in titles:
        ws = [w for w in _WORD.findall(t or "") if w.strip("_")][:16]
        if not ws:
            continue
        # Önce bitişik ifade (tam başlık): FTS5 yaygın kelimeli başlıklarda (AND) milyonlarca
        # eşleşmeyi bm25 ile sıralıyordu (tek başlık dakikalar-saatler); ifade seçici ve hızlı.
        got, _ = _match(dz, "baslik : " + _fts_term(" ".join(ws)), None, per_title, count=False)
        if not got:
            got, _ = _match(dz, "baslik : (" + " AND ".join(_fts_term(w) for w in ws) + ")", None,
                            per_title, count=False)
        if not got:
            long_ = [w for w in ws if len(w) >= 4] or ws
            got, _ = _match(dz, "baslik : (" + " OR ".join(_fts_term(w) for w in long_) + ")", None,
                            per_title, count=False)
        for r in got:
            if r["arxiv_id"] not in seen:
                seen.add(r["arxiv_id"])
                out.append(r)
    return out


def by_ids(dz: Dizin, ids: list[str]) -> list[dict]:
    """Yerel id araması (denetim/eşdeğerlik için; hattın by_ids'i canlıdır)."""
    out = []
    for i in range(0, len(ids), 500):
        chunk = [x.lower() for x in ids[i:i + 500]]
        q = ("SELECT id, baslik, ozet_z, doi, v1_tarih, yazarlar, dergi FROM kayit WHERE id IN (%s)"
             % ",".join("?" * len(chunk)))
        out.extend(to_record(r) for r in dz.query(q, tuple(chunk)))
    return out


def durum(dz: Dizin) -> dict:
    return {"mod": "yerel", "anlik_en_yeni_v1": str(dz.max_v1), "dizin_kayit": dz.n,
            "anlik_update_date": dz.meta.get("en_yeni_update_date", ""),
            "kaynak_dosyalar": len(json.loads(dz.meta.get("kaynak_dosyalar") or "[]"))}
