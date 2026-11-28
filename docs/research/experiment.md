# ExperimentAtlas: related work and design proposal

*Status: first-draft related-work review (2026-11-28). Items marked **[unverified]** were cited from memory and not re-checked against the primary source during this review. Arxiv IDs not marked were fetched or confirmed by search.*

ExperimentAtlas has one unit: **one experiment inside one paper**. Each entry records the question, the claim tested, the manipulation, the variables, baselines, data, metrics, the result, threats to validity, linked figures and tables, and a design template that carries over to other domains. A user brings a claim and gets back (a) analogous experiments from the ~17.5k-paper corpus and (b) concrete designs that could *confirm or falsify* it. This review covers four areas: methodology literature, extraction datasets and ontologies, and AI-scientist systems, followed by a proposed taxonomy, an extraction schema and a validity checklist.

---

## 1. Methodology literature and its failure modes

### 1.1 Critiques of ML practice

| Source | Core finding | What ExperimentAtlas should take from it |
|---|---|---|
| Lipton & Steinhardt, *Troubling Trends in ML Scholarship* (2018) [1] | Four trends: (i) explanation is not separated from speculation, (ii) the sources of empirical gains are not identified (the missing ablation), (iii) "mathiness", (iv) misused language, such as overloaded terms and suggestive definitions. | Mark each conclusion as **tested** or **speculated**. Flag a gain claim when no ablation isolates its source. |
| Sculley, Snoek, Rahimi, Wiltschko, *Winner's Curse?* (ICLR-W 2018) [2] | Empirical work is run as a "win" rather than as a way to gain insight. Gains often come from tuning effort and are not credited to the method. | Record the **tuning budget for the proposed method and for each baseline**. |
| Melis, Dyer, Blunsom (ICLR 2018) [3] | With equal, large-scale hyperparameter search, standard LSTMs beat newer architectures. | Name the threat **unequal-tuning confound** and check for it. |
| Henderson et al., *Deep RL that Matters* (AAAI 2018) [4] | Seeds, code base, reward scaling and network size can change conclusions. Results that use few seeds are unreliable. | Record seeds or runs, and implementation provenance. |
| Dodge et al., *Show Your Work* (EMNLP 2019) [5] | Report **expected validation performance as a function of the hyperparameter-search budget**. A model's ranking can flip with budget. | Budget-aware comparison as an evidence form. |
| Bouthillier et al., *Accounting for Variance in ML Benchmarks* (MLSys 2021) [6] | Variance comes from data sampling, initialization and hyperparameter optimization. Randomizing many sources at once gives a cheaper and better estimate of variance. | Record **which variance sources were randomized**. |
| Agarwal et al., *Statistical Precipice* (NeurIPS 2021) [7] | With few runs, point estimates mislead. Use stratified-bootstrap CIs, IQM, performance profiles and probability of improvement. | List the aggregation statistic and the uncertainty type. |
| Liao, Taori, Raji, Schmidt, *Are We Learning Yet?* (NeurIPS D&B 2021) [8] | A meta-review of 107 surveys. It gives a taxonomy of benchmark failures split into **internal validity** (improper baselines, test-set reuse) and **external validity** (benchmark gains that do not transfer). | Use this as the backbone of the threat taxonomy. |
| Kapoor & Narayanan, *Leakage and the Reproducibility Crisis* (Patterns 2023) [9]; REFORMS checklist (Sci. Adv. 2024; 32 items in 8 modules) [10] | Leakage affects ≥294 papers in 17 fields. Eight leakage types are named, e.g. preprocessing fit on train and test together, illegitimate features, and temporal leakage. | Use leakage as its own threat class, with subtypes. |
| Dehghani et al., *The Benchmark Lottery* (2021) [11] **[unverified]**; Musgrave et al., *Metric Learning Reality Check* (ECCV 2020) [12] **[unverified]** | Which benchmark is chosen decides the ranking. Under a fair protocol, claimed gains disappear. | Threats: benchmark-selection bias and protocol mismatch. |
| Herrmann et al., *Position: Why We Must Rethink Empirical Research in ML* (ICML 2024) [13] | Most ML work is written as **confirmatory** but is really **exploratory**. The paper names insight-oriented exploratory research, method-developing exploratory research, neutral method comparisons, and replication or meta-studies. It warns that adding significance tests to biased designs does not make them rigorous, and that operationalization is often unclear. | Add a **study-mode** field: exploratory, confirmatory, or neutral comparison. |
| Vranješ & Niggemann (2024) [14] | A process model: hypothesis, then design, then execution, then statistical analysis. Hypotheses must be clear, specific and refutable. | Gives the *plan* skeleton for designs generated for a user. |
| Sadeqi Azer et al., *Not All Claims are Created Equal* (ACL 2020) [15] | Fix the target hypothesis before choosing the assessment method, whether a p-value or a Bayesian approach. Misuse is common across 439 ACL papers. | The claim type determines the right test. |
| Meyes et al., *Ablation Studies in ANNs* (2019) [16] **[unverified]** | Ablation is taken from neuroscience lesion studies. Removing a component measures how necessary it is. | Ablation is a manipulation, not a claim. |

