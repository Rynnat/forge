# Forge

Forge is an experiment in multi-agent literature search with a pre-registered evaluation. An expensive model
(Claude Opus) acts as the *chef*: it breaks a research question into sub-questions, decides what counts as
"enough", and makes the final call. Cheap *players* do the bulk work: Python collectors for arXiv, Crossref,
DBLP and OpenCitations, and Claude Haiku readers and web workers. They screen about 1,200 candidate papers per
question and verify quotes in code, so the chef only sees a distilled, evidence-backed summary.

The interesting part is the evaluation. Before writing any pipeline code, I committed a pre-registration with
the hypothesis, the metric, the thresholds and a kill criterion. The gold set was 30 recent arXiv surveys from
10 CS areas, giving 4,089 reference papers. It was kept in a separate repository, and only its SHA-256 hash was
committed here. The orchestra was then compared against a single Opus agent doing web search.

**It lost.** The orchestra averaged 36.7% recall@30 against 45.7% for the single agent (−9.0 points, 3 wins /
25 losses / 2 ties). It cost 67% as much, and the pre-registered target was ≤ 50%. Faithfulness was perfect:
30/30 audited claims were supported and none were fabricated. Under the pre-set kill criterion the orchestra
was archived.

**Full evaluation report: [docs/EVALUATION.md](docs/EVALUATION.md)**

> Note on the metric: "recall@30" here is |gold ∩ top-30| / min(30, |gold|). Every survey has at least 46 gold
> references, so the metric is the share of a system's 30 picks that appear in the survey's bibliography. It is
> not the share of all 4,089 references. The evaluation report covers this distinction in detail.

## Results at a glance

| System | recall@30 | Cost / question | Time / question |
|---|---|---|---|
| **B**: Forge orchestra v0 (Opus chef + Haiku/code players) | 36.7 | $0.64 | ~23 min |
| **A1**: single Opus agent, web search required (primary baseline) | **45.7** | $0.95 | ~3 min |
| A0: single Opus agent, original prompt, mostly from memory (descriptive) | 40.8 | $0.17 | ~1 min |

The numbers are 30 paired questions with one run each. Costs are theoretical API list prices. The verdict is
**ARCHIVE (REJECT)**. Re-scoring the committed runs reproduces the committed report byte-for-byte.

## Architecture

```
research question + cutoff date
          │
  1. Chef plan (Opus) ─────────── 4–8 sub-questions, query variants, "enough" criterion, anchor papers
          │
  2. Collectors (parallel) ────── arXiv · Crossref · DBLP · OpenAlex · Haiku web workers
          │                       (web hits must resolve to a real arXiv/Crossref record to enter the pool)
  3. Dedup + cutoff filter ────── arXiv ID / DOI / normalized title; preprint↔publication merge
  4. Citation expansion ───────── OpenCitations references + citing works of top seeds
  5. Readers (Haiku ×4) ───────── relevance 0–3 + quote; only "certainly irrelevant" is dropped;
          │                       quotes verified against the source text in code
  6. Distiller (code) ─────────── BM25 + embeddings (RRF) + reader score + citations, KMeans diversity cap → 80 cards
  7. Chef final (Opus) ────────── ranks 30 works from the 80 cards, ≤ 4,000-token summary
```

Every stage logs `in = out + Σ dropped(reason)`. A missing or rate-limited source marks the run `EKSİK`
(incomplete) instead of failing silently.

## Repository layout

| Path | What it is |
|---|---|
| [`orkestra/`](orkestra/) | The chef–player pipeline (`python -m orkestra run/batch`), baseline runners (`deney/taban.py`), faithfulness auditor (`deney/sadakat.py`) and recall@30 scorer (`orkestra/deney/puanla.py`) |
| [`orkestra/deney-sonuc/`](orkestra/deney-sonuc/) | Raw outputs of every experiment run (B, A1, A0, audit) and the generated report `RAPOR.md` |
| [`analiz/`](analiz/) | Report generator: paired statistics, sign test, thresholds, per-area breakdown |
| [`araclar/makale-okuyucu/`](araclar/makale-okuyucu/) | Paper reader: PDF → quote-verified summary card, cached |
| [`araclar/maliyet-sayaci/`](araclar/maliyet-sayaci/) | Cost counter: token and dollar accounting from Claude Code transcripts (reads only usage fields) |
| [`ONKAYIT-*.md`](ONKAYIT-orkestra-v0.md) | Pre-registrations, committed before the code or runs they describe |
| [`TAHMIN-orkestra-v0.md`](TAHMIN-orkestra-v0.md) | Prediction written before the results were seen |
| [`gelistirme/`](gelistirme/), [`pilot-fikir/`](pilot-fikir/) | Side measurements and pilots (e.g. Opus arXiv-ID accuracy: 0 non-existent IDs out of 602) |
| [`README.tr.md`](README.tr.md), `KURALLAR.md`, `KAYIT.md` | Original working rules and registry (Turkish) |

Most internal notes, identifiers and log messages are in Turkish. The two entry points in English are this
README and the evaluation report.

## Quickstart

Requirements: Python ≥ 3.11. Running the pipeline live also needs the
[`claude` CLI](https://docs.claude.com/en/docs/claude-code), which handles the Opus and Haiku calls.

```bash
git clone https://github.com/Rynnat/forge.git && cd forge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline test suites (179 tests, no network, mocked LLM)
(cd orkestra && python -m pytest -q)
(cd araclar/makale-okuyucu && python -m pytest -q)
(cd araclar/maliyet-sayaci && python -m pytest -q)
python -m pytest -q analiz -p no:cacheprovider

# Live run on one question (calls Opus/Haiku via the claude CLI, ~$0.6, ~20 min)
cd orkestra
python -m orkestra run --soru "What are the key works on protocol fuzzing?" --kesim 2025-06-01 --out ../out/demo
```

The output directory contains `sonuc.json` (the 30 ranked works with identifiers and justifications),
`ozet.md` (the summary returned to the chef), `funnel.json` (per-stage accounting) and `kartlar.json` (the 80
cards the chef saw).

## Status

The orchestra v0 is archived. A v1 idea, a local arXiv index to remove the rate-limit bottleneck, is on the
`v1` branch, but it has not been evaluated. Under the project's own rules, v1 gets one attempt and must clear a
new pre-registration.

## License

[MIT](LICENSE)
