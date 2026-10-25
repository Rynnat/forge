"""Deterministik sahte LLM (testler ve çevrimdışı deneme). İstem türünü TASK işaretinden anlar."""
from __future__ import annotations

import json
import re

from makale_okuyucu.config import FIELD_CAPS

_SENT = re.compile(r"(?<=[.!?])\s+")
PATTERNS = {
    "problem": r"\b(problem|challenge|we address|gap)\b",
    "katkilar": r"\b(we propose|we introduce|our contribution|we present)\b",
    "yontem": r"\b(our method|our approach|consists of|we use a)\b",
    "veri_setleri_ve_kaynaklar": r"\b(dataset|benchmark|corpus)\b",
    "deney_kurulumu": r"\b(gpu|parameters|we train|baseline)\b",
    "ana_sonuclar": r"\b(achieves|improves|accuracy|outperforms)\b",
    "sinirliliklar": r"\b(limitation|limited|fails to|does not generalize)\b",
    "gelecek_calisma": r"\b(future work|in the future)\b",
    "kapsam_disi": r"\b(do not address|out of scope|we do not|beyond the scope)\b",
    "en_yakin_isler": r"\b(et al\.|prior work|previous work)\b",
}


def _sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in _SENT.split(flat) if len(s.strip()) >= 20]


def _toks(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if len(t) > 2}


def default_responder(prompt: str, system: str) -> str:
    if "TASK: extract_chunk" in prompt:
        m = re.search(r"<text>\n(.*)\n</text>", prompt, re.S)
        sents = _sentences(m.group(1) if m else "")
        out: dict[str, list] = {}
        for f, pat in PATTERNS.items():
            for s in sents:
                if re.search(pat, s, re.I):
                    it = {"text": s[:150], "quote": s[:250]}
                    if f == "veri_setleri_ve_kaynaklar":
                        it.update(name=s.split()[0], link=None)
                    if f == "en_yakin_isler":
                        it.update(name=s.split()[0], relation="related")
                    out.setdefault(f, []).append(it)
                    if len(out[f]) >= 4:
                        break
        return json.dumps(out)
    if "TASK: merge_card" in prompt:
        fields: dict[str, list] = {}
        cur = None
        for ln in prompt.splitlines():
            if ln.startswith("## "):
                cur = ln[3:].strip()
                fields[cur] = []
            elif cur and (mm := re.match(r"\[([^\]]+)\] \(([VU])\)", ln)):
                fields[cur].append((mm.group(2) != "V", mm.group(1)))
        return json.dumps({"fields": {f: [i for _, i in sorted(v)][: FIELD_CAPS.get(f, 5)]
                                      for f, v in fields.items()}})
    if "TASK: ask_card" in prompt:
        q = re.search(r"Question: (.*)", prompt).group(1)
        qt = _toks(q)
        best, best_id = 0.0, None
        for mm in re.finditer(r"^\[([^\]]+)\] \w+: (.*)$", prompt, re.M):
            ov = len(_toks(mm.group(2)) & qt) / max(1, len(qt))
            if ov > best:
                best, best_id = ov, mm.group(1)
        if best >= 0.6:
            return json.dumps({"answerable": True, "answer": "mock answer", "item_ids": [best_id], "search_terms": []})
        return json.dumps({"answerable": False, "answer": "", "item_ids": [], "search_terms": sorted(qt)})
    if "TASK: ask_sections" in prompt:
        q = re.search(r"Question: (.*)", prompt).group(1)
        qt = _toks(q)
        best, best_q, best_p = 0.0, "", ""
        for pm in re.finditer(r'<passage id="(P\d+)"[^>]*>\n(.*?)\n</passage>', prompt, re.S):
            for s in _sentences(pm.group(2)):
                ov = len(_toks(s) & qt) / max(1, len(qt))
                if ov > best:
                    best, best_q, best_p = ov, s, pm.group(1)
        if best >= 0.5:
            return json.dumps({"found": True, "answer": "mock", "quotes": [{"passage": best_p, "quote": best_q[:250]}]})
        return json.dumps({"found": False, "answer": "", "quotes": []})
    return "{}"
