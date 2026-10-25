from __future__ import annotations

import pytest

from makale_okuyucu.config import Config
from makale_okuyucu.fetch import HttpResponse

PAPER_PAGES = [
    [
        "A Tiny Paper About Widget Learning",
        "Abstract",
        "We address the problem of widget learning under noisy labels.",
        "We propose WidgetNet, a simple model for widgets.",
        "1 Introduction",
        "Widget learning is a hard challenge for current systems.",
        "Our contribution is a new loss and a new benchmark.",
    ],
    [
        "2 Related Work",
        "Smith et al. proposed GadgetNet for gadgets in prior work.",
        "Previous work by Lee et al. studied noisy labels without widgets.",
        "3 Method",
        "Our method consists of an encoder and a robust loss.",
        "The encoder uses twelve transformer layers.",
        "We do not address multi-modal widgets in this paper.",
    ],
    [
        "4 Experiments",
        "We use the WidgetBench dataset with 10k samples.",
        "We train on one GPU with 7 billion parameters.",
        "5 Results",
        "WidgetNet achieves 91.2 percent accuracy on WidgetBench.",
        "It outperforms GadgetNet by 4.1 points in every split.",
    ],
    [
        "6 Conclusion",
        "A limitation is that the loss does not generalize to video.",
        "In future work we will study widget video streams.",
        "References",
        "[1] J. Smith et al. GadgetNet. 2020. Secret reference sentence here.",
        "[2] K. Lee et al. Noisy labels. 2021.",
    ],
]


def make_pdf(pages: list[list[str]]) -> bytes:
    import pymupdf

    doc = pymupdf.open()
    for lines in pages:
        page = doc.new_page()
        y = 72
        for ln in lines:
            page.insert_text((60, y), ln, fontsize=10)
            y += 16
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def paper_pdf() -> bytes:
    return make_pdf(PAPER_PAGES)


@pytest.fixture
def cfg(tmp_path) -> Config:
    return Config(data_dir=tmp_path / "data", llm_backend="mock", llm_workers=2, chunk_chars=400,
                  passage_chars=300)


class FakeHttp:
    def __init__(self, routes: dict):
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, url: str) -> HttpResponse:
        self.calls.append(url)
        for prefix, resp in self.routes.items():
            if url.startswith(prefix):
                return resp(url) if callable(resp) else resp
        return HttpResponse(404, "text/html", b"not found")


@pytest.fixture
def fake_http():
    return FakeHttp
