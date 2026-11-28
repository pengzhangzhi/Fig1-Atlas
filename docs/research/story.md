# StoryAtlas: related work on modeling a paper's scientific narrative

*Research note for Fig1 Atlas, 2026-11-28. Items marked **[unverified]** were cited from background knowledge and not checked against the primary source in this review.*

StoryAtlas wants one record per paper that captures *why the paper exists and how it argues*, and then retrieves papers with analogous arguments from other domains. Four bodies of work bear on this: (1) genre and rhetoric studies (moves, zones), (2) typologies of what a contribution is and what makes a question interesting, (3) corpora and extractors, and (4) tools. The short version: the move schemes are mature but describe *sentences*, not *stories*. Contribution typologies are coarse and agree well. "Narrative twist" typologies such as Davis's index of the interesting are the best fit for StoryAtlas's seed categories, but nobody has annotated them at scale. And the labels that matter most to StoryAtlas (counter-claims, key insight) are exactly the ones annotators agree on least.

---

## 1. Literature on rhetorical structure

### 1.1 Move analysis (Swales, Hyland)
Swales' **CARS (Create a Research Space)** model describes introductions as three moves (1990 version, as reproduced by the UMass Writing Center):

- **Move 1, Establishing a territory:** Claiming centrality / Making topic generalization(s) / Reviewing items of previous research.
- **Move 2, Establishing a niche:** 1A Counter-claiming / 1B Indicating a gap / 1C Question-raising / 1D Continuing a tradition.
- **Move 3, Occupying the niche:** Outlining purposes or Announcing present research / Announcing principal findings / Indicating research article structure.

Swales (2004) revised the model to be more discipline-neutral. Move 1 became "topic generalizations of increasing specificity", Move 2 was broadened, and Move 3 was made more cyclical. I could not retrieve the exact 2004 step tables. **Move 2 is StoryAtlas's "limitation of prior work" field, and its four steps already distinguish the challenge, gap, question and continuation framings.** For abstracts, Hyland's five-move model (Introduction, Purpose, Method, Product, Conclusion) is the standard **[unverified wording]**. Kording and Mensh's "Ten simple rules for structuring papers" (2017) give a practitioner version: context, gap, "here we", results, implications **[unverified]**.

### 1.2 Argumentative Zoning and CoreSC (sentence-level schemes)
- **Argumentative Zoning (AZ; Teufel 1999, Teufel and Moens 2002)** labels each sentence with one of 7 categories. The labels are AIM, TEXTUAL, OWN, BACKGROUND, CONTRAST, BASIS and OTHER (TEXTUAL and BASIS are from background knowledge). AIM corresponds to Swales' "explicit statement of research goal". **AZ-II** (Teufel, Siddharthan and Batchelor, EMNLP 2009) expands this to 15 categories. It drops TEXTUAL and adds, among others, NOV_ADV (advantage of the new claim) and FUT (limitations or future work). Its guidelines include a decision tree and 75 pairwise-disambiguation rules. Secondary sources report trained-annotator κ≈0.71 for AZ **[exact figure unverified]**.
- **CoreSC (Liakata et al. 2010/2012)** is ontology-driven, derived from the EXPO and CISP ontologies of scientific investigations. Its 11 concepts are Hypothesis, Motivation, Background, Goal, Object, Method, Experiment, Model, Observation, Result and Conclusion. They have New/Old and Advantage/Disadvantage properties plus a conceptID layer that links mentions of the same method. The full guidelines run to 45 pages. The corpus covers 265 chemistry and biochemistry papers. 41 papers were multiply annotated by 16 experts, and the best 9 annotators did the rest. This *ranking of annotators by κ* is itself a sign that agreement was uneven. Ravenscroft et al. (LREC 2016) showed that many sentences carry **several** CoreSC labels and proposed multi-label κ variants.

The lesson for StoryAtlas: AZ's CONTRAST/BASIS and CoreSC's Method-Old-Disadvantage are the sentence-level signals of the "relation to prior work". CoreSC's conceptID layer is the right idea for linking the insight, the method and the evidence across a paper.

