"""Yerel arXiv dizini (v1): kurulum, kademeler, kesim, alt çizgi, dürüst durum, hat bağlantısı.
Ağsız: küçük sentetik parquet → FTS5 dizini (tmp_path)."""
import datetime as dt
import sqlite3

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import rec

from orkestra import arxiv_yerel_kur as kur
from orkestra.funnel import EKSIK, OK, Funnel
from orkestra.pipeline import Ctx, harvest_source, preprint_abstracts
from orkestra.sources import arxiv, arxiv_yerel

CUT = dt.date(2025, 6, 1)


def _v(*dates):
    return [{"version": f"v{i + 1}", "created": d} for i, d in enumerate(dates)]


ROWS = [
    # id, title, abstract, versions
    ("2401.00001", "Fuzzing io_uring in the Linux kernel", "We fuzz the io_uring interface for kernel exploitation.",
     _v("Tue, 2 Jan 2024 10:00:00 GMT")),
    ("2402.00002", "Hardening io-uring", "Kernel exploitation mitigations for io-uring.",
     _v("Fri, 2 Feb 2024 10:00:00 GMT", "Sat, 3 Feb 2024 10:00:00 GMT")),
    ("2403.00003", "Uring scheduling and IO", "The io scheduler; uring is a ring. Kernel paper.",
     _v("Fri, 1 Mar 2024 10:00:00 GMT")),
    ("2505.00004", "Graph neural networks for molecules", "Message passing graph neural network for molecule property.",
     _v("Sat, 31 May 2025 23:59:00 GMT")),  # kesimden bir gün önce: geçer
    ("2506.00005", "Graph neural network molecule benchmark", "A molecule benchmark for graph neural networks.",
     _v("Sun, 1 Jun 2025 00:10:00 GMT")),  # kesim günü: düşer
    ("2301.00006", "Molecule generation with diffusion", "Diffusion for molecule design.",
     _v("Mon, 2 Jan 2023 08:00:00 GMT")),
    ("2302.00007", "Graph kernels revisited", "Classic graph kernels.", _v("Thu, 2 Feb 2023 08:00:00 GMT")),
    ("2302.00007v2", "Duplicate id row", "Should be skipped.", _v("Thu, 2 Feb 2023 08:00:00 GMT")),
    ("2303.00008", "", "No title: skipped.", _v("Thu, 2 Mar 2023 08:00:00 GMT")),
    ("2304.00009", "Neural Message Passing for Quantum Chemistry",
     "Supervised learning on molecules has incredible potential.", _v("Mon, 3 Apr 2023 22:30:00 -0200")),
]


def make_parquet(path, rows=ROWS):
    t = pa.table({
        "id": [r[0] for r in rows],
        "title": [r[1] for r in rows],
        "abstract": ["  " + r[2] + "\n" for r in rows],
        "categories": ["cs.OS" for _ in rows],
        "doi": [None if i % 2 else f"10.1/X{i}" for i in range(len(rows))],
        "journal-ref": [None for _ in rows],
        "versions": [r[3] for r in rows],
        "authors": ["A. Author, B. Author and C. Author" for _ in rows],
        "update_date": pa.array([dt.datetime(2025, 6, 3)] * len(rows), pa.timestamp("ms")),
    })
    pq.write_table(t, path)


@pytest.fixture
def db(tmp_path):
    p = tmp_path / "a.parquet"
    make_parquet(p)
    out = tmp_path / "arxiv_yerel.sqlite"
    meta = kur.build([str(p)], out, log=lambda *a: None)
    return out, meta


@pytest.fixture
def dz(db):
    d = arxiv_yerel.Dizin(db[0])
    yield d
    d.close()


def test_rfc2822_dates():
    assert kur.rfc2822_date("Sat, 30 Aug 2008 17:09:12 GMT") == "2008-08-30"
    assert kur.rfc2822_date("Mon, 3 Apr 2023 22:30:00 -0200") == "2023-04-04"  # UTC'ye çevrilir
    assert kur.rfc2822_date("") is None and kur.rfc2822_date("bozuk") is None


