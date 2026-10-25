"""Deterministik alıntı doğrulama (gapmine/quotecheck.py kopyası, değişmeden).

Bir alıntı, kaynak metnin içinde boşluk + büyük/küçük harf normalize edilmiş haliyle
aranır. Ek (yalnız biçimsel) normalizasyonlar:
  * Unicode NFKC (ligatürler: "ﬁ" -> "fi"), kıvrık tırnak/tire -> düz,
  * yumuşak tire ve sıfır genişlikli karakterler silinir,
  * PDF satır sonu tirelemesi ("equiva-\\nlence") yalnızca KAYNAKTA birleştirilir
    ve ikinci bir deneme olarak kullanılır.
Üç nokta ("...", "…") içeren alıntı parçalara bölünür; her parça en az
MIN_FRAGMENT karakter olmalı ve kaynakta SIRAYLA bulunmalıdır.

Sonuçlar: VERIFIED | UNVERIFIED | TOO_SHORT | NONE (alıntı yok).
UNVERIFIED / TOO_SHORT alıntılar karara katılmaz.
"""
from __future__ import annotations

import re
import unicodedata

MIN_QUOTE = 20  # karakter; kısa alıntılar ("SQL") her metinde geçer -> kanıt değil
MIN_FRAGMENT = 15

VERIFIED = "VERIFIED"
UNVERIFIED = "UNVERIFIED"
TOO_SHORT = "TOO_SHORT"
NONE = "NONE"

_TRANS = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ",
})
_INVISIBLE = re.compile("[­​‌‍⁠﻿]")
_ELLIPSIS = re.compile(r"\s*(?:\.\s*\.\s*\.|…|\[\s*\.\.\.\s*\])\s*")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = _INVISIBLE.sub("", t)
    t = t.translate(_TRANS)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


def dehyphenate(text: str) -> str:
    """'equiva-\\n lence' -> 'equivalence' (yalnız satır sonu tirelemesi)."""
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text or "")


def _find_in_order(fragments: list[str], hay: str) -> bool:
    pos = 0
    for frag in fragments:
        i = hay.find(frag, pos)
        if i < 0:
            return False
        pos = i + len(frag)
    return True


def check_quote(quote: str | None, source: str | None) -> str:
    if not quote or not quote.strip():
        return NONE
    q = normalize(quote).strip(" \"'")
    fragments = [f.strip(" \"'") for f in _ELLIPSIS.split(q)]
    fragments = [f for f in fragments if f]
    if not fragments:
        return NONE
    if sum(len(f) for f in fragments) < MIN_QUOTE:
        return TOO_SHORT
    if len(fragments) > 1 and any(len(f) < MIN_FRAGMENT for f in fragments):
        return TOO_SHORT
    hay = normalize(source or "")
    if _find_in_order(fragments, hay):
        return VERIFIED
    hay2 = normalize(dehyphenate(source or ""))
    if hay2 != hay and _find_in_order(fragments, hay2):
        return VERIFIED
    return UNVERIFIED