### 1.2 Reproducibility checklists

The **NeurIPS Paper Checklist** [17] has 16 items. The ones that matter for experiments are: 1 Claims (contributions stated with their assumptions and limits), 2 Limitations, 4 Reproducibility, 5 Open access, 6 Experimental setting (key details belong in the main text), 7 Statistical significance (error bars, CIs or tests "at least for the experiments that support the main claims") and 8 Compute. The checklist began with Pineau et al.'s reproducibility program (JMLR 2021) [18] **[unverified details]**. ICML and JMLR have similar requirements. REFORMS [10] is the cross-discipline version.

**Implication.** For each 2026 paper, the checklist answers are a cheap, author-stated signal (for example, "error bars: Yes") that can be stored as source-stated fields. Authors fill in the checklist themselves, so it is evidence of a claim, not verification.

### 1.3 Typologies to borrow

No canonical *typology of ML experiments* exists. The closest pieces:

- **Study mode** [13]: exploratory (insight or method development), confirmatory, neutral comparison, replication.
- **Result role** in leaderboards, from MetaLead (EACL 2026) [19]: each result is a *baseline*, the *proposed method*, or a *variation of the proposed method*.
- **Planning stages** in SCOPE (2026) [20]: experiments are *main*, *ablation* or *analysis*, and configuration is the datasets, baselines and metrics.
- **Validity** from Shadish, Cook & Campbell [21]: statistical-conclusion, internal, construct and external validity. [8] uses internal and external validity for ML. Construct validity (does the metric measure the concept?) is what [13] calls the operationalization problem.

---

## 2. Datasets, extraction systems and ontologies

### 2.1 Result and leaderboard extraction

- **TDMS-IE** (Hou et al., ACL 2019) [22] **[unverified ID]**: extracts (Task, Dataset, Metric, Score) tuples for leaderboards.
- **AxCell** (Kardas et al., EMNLP 2020) [23]: segments and classifies results tables from LaTeX source and links them to Papers with Code leaderboards. Its pipeline (table type, then cell role, then linking) is a good model for ExperimentAtlas's figure/table links.
- **SciREX** (Jain et al., ACL 2020) [24]: document-level N-ary relations between Dataset, Metric, Task and Method across a full paper. It shows that the facts of one experiment are spread across sections.
- **SciLead** (Şahinuç et al., EMNLP 2024) [25]: an LLM pipeline that extracts TDMR (task, dataset, metric, result), normalizes it and builds leaderboards. Its finding that community leaderboards are incomplete or wrong argues for curated gold sets.
- **MetaLead** (EACL 2026) [19]: human-curated leaderboards that record each result's experiment type and separate training from test datasets.
- **Papers with Code** was shut down in July 2025, and its domain redirects to Hugging Face Trending Papers, which has no SOTA tables. Community snapshots of its evaluation tables survive on HF [26]. This leaves a gap that ExperimentAtlas can partly fill.

**Gap.** All of these treat an experiment as a *row of numbers* (task, dataset, metric, score). None records *why* the experiment was run, what was manipulated, or what would have refuted the claim. ExperimentAtlas's contribution is that layer of intent and design.

### 2.2 Claim and evidence linking