### 1.3 Contribution-type typologies
- **Shaw, "What makes good research in software engineering?" (2002)** characterizes a paper along three **separate** axes:
  - *Question type:* Method or means of development / Method for analysis / Design, evaluation, or analysis of a particular instance / Generalization or characterization / Feasibility.
  - *Result type:* Procedure or technique / Qualitative or descriptive model / Empirical model / Analytic model / Notation or tool / Specific solution / Answer or judgment / Report.
  - *Validation type:* Analysis / Experience / Example / Evaluation / Persuasion / Blatant assertion.

  "Procedure or technique" was 44% of ICSE 2002 submissions and 51% of acceptances. Shaw's three-axis split is the strongest precedent for separating contribution, question and evidence in StoryAtlas.
- **Pramanick, Hou, Mohammad and Gurevych, "The Nature of NLP" (ACL 2025)** split contributions into **Artifact** (a-dataset, a-method, a-task) and **Knowledge** (k-dataset, k-language, k-method, k-people, k-task). Annotators reached Fleiss' κ=0.71 overall (0.67 to 0.76 per type) on 1,995 papers. SciBERT and GPT-4-Turbo both classify at macro-F1 0.80. Applied to 28,937 NLP papers (1974 to 2024), the scheme shows contributions per paper have increased over time.
- **ORKG** models a paper as one or more *contributions*, each linking a research problem, a method and results. Contributions are made comparable through templates and side-by-side *comparisons*, and ORKG Ask answers natural-language questions over them. **NLPContributionGraph (SemEval-2021 Task 11)** defines 12 information units: ResearchProblem, Approach, Model, Code, Dataset, ExperimentalSetup, Hyperparameters, Baselines, Results, Tasks, Experiments and AblationAnalysis. Note that Approach (the abstract idea) is kept separate from Model (the concrete implementation). The dataset has only ~440 articles and a single annotator. The best end-to-end F1 was 57% for contribution sentences and 22% for triples.
- **Heilmeier catechism (DARPA)** asks: What are you trying to do? How is it done today and what are the limits? What is new in your approach and why will it succeed? Who cares? What difference will it make? What are the risks? What does it cost and how long will it take? What are the midterm and final exams? **[list from background knowledge]** This list maps cleanly onto question, limitation, insight, significance and evidence.
- **Kuhn** distinguishes normal-science "puzzle-solving", anomaly, crisis and revolution. This is useful as a coarse "scale of the claim" axis (incremental, anomaly report, reframing), not as labels.

### 1.4 What makes a question interesting: gap vs. problematization
- **Davis, "That's Interesting!" (1971)** argues that theories get attention when they deny an assumption the audience holds weakly. His *index of the interesting* has 12 "what seems X is really non-X" moves:
  - *Single phenomenon:* Organization, Composition, Abstraction, Generalization (local↔general), Stabilization, Function (ineffective↔effective), Evaluation (bad↔good).
  - *Multiple phenomena:* Co-relation, Co-existence, Co-variation, Opposition (similar↔opposite), Causation (independent↔dependent).

  This is the closest existing typology to StoryAtlas's "narrative arcs". "Unify" is Composition or Opposition (seems opposite, really similar). "Simpler is better" is Function or Evaluation. "Resolve a trade-off" is Co-existence (seems unable to coexist, really can).
- **Sandberg and Alvesson (Organization, 2011)** reviewed 52 articles and found **gap-spotting** dominant, in three modes: *confusion spotting* (competing explanations), *neglect spotting* (overlooked area / under-researched area / lack of empirical support) and *application spotting* (extending or complementing a literature). Their alternative is **problematization**, which challenges underlying assumptions (Alvesson and Sandberg, AMR 2011). Locke and Golden-Biddle (1997) similarly separate how a paper *constructs coherence* in prior work (synthesized, progressive, noncoherent) from how it *problematizes* it (incomplete, inadequate, incommensurate) **[unverified]**.

