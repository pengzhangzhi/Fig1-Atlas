# Evaluation: extraction faithfulness, label stability and retrieval

This report covers the three new atlases (StoryAtlas, ExperimentAtlas, PlotAtlas), which share one extraction
pipeline. It was produced on the preview sample: 100 papers (60 used to induce the taxonomy, 40 held out), with
the scripts in [Fig1-Atlas/pipeline](https://github.com/pengzhangzhi/Fig1-Atlas/tree/main/pipeline) (`e1_stability.py`, `e2_retrieval.py`).
Annotation model: Claude Sonnet via `claude -p`; cross-model check: Claude Opus.

## 1. Faithfulness: are quotes really the paper's words?

Every field ending in `_quote` is checked by string match against the parsed paper text (whitespace and case
normalized; small edits tolerated at the 6-word-shingle level). Unverified quotes are dropped at publish time, so
the sites never show them as the authors' words.

| Stage | Quotes | Verified verbatim |
|---|---:|---:|
| Story, claims, experiments (`k1_read`) | 1,442 | 98.7% |
| Plots (`k2_plots`; quotes come from captions and citing sentences) | 1,016 | 83.7% |

Interpretive fields (archetypes, templates, threats, falsifiers, critiques) are labelled as the atlas's own on the
sites and in the agent output. The extraction prompt forbids filling in missing details ("not stated" is a valid
value).

**Numbers.** Of the 2,888 numbers in extracted experiment results, 90.1% appear verbatim in the parsed paper text.
For a random 100 of the remaining 287, 96 appear in the full PDF text (mostly table cells the parser cut short), so
an estimated 99.6% of reported numbers come from the paper. The rest may be rounding or derived values (e.g. a
difference of two table cells); a few could be errors.

## 2. Label stability

Agreement between two independent annotations of the same 15 papers: mean Jaccard of the label sets, with the
share of items whose primary (first) label agrees in parentheses. "Repeat" reruns the same model; "Opus" is a
different, stronger model, so it is the more honest test. Experiments and panels are aligned across runs by the
figures/tables they cite and their names (97 experiments, 107 panels aligned).

| Axis | v0 repeat | v1 repeat | v1 vs Opus |
|---|---|---|---|
| Story archetype (v0: arc) | 0.53 (67%) | 0.78 (87%) | 0.80 (100%) |
| Story niche | 0.67 (67%) | 0.87 (93%) | 0.72 (80%) |
| Story contribution | 0.77 (100%) | 0.77 (100%) | 0.72 (87%) |
| Story evidence | 0.85 (100%) | 0.85 (100%) | 0.72 (80%) |
| Story insight origin | 0.82 (87%) | 0.87 (87%) | 0.60 (53%) |
| Experiment claim type | 0.82 (93%) | 0.87 (91%) | 0.79 (80%) |
| Experiment design (v0: manipulation) | 0.90 (90%) | 0.76 (81%) | 0.63 (70%) |
| Experiment controls | – | 0.84 (88%) | 0.73 (68%) |
| Experiment evidence form | 0.93 (98%) | 0.96 (99%) | 0.89 (93%) |
| Experiment role | 0.90 (90%) | 0.96 (96%) | 0.90 (90%) |

| Plot axis (v1) | Repeat | vs Opus |
|---|---|---|
| Is a data figure | 1.00 (100%) | 0.98 (100%) |
| Same panel split | 0.91 (100%) | 0.91 (100%) |
| Message (33 labels) | 0.71 (73%) | 0.70 (65%) |
| Message family (10) | 0.85 (90%) | 0.81 (80%) |
| Chart form | 0.97 (96%) | 0.90 (99%) |
| Devices | 0.81 (78%) | 0.57 (66%) |

What this says:
- Replacing the literature's narrative arcs (v0) with data-induced story archetypes (v1) raised agreement on a
  paper's pitch from 0.53 to 0.78, and Sonnet and Opus picked the same primary archetype for all 15 papers.
- Fine-grained labels are less stable than their families: plot messages agree 0.70, their families 0.81-0.85.
  The sites let you filter by family when a fine label is ambiguous.
- **Insight origin is unreliable across models** (primary label agrees 53%); treat it as a weak hint.
- Self-agreement is an upper bound. No human-labelled gold set exists yet; building one (about 100 papers, two
  annotators) is the next step before claiming accuracy.

## 3. Retrieval: structural analogy, not just topic

36 realistic queries (12 per atlas, written as a researcher would describe their own work, deliberately in topics
the sample barely covers). Four rankers; the top 5 of each were pooled and judged blind by an LLM on two separate
0-2 scales: **useful** (would it serve as a template for what was asked) and **topical** (same research topic).
"hybrid" is what the sites and skills run: keyword relevance plus an embedding of the abstracted, topic-free fields.

StoryAtlas

| Ranker | useful@5 | nDCG@5 | topical@5 |
|---|---:|---:|---:|
| bm25-all | 0.68 | 0.59 | 0.32 |
| emb-all | 0.62 | 0.49 | 0.48 |
| emb-struct | 0.72 | 0.56 | 0.50 |
| hybrid | 0.83 | 0.71 | 0.45 |

ExperimentAtlas

| Ranker | useful@5 | nDCG@5 | topical@5 |
|---|---:|---:|---:|
| bm25-all | 0.80 | 0.59 | 0.53 |
| emb-all | 0.75 | 0.57 | 0.57 |
| emb-struct | 0.90 | 0.58 | 0.52 |
| hybrid | 1.03 | 0.69 | 0.65 |

PlotAtlas

| Ranker | useful@5 | nDCG@5 | topical@5 |
|---|---:|---:|---:|
| bm25-all | 0.78 | 0.49 | 0.47 |
| emb-all | 0.60 | 0.39 | 0.33 |
| emb-struct | 0.62 | 0.36 | 0.32 |
| hybrid | 0.88 | 0.54 | 0.53 |

The hybrid ranker is the most useful on all three atlases, and it reaches that with results that are often from a
different topic (topical well below useful), which is the point: analogies across fields. Embedding the full text
including titles (emb-all) is the worst, because it matches topic. Absolute usefulness is moderate (around 1 on a
0-2 scale) because 100 papers rarely contain a close analogue; it should rise with the full corpus. The judge is an
LLM and the queries were written by the project, so treat these as relative comparisons. Judge cost: $1.84.

## 4. Taxonomy development

1. **v0 from the literature** (reports in each repo's `docs/research.md`): CARS moves, Shaw's paper types and Davis's
   "that's interesting" for stories; Herrmann et al., validity types and reproducibility checklists for experiments;
   Elzer and Carberry's intended messages, the FT Visual Vocabulary and Amar's tasks for plots.
2. **Extraction on 60 papers with v0 plus a free-text name** for each item ("story in your own words", ...).
3. **Discovery** (`t1_discover.py`): a strong model induced categories from the free-text names and labels, with
   decision rules, and reported overlapping, missing and over-assigned v0 labels (e.g. "challenged belief" was
   filled for 56 of 60 papers; seems-necessary and trade-off-resolved were co-assigned on 10).
4. **v1** merged and split labels accordingly, added axes the data asked for (experiment controls; plot modifiers),
   and was run on the 60 papers plus **40 held-out papers**. On v1, one paper needed an "other" archetype.
5. **Open issues** listed in each `references/taxonomy.md`: the diagnose-then-fix archetype is large (25%) and may
   need splitting by what is diagnosed; experiment patterns are fine-grained (33) and agree less across models than
   their families; panel splitting is by the model, not by pixel boxes.

## 5. Cost and scaling

| | Per paper | 100-paper preview | Full corpus (~18,400 papers with PDFs) |
|---|---:|---:|---:|
| Story + experiments (Sonnet) | $0.25 | $25 | ~$4,700 |
| Plots (Sonnet) | $0.18 | $18 | ~$3,300 |
| Both with Opus | $0.89 | $89 | ~$16,400 |
| Parsing and cropping (CPU) | – | 5 min on 12 cores | ~15 h on 12 cores |

Image hosting: about 0.18 MB per figure crop; roughly 10 GB on Hugging Face for the openly licensed papers.