- **SciFact** (Wadden et al., EMNLP 2020) [27] **[unverified ID]**: verifies claims against abstracts.
- **SciGen** (Moosavi et al., NeurIPS D&B 2021) [28] **[unverified ID]**: reasoning-aware text generation from scientific tables. Its analysis shows models hallucinate when describing results, which supports keeping numbers source-anchored.
- **CLAIM-BENCH** (2025) [29]: claim and evidence extraction on 100 2024 AI/ML papers. Reported F1 is about 0.5 for claims and about 0.4 for evidence (from the search snippet), so LLM extraction of claim-evidence links is far from solved.
- **SciClaimEval** (2026) [30]: 1,664 claims from 180 papers in ML, NLP and medicine, with figures and tables as evidence. Refuted claims are built by **editing the evidence, not the claim**. Figure-based verification is hardest. This is a useful recipe for testing whether ExperimentAtlas's links are correct.

### 2.3 Experiment-level benchmarks (closest to ExperimentAtlas)

- **EXP-Bench** (ICLR 2026) [31]: a semi-automated pipeline that extracts 461 research tasks (about 12.7k gradable subtasks) from 51 NeurIPS/ICLR 2024 papers and their code. Each task is a research question, a hypothesis, a design, an implementation and an expected conclusion. Agents score 20-35% on individual aspects but 0.5% on complete experiments. *Its task schema is the nearest existing analogue to an ExperimentAtlas record.*
- **SCOPE** (2026) [20]: 300 design tasks from ICML, NeurIPS and ICLR papers in 19 domains. Designs are judged on planning completeness (main, ablation and analysis experiments) and configuration (datasets, baselines, metrics). LLMs are weakest at low-level configuration, so ExperimentAtlas should return concrete baselines and metrics, not generic advice.
- **RECLAIM** (2026) [32]: reproduces claims from 100 NeurIPS 2025 papers in three tiers: Run, Retrain and Reimplement. A target result and a success criterion are fixed in advance. The most common failure (63 of 400 runs) was never checking intermediate numbers against the paper.
- **PaperBench** **[unverified]**: 23 ICML 2024 papers with hierarchical replication rubrics.

### 2.4 Ontologies

- **EXPO** (Soldatova & King, J. R. Soc. Interface 2006) [33] **[unverified details]**: a general ontology of scientific experiments (hypothesis, experimental design, independent and dependent variables, result, conclusion). It underlies the "Robot Scientist" work.
- **Exposé / ExpML** (Vanschoren & Soldatova, built on **OntoDM**) [34]: an ML experimentation ontology used in experiment databases.
- **ML Schema** (W3C Community Group, 2018) [35]: a top-level ontology of Algorithm, Implementation, Run, Data, Task, Model and EvaluationMeasure, mapped to Exposé, OntoDM and DMOP. OpenML uses it to export runs as RDF.

**Takeaway.** EXPO supplies the *scientific* fields (hypothesis, variables, conclusion). ML Schema supplies the *computational* fields (run, implementation, measure). Neither covers claim types or threats to validity. ExperimentAtlas should **map** onto both, for example with `expo:` and `mls:` crosswalk IDs in exports, rather than invent a parallel ontology.

---

## 3. AI-scientist systems and how they represent experiments

| System | How it represents an experiment | Notes |
|---|---|---|
| **AI Scientist v1** (Sakana, 2024) **[unverified]** | A human-written code template plus an LLM-proposed idea (JSON with name, title, experiment, interestingness and other fields). | Templates limit which designs are possible. |
| **AI Scientist v2** (2025) [36] | A tree search over **nodes**. Each node holds a plan summary, script, error trace, runtime, metrics, LLM feedback, plot script, figure paths, VLM feedback on figures, and a buggy/non-buggy status. Four stages: preliminary investigation, hyperparameter tuning, research-agenda execution, ablation studies. Node types: hyperparameter, ablation, **replication** (re-run with new seeds for mean and std) and **aggregation**. | Seed replication and ablation are explicit node types, an example to follow. |
| **Agent Laboratory** (Findings EMNLP 2025) [37] | Three phases: literature review, experimentation, report writing. The research plan is free text. `mle-solver` refines code by score, and `paper-solver` writes the report. | The plan has no structured schema. |
| **MLAgentBench** (Huang et al., 2023/24) [38] | 13 tasks. Each task gives a starter repo, a problem description and a target metric. The agent acts through file and exec actions. | An experiment is reduced to "improve metric X". |
| **POPPER** (ICML 2025) [39] | Two agents. One designs **falsification experiments** for a hypothesis and the other runs them. Each experiment yields a p-value, which is turned into an e-value and combined sequentially with Type-I error control. | The closest system to the "validate or falsify a claim" use case, and a model for how to aggregate evidence. |
| **EXP-Bench / Curie** [31] | Question, hypothesis, setup, expected outcome, with grading against the paper. | See §2.3. |

