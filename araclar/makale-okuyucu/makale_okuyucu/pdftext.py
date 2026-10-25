"""PDF → sayfa metni → bölümler → parçalar / pasajlar. LLM yok.

Sayfa numarası (1 tabanlı) her satırda taşınır; bölüm ve parçalar `segments=[(sayfa, metin)]`
listesi tutar, böylece alıntının sayfası kodla bulunabilir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

CANONICAL = [
    "abstract", "introduction", "related_work", "method", "experiments", "results",
    "limitations", "conclusion", "references", "appendix", "other",
]

# sıra önemli: ilk eşleşen kazanır
_KEYWORDS: list[tuple[str, re.Pattern]] = [
    ("references", re.compile(r"^(references?|bibliography|works cited)$")),
    ("appendix", re.compile(r"^(appendix|appendices|supplementary|supplemental)\b")),
    ("abstract", re.compile(r"^abstract$")),
    ("limitations", re.compile(r"limitation|threats? to validity|broader impact|ethic")),
    ("conclusion", re.compile(r"conclu|concluding|summary and|future work|final remarks")),
    ("introduction", re.compile(r"^introduction|^overview$|^motivation$")),
    ("related_work", re.compile(r"related work|prior work|previous work|background|literature|related research")),
    ("results", re.compile(r"result|analysis|discussion|ablation|finding|case stud")),
    ("experiments", re.compile(r"experiment|evaluation|empirical|setup|benchmark|implementation detail")),
    ("method", re.compile(r"method|approach|model|framework|architecture|algorithm|design|formulation"
                          r"|preliminar|problem (setup|statement|definition|formulation)|system|pipeline"
                          r"|proposed|our |overview of")),
]

# yalnız başına satır olarak görülünce başlık sayılan anahtar kelimeler (numarasız)
_BARE = re.compile(
    r"^(abstract|introduction|related work|background|references|bibliography|acknowledge?ments?"
    r"|limitations?|conclusions?|discussion|appendix|appendices|broader impacts?"
    r"|limitations and future work|conclusion and future work|conclusions and future work"
    r"|ethics statement|impact statement|reproducibility statement)$", re.I)
_NUMBERED = re.compile(r"^(?P<num>\d{1,2}|[IVX]{1,6})\.?\s+(?P<title>[A-Z][^\n]{1,80})$")
_LETTERED = re.compile(r"^(?:[Aa]ppendix\s+|APPENDIX\s+)?(?P<num>[A-H])(?:\.|:)?\s+(?P<title>[A-Z][a-zA-Z\-]{2,}[^\n]{0,78})$")
_ABSTRACT_INLINE = re.compile(r"^abstract\s*[.:—–-]\s*(?P<rest>.+)$", re.I)
_ROMAN = {"I": 1, "V": 5, "X": 10}


def _roman(s: str) -> int:
    total, prev = 0, 0
    for ch in reversed(s):
        v = _ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def _num(s: str) -> int:
    return int(s) if s.isdigit() else _roman(s)


def canonical(title: str) -> str:
    t = re.sub(r"[^a-z ]+", " ", title.lower())
    t = re.sub(r"\s+", " ", t).strip()
    for name, pat in _KEYWORDS:
        if pat.search(t):
            return name
    return "other"


@dataclass
class Section:
    name: str
    title: str
    segments: list[tuple[int, str]] = field(default_factory=list)
    head: int = 0  # baştaki başlık satırı sayısı (metinde kalır: bağlam + alıntı için)

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.segments)

    @property
    def body(self) -> str:
        return "\n".join(t for _, t in self.segments[self.head:])

    @property
    def pages(self) -> list[int]:
        return sorted({p for p, _ in self.segments})

    def to_dict(self) -> dict:
        return {"name": self.name, "title": self.title, "head": self.head,
                "segments": [list(s) for s in self.segments]}

    @classmethod
    def from_dict(cls, d: dict) -> "Section":
        return cls(d["name"], d["title"], [(int(p), t) for p, t in d["segments"]], int(d.get("head", 0)))


@dataclass
class Chunk:
    idx: int
    sections: list[str]
    segments: list[tuple[int, str]]

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.segments)

    @property
    def pages(self) -> list[int]:
        return sorted({p for p, _ in self.segments})

    def page_texts(self) -> list[tuple[int, str]]:
        """Sayfa başına birleştirilmiş metin (sıralı)."""
        out: dict[int, list[str]] = {}
        for p, t in self.segments:
            out.setdefault(p, []).append(t)
        return [(p, "\n".join(ts)) for p, ts in sorted(out.items())]

    def label(self) -> str:
        pg = self.pages
        rng = f"p.{pg[0]}-{pg[-1]}" if pg else "p.?"
        return f"#{self.idx} {'+'.join(dict.fromkeys(self.sections))} {rng}"


# --------------------------------------------------------------------------- PDF
def pdf_pages(body: bytes) -> list[tuple[int, str]]:
    import pymupdf

    with pymupdf.open(stream=body, filetype="pdf") as doc:
        return [(i + 1, page.get_text()) for i, page in enumerate(doc)]


def pdf_styled_lines(body: bytes) -> set[tuple[int, str]] | None:
    """Başlık biçimli satırlar: gövde yazı boyundan >= %8 büyük ya da kalın.
    Belge tek boyut/kalınlıksızsa None (biçim bilgisi kullanılmaz)."""
    import pymupdf
    from collections import Counter

    sizes: Counter = Counter()
    lines: list[tuple[int, str, float, bool]] = []
    with pymupdf.open(stream=body, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            for blk in page.get_text("dict").get("blocks", []):
                for ln in blk.get("lines", []):
                    spans = [s for s in ln.get("spans", []) if s.get("text", "").strip()]
                    if not spans:
                        continue
                    text = "".join(s["text"] for s in ln["spans"]).strip()
                    for s in spans:
                        sizes[round(s["size"], 1)] += len(s["text"])
                    big = max(s["size"] for s in spans)
                    bold = all((s.get("flags", 0) & 16) or "bold" in s.get("font", "").lower() for s in spans)
                    lines.append((i + 1, text, big, bold))
    if not sizes:
        return None
    body_size = sizes.most_common(1)[0][0]
    styled = {(pg, t) for pg, t, big, bold in lines if big >= body_size * 1.08 or bold}
    return styled or None


def pdf_title(body: bytes) -> str:
    import pymupdf

    with pymupdf.open(stream=body, filetype="pdf") as doc:
        return ((doc.metadata or {}).get("title") or "").strip()


# --------------------------------------------------------------------------- bölümleme
def split_sections(pages: list[tuple[int, str]], styled: set[tuple[int, str]] | None = None) -> list[Section]:
    """Satır sezgisiyle bölümleme.
    - İçindekiler (ToC) girdisi başlık sayılmaz: başlık adayından hemen sonraki satır yalnız
      sayıysa (sayfa no) ya da satır nokta dizisi + sayı ile bitiyorsa.
    - `styled` verilirse numaralı/harfli başlık adayı biçimli (büyük/kalın) olmalı; bu,
      giriş bölümündeki numaralı listelerin başlık sanılmasını engeller."""
    lines: list[tuple[int, str]] = []
    for pno, text in pages:
        for ln in text.splitlines():
            lines.append((pno, ln))
    secs, _ = _split(lines, styled)
    # boş bölümleri at (yalnız başlık satırı olanlar)
    return [sec for sec in secs if sec.body.strip()]


_PAGENO = re.compile(r"\d{1,4}|[ivxl]{1,6}")
_DOT_LEADER = re.compile(r"(\.\s*){3,}\d{1,4}$")


def _split(lines: list[tuple[int, str]],
           styled: set[tuple[int, str]] | None = None) -> tuple[list[Section], list[int]]:
    def ok_style(pno: int, *texts: str) -> bool:
        return styled is None or any((pno, t.strip()) in styled for t in texts)

    def toc_entry(title_idx: int) -> bool:
        if _DOT_LEADER.search(lines[title_idx][1].strip()):
            return True
        j = title_idx + 1
        while j < len(lines) and not lines[j][1].strip():
            j += 1
        return j < len(lines) and bool(_PAGENO.fullmatch(lines[j][1].strip()))

    sections: list[Section] = [Section("front", "")]
    starts: list[int] = [0]
    last_num = 0
    in_back = False  # references/appendix'ten sonra arap rakamlı başlık kabul edilmez

    def start(name: str, title: str, pno: int, heading: str, idx: int) -> None:
        nonlocal in_back
        sections.append(Section(name, title, [(pno, heading)], head=1))
        starts.append(idx)
        if name in ("references", "appendix"):
            in_back = True

    i = 0
    while i < len(lines):
        pno, raw = lines[i]
        s = raw.strip()
        handled = False
        if 1 <= len(s) <= 90 and not toc_entry(i):
            m_abs = _ABSTRACT_INLINE.match(s)
            if _BARE.match(s.rstrip(":. ")):
                start(canonical(s), s.rstrip(":. "), pno, raw, i)
                handled = True
            elif m_abs and not any(sec.name == "abstract" for sec in sections):
                start("abstract", "Abstract", pno, raw, i)
                sections[-1].head = 0  # satırın geri kalanı özet metni
                handled = True
            else:
                m = _NUMBERED.match(s)
                if (m and not in_back and not s.endswith(".") and len(m.group("title").split()) <= 12
                        and ok_style(pno, s)):
                    n = _num(m.group("num"))
                    if n == last_num + 1 or (last_num == 0 and n in (1, 2)):
                        title = m.group("title").strip()
                        start(canonical(title), title, pno, raw, i)
                        last_num = n
                        handled = True
                elif (re.fullmatch(r"\d{1,2}|[IVX]{1,6}", s) and not in_back
                      and _num(s) == last_num + 1 and i + 1 < len(lines)):
                    nxt = lines[i + 1][1].strip()
                    if (re.match(r"^[A-Z][^\n]{1,80}$", nxt) and len(nxt.split()) <= 12 and not nxt.endswith(".")
                            and ok_style(lines[i + 1][0], s, nxt) and not toc_entry(i + 1)):
                        start(canonical(nxt), nxt, pno, f"{s} {nxt}", i)
                        last_num = _num(s)
                        i += 2
                        continue
                elif in_back:
                    m2 = _LETTERED.match(s)
                    if m2 and len(m2.group("title").split()) <= 12 and not s.endswith(".") and ok_style(pno, s):
                        start("appendix", s, pno, raw, i)
                        handled = True
        if not handled:
            sections[-1].segments.append((pno, raw))
        i += 1
    return sections, starts


# --------------------------------------------------------------------------- parçalama
def _windows(segments: list[tuple[int, str]], max_chars: int) -> list[list[tuple[int, str]]]:
    out, cur, size = [], [], 0
    for p, t in segments:
        if size + len(t) + 1 > max_chars and cur:
            out.append(cur)
            cur, size = [], 0
        cur.append((p, t))
        size += len(t) + 1
    if cur:
        out.append(cur)
    return out


def make_chunks(sections: list[Section], max_chars: int) -> tuple[list[Chunk], list[Section]]:
    """(parçalar, atlananlar). references LLM'e gitmez."""
    chunks: list[Chunk] = []
    skipped: list[Section] = []
    cur_secs: list[str] = []
    cur: list[tuple[int, str]] = []
    size = 0

    def flush():
        nonlocal cur, cur_secs, size
        if cur and "".join(t for _, t in cur).strip():
            chunks.append(Chunk(len(chunks) + 1, cur_secs, cur))
        cur, cur_secs, size = [], [], 0

    for sec in sections:
        if sec.name == "references":
            skipped.append(sec)
            continue
        n = len(sec.text)
        if size + n <= max_chars:
            cur.extend(sec.segments)
            cur_secs.append(sec.name)
            size += n
            continue
        flush()
        if n <= max_chars:
            cur, cur_secs, size = list(sec.segments), [sec.name], n
            continue
        wins = _windows(sec.segments, max_chars)
        for w in wins[:-1]:
            chunks.append(Chunk(len(chunks) + 1, [sec.name], w))
        cur, cur_secs, size = list(wins[-1]), [sec.name], sum(len(t) + 1 for _, t in wins[-1])
    flush()
    return chunks, skipped


@dataclass
class Passage:
    idx: int
    section: str
    title: str
    segments: list[tuple[int, str]]

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.segments)

    def page_texts(self) -> list[tuple[int, str]]:
        return Chunk(0, [], self.segments).page_texts()


def make_passages(sections: list[Section], max_chars: int) -> list[Passage]:
    out: list[Passage] = []
    for sec in sections:
        if sec.name == "references":
            continue
        for w in _windows(sec.segments, max_chars):
            if "".join(t for _, t in w).strip():
                out.append(Passage(len(out) + 1, sec.name, sec.title, w))
    return out