def test_build_meta_and_rows(db, dz):
    _, meta = db
    assert meta["kayit_sayisi"] == "8" and meta["tekrar_id"] == "1" and meta["atlanan_bos"] == "1"
    assert meta["en_yeni_v1"] == "2025-06-01" and meta["en_yeni_update_date"] == "2025-06-03"
    assert dz.n == 8 and dz.max_v1 == dt.date(2025, 6, 1)
    r = arxiv_yerel.by_ids(dz, ["2402.00002"])[0]
    assert r["abstract"] == "Kernel exploitation mitigations for io-uring."  # zlib + boşluk temizliği
    assert r["dates"][0] == [2024, 2, 2]  # v1, v2 değil
    assert r["authors"] == ["A. Author", "B. Author", "C. Author"] and r["sources"] == ["arxiv"]
    con = sqlite3.connect(db[0])
    assert con.execute("SELECT v1_tarih FROM kayit WHERE id='2304.00009'").fetchone()[0] == "2023-04-04"
    assert {x[0] for x in con.execute("SELECT name FROM sqlite_master")} >= {"kayit", "ara", "meta", "kayit_v1"}


def test_underscore_is_adjacent_phrase_not_or(dz, cfg):
    got = arxiv_yerel.search(dz, "io_uring", CUT, cfg, Funnel())
    ids = {r["arxiv_id"] for r in got}
    assert ids == {"2401.00001", "2402.00002"}  # "io uring" bitişik; 2403'te io ve uring ayrı → yok
    assert arxiv_yerel._fts_term("io_uring") == '"io_uring"'
    assert arxiv_yerel._fts_term('"graph neural network"') == '"graph neural network"'


def test_tiers_same_structure_as_live():
    for q in ["io_uring kernel exploitation", '"graph neural network" zero-shot', "a b c d e f g h i",
              "single", "graph neural molecule benchmark dataset property prediction"]:
        assert [t for t, _ in arxiv_yerel.tier_matches(q)] == [t for t, _ in arxiv.tier_queries(q)]
    m = dict(arxiv_yerel.tier_matches("io_uring kernel exploitation"))
    assert m["AND"] == '"io_uring" AND "kernel" AND "exploitation"'
    assert '("io_uring" AND "kernel")' in m["MAJ"]


def test_falls_through_tiers_and_counts(dz, cfg):
    f = Funnel()
    # AND (io_uring ∧ kernel ∧ exploitation ∧ benchmark) = 0; MAJ ⌈0.6·4⌉=3 → 2401, 2402; OR → hepsi
    got = arxiv_yerel.search(dz, "io_uring kernel exploitation benchmark", CUT, cfg, f)
    assert f.info["arxiv.kademe.AND=0"] == 1 and f.info["arxiv.kademe.MAJ"] == 1 and f.info["arxiv.kademe.OR"] == 1
    assert {r["arxiv_id"] for r in got} >= {"2401.00001", "2402.00002", "2403.00003"}


def test_enough_stops_and_cap_counter(dz, cfg):
    cfg.arxiv_enough = 1
    cfg.arxiv_or_max = 1
    f = Funnel()
    got = arxiv_yerel.search(dz, "kernel", CUT, cfg, f)
    assert len(got) == 4 and f.info["arxiv.kademe.AND"] == 1  # porter: kernels ~ kernel and "arxiv.kademe.OR" not in f.info
    f = Funnel()
    got = arxiv_yerel.search(dz, "diffusion kernels", CUT, cfg, f)  # AND=0 → OR, tavan 1
    assert len(got) == 1 and f.info["arxiv.api_kesilen(havuza_girmedi)"] == 4


def test_cutoff_in_sql_uses_v1(dz, cfg):
    got = arxiv_yerel.search(dz, "graph neural molecule", CUT, cfg, Funnel())
    ids = {r["arxiv_id"] for r in got}
    assert "2505.00004" in ids and "2506.00005" not in ids
    late = arxiv_yerel.search(dz, "graph neural molecule", dt.date(2025, 6, 2), cfg, Funnel())
    assert "2506.00005" in {r["arxiv_id"] for r in late}


def test_uncovered_cutoff_is_eksik(dz, cfg):
    f = Funnel()
    assert dz.covers(dt.date(2025, 6, 1)) and not dz.covers(dt.date(2025, 6, 2))
    arxiv_yerel.search(dz, "kernel", dt.date(2025, 7, 1), cfg, f)
    assert f.sources["arxiv"]["durum"] == EKSIK and "kapsamıyor" in f.sources["arxiv"]["sebep"]


def test_by_titles_and_fallback(dz):
    c = arxiv_yerel.by_titles(dz, ["Neural message passing for quantum chemistry",
                                   "Neural Message Passing for Quantum Chemistry: extended"])
    assert c and c[0]["arxiv_id"] == "2304.00009" and len({x["arxiv_id"] for x in c}) == len(c)
    assert arxiv_yerel.by_titles(dz, ["", "   ", "()"]) == []