**Pattern.** Current agents represent an experiment as *code plus metric*. Only POPPER and EXP-Bench make the hypothesis, and what would count as refuting it, explicit. Coding agents using ExperimentAtlas would gain most from records that state **what result would refute the claim** and **which controls are required**.

---

## 4. Synthesis

### 4.1 Critique of the seed list

The seed list (data efficiency, compute efficiency, scaling, generalization, robustness, component ablation, mechanistic understanding, controlled synthetic, sensitivity analysis, quality-compute trade-off) mixes **at least three axes**:

- **What is claimed**: data efficiency, compute efficiency, generalization, robustness, mechanistic understanding.
- **What is manipulated**: component ablation, sensitivity analysis (sweeping a hyperparameter), scaling (sweeping size, data or compute).
- **Where the evidence comes from or what form it takes**: controlled synthetic (the data regime), quality-compute trade-off (a Pareto frontier).

"Scaling" can be either a claim (a power law holds) or a manipulation (sweeping N). The list also leaves out the most common claim in ML papers, **comparative superiority** ("ours beats X"). It also misses negative or replication claims, calibration, fairness, safety, and human evaluation.

### 4.2 Proposed taxonomy: multi-label, five orthogonal facets

Each experiment gets **one or more labels per facet**. Facets A-C are the core. D and E are qualifiers.

**A. Claim type: what is being asserted**
- A1 Comparative performance: superiority, parity ("matches at lower cost"), or non-inferiority.
- A2 Efficiency: A2.1 data or sample efficiency, A2.2 compute, memory or latency, A2.3 parameter efficiency. A Pareto or trade-off claim is A1 combined with A2.
- A3 Scaling behavior: a functional form (power law, emergence, saturation) or extrapolation.
- A4 Generalization: A4.1 in-distribution held-out data, A4.2 OOD or domain shift, A4.3 compositional or length generalization, A4.4 cross-task or zero-shot transfer.
- A5 Robustness and reliability: A5.1 noise or corruption, A5.2 adversarial, A5.3 calibration and uncertainty, A5.4 stability across seeds or hyperparameters.
- A6 Attribution or necessity: component X causes the gain.
- A7 Mechanism or explanation: how or why something works, through representations, circuits or dynamics.
- A8 Theory validation: an empirical check of a theorem's prediction or assumption.
- A9 Phenomenon discovery or characterization: an exploratory "we observe X".
- A10 Negative, failure or limitation claim: X does not help, or X breaks under Y.
- A11 Replication or re-evaluation of prior claims.
- A12 Societal and safety properties: fairness, privacy, safety, alignment.
- A13 Human-perceived quality: user studies, human preference.

**B. Design manipulation: what is varied (independent variable)**
- B1 Method swap against baselines (head-to-head).
- B2 Ablation or removal (leave-one-out, add-one-in, replacement with a null or random version).
- B3 Hyperparameter or design-choice sweep (sensitivity).
- B4 Scale sweep (parameters, data, compute, inference steps).
- B5 Data or distribution manipulation (shift, corruption, subsampling, label noise, contamination control).
- B6 Controlled synthetic or toy setting with known ground truth.
- B7 Intervention on internals (probing, patching, freezing, lesioning).
- B8 Budget-matched or constraint-matched comparison (FLOPs, wall-clock, tuning trials).
- B9 Observational or correlational analysis, with no manipulation.
- B10 Human or expert evaluation protocol.

**C. Evidence form: how the result is shown**
Results table, curve against a swept variable, scaling-law fit, Pareto frontier, distribution or variance plot, statistical test or CI, qualitative examples, visualization (attention, embedding, attribution), case study, theoretical-vs-empirical overlay.

