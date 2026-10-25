"""Kimlik ve metin normalizasyonu (gapmine/normalize.py kopyası)."""
from __future__ import annotations

import re
import unicodedata

_DOI_PREFIX = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:)", re.I)
_ARXIV_DOI = re.compile(r"^10\.48550/arxiv\.(.+)$", re.I)
_ARXIV_URL = re.compile(r"arxiv\.org/(?:abs|pdf)/([^\s?#]+?)(?:\.pdf)?(?:[?#].*)?$", re.I)
_ARXIV_VERSION = re.compile(r"v\d+$", re.I)


def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = _DOI_PREFIX.sub("", doi.strip()).strip().lower()
    return d or None


def norm_arxiv(aid: str | None) -> str | None:
    """'arXiv:2401.01234v2' / URL / 10.48550 DOI -> '2401.01234'. Eski stil 'cs/0101001' korunur."""
    if not aid:
        return None
    s = aid.strip()
    m = _ARXIV_URL.search(s)
    if m:
        s = m.group(1)
    m = _ARXIV_DOI.match(norm_doi(s) or "")
    if m:
        s = m.group(1)
    s = re.sub(r"^arxiv:", "", s, flags=re.I).strip()
    s = _ARXIV_VERSION.sub("", s)
    return s.lower() or None


def arxiv_from_doi(doi: str | None) -> str | None:
    d = norm_doi(doi)
    if not d:
        return None
    m = _ARXIV_DOI.match(d)
    return norm_arxiv(m.group(1)) if m else None


def norm_title(title: str | None) -> str:
    if not title:
        return ""
    t = unicodedata.normalize("NFKD", title)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.lower()
    t = re.sub(r"<[^>]+>", " ", t)  # <i>, <sub> vb. HTML/MathML etiketleri
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def clean_ws(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def inverted_index_to_text(inv: dict[str, list[int]] | None) -> str:
    """OpenAlex abstract_inverted_index -> düz metin.

    Boş/None -> "". Pozisyon boşlukları (eksik indeksler) atlanır; aynı pozisyona
    iki kelime düşerse (bozuk veri) ilk gelen korunur.
    """
    if not inv:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inv.items():
        for pos in positions or []:
            if isinstance(pos, int) and pos not in slots:
                slots[pos] = word
    return " ".join(slots[i] for i in sorted(slots))
