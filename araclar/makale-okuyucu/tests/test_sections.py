from makale_okuyucu.pdftext import canonical, make_chunks, make_passages, pdf_pages, pdf_styled_lines, split_sections


def _pages(*texts):
    return [(i + 1, t) for i, t in enumerate(texts)]


def test_canonical_names():
    assert canonical("Introduction") == "introduction"
    assert canonical("Related Work") == "related_work"
    assert canonical("Background and Motivation") == "related_work"
    assert canonical("Our Approach") == "method"
    assert canonical("Experimental Setup") == "experiments"
    assert canonical("Results and Analysis") == "results"
    assert canonical("Limitations and Discussion") == "limitations"
    assert canonical("Conclusion and Future Work") == "conclusion"
    assert canonical("References") == "references"
    assert canonical("SpotIt Toolkit") == "other"


def test_generated_pdf_sections_and_pages(paper_pdf):
    secs = split_sections(pdf_pages(paper_pdf))
    names = [s.name for s in secs]
    assert names == ["front", "abstract", "introduction", "related_work", "method", "experiments",
                     "results", "conclusion", "references"]
    by = {s.name: s for s in secs}
    assert by["method"].pages == [2]
    assert by["results"].pages == [3]
    assert by["conclusion"].pages == [4]
    assert "Our method consists" in by["method"].text


def test_numbering_must_increase_rejects_table_noise():
    p = _pages("1 Introduction\nText here.\n2 Method\nWe do X.\n7 Tables Are Noise\n42 Big Row\n3 Experiments\nRun.")
    secs = split_sections(p)
    assert [s.title for s in secs] == ["Introduction", "Method", "Experiments"]
    assert "7 Tables Are Noise" in secs[1].text


def test_roman_and_split_number_lines():
    p = _pages("I. INTRODUCTION\nHello world.\nII. RELATED WORK\nOthers.\n3\nEvaluation\nNumbers.")
    secs = split_sections(p)
    assert [s.name for s in secs] == ["introduction", "related_work", "experiments"]


def test_subsections_are_not_boundaries():
    p = _pages("1 Introduction\nA.\n1.1 Scope Of Things\nB.\n2 Method\nC.")
    secs = split_sections(p)
    assert [s.title for s in secs] == ["Introduction", "Method"]
    assert "1.1 Scope Of Things" in secs[0].text


def test_inline_abstract_and_bare_keywords():
    p = _pages("Title\nAbstract—We study X deeply.\n1 Introduction\nIntro.", "Limitations\nWe only test English.\nReferences\n[1] A.")
    secs = split_sections(p)
    names = [s.name for s in secs]
    assert names == ["front", "abstract", "introduction", "limitations", "references"]
    assert "We study X" in secs[1].text
    assert secs[3].pages == [2]


def test_appendix_lettered_after_references_and_no_numbered_after():
    p = _pages("1 Introduction\nI.\n2 Method\nM.\nReferences\n3 Smith J. Something\nA Additional Proofs\nProof.")
    secs = split_sections(p)
    assert [s.name for s in secs] == ["introduction", "method", "references", "appendix"]
    assert "3 Smith J. Something" in secs[2].text


def test_chunks_skip_references_and_respect_size(paper_pdf):
    secs = split_sections(pdf_pages(paper_pdf))
    chunks, skipped = make_chunks(secs, 250)
    assert [s.name for s in skipped] == ["references"]
    assert all("Secret reference sentence" not in c.text for c in chunks)
    for c in chunks:
        assert len(c.text) <= 250 or len(c.segments) == 1
    # her satır tam bir kez parçalarda
    text_all = "\n".join(c.text for c in chunks)
    assert text_all.count("WidgetNet achieves 91.2") == 1


def test_long_section_split_keeps_pages():
    body = "\n".join(f"Sentence number {i} about widgets." for i in range(60))
    p = _pages("1 Method\n" + body, body)
    chunks, _ = make_chunks(split_sections(p), 500)
    assert len(chunks) > 3
    assert chunks[0].pages == [1] and chunks[-1].pages == [2]
    assert all(c.sections == ["method"] for c in chunks)


def test_passages(paper_pdf):
    ps = make_passages(split_sections(pdf_pages(paper_pdf)), 200)
    assert ps and all(p.section != "references" for p in ps)
    assert [p.idx for p in ps] == list(range(1, len(ps) + 1))

def test_table_of_contents_is_not_sections():
    toc = "Contents\n1 Introduction\n2\n2 Method\n4\n3 Experiments\n6\n4 Conclusion\n8\nAppendices\n9\n"
    body = ("1 Introduction\n" + "Intro text sentence. " * 12 + "\n2 Method\n" + "Method text sentence. " * 12
            + "\n3 Experiments\n" + "Exp text sentence. " * 12 + "\n4 Conclusion\n" + "Conc text. " * 12
            + "\nReferences\n[1] A.\nA Extra Proofs\nProof text here.")
    secs = split_sections(_pages(toc, body))
    names = [s.name for s in secs]
    assert names == ["front", "introduction", "method", "experiments", "conclusion", "references", "appendix"]
    assert secs[1].pages == [2] and "Contents" in secs[0].text


def test_spaced_letters_not_appendix_heading():
    p = _pages("References\n[1] A.\nc l a s s\nx\nB Real Appendix Title\nBody.")
    assert [s.title for s in split_sections(p)] == ["References", "B Real Appendix Title"]


def test_styled_headings_gate_numbered_lists():
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for txt, size in [("1 Introduction", 14), ("Some intro text here.", 10), ("2 Dataset Size", 10),
                      ("Bullet text about data.", 10), ("2 Method", 14), ("Method text here.", 10)]:
        page.insert_text((60, y), txt, fontsize=size)
        y += 20
    body = doc.tobytes()
    st = pdf_styled_lines(body)
    assert st and (1, "1 Introduction") in st and (1, "2 Dataset Size") not in st
    assert [s.title for s in split_sections(pdf_pages(body), st)] == ["Introduction", "Method"]
    assert [s.title for s in split_sections(pdf_pages(body), None)] == ["Introduction", "Dataset Size"]