**D. Study mode** [13]: exploratory-insight, exploratory-method-development, confirmatory (pre-specified), neutral comparison, replication.

**E. Experiment role in the paper** [19, 20]: main result, ablation, analysis, sanity check or diagnostic, appendix-only.

Seed items map as follows: data efficiency → A2.1. Compute efficiency → A2.2. Scaling → A3 and/or B4. Generalization → A4. Robustness → A5. Component ablation → B2, usually with A6. Mechanistic understanding → A7, often with B7. Controlled synthetic → B6. Sensitivity analysis → B3, often with A5.4. Quality-compute trade-off → A1+A2 with evidence C = Pareto frontier.

**The reusable template** is the triple (A, B, C) plus the required controls. For example, "A6 × B2 × table" becomes "remove X while holding parameter count and tuning budget fixed, report the mean ± CI over ≥3 seeds, and include a random-replacement control." This triple is how a user's claim is matched to analogous experiments in other domains.

### 4.3 Per-experiment extraction schema (draft)

Every field is an object `{value, provenance, support}`:
- `provenance` ∈ {`stated`, `derived`, `inferred`, `absent`}.
  - `stated`: the text is quoted or near-verbatim.
  - `derived`: deterministic from stated content, e.g. computing a delta from two table cells.
  - `inferred`: the model's interpretation.
  - `absent`: the paper does not say.
- `support` is a list of anchors (`section`, `page`, `figure/table id`, `char span`, `quote` ≤ 40 words).

```yaml
experiment_id: <paper_id>#E<k>
paper: {venue, year, openreview_id, arxiv_id}
role: main | ablation | analysis | sanity | appendix          # facet E
study_mode: exploratory_insight | exploratory_method | confirmatory | neutral | replication  # usually inferred
question: "..."                     # stated, or inferred and flagged
claim:
  text: "..."                       # must be stated (verbatim); never inferred
  type: [A1, A6]                    # facet A, inferred labels
  scope_qualifiers: "on ImageNet, ViT-B"   # stated
  predicted_direction: increase | decrease | equal | functional_form
manipulation: {type: [B2], independent_vars: [{name, levels}]}
dependent_vars: [{metric, direction(higher_better), split}]
controlled_vars: [{name, how_controlled}]   # "absent" is common and informative
baselines: [{name, source(reimplemented|reported|official), tuned_equally: yes|no|absent}]
datasets: [{name, version, split, train/test role}]
replication: {n_seeds, variance_sources_randomized, uncertainty: std|se|ci|none}
compute: {hardware, budget, matched_across_arms: yes|no|absent}
results: [{arm, metric, value, unc, table_cell_ref}]   # stated numbers only
conclusion: {author_text (stated), supports_claim: yes|partial|no (inferred)}
evidence_form: [C...]
limitations_stated: [...]
threats_identified: [{threat_id, rationale, provenance: inferred}]   # Atlas's critique, kept separate
figures_tables: [Fig 3, Tab 2]
template: {A, B, C, required_controls, falsifier: "result that would refute claim"}
extraction: {model, prompt_version, date, confidence, human_verified: bool}
```

**Anti-fabrication rules.**
1. Numbers in `results` must resolve to a table cell or a quoted sentence. If not, the field is `absent`.
2. `absent` is a first-class value. Never impute seeds, budgets or splits. A missing control shows up as a *threat*, not as a filled-in default.
3. Author voice is kept apart from Atlas voice. `claim.text`, `conclusion.author_text` and `limitations_stated` are stated-only. `threats_identified`, `supports_claim` and the facet labels are inferred and shown in a visually separate "Atlas assessment" block.
4. Run a self-consistency check: a second pass verifies every `support.quote` against the source text by string match and drops any field it cannot match.
5. Calibrate on a gold set. Hand-annotate about 200 experiments and adapt SciClaimEval-style perturbations [30] (edit a table, check that the link breaks) to measure link precision.

### 4.4 Standard validity checks for a generated experimental plan

Grouped by Shadish-Cook-Campbell validity type, each with its ML source:

**Statistical-conclusion validity**
1. Multiple seeds, with the variance sources stated [4, 6]. Report CIs or bootstrap intervals, and IQM or probability of improvement when there are few runs [7].
2. Choose the test to fit the claim type: superiority vs. non-inferiority, paired tests, multiple-comparison correction [15].
3. Fix the primary metric and the success or falsification threshold in advance (as RECLAIM does with success criteria [32] and POPPER with falsification tests [39]).

