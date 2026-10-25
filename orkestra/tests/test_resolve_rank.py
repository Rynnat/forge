import numpy as np
from conftest import rec

from orkestra import rank, web
from orkestra.funnel import Funnel
from orkestra.sources import arxiv, crossref


def test_resolve_rejects_fabricated_titles(cfg, monkeypatch):
    real = rec("Neural Message Passing for Quantum Chemistry", arxiv_id="1704.01212")
    monkeypatch.setattr(arxiv, "by_ids", lambda http, ids: [real] if "1704.01212" in ids else [])
    monkeypatch.setattr(arxiv, "by_titles", lambda http, ts: [real])
    monkeypatch.setattr(crossref, "by_title", lambda http, t, cfg, rows=3: [rec("Completely different", src="crossref", doi="10.1/z")])
    items = [
        {"baslik": "Neural message passing for quantum chemistry", "arxiv": "", "koken": "sef"},
        {"baslik": "Neural Message Passing for Quantum Chemistry", "arxiv": "1704.01212", "koken": "web"},  # tekrar
        {"baslik": "A Totally Invented Paper About Molecules", "arxiv": "1704.01212", "koken": "web"},  # yanlış id
    ]
    f = Funnel()
    out, drop = web.resolve(None, cfg, items, f, "test")
    assert len(out) == 1 and out[0]["anchor"] is True
    assert drop["tekrar_baslik"] == 1 and drop["cozulemedi"] == 1
    assert f.balanced


def test_bm25_prefers_matching_doc():
    docs = [rank.toks("graph neural network molecules"), rank.toks("cooking pasta recipe"), rank.toks("graph theory")]
    s = rank.BM25(docs).scores(rank.toks("graph neural molecules"))
    assert int(np.argmax(s)) == 0 and s[1] == 0


def test_score_and_cluster_cap(cfg):
    recs = [rec(f"Graph neural network for molecules variant {i}", abstract="graph neural molecules property", citations=i)
            for i in range(10)] + [rec(f"Protein folding structure {i}", abstract="protein structure folding") for i in range(10)]
    subs = [{"id": "S1", "soru": "graph neural molecules", "sorgular": []}]
    rank.score(recs, "graph neural network molecules", subs, cfg, rank.Embedder(cfg))
    rank.cluster(recs, 2)
    top = rank.top_with_cap(recs, 10, 0.5)
    assert len(top) == 10
    kumeler = [r["kume"] for r in top]
    assert max(kumeler.count(k) for k in set(kumeler)) <= 5


def test_embed_truncation_counted(cfg):
    f = Funnel()
    long_ab = " ".join(["word"] * 500)
    recs = [rec("t1 graph", abstract=long_ab), rec("t2 graph", abstract="short")]
    rank.score(recs, "graph", [], cfg, rank.Embedder(cfg), f)
    assert f.info["embed.kesilen_metin(son)"] == 1