### 1.5 ML-specific rhetoric and persuasion
- **Birhane et al., "The Values Encoded in ML Research" (FAccT 2022)** annotated 100 highly cited ICML and NeurIPS papers (over 3,500 sentences). The papers most often justify themselves by *performance, generalization, quantitative evidence, efficiency, building on past work and novelty*. Only 15% connect to a societal need. The value count differs between versions (59 vs. 67).
- **Lipton and Steinhardt, "Troubling Trends in ML Scholarship" (2018)** name four failure patterns: not distinguishing explanation from speculation, not identifying the sources of empirical gains, mathiness, and misuse of language. These are pitfalls for a "supporting evidence" field: the narrative a paper claims and the evidence it actually provides can diverge.
- **Sadallah, Sheikh Asadi and van der Plas (arXiv 2610.01353, 2026)** apply CARS to human-written and LLM-generated introductions. Human introductions are more flexible in which moves they use and in what order. Generated ones are more uniform, and **giving the model the CARS definitions makes it more rigid**. Their LLM annotator reaches step accuracy 0.694 vs. a human baseline of 0.752, and move accuracy 0.901 vs. 0.911.

---

## 2. Datasets and open-source resources

| Resource | Unit / labels | Size | Relevance |
|---|---|---|---|
| PubMed 200k RCT (Dernoncourt and Lee 2017) | abstract sentences: Background/Objective/Methods/Results/Conclusions | ~200k abstracts | move tagging baseline (biomed) |
| CSAbstruct (Cohan et al. 2019) | same 5 labels, CS abstracts | ~2.2k abstracts **[size unverified]** | closest move corpus for ML |
| AZ / AZ-II corpora (Teufel) | 7 / 15 zones | CL and chemistry papers | prior-work stance |
| CoreSC corpus (Liakata) | 11 concepts + properties | 265 papers | investigation structure |
| NLPContributions (Pramanick et al. 2025) | artifact/knowledge contribution types | 1,995 papers, κ=0.71 | **contribution-type labels; reuse** |
| NLPContributionGraph (SemEval-21 T11) | 12 information units + triples | ~440 papers | problem/approach/results slots |
| ORKG | contribution graphs, comparisons | crowd-curated | schema precedent |
| SciFact (Wadden et al. 2020) | claims + support/refute rationales | 1.4k claims | claim↔evidence linking |
| SciClaim (Magnusson and Friedman 2021) | fine-grained claim graphs (causation, comparison, qualifiers) | 901 sentences, 12.7k annotations | claim structure |
| SciTLDR (Cachola et al. 2020) | one-sentence TLDRs | 5.4k TLDRs / 3.2k papers | powers S2 TLDRs |
| MASSW (Zhang et al. 2024) | LLM-extracted Context, Key Idea, Method, Outcome, Projected Impact | 152k CS papers, 17 venues incl. ICLR/ICML/NeurIPS | **closest to StoryAtlas fields** |
| HypoGen / Sparks of Science (2025) | Bit (conventional assumption), Spark (key insight), Flip (counterproposal), chain of reasoning | ~5.5k pairs (NeurIPS 2023 / ICLR 2024) | **closest to "challenge" arc + insight** |
| CS-PaperSum (2025) | LLM structured summaries (contributions, methods, evaluation, future work) | 91,919 CS papers | weak supervision |
| SOLVENT (Chan et al. CSCW 2018) | Background / Purpose / Mechanism / Findings annotations | — | **cross-domain analogy retrieval** |
| ACL-ARC, SciCite **[unverified details]** | citation intent (background, uses, extends, compares, motivation) | — | relation to prior work |

MASSW's validation is the most useful data point for StoryAtlas. Human-human and GPT-4-human agreement on its aspects were close on semantic similarity (cosine ~0.90). But GPT-4 recognized a *missing* Context only ~58% of the time and a missing Method ~42% of the time. In other words, LLMs fill empty slots with plausible text, so StoryAtlas fields need an explicit "not stated" option and a quote to support each filled one.

