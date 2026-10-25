import json
import math

from orkestra.deney import puanla as P


def c(ax=None, doi=None, b=None):
    return {"arxiv_id": ax, "doi": doi, "baslik": b}


def kurallar(liste, altin, k=30):
    return [(m["sira"], m["altin"], m["kural"]) for m in P.esle(liste, altin, k)]


def test_arxiv_surum_soyulur():
    assert kurallar([c("2401.01234v3")], [c("arXiv:2401.01234v1")]) == [(1, 0, "arxiv")]
    assert kurallar([c("2401.01234")], [c("2401.01235")]) == []


def test_doi_bicimleri():
    g = [c(doi="10.1109/ABC.2020.1")]
    assert kurallar([c(doi="https://doi.org/10.1109/abc.2020.1")], g) == [(1, 0, "doi")]
    assert kurallar([c(doi="DOI:10.1109/ABC.2020.1 ")], g) == [(1, 0, "doi")]
    assert kurallar([c(doi="10.1109/abc.2020.2")], g) == []


def test_arxiv_doi_formu():
    assert kurallar([c(doi="10.48550/arXiv.2401.01234")], [c("2401.01234v2")]) == [(1, 0, "arxiv")]
    assert kurallar([c("2401.01234")], [c(doi="https://doi.org/10.48550/ARXIV.2401.01234")]) == [(1, 0, "arxiv")]


def test_baslik_bulanik_ve_yakin_kacirma():
    g = [c(b="AFLNet: A Greybox Fuzzer for Network Protocols")]
    assert kurallar([c(b="AFLNET - a greybox fuzzer for network protocols!")], g) == [(1, 0, "baslik")]
    assert kurallar([c(b="Greybox fuzzing of web servers")], g) == []
    # Part I / Part II: karakter benzerliği >=0.90 ama _conflict engeller
    p1 = "A Survey of Deep Learning for Program Analysis and Synthesis Part I"
    p2 = "A Survey of Deep Learning for Program Analysis and Synthesis Part II"
    assert P.title_sim(P.N.norm_title(p1), P.N.norm_title(p2)) >= 0.90
    assert kurallar([c(b=p2)], [c(b=p1)]) == []
    assert kurallar([c(b=p1)], [c(b=p1.upper())]) == [(1, 0, "baslik")]


def test_cift_eslesme_yok():
    assert kurallar([c("2401.1"), c("2401.1v2")], [c("2401.1")]) == [(1, 0, "arxiv")]
    assert len(P.esle([c("2401.1")], [c("2401.1"), c("2401.1v2")])) == 1
    b = "Some Very Specific Title About Fuzzing"
    assert kurallar([c("2401.1", b=b), c(b=b)], [c("2401.1", b=b)]) == [(1, 0, "arxiv")]


def test_k_kesimi_ve_payda():
    liste = [c(f"2401.{i:05d}") for i in range(40)]
    altin = [c("2401.00035"), c("2401.00002")]  # biri 30'un dışında
    r = P.recall_at_k(liste, altin)
    assert (r["eslesen"], r["payda"], r["recall"]) == (1, 2, 0.5)  # |altın|<30 -> payda 2
    altin60 = [c(f"2401.{i:05d}") for i in range(60)]
    r = P.recall_at_k(liste, altin60)
    assert (r["eslesen"], r["payda"], r["recall"]) == (30, 30, 1.0)  # |altın|>30 -> payda 30
    assert P.recall_at_k(liste, [])["recall"] is None


def test_isaret_testi_bilinen_degerler():
    assert P.isaret_testi([1] * 10)["p"] == 1 / 1024
    r = P.isaret_testi([1] * 8 + [-1] * 2 + [0] * 5)  # beraberlik atılır: n=10, 8 pozitif
    assert (r["n"], r["beraber"]) == (10, 5)
    assert math.isclose(r["p"], 56 / 1024)  # (45+10+1)/1024
    assert math.isclose(P.isaret_testi([1, -1])["p"], 0.75)
    assert P.isaret_testi([0, 0])["p"] == 1.0


def test_wilson():
    assert round(P.wilson_alt(28, 30), 3) == 0.787
    assert round(P.wilson_alt(28, 30, 1.645), 3) == 0.817
    assert P.wilson_alt(30, 30) > 0.88 and P.wilson_alt(0, 0) == 0.0


def test_esli_ve_cli(tmp_path, capsys):
    altin = [{"arxiv_id": f"2401.{i:05d}"} for i in range(4)]
    (tmp_path / "g.json").write_text(json.dumps(altin))
    for ad, idler in (("a", [0]), ("b", [0, 1, 2])):
        (tmp_path / f"{ad}.json").write_text(json.dumps(
            {"calismalar": [{"arxiv_id": f"2401.{i:05d}", "doi": None, "baslik": "x", "yil": 2024} for i in idler]}))
    man = {"sorular": [{"id": "q1", "A": "a.json", "B": "b.json", "altin": "g.json"}]}
    (tmp_path / "m.json").write_text(json.dumps(man))
    assert P._cli(["tek", "--sistem", str(tmp_path / "b.json"), "--altin", str(tmp_path / "g.json")]) == 0
    assert json.loads(capsys.readouterr().out)["recall"] == 0.75
    assert P._cli(["esli", "--manifest", str(tmp_path / "m.json")]) == 0
    o = json.loads(capsys.readouterr().out)
    assert o["ortalama_fark"] == 0.5 and o["isaret"]["p"] == 0.5