class NoNet:
    exhausted = {"arxiv": "tükendi"}  # yerel kipte bakılmamalı

    def get(self, *a, **k):
        raise AssertionError("yerel kipte ağ çağrısı yapılmamalı")

    request = get


def _ctx(cfg, tmp_path, kesim="2025-06-01", **kw):
    return Ctx(cfg, "q", kesim, tmp_path / "o", llm=object(), http=NoNet(), **kw)


def test_pipeline_uses_local_when_db_exists(db, cfg, tmp_path):
    cfg.arxiv_yerel_db = db[0]
    ctx = _ctx(cfg, tmp_path)
    assert ctx.arxiv_dizin is not None and ctx.preprint_yerel
    assert ctx.funnel.sources["arxiv"]["mod"] == "yerel" and ctx.funnel.sources["arxiv"]["dizin_kayit"] == 8
    got = harvest_source(ctx, "arxiv", [{"id": "S1", "soru": "x", "sorgular": ["io_uring kernel"]}])
    assert {r["arxiv_id"] for r in got} >= {"2401.00001", "2402.00002"}  # AND 2 < enough → OR da koşar
    assert ctx.funnel.info["arxiv.kademe.OR"] == 1
    assert ctx.funnel.sources["arxiv"]["durum"] == OK and ctx.funnel.balanced
    # başlık çözümleme (şef/web çapası) da yerel: canlı by_titles çağrılırsa NoNet patlar
    out, drop = ctx.resolver([{"baslik": "Neural Message Passing for Quantum Chemistry", "koken": "sef"}], "sef_capa")
    assert len(out) == 1 and out[0]["arxiv_id"] == "2304.00009" and out[0]["anchor"]


def test_pipeline_uncovered_cutoff_marks_eksik_and_stays(db, cfg, tmp_path):
    cfg.arxiv_yerel_db = db[0]
    ctx = _ctx(cfg, tmp_path, kesim="2025-08-01")
    harvest_source(ctx, "arxiv", [{"id": "S1", "soru": "x", "sorgular": ["kernel"]}])
    s = ctx.funnel.sources["arxiv"]
    assert s["durum"] == EKSIK and "2025-06-01" in s["sebep"]


def test_force_live_and_missing_db(db, cfg, tmp_path):
    cfg.arxiv_yerel_db = db[0]
    cfg.arxiv_canli_zorla = True
    assert arxiv_yerel.ac(cfg) is None
    cfg.arxiv_canli_zorla = False
    cfg.arxiv_yerel_db = tmp_path / "yok.sqlite"
    assert arxiv_yerel.ac(cfg) is None
    ctx = _ctx(cfg, tmp_path)
    assert ctx.arxiv_dizin is None and not ctx.preprint_yerel and "arxiv" not in ctx.funnel.sources


def test_preprint_local_no_cap_no_quota_check(db, cfg, tmp_path):
    cfg.arxiv_yerel_db = db[0]
    cfg.arxiv_ozet_k = 2  # canlı tavan; yerelde geçerli değil
    ctx = _ctx(cfg, tmp_path)
    rs = [rec("Neural Message Passing for Quantum Chemistry", src="crossref", doi="10.1/n", dates=[[2017, 4, 4]])]
    rs += [rec(f"Unmatched distinct title number {'z' * i}", src="crossref", doi=f"10.1/u{i}", dates=[[2020, 1, 1]])
           for i in range(4)]
    preprint_abstracts(ctx, rs)
    i = ctx.funnel.info
    assert i["ozet_arxiv.denendi"] == 5 and i["ozet_arxiv.bulundu"] == 1 and "ozet_arxiv.atlandi_tavan" not in i
    assert rs[0]["ozet_kaynagi"] == "arxiv_onbaski" and rs[0]["arxiv_id"] == "2304.00009"
    assert ctx.funnel.sources["ozet_arxiv"]["durum"] == OK and ctx.funnel.sources["ozet_arxiv"]["mod"] == "yerel"
    cfg.arxiv_yerel_ozet_tavan = 3
    ctx = _ctx(cfg, tmp_path)
    preprint_abstracts(ctx, [dict(r, abstract="") for r in rs])
    assert ctx.funnel.info["ozet_arxiv.atlandi_tavan"] == 2