---

## 3. Products

- **Elicit:** search plus a structured extraction table with user-defined columns, and systematic-review workflows (PRISMA 2020, recurring "Routines"). It is good at *facts per paper* (population, method, outcome). It offers no narrative or framing analysis.
- **SciSpace:** a PDF reader with an AI copilot, chat with a paper, and literature review tables. Per competitor comparisons it is stronger for reading single papers than for interrogating many papers at once.
- **Consensus:** answers yes/no-style questions from claim extraction across papers **[features not checked in this review]**.
- **Semantic Scholar:** SciTLDR-based TLDRs, the Semantic Reader with skimming highlights (goal, method and result sentences) **[unverified]**, and citation-intent labels.
- **alphaXiv:** one-line summaries, video overviews, grounded literature review, conference "paper maps", an MCP server and "Autoresearch".
- **ORKG Ask:** natural-language QA over structured contributions, with comparison tables.
- **Writefull / Paperpal / Grammarly:** sentence-level academic language editing **[not checked]**.
- **Scideator (Radensky et al.):** a research prototype that extracts *purpose, mechanism and evaluation* facets and recombines them, for example a mechanism paired with a distant purpose, then checks novelty. It was more creativity-supporting than an LLM baseline in a 19 to 22 person study.

**Gap:** every product extracts *what* a paper did (its facts, method and claims). None I found indexes *how the paper argues* (its arc, the type of niche it opens, its framing alternatives), or retrieves by narrative analogy across topics. SOLVENT and Scideator show that purpose/mechanism abstraction supports cross-domain analogy. They are the closest prior art to StoryAtlas's retrieval goal.

---

## 4. Synthesis

### 4.1 Which axes are really separate
The literature consistently separates at least five axes. Collapsing them is the main flaw of the seed list:

1. **Niche / problematization (why this paper is needed).** Sources: CARS Move 2, Sandberg and Alvesson, Locke and Golden-Biddle.
2. **Contribution type (what kind of thing is delivered).** Sources: Shaw result types, Pramanick artifact/knowledge, ORKG.
3. **Narrative arc / twist (what belief changes).** Source: Davis's index of the interesting, Bit→Flip.
4. **Evidence type (why we should believe it).** Source: Shaw validation types.
5. **Scope of claim.** Kuhn-style: incremental, anomaly, reframing.

The seed categories mix these axes. **"Identify and address an overlooked limitation"** is a *niche* (neglect spotting). **"Unify existing approaches"** is a *contribution* (a qualitative or analytic model) delivered through a *Composition/Opposition* twist. **"Challenge conventional wisdom"** is a *problematization* niche that can carry any twist. **"Simpler is better"** is a twist (Function/Evaluation: what seems inferior is really effective). **"Discover and explain a phenomenon"** is a knowledge contribution, often with a Co-relation or Causation twist. **"Resolve a trade-off"** is a Co-existence twist. **"Transfer an insight across domains"** is *application spotting* plus an *origin-of-insight* attribute. A paper can be a transfer *and* simpler-is-better. Multi-label is therefore required, but it should be multi-label *within* each axis, not one flat list.

