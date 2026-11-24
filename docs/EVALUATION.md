# Evaluation: Forge orchestra v0 vs. a single Opus agent

**Verdict: the orchestra lost. It was archived (REJECT) under the kill criterion written before the code existed.**

| | |
|---|---|
| Pre-registration | [`ONKAYIT-orkestra-v0.md`](../ONKAYIT-orkestra-v0.md), commit `a703178` (2026-10-25 14:40 +03:00) |
| First orchestra code | commit `1809854` (2026-10-25 15:45 +03:00), about an hour after the pre-registration |
| Gold-set hash committed | commit `b3c1fd7` (2026-10-25 17:39 +03:00), before any experiment run |
| Prediction written before results | [`TAHMIN-orkestra-v0.md`](../TAHMIN-orkestra-v0.md) |
| Generated result report | [`orkestra/deney-sonuc/RAPOR.md`](../orkestra/deney-sonuc/RAPOR.md), commit `bce6e65` (2026-10-26) |
| Re-scored for this document | 2026-11-24. Byte-identical to the committed report (see [Reproduce](#reproduce)) |

The internal project documents are in Turkish. This file is the English summary. Every number here comes from
committed run artifacts or from re-running the committed scorer on them. Nothing was re-estimated by hand.

---

## 1. Question

Forge splits a literature search between an expensive "chef" model (Claude Opus: plans, sets the stopping
criterion, makes the final ranking) and cheap "players" (Python collectors for arXiv, Crossref, DBLP and
OpenCitations, plus Claude Haiku readers and web workers). The hypothesis was:

> On a broad literature-search task, the orchestra finds more of the works that matter than one Opus agent,
> for less money and without fabricating sources.

## 2. Task and gold set

- **Gold source:** 30 survey or SoK papers posted to arXiv between 2025-07 and 2026-10. They cover 10 computer
  engineering areas with 3 surveys each: hardware, security, HCI/visualization, ML/vision, NLP, robotics,
  systems/networking, theory/algorithms, databases, and software engineering/PL.
- **Selection:** candidates came from the arXiv API (title contains survey / SoK / systematic review). Each
  area's pool was shuffled with a fixed seed (`20261025`), and the first 3 surveys with at least 60 references
  were taken. Three manual swaps were logged with reasons: a topic collision, an off-area paper, and a
  monograph.
- **Gold items:** the survey's references that were published before the cutoff and resolve to an arXiv ID or
  DOI. That gives **4,089 gold references** in total, between 46 and 305 per survey (median 132).
- **Cutoff:** one month before the survey's first version. Systems may only list works published before the
  cutoff, so they cannot simply return the survey or copy its bibliography.
- **Quality control:** a 3 × 10 spot check found 2 errors out of 30 (truncated DOIs that resolved to a
  proceedings volume). A systematic filter then removed 26 records (0.6%).
- **Blinding:** the gold set lives in a separate repository (`forge-altin`). Only its SHA-256
  (`3aa01a9f…8681`) and summary counts were committed here. The session that wrote and ran the orchestra never
  read it.
- **Question text:** each survey's topic was rewritten as a research question in Turkish. Both systems received
  the same text.

## 3. Systems compared

| ID | System | Role in the decision |
|---|---|---|
| **B** | Forge orchestra v0. Opus plans and does the final ranking. Code collectors pull arXiv, Crossref, DBLP and OpenCitations, and keyless OpenAlex where available. Haiku web workers and 4 parallel Haiku readers score the candidates. Ranking combines BM25, embeddings, reader scores and citation signals. Opus sees only 80 compact cards. | System under test |
| **A1** | A single Opus agent with mandatory web search. It is told to verify every title, date and identifier online, and gets the same "what a careful expert survey would cite" framing as B. Prompt: `PROMPT_A1` in [`orkestra/deney/taban.py`](../orkestra/deney/taban.py). | **Primary baseline** (the decision is B − A1) |
| **A0** | A single Opus agent with the original pre-registered prompt, where web search is optional. In practice it answered almost entirely from memory (about 1 search per question). | Descriptive only |

A1 was added through a dated amendment to the pre-registration, before any experiment run and before anyone
saw the gold set. On a smoke question, the original prompt made Opus answer from memory with zero searches.
That would have turned the cost comparison into "orchestra vs. a model that does no research". A0 was kept
unchanged and reported as well.

Every system outputs a ranked list of **30 works** with identifiers.

## 4. Metrics: what "recall@30" means here

**recall@30 = |gold ∩ top-30 list| / min(30, |gold|)**, as written in the pre-registration. Matching is done in
this order: arXiv ID, then DOI, then normalized title with similarity ≥ 0.90. A title match is rejected when
numbers or Roman numerals conflict ("Part I" ≠ "Part II"). Each gold item and each list item can match at most
once. Implementation: [`orkestra/orkestra/deney/puanla.py`](../orkestra/orkestra/deney/puanla.py), with 17 unit
tests.

Every survey has at least 46 gold references, so the denominator is always **30**. The metric is therefore the
**share of the system's 30 picks that appear in the expert survey's bibliography**. It is a hit rate (in IR
terms, precision@30 against the gold set). It is not the share of the whole bibliography that was recovered.

This explains the apparent contradiction between "36.7 / 45.7" and "4,089 gold references". Both are true, and
they measure different things:

| System | Gold hits (out of 30 × 30 = 900 picks) | recall@30 as pre-registered (hits / 30, averaged) | Share of the full bibliography recovered (hits / \|gold\|, averaged) |
|---|---|---|---|
| B (orchestra) | 330 | **36.7%** | 9.5% |
| A1 (Opus + web) | 411 | **45.7%** | 11.9% |
| A0 (Opus, memory) | 367 | **40.8%** | 10.8% |

The pre-registered values, **36.7 vs. 45.7**, are correct. When quoted, they should be described as "share of
30 picks found in the survey's bibliography", not as recall over the 4,089 references. The last column is
included only to show that scale. It was not a pre-registered metric.

Secondary metrics from the pre-registration:

- **Cost:** theoretical API list-price dollars per question, taken from the Claude CLI's `total_cost_usd` and
  logged per call.
- **Context:** estimated token size of the final summary returned to the chef, computed as ceil(characters / 3).
- **Faithfulness:** 30 random (work, justification) claims from B, audited against the source by a different
  model (Claude Sonnet with web access). "Could not check" counts as unsupported.

## 5. Decision thresholds (fixed in advance; all four required to ACCEPT)

1. Mean paired difference (B − A1) **≥ +10 points** and one-sided sign test **p < 0.05**.
2. Mean cost: B **≤ 50%** of A1.
3. Faithfulness: **≥ 28/30** supported and **0** fabricated works.
4. Context: B's final summary **≤ 4,000 tokens** on average.

Kill rule: if mean(B − A1) < 0 or cost(B) > cost(A1), v0 is **archived**. One interim check was also fixed in
advance: after the first 10 questions, stop if the mean of B − A1 is ≤ −10 points.

## 6. Results (n = 30 paired questions, k = 1 run each)

| Threshold | Result | Required | Pass |
|---|---|---|---|
| Paired recall@30 difference B − A1 | **−9.0 points** (bootstrap 95% CI −13.6 to −4.4); sign test +3 / −25 / =2, one-sided p (B > A1) = 1.00 | ≥ +10 and p < 0.05 | **No** |
| Cost B / A1 | $0.639 / $0.951 = **67%** | ≤ 50% | **No** |
| Faithfulness | **30/30** supported, 0 fabricated (Wilson 95% lower bound 0.886) | ≥ 28/30 and 0 fabricated | Yes |
| Context | **3,793** tokens on average | ≤ 4,000 | Yes |

- Interim check after 10 questions: mean −6.0, so the stop was not triggered.
- **Verdict: ARCHIVE (REJECT).** mean(B − A1) < 0.
- The difference also goes the other way decisively. A1 beat B on 25 of 28 non-tied questions, with a
  one-sided sign-test p ≈ 1.4 × 10⁻⁵ for A1 > B. This test was not pre-registered and is reported only for
  completeness.

### Per-system summary

| System | Mean recall@30 | Mean cost / question | Mean wall time / question | Web searches / question |
|---|---|---|---|---|
| B | 36.7 | $0.639 | ~1,361 s (from batch logs) | n/a (6 APIs + Haiku web workers) |
| A1 | 45.7 | $0.951 | 168 s | 28.0 |
| A0 | 40.8 | $0.173 | 66 s | 1.0 |

### Descriptive comparisons (not used for the decision)

| Pair | Mean difference | Bootstrap 95% CI | W / L / T | One-sided sign-test p |
|---|---|---|---|---|
| B − A0 | −4.1 | −8.9 to +0.5 | 10 / 19 / 1 | 0.97 |
| A1 − A0 | +4.9 | +1.8 to +8.2 | 18 / 8 / 4 | 0.038 |

The bootstrap intervals were added for this write-up: 20,000 resamples of the 30 paired differences, seed 1.

### By area (3 questions per area, too few for per-area conclusions)

| Area | B | A1 | A0 | B − A1 |
|---|---|---|---|---|
| Hardware | 33.3 | 42.2 | 32.2 | −8.9 |
| Security | 54.4 | 71.1 | 60.0 | −16.7 |
| HCI / Visualization | 41.1 | 56.7 | 46.7 | −15.6 |
| ML / Vision | 48.9 | 44.4 | 50.0 | +4.4 |
| NLP | 34.4 | 41.1 | 40.0 | −6.7 |
| Robotics | 21.1 | 38.9 | 34.4 | −17.8 |
| Systems / Networking | 22.2 | 32.2 | 22.2 | −10.0 |
| Theory / Algorithms | 36.7 | 48.9 | 45.6 | −12.2 |
| Databases | 26.7 | 24.4 | 23.3 | +2.2 |
| Software Eng. / PL | 47.8 | 56.7 | 53.3 | −8.9 |

The per-question table is in [`orkestra/deney-sonuc/RAPOR.md`](../orkestra/deney-sonuc/RAPOR.md).

### Prediction vs. outcome

Before the results, the chef model predicted these mean recall@30 values: A0 ≈ 20, A1 ≈ 25, B ≈ 28, so
B − A1 ≈ +3. It gave REJECT a probability of about 80% and ARCHIVE about 30%. All three systems scored far
higher than predicted. The direction of B − A1 was also wrong.

## 7. Why the orchestra lost (interpretation, not tested)

- **Opus already knows this literature.** A0, answering from memory, beat the orchestra on average. A separate
  offline check ([`gelistirme/OLCUM-kimlik-dogrulugu.md`](../gelistirme/OLCUM-kimlik-dogrulugu.md)) found that
  575 of A0's 602 arXiv IDs (95.5%) matched the title it listed, 17 were near matches such as a renamed version,
  10 pointed to a different real paper, and **0 IDs did not exist** (98.3% excluding the 10 mismatches). So
  Forge's "every source is verified" advantage is real but small in practice.
- **A broad search does not make a better top 30.** B screened about 1,200 candidates per question, but the
  final ranking still has to choose 30. Opus choosing from 80 compressed cards did worse than Opus choosing
  directly with search.
- **Missing sources.** All 30 B runs were flagged `EKSİK` (incomplete). OpenAlex and Semantic Scholar were used
  without API keys and were unavailable, and arXiv was rate-limited on 7 questions. This may be an unfair
  handicap for B, but it is how the system ran.
- **It was not cheaper.** About 1.2M Haiku tokens per question (measured on the first 4 questions) cost more than the expected saving on Opus tokens.

## 8. Limitations

- **k = 1.** The pre-registered stability check (10 questions × 3 runs for B) was not run, so run-to-run
  variance is unknown.
- **The gold set is a single survey's bibliography.** Important work the survey did not cite counts as a miss,
  so the ceiling is below 100%. One survey is a noisy stand-in for "what matters".
- **The faithfulness auditor (Sonnet) is from the same model family** as the systems it audits.
- **Questions were in Turkish**, while the chef generates English queries. The effect of language was not
  measured.
- **Keyless run.** OpenAlex and Semantic Scholar were unavailable to B (see section 7).
- **Cost is theoretical list price.** The runs used a Claude subscription through the CLI. Token counts for the
  context metric are a character-based estimate, not a real tokenizer.
- **Builder = evaluator.** The system, the scorer and this report were all produced in AI-assisted sessions
  directed by one person. The mitigations were pre-registration, a hash-sealed gold set kept away from the
  builder session, a scorer with unit tests, and an auditor from a different model.
- [`raporlar/forge-benchmark.xlsx`](../raporlar/forge-benchmark.xlsx) is a snapshot from before the experiment
  finished. Its recall row is "?". This document and `RAPOR.md` replace it.

## 9. Reproduce

### a) Re-score the committed runs (offline, free, about 5 seconds)

This needs Python ≥ 3.11 and read access to the gold-set repository `forge-altin`, which is currently private.
Check the gold file first. Its SHA-256 must equal the value committed in the pre-registration:

```bash
shasum -a 256 ../forge-altin/altin.json
# 3aa01a9fe2b04af88eca025342bb954de4f76e0108125228e13ef50b98ec8681
```

Then re-score:

```bash
cd forge
R=orkestra/deney-sonuc
python -m analiz.rapor --b $R/B --a1 $R/A1 --a0 $R/A0 \
  --altin-dizin ../forge-altin --sadakat $R/sadakat/sadakat.json --out /tmp/RAPOR.md
diff $R/RAPOR.md /tmp/RAPOR.md && echo IDENTICAL
```

The run on 2026-11-24 (Python 3.12) printed `ARŞİV (RED)` and `IDENTICAL`.

### b) Re-run the systems (not done)

Re-running B, A1 and A0 on all 30 questions would cost about **$54** at list price: B about $19.2, A1 about
$28.5, A0 about $5.2 and the audit about $0.9. It would take roughly **12–14 hours** of wall time, mostly B at
about 23 minutes per question, because arXiv's per-IP rate limit means it should not run in parallel with other
arXiv users. It also needs the `claude` CLI. Commands: `python -m orkestra batch ...` for B and
`python -m deney.taban ...` for A0/A1 (see [`orkestra/README.md`](../orkestra/README.md)).

### c) Unit tests (179 tests, offline)

```bash
pip install -r requirements.txt
(cd orkestra && python -m pytest -q)                 # 70 passed
(cd araclar/makale-okuyucu && python -m pytest -q)   # 67 passed
(cd araclar/maliyet-sayaci && python -m pytest -q)   # 26 passed, 1 skipped
python -m pytest -q analiz -p no:cacheprovider       # 16 passed
```