**Internal validity**
4. Equal tuning budget for all arms, reported. Budget-performance curves where possible [3, 5].
5. Strong, current baselines, ideally the authors' official code and settings [8, 12].
6. Matched compute, parameters and data when an efficiency or architecture claim is made.
7. Ablations that isolate each claimed component, including a "replace with random/null" control and not only removal [1, 16].
8. A leakage audit: preprocessing fit on train only, temporal splits, duplicate or contamination checks, illegitimate features [9].
9. No test-set reuse for model selection. Keep a held-out validation split [8].

**Construct validity**
10. The metric operationalizes the claimed concept, e.g. "reasoning" or "robustness". Justify the proxy or add a second metric [13].
11. Sanity checks: the trivial baseline, the oracle or upper bound, and whether the effect disappears on a control task.

**External validity**
12. Several datasets or domains, chosen *before* seeing results, which guards against the benchmark lottery [11].
13. Sweep the scale or setting so the claim is not shown at a single point. State the scope qualifier explicitly.
14. Report negative results and limitations, as checklist items 1 and 2 require [17].

**Reporting and reproducibility**
15. Release code, configs and seeds. Report compute (checklist items 4-8 [17]). Label the study mode as exploratory or confirmatory, and do not run post hoc significance tests on exploratory method development [13].

---

## References