Missing from the seeds, and common in ML venues: **new capability/method** (the plurality case: Shaw's "procedure or technique" at 44%), **new resource** (benchmark/dataset), **new problem formulation/task**, **negative result / debunking** (seems effective, really not), **theory/guarantee**, **scaling/characterization** ("how does Y vary with X"), and **feasibility** ("can X be done at all").

### 4.2 Proposed first-draft taxonomy (hierarchical, multi-label per axis)

**A. Niche (why needed)** (pick 1 or 2)
- A1 Gap: A1a overlooked aspect · A1b under-explored setting · A1c missing evidence/evaluation
- A2 Limitation of prior methods: A2a performance · A2b cost/efficiency · A2c robustness/generalization · A2d assumptions too strong
- A3 Confusion: conflicting results or explanations
- A4 Problematization: a widely held assumption is wrong
- A5 Application/extension: a known idea not yet used in setting S
- A6 New problem or demand: a new capability or task is needed

**B. Contribution type (what is delivered)** (multi)
- B1 Artifact: method/model · system/tool · dataset/benchmark · task/formulation
- B2 Knowledge: empirical finding/phenomenon · explanation/mechanism · theory/guarantee · characterization/scaling law · analysis of existing methods · negative result

**C. Narrative arc / twist (the belief change)** (multi, ≤2)
- C1 *Seems necessary → isn't* (simpler is better; component X is unnecessary)
- C2 *Seems to work → doesn't / for other reasons* (debunk, re-attribute gains)
- C3 *Seem different → are the same* (unification)
- C4 *Seems one thing → is several* (decomposition, disentangling)
- C5 *Seem incompatible → can coexist* (resolve trade-off)
- C6 *Seems local → general*, or the reverse (transfer; scope limits)
- C7 *Unrelated → related; correlation → cause* (phenomenon discovery and explanation)
- C8 *Impossible/unknown → feasible* (first demonstration)
- C9 *Better on axis X* (no twist; standard improvement arc)

**D. Insight origin**: analogy from another domain · first-principles/theory · empirical observation · reframing as a known problem · scale/engineering.

**E. Evidence type** (multi): benchmark comparison · ablation · controlled/synthetic experiment · theoretical proof · case study/qualitative · human study · large-scale characterization · existence demonstration.

**F. Claim scope**: incremental · significant extension · reframing/paradigm.

### 4.3 Per-paper extraction schema (draft)

```yaml
paper_id, venue, year
research_question: str            # one sentence, domain terms allowed
niche: {labels: [A*], prior_work_limitation: str, evidence_quote: str}
conventional_belief: str|null     # Bit, if any
key_insight: str                  # Spark
main_contribution: {labels: [B*], statement: str}
arc: {labels: [C*], seems: str, really: str}   # Davis-style pair
insight_origin: [D*]
evidence: [{type: E*, claim_supported: str, location: "Sec/Fig/Table"}]
claim_scope: F*
abstract_moves: [{sentence_idx, move: Context|Gap|Purpose|Method|Result|Implication}]
intro_moves:    [{para_idx, move: M1-territory|M2-counterclaim|M2-gap|M2-question|M2-continue|M3-purpose|M3-findings|M3-structure}]
abstract_template: str            # domain-free, e.g. "Prior methods for <TASK> assume <A>; we show <A> is unnecessary because <INSIGHT>, yielding <BENEFIT> on <EVAL>."
alternative_framings: [{arc: C*, niche: A*, one_line: str}]
confidence: {per_field: 0-1}, not_stated: [field...]
```

Retrieval for analogous narratives should match on `(niche, arc, insight_origin, abstract_template embedding)` and down-weight topic, as SOLVENT does by matching on purpose and mechanism rather than all words.

### 4.4 Extraction pitfalls the literature reports
1. **Counter-claims are the least reliable label.** In the 2026 CARS study even trained humans scored only **F1 0.23** on M2 Counter-claiming and 0.42 on Question-raising, against 0.77 on Indicating a gap. "Challenge conventional wisdom" will be noisy. Require a quoted `conventional_belief` and an evidence pointer before assigning A4 or C2.
2. **Sentences are multi-functional.** CoreSC multi-label work and Yu, Bondi and Hyland (GPT-4 move analysis, 2024) both report several moves per sentence. Avoid single-label sentence schemes.
3. **Agreement ceilings are modest.** κ≈0.71 for AZ and for contribution types is the realistic ceiling for coarse labels. Finer schemes (AZ-II's 15 categories, NCG triples at 22% F1) are much worse. Keep the top levels small and make subtypes optional.
4. **LLMs hallucinate missing slots and homogenize structure.** MASSW: missing Context or Method was flagged only 42 to 58% of the time. Sadallah et al.: giving the model the move definitions made it *more* rigid. Require quote grounding and a "not_stated" option, and don't over-prompt with the taxonomy.
5. **Stated vs. actual story.** Lipton and Steinhardt and Birhane et al. show that ML papers frame themselves around performance and novelty, and that the source of the gains is often misattributed. Store the *authors' framing* and the *evidence actually provided* separately.
6. **Abstract-only extraction loses the story.** MASSW and HypoGen work largely from abstracts. The niche and the "conventional belief" usually live in the introduction, so extract from the abstract plus the introduction.
7. **Annotator expertise matters.** CoreSC filtered its annotators. SOLVENT found crowd workers struggled with the purpose vs. mechanism distinction. Validate on a small expert-labelled ICLR/ICML/NeurIPS set (~100 papers, two annotators) before scaling.

---

## References
- Swales CARS steps (1990), UMass Writing Center: https://www.umass.edu/writing-center/resources/creating-research-space
- Swales 2004 revision discussion: https://www.readingmatrix.com/files/1-81670md8.pdf
- Teufel, Siddharthan, Batchelor 2009, AZ-II: https://aclanthology.org/D09-1155/
- Teufel PhD thesis: https://www.cl.cam.ac.uk/~sht25/thesis/t.pdf
- Liakata et al. 2010, CoreSC zones: https://aclanthology.org/W10-3101.pdf
- Ravenscroft et al. 2016, multi-label CoreSC: https://aclanthology.org/L16-1650/
- Shaw 2002, What makes good research in SE: https://www.cs.cmu.edu/~Compose/ftp/shaw-fin-etaps.pdf
- Pramanick et al. 2025, The Nature of NLP: https://arxiv.org/abs/2409.19505 · https://aclanthology.org/2025.acl-long.1224
- D'Souza et al. 2021, NLPContributionGraph: https://arxiv.org/abs/2106.07385
- ORKG: https://arxiv.org/abs/1901.10816 · https://orkg.org
- Davis 1971, That's Interesting!: https://www.sfu.ca/~palys/interest.htm
- Sandberg and Alvesson 2011, Gap-spotting or problematization: https://lup.lub.lu.se/record/1925769
- Alvesson and Sandberg 2011, Problematization (AMR): https://lup.lub.lu.se/record/1965150
- Birhane et al. 2022, Values Encoded in ML Research: https://arxiv.org/abs/2106.15590
- Lipton and Steinhardt 2018, Troubling Trends: https://arxiv.org/abs/1807.03341
- Sadallah et al. 2026, CARS human vs. AI introductions: https://arxiv.org/abs/2610.01353
- Yu, Bondi, Hyland 2024, GPT-4 move analysis: https://arxiv.org/abs/2407.15612
- MASSW: https://arxiv.org/abs/2406.06357
- Sparks of Science / HypoGen: https://arxiv.org/abs/2504.12976
- CS-PaperSum: https://arxiv.org/abs/2502.20582
- SciClaim: https://aclanthology.org/2021.emnlp-main.381
- SciFact: https://arxiv.org/abs/2004.14974 [not fetched]
- SciTLDR: https://arxiv.org/abs/2004.15011 [not fetched]
- PubMed 200k RCT: https://arxiv.org/abs/1710.06071 [not fetched]
- CSAbstruct (Cohan et al. 2019): https://arxiv.org/abs/1909.04054 [not fetched]
- SOLVENT, Chan et al. 2018: https://par.nsf.gov/servlets/purl/10109292
- Scideator: https://arxiv.org/abs/2409.14634
- Elicit changelog: https://support.elicit.com/en/articles/14823097-changelog
- Elicit vs. SciSpace (third-party): https://paperguide.ai/blog/elicit-vs-scispace/
- alphaXiv: https://www.alphaxiv.org/
- Heilmeier catechism: https://www.darpa.mil/about/heilmeier-catechism [not fetched]
- Kording and Mensh 2017, Ten simple rules for structuring papers: https://doi.org/10.1371/journal.pcbi.1005619 [not fetched]
