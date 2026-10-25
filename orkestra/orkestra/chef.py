"""Şef (Opus) istemleri: plan ve final sıralama. Şefe giden bağlam küçük tutulur:
planda yalnız soru + kesim; finalde yalnız kompakt aday kartları."""
from __future__ import annotations

import json

from orkestra.llm import call_json

PLAN_PROMPT = """TASK: plan a literature search.

Research question: <q>{soru}</q>
Cutoff date: {kesim}. Only works published BEFORE this date count.

Goal of the whole pipeline: find the ~30 most important prior works (papers) for this question,
the kind a careful expert survey published right after the cutoff would cite.

Produce JSON with:
- "alt_sorular": 4-8 sub-questions that together cover the field (foundations/classic methods,
  main method families, datasets/benchmarks, evaluation, applications, open problems, adjacent
  areas whose methods are reused). Each item:
    {{"id": "S1", "soru": "...",
      "sorgular": [4-6 short keyword queries for academic search engines, 2-6 terms each; vary the
                   terminology: synonyms, older and newer names, acronyms AND expansions, British/American
                   spelling, names used in neighbouring communities; use "double quotes" for fixed phrases],
      "yeterli": "one sentence: what would make coverage of this sub-question sufficient"}}
- "capa_calismalar": up to 25 specific works you are confident exist and that are central to the
  question (landmark/seminal papers, widely used benchmarks, key recent advances before the cutoff).
  Each: {{"baslik": exact title as best you know it, "yil": year}}. Do not invent titles; omit if unsure.
- "web_odaklari": 3 short English search phrases for finding curated lists of papers on the web
  (e.g. "awesome <topic> papers github", "<topic> reading list").

Reply with ONLY the JSON object."""

FINAL_PROMPT = """TASK: final ranking for a literature search.

Research question: <q>{soru}</q>
Cutoff: {kesim} (all candidates below are already verified to be published before it).
Sub-questions: {alt}

Below are {n} candidate cards, pre-ranked by retrieval signals. Format per line:
#<card> | <year> | cites=<n or ?> | <sources> | <title> | rel=<0-3 or ?> | <short reader note> | Q: "<verified quote from abstract>"

{kartlar}

Select the {k} works that matter MOST for answering the research question, as an expert surveying
the field would: seminal/foundational works, most influential method families, key benchmarks,
and the strongest recent advances. Prefer coverage across sub-questions over near-duplicates.
For each, write ONE sentence (max 25 words) explaining why it matters, grounded ONLY in what the
card says (title, quote, note). Do not add facts that the card does not support.

Reply ONLY with JSON: {{"secim": [{{"kart": <card number>, "gerekce": "..."}}, ... exactly {k} items, most important first]}}"""


def plan(llm, cfg, soru: str, kesim: str) -> tuple[dict | None, str]:
    obj, st = call_json(llm, PLAN_PROMPT.format(soru=soru, kesim=kesim), model=cfg.sef_model, stage="sef_plan")
    if st != "OK" or not isinstance(obj, dict):
        return None, st
    subs = []
    for i, s in enumerate(obj.get("alt_sorular") or []):
        if not isinstance(s, dict):
            continue
        qs = [str(q).strip() for q in (s.get("sorgular") or []) if str(q).strip()]
        subs.append({"id": str(s.get("id") or f"S{i + 1}"), "soru": str(s.get("soru") or ""),
                     "sorgular": qs[: cfg.max_queries_per_subq], "yeterli": str(s.get("yeterli") or "")})
    anchors = [{"baslik": str(a.get("baslik") or "").strip(), "yil": a.get("yil")}
               for a in (obj.get("capa_calismalar") or []) if isinstance(a, dict) and a.get("baslik")]
    web = [str(w) for w in (obj.get("web_odaklari") or []) if str(w).strip()][:5]
    return {"alt_sorular": subs, "capa_calismalar": anchors[:25], "web_odaklari": web}, "OK"


def fallback_plan(soru: str) -> dict:
    """Şef planı alınamazsa: soru metninin kendisi tek alt soru (EKSİK işaretlenir)."""
    return {"alt_sorular": [{"id": "S1", "soru": soru, "sorgular": [soru], "yeterli": ""}],
            "capa_calismalar": [], "web_odaklari": [soru + " papers list"]}


def card_line(i: int, c: dict) -> str:
    q = (c.get("alinti") or "").replace('"', "'")
    note = (c.get("not") or "").replace("|", "/")[:90]
    rel = c.get("rel")
    return (f"#{i} | {c.get('yil') or '?'} | cites={c.get('cites') if c.get('cites') is not None else '?'} | "
            f"{','.join(c.get('kaynaklar') or [])} | {c['baslik'][:160]} | rel={rel if rel is not None else '?'} | "
            f"{note} | Q: \"{q[:220]}\"")


def final(llm, cfg, soru: str, kesim: str, subs: list[dict], cards: list[dict]) -> tuple[list[dict] | None, str]:
    alt = json.dumps([f"{s['id']}: {s['soru']}" for s in subs], ensure_ascii=False)
    kartlar = "\n".join(card_line(i + 1, c) for i, c in enumerate(cards))
    k = min(cfg.final_n, len(cards))
    prompt = FINAL_PROMPT.format(soru=soru, kesim=kesim, alt=alt, n=len(cards), kartlar=kartlar, k=k)
    obj, st = call_json(llm, prompt, model=cfg.sef_model, stage="sef_final")
    if st != "OK" or not isinstance(obj, dict):
        return None, st
    return [x for x in (obj.get("secim") or []) if isinstance(x, dict)], "OK"