1. Lipton & Steinhardt, *Troubling Trends in Machine Learning Scholarship*, 2018. https://arxiv.org/abs/1807.03341
2. Sculley, Snoek, Rahimi, Wiltschko, *Winner's Curse? On Pace, Progress, and Empirical Rigor*, ICLR Workshop 2018. https://openreview.net/forum?id=rJWF0Fywf **[URL unverified]**
3. Melis, Dyer, Blunsom, *On the State of the Art of Evaluation in Neural Language Models*, ICLR 2018. https://arxiv.org/abs/1707.05589 **[unverified]**
4. Henderson et al., *Deep Reinforcement Learning that Matters*, AAAI 2018. https://arxiv.org/abs/1709.06560 **[unverified]**
5. Dodge et al., *Show Your Work: Improved Reporting of Experimental Results*, EMNLP 2019. https://arxiv.org/abs/1909.03004 **[unverified]**
6. Bouthillier et al., *Accounting for Variance in Machine Learning Benchmarks*, MLSys 2021. https://arxiv.org/abs/2103.03098 **[unverified]**
7. Agarwal et al., *Deep RL at the Edge of the Statistical Precipice*, NeurIPS 2021. https://arxiv.org/abs/2108.13264 **[unverified]**
8. Liao, Taori, Raji, Schmidt, *Are We Learning Yet? A Meta Review of Evaluation Failures Across ML*, NeurIPS D&B 2021. https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/757b505cfd34c64c85ca5b5690ee5293-Abstract-round2.html
9. Kapoor & Narayanan, *Leakage and the Reproducibility Crisis in ML-based Science*, Patterns 2023. https://arxiv.org/abs/2207.07048 ; https://reproducible.cs.princeton.edu/
10. Kapoor et al., *REFORMS: Consensus-based Recommendations for ML-based Science*, Science Advances 2024. https://reforms.cs.princeton.edu/
11. Dehghani et al., *The Benchmark Lottery*, 2021. https://arxiv.org/abs/2107.07002 **[unverified]**
12. Musgrave, Belongie, Lim, *A Metric Learning Reality Check*, ECCV 2020. https://arxiv.org/abs/2003.08505 **[unverified]**
13. Herrmann et al., *Position: Why We Must Rethink Empirical Research in Machine Learning*, ICML 2024. https://proceedings.mlr.press/v235/herrmann24b.html ; https://arxiv.org/abs/2405.02200
14. Vranješ & Niggemann, *Design Principles for Falsifiable, Replicable and Reproducible Empirical ML Research*, 2024. https://arxiv.org/abs/2405.18077
15. Sadeqi Azer, Khashabi, Sabharwal, Roth, *Not All Claims are Created Equal*, ACL 2020. https://arxiv.org/abs/1911.03850
16. Meyes et al., *Ablation Studies in Artificial Neural Networks*, 2019. https://arxiv.org/abs/1901.08644 **[unverified]**
17. NeurIPS Paper Checklist Guidelines. https://neurips.cc/public/guides/PaperChecklist
18. Pineau et al., *Improving Reproducibility in Machine Learning Research*, JMLR 2021. https://arxiv.org/abs/2003.12206 **[unverified]**
19. Timmer, Bölücü, Wan, *MetaLead: A Human-Curated Leaderboard Dataset*, EACL 2026. https://arxiv.org/abs/2601.22420
20. Liu et al., *Can LLM Design High-Quality Experiments? (SCOPE)*, 2026. https://arxiv.org/abs/2608.03501
21. Shadish, Cook, Campbell, *Experimental and Quasi-Experimental Designs for Generalized Causal Inference*, 2002 (book). **[unverified]**
22. Hou et al., *Identification of Tasks, Datasets, Evaluation Metrics, and Numeric Scores for Scientific Leaderboards Construction*, ACL 2019. https://aclanthology.org/P19-1513/ **[unverified]**
23. Kardas et al., *AxCell: Automatic Extraction of Results from ML Papers*, EMNLP 2020. https://arxiv.org/abs/2004.14356 **[unverified]**
24. Jain et al., *SciREX: A Challenge Dataset for Document-Level Information Extraction*, ACL 2020. https://arxiv.org/abs/2005.00512 **[unverified]**
25. Şahinuç et al., *Efficient Performance Tracking: LLMs for Automated Construction of Scientific Leaderboards (SciLead)*, EMNLP 2024. https://aclanthology.org/2024.emnlp-main.453/
26. Papers with Code shutdown and successors. https://codesota.com/papers-with-code ; https://hyper.ai/en/news/42900
27. Wadden et al., *Fact or Fiction: Verifying Scientific Claims (SciFact)*, EMNLP 2020. https://arxiv.org/abs/2004.14974 **[unverified]**
28. Moosavi et al., *SciGen: A Dataset for Reasoning-Aware Text Generation from Scientific Tables*, NeurIPS D&B 2021. https://arxiv.org/abs/2104.08296 **[unverified]**
29. *Can AI Validate Science? Benchmarking LLMs for Scientific Claim→Evidence Reasoning (CLAIM-BENCH)*, 2025. https://arxiv.org/abs/2506.08235 (figures from search snippet only)
30. Ho et al., *SciClaimEval: Cross-modal Claim Verification in Scientific Papers*, 2026. https://arxiv.org/abs/2602.07621
31. *EXP-Bench: Can AI Conduct AI Research Experiments?*, ICLR 2026. https://arxiv.org/abs/2505.24785 ; code: https://github.com/Just-Curieous/Curie
32. Salunkhe et al., *RECLAIM: Can Agents Reproduce the Claims of ML Papers?*, 2026. https://arxiv.org/abs/2609.28850
33. Soldatova & King, *An Ontology of Scientific Experiments (EXPO)*, J. R. Soc. Interface 2006. https://doi.org/10.1098/rsif.2006.0134 **[unverified]**
34. Vanschoren & Soldatova, *Exposé: An Ontology for Data Mining Experiments*, 2010 (builds on OntoDM). **[unverified details]**
35. Publio et al., *ML-Schema: Exposing the Semantics of Machine Learning with Schemas and Ontologies*, 2018. https://arxiv.org/abs/1807.05351 ; https://ml-schema.github.io/documentation/ML%20Schema.html
36. Yamada et al., *The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search*, 2025. https://arxiv.org/abs/2504.08066 ; https://github.com/SakanaAI/AI-Scientist-v2
37. Schmidgall et al., *Agent Laboratory: Using LLM Agents as Research Assistants*, Findings EMNLP 2025. https://arxiv.org/abs/2501.04227
38. Huang, Vora, Liang, Leskovec, *MLAgentBench: Evaluating Language Agents on ML Experimentation*. https://arxiv.org/abs/2310.03302
39. Huang et al., *Automated Hypothesis Validation with Agentic Sequential Falsifications (POPPER)*, ICML 2025. https://arxiv.org/abs/2502.09858
