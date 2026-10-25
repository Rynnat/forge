import json

import pytest

from makale_okuyucu.fetch import HttpResponse, InputError, classify, download, resolve_input

CF_BODY = b"<html><title>Just a moment...</title><script src='/cdn-cgi/challenge-platform/x'></script></html>"


@pytest.mark.parametrize("raw,kind,key", [
    ("2501.08156", "arxiv", "arxiv:2501.08156"),
    ("2501.08156v3", "arxiv", "arxiv:2501.08156"),
    ("arXiv:2501.08156", "arxiv", "arxiv:2501.08156"),
    ("https://arxiv.org/abs/2501.08156v2", "arxiv", "arxiv:2501.08156"),
    ("https://arxiv.org/pdf/2501.08156", "arxiv", "arxiv:2501.08156"),
    ("hep-th/9901001", "arxiv", "arxiv:hep-th/9901001"),
    ("10.1145/3368089.3409741", "doi", "doi:10.1145/3368089.3409741"),
    ("https://doi.org/10.1145/3368089.3409741", "doi", "doi:10.1145/3368089.3409741"),
    ("doi:10.48550/arXiv.2501.08156", "arxiv", "arxiv:2501.08156"),
])
def test_resolve_input(raw, kind, key):
    inp = resolve_input(raw)
    assert (inp.kind, inp.key) == (kind, key)


def test_resolve_url_and_local(tmp_path, paper_pdf):
    inp = resolve_input("https://example.org/paper.pdf")
    assert inp.kind == "url" and inp.key.startswith("url:")
    f = tmp_path / "x.pdf"
    f.write_bytes(paper_pdf)
    loc = resolve_input(str(f))
    assert loc.kind == "local" and loc.key.startswith("sha:")


def test_resolve_bad_input():
    with pytest.raises(InputError):
        resolve_input("hello world")
    with pytest.raises(InputError):
        resolve_input("   ")


def test_classify_statuses(paper_pdf):
    assert classify(HttpResponse(200, "application/pdf", paper_pdf)) == "OK"
    assert classify(HttpResponse(403, "text/html", CF_BODY)) == "BOT_BLOCKED"
    assert classify(HttpResponse(200, "text/html", CF_BODY)) == "BOT_BLOCKED"
    assert classify(HttpResponse(403, "text/html", b"<html>forbidden</html>")) == "PAYWALL"
    assert classify(HttpResponse(402, "text/html", b"")) == "PAYWALL"
    assert classify(HttpResponse(200, "text/html", b"<p>Access through your institution</p>")) == "PAYWALL"
    assert classify(HttpResponse(200, "text/html", b"<p>landing page</p>")) == "NOT_PDF"
    assert classify(HttpResponse(404, "text/html", b"")) == "NOT_FOUND"
    assert classify(HttpResponse(500, "text/html", b"")) == "HTTP_ERROR"
    assert classify(HttpResponse(None, error="timeout")) == "NETWORK_ERROR"
    assert classify(HttpResponse(503, "text/html", b"x", {"cf-mitigated": "challenge"})) == "BOT_BLOCKED"


def test_download_arxiv_ok(fake_http, paper_pdf):
    http = fake_http({"https://arxiv.org/pdf/": HttpResponse(200, "application/pdf", paper_pdf)})
    fr = download(resolve_input("2501.08156"), http)
    assert fr.status == "OK" and fr.body == paper_pdf and fr.source_url == "https://arxiv.org/pdf/2501.08156"


def test_download_doi_via_openalex_prefers_arxiv(fake_http, paper_pdf):
    work = {"title": "T", "locations": [{"landing_page_url": "https://arxiv.org/abs/2401.00001v2"}],
            "best_oa_location": {"pdf_url": "https://pub.example/x.pdf", "landing_page_url": "https://pub.example/x"}}
    http = fake_http({
        "https://api.openalex.org/works/doi:": HttpResponse(200, "application/json", json.dumps(work).encode()),
        "https://arxiv.org/pdf/2401.00001": HttpResponse(200, "application/pdf", paper_pdf),
    })
    fr = download(resolve_input("10.1000/xyz"), http)
    assert fr.status == "OK" and fr.title == "T"
    assert fr.source_url == "https://arxiv.org/pdf/2401.00001"


def test_download_doi_cloudflare_then_paywall_reports_bot_blocked(fake_http):
    work = {"title": "T", "locations": [],
            "best_oa_location": {"pdf_url": "https://pub.example/x.pdf", "landing_page_url": "https://pub.example/land"}}
    http = fake_http({
        "https://api.openalex.org/": HttpResponse(200, "application/json", json.dumps(work).encode()),
        "https://pub.example/x.pdf": HttpResponse(403, "text/html", CF_BODY),
        "https://pub.example/land": HttpResponse(402, "text/html", b""),
    })
    fr = download(resolve_input("10.1000/xyz"), http)
    assert fr.status == "BOT_BLOCKED"
    assert len([a for a in fr.attempts if "pub.example" in a]) == 2
    # atlatma yok: her URL yalnız bir kez istendi
    assert http.calls.count("https://pub.example/x.pdf") == 1


def test_download_doi_paywall_only(fake_http):
    work = {"title": "T", "locations": [], "best_oa_location": {"landing_page_url": "https://pub.example/land"}}
    http = fake_http({
        "https://api.openalex.org/": HttpResponse(200, "application/json", json.dumps(work).encode()),
        "https://pub.example/land": HttpResponse(200, "text/html", b"<a>Buy article</a>"),
    })
    assert download(resolve_input("10.1000/xyz"), http).status == "PAYWALL"


def test_download_doi_no_oa_and_unknown(fake_http):
    http = fake_http({"https://api.openalex.org/": HttpResponse(200, "application/json",
                                                                  json.dumps({"title": "T", "best_oa_location": None}).encode())})
    assert download(resolve_input("10.1000/xyz"), http).status == "NO_OA"
    http2 = fake_http({})
    assert download(resolve_input("10.1000/xyz"), http2).status == "NOT_FOUND"


def test_download_network_error(fake_http):
    http = fake_http({"https://arxiv.org/": HttpResponse(None, error="ConnectionError")})
    fr = download(resolve_input("2501.08156"), http)
    assert fr.status == "NETWORK_ERROR" and "ConnectionError" in fr.attempts[-1]


def test_download_local_not_pdf(tmp_path):
    f = tmp_path / "x.pdf"
    f.write_bytes(b"hello, not a pdf")
    assert download(resolve_input(str(f)), lambda u: None).status == "NOT_PDF"
