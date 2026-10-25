import datetime as dt

from conftest import rec

from orkestra.config import Config
from orkestra.funnel import EKSIK, Funnel
from orkestra.http import QuotaExhausted
from orkestra.pipeline import preprint_abstracts
from orkestra.records import cutoff_filter

CUT = dt.date(2025, 6, 1)


class Ctx:
    def __init__(self, preprinter, k=150, exhausted=None):
        self.cfg = Config(arxiv_ozet_k=k)
        self.funnel = Funnel()
        self.cut = CUT
        self.preprinter = preprinter

        class H:
            pass
        self.http = H()
        self.http.exhausted = exhausted or {}


def pre(title, aid="2301.00001", date=(2023, 1, 5), abstract="We show a thing."):
    return rec(title, abstract=abstract, arxiv_id=aid, dates=[list(date)])


def doi_rec(title, date=(2023, 5, 1)):
    return rec(title, src="crossref", doi="10.1109/x." + title[:5], dates=[list(date)])


def test_found_copies_abstract_marks_and_counts():
    a = doi_rec("Fuzzing the Kernel Protocol Stack")
    b = doi_rec("Totally Unmatched Work On Cats")
    ctx = Ctx(lambda ts: [pre("Fuzzing the kernel protocol stack")])
    preprint_abstracts(ctx, [a, b])
    assert a["abstract"] == "We show a thing." and a["ozet_kaynagi"] == "arxiv_onbaski"
    assert a["arxiv_id"] == "2301.00001" and [2023, 1, 5] in a["dates"]
    assert not b["abstract"] and "ozet_kaynagi" not in b
    i = ctx.funnel.info
    assert (i["ozet_arxiv.aday"], i["ozet_arxiv.denendi"], i["ozet_arxiv.bulundu"], i["ozet_arxiv.bulunamadi"]) == (2, 2, 1, 1)


def test_conflict_number_blocks_match():
    a = doi_rec("Fuzzing Part II of the Kernel Stack")
    ctx = Ctx(lambda ts: [pre("Fuzzing Part III of the Kernel Stack")])
    preprint_abstracts(ctx, [a])
    assert not a["abstract"] and ctx.funnel.info["ozet_arxiv.bulunamadi"] == 1


def test_cap_k_and_batches_of_six():
    rs = [doi_rec(f"Unique Paper Title Number {'x' * i} here") for i in range(14)]
    calls = []
    ctx = Ctx(lambda ts: calls.append(ts) or [], k=8)
    preprint_abstracts(ctx, rs)
    assert [len(c) for c in calls] == [6, 2]
    assert ctx.funnel.info["ozet_arxiv.atlandi_tavan"] == 6 and ctx.funnel.info["ozet_arxiv.denendi"] == 8


def test_quota_stops_and_records_why():
    rs = [doi_rec(f"Another Distinct Title {'y' * i} study") for i in range(13)]
    n = []

    def boom(ts):
        n.append(1)
        raise QuotaExhausted("arxiv", 429, "5 denemede 429")
    ctx = Ctx(boom)
    preprint_abstracts(ctx, rs)
    assert len(n) == 1  # ilk istekten sonra durur
    assert ctx.funnel.info["ozet_arxiv.atlandi_kota"] == 13
    assert ctx.funnel.sources["ozet_arxiv"]["durum"] == EKSIK and "429" in ctx.funnel.sources["ozet_arxiv"]["sebep"]


def test_already_exhausted_makes_no_call():
    ctx = Ctx(lambda ts: (_ for _ in ()).throw(AssertionError("çağrılmamalı")), exhausted={"arxiv": "x"})
    preprint_abstracts(ctx, [doi_rec("Some Quite Long Distinct Title Here")])
    assert ctx.funnel.info["ozet_arxiv.atlandi_kota"] == 1 and ctx.funnel.info["ozet_arxiv.denendi"] == 0


def test_disabled_counts_skipped():
    ctx = Ctx(lambda ts: [], k=0)
    preprint_abstracts(ctx, [doi_rec("Some Quite Long Distinct Title Here")])
    assert ctx.funnel.info["ozet_arxiv.atlandi_kapali"] == 1


def test_existing_abstract_untouched_and_arxiv_id_not_reused():
    has = rec("Has Abstract Already Title Long", abstract="orig", dates=[[2020, 1, 1]], src="crossref", doi="10.1/a")
    a = doi_rec("Fuzzing the Kernel Protocol Stack")
    ctx = Ctx(lambda ts: [pre("Fuzzing the kernel protocol stack")])
    preprint_abstracts(ctx, [has, a], {"2301.00001"})
    assert has["abstract"] == "orig" and "ozet_kaynagi" not in has
    assert a["abstract"] and not a["arxiv_id"]  # id havuzda zaten var: yalnız özet kopyalanır


def test_postcutoff_preprint_does_not_change_cutoff_verdict():
    # yayın kesim öncesi (geçer); önbaskı sürümü kesim SONRASI: yine geçer, sayaç tutulur
    a = doi_rec("Fuzzing the Kernel Protocol Stack", date=(2023, 5, 1))
    ctx = Ctx(lambda ts: [pre("Fuzzing the kernel protocol stack", aid="2507.00001", date=(2025, 7, 1))])
    assert cutoff_filter([a], CUT)[0] == [a]
    preprint_abstracts(ctx, [a])
    assert [2025, 7, 1] in a["dates"] and cutoff_filter([a], CUT)[0] == [a]
    assert ctx.funnel.info["ozet_arxiv.onbaski_kesim_sonrasi"] == 1
    # kesim sonrası yayın zaten düşer; fonksiyon yalnız verilen (geçmiş) listeye dokunur
    late = doi_rec("Fuzzing the Kernel Protocol Stack", date=(2025, 9, 1))
    assert cutoff_filter([late], CUT)[0] == []
    # kesim öncesi önbaskı, kesim sonrası yayını KURTARMAZ: süzgeç çağıran sırada önce çalışır
    # (burada yalnız belgelenir: preprint_abstracts kesimden sonra koşar, düşenleri geri getirmez)
