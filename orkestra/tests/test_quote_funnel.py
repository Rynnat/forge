from orkestra.funnel import EKSIK, OK, Funnel
from orkestra.quotecheck import TOO_SHORT, UNVERIFIED, VERIFIED, check_quote

SRC = "We propose a message passing framework. It achieves state-of-the-art results on QM9 benchmarks."


def test_quote_verified_with_case_and_space():
    assert check_quote("it achieves  STATE-of-the-art results on QM9", SRC) == VERIFIED


def test_quote_unverified_and_short():
    assert check_quote("it achieves the best results on ZINC benchmark", SRC) == UNVERIFIED
    assert check_quote("QM9", SRC) == TOO_SHORT


def test_quote_ellipsis_in_order():
    assert check_quote("We propose a message passing ... results on QM9 benchmarks", SRC) == VERIFIED
    assert check_quote("results on QM9 benchmarks ... We propose a message passing", SRC) == UNVERIFIED


def test_funnel_conservation_and_unaccounted():
    f = Funnel()
    f.stage("a", 10, 7, {"x": 3})
    assert f.balanced
    f.stage("b", 10, 7, {"x": 1})
    assert not f.balanced
    assert f.stages[-1].dusen["UNACCOUNTED"] == 2


def test_eksik_sticky():
    f = Funnel()
    f.source("arxiv", EKSIK, "429")
    f.source("arxiv", OK, istek=3)
    assert f.sources["arxiv"]["durum"] == EKSIK and f.sources["arxiv"]["sebep"] == "429"
    assert f.as_dict()["durum"] == EKSIK
