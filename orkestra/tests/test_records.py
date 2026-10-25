import datetime as dt

from conftest import rec

from orkestra.records import (arxiv_id_date, before_cutoff, cutoff_filter, date_before, dedup, parse_date,
                              public_id)

CUT = dt.date(2025, 6, 1)


def test_parse_date_forms():
    assert parse_date("2024") == (2024, None, None)
    assert parse_date("2024-03-05") == (2024, 3, 5)
    assert parse_date([2024, 3]) == (2024, 3, None)
    assert parse_date(None) is None


def test_arxiv_id_date():
    assert arxiv_id_date("2505.01234") == (2025, 5, None)
    assert arxiv_id_date("cs/9901001") == (1999, 1, None)
    assert arxiv_id_date("garbage") is None


def test_date_before_strict_and_uncertain():
    assert date_before((2024, None, None), CUT) is True
    assert date_before((2026, None, None), CUT) is False
    assert date_before((2025, None, None), CUT) is None  # aynı yıl, ay yok → belirsiz
    assert date_before((2025, 5, None), CUT) is True
    assert date_before((2025, 6, None), CUT) is False  # kesim ayın 1'i → o ay kesin sonra
    assert date_before((2025, 6, 1), CUT) is False  # kesim günü dahil değil
    assert date_before((2025, 5, 31), CUT) is True
    assert date_before((2025, 6, None), dt.date(2025, 6, 15)) is None


def test_cutoff_filter_counts_and_any_version_rule():
    a = rec("Old paper about graphs", dates=[[2020, 1, 1]])
    b = rec("Too new paper about graphs", dates=[[2025, 7, 1]])
    c = rec("Same year unknown month", src="dblp", dates=[[2025]])
    d = rec("No date at all paper here", src="dblp")
    # preprint kesimden önce, dergi sürümü sonra → geçer (ilk yayın önce)
    e = rec("Preprint then journal", dates=[[2025, 8, 1], [2024, 12, 1]])
    keep, drop = cutoff_filter([a, b, c, d, e], CUT)
    assert [r["title"] for r in keep] == [a["title"], e["title"]]
    assert drop == {"kesim_sonrasi": 1, "tarih_belirsiz": 1, "tarih_yok": 1}
    assert len(keep) + sum(drop.values()) == 5


def test_survey_after_cutoff_is_dropped():
    s = rec("A Survey of Everything", arxiv_id="2507.00001")  # arXiv id → 2025-07
    assert before_cutoff(s, CUT) is False


def test_dedup_by_arxiv_doi_title():
    a = rec("Neural Message Passing for Quantum Chemistry", arxiv_id="1704.01212v2", abstract="abc")
    b = rec("Neural message passing for quantum chemistry.", src="dblp", dates=[[2017]], venue="ICML")
    c = rec("Something else entirely different", src="crossref", doi="10.1/xyz")
    d = rec("Other title but same doi", src="openalex", doi="https://doi.org/10.1/XYZ")
    e = rec("Arxiv doi form", src="crossref", doi="10.48550/arXiv.1704.01212")
    out, n = dedup([a, b, c, d, e])
    assert n == 3 and len(out) == 2
    m = next(r for r in out if r.get("arxiv_id") == "1704.01212")
    assert set(m["sources"]) == {"arxiv", "dblp", "crossref"}
    assert m["venue"] == "ICML"


def test_preprint_publication_merge_keeps_both_ids_and_earliest():
    pre = rec("Attention Is All You Need for Molecules", arxiv_id="1706.03762", abstract="long abstract text")
    pub = rec("Attention is all you need for molecules", src="crossref", doi="10.5555/3295222", dates=[[2017, 12, 4]],
              citations=1000)
    out, n = dedup([pre, pub])
    assert n == 1
    r = out[0]
    assert r["arxiv_id"] == "1706.03762" and r["doi"] == "10.5555/3295222"
    assert r["citations"] == 1000 and r["abstract"] == "long abstract text"
    assert public_id(r) == "arXiv:1706.03762"


def test_fuzzy_title_merge_but_not_different_arxiv_ids():
    a = rec("Graph Attention Networks for Molecular Property Prediction", arxiv_id="2001.00001")
    b = rec("Graph Attention Networks for Molecular Property Predictions", src="crossref", doi="10.1/a")
    c = rec("Graph Attention Networks for Molecular Property Prediction II", arxiv_id="2002.00002")
    out, n = dedup([a, b, c])
    assert n == 1  # a+b birleşir, c farklı arXiv id → ayrı
    assert len(out) == 2


def test_fuzzy_needs_both_char_and_word_similarity():
    # karakterce çok yakın ama bir anahtar kelime farklı: birleşmemeli (kelime kümesi süzgeci)
    a = rec("Deep Learning for Protein Folding", src="crossref", doi="10.1/a")
    b = rec("Deep Learning for Protein Holding", src="crossref", doi="10.1/b")
    # aynı başlığın üç ortak anahtar kelimeli iki yazımı: birleşmeli (çift birden çok blokta)
    c = rec("Deep learning for protein folding.", src="arxiv", arxiv_id="2101.00001")
    out, n = dedup([a, b, c])
    assert n == 1 and len(out) == 2
