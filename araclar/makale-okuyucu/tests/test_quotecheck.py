from makale_okuyucu import quotecheck as qc

SRC = "We propose a novel ﬁne-tuning method. The results are “significantly” better than\nthe base-\nline models on all tasks."


def test_verified_basic_and_case_whitespace():
    assert qc.check_quote("we PROPOSE a novel   fine-tuning method", SRC) == qc.VERIFIED


def test_curly_quotes_and_ligature():
    assert qc.check_quote('The results are "significantly" better', SRC) == qc.VERIFIED


def test_dehyphenation_line_break():
    assert qc.check_quote("better than the baseline models on all tasks", SRC) == qc.VERIFIED


def test_unverified_paraphrase():
    assert qc.check_quote("We propose a new fine-tuning approach", SRC) == qc.UNVERIFIED


def test_ellipsis_fragments_in_order():
    assert qc.check_quote("We propose a novel ... better than the base", SRC) == qc.VERIFIED
    assert qc.check_quote("better than the base ... We propose a novel", SRC) == qc.UNVERIFIED


def test_too_short_and_none():
    assert qc.check_quote("We propose", SRC) == qc.TOO_SHORT
    assert qc.check_quote("", SRC) == qc.NONE
    assert qc.check_quote(None, SRC) == qc.NONE


def test_locate_page_single_and_spanning():
    pages = [(3, "Alpha beta gamma delta epsilon zeta."), (4, "Eta theta iota kappa lambda mu nu.")]
    assert qc.locate_page("gamma delta epsilon zeta", pages) == "3"
    assert qc.locate_page("iota kappa lambda mu nu", pages) == "4"
    assert qc.locate_page("epsilon zeta. Eta theta iota", pages) == "3-4"
    assert qc.locate_page("not present anywhere at all", pages) is None
