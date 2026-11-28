# PlotAtlas: related work and a first-draft intent taxonomy

*Related-work review for PlotAtlas, the Fig1 Atlas component whose unit is one experimental plot or figure panel. Written 2026-11-28. Claims marked **[unverified]** were not checked against a primary source during this review.*

## 0. Summary

1. **The "message" literature already exists, but nobody has applied it to ML papers.** Carberry and Elzer's bar-chart work names 12 *intended-message* categories ([SIGIR'06](https://www.eecis.udel.edu/~carberry/Papers/SigIR-06.pdf)). The FT Visual Vocabulary sorts charts into 9 *communicative* families ([FT chart-doctor](https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md)). Lundgard and Satyanarayan separate *perceptual/trend* content from *contextual/domain* content in chart descriptions (L3 vs. L4). None of these covers ML-specific messages such as scaling, Pareto dominance, ablation attribution or crossover.
2. **Every scientific-figure dataset labels form, not intent.** SciCap, ACL-Fig, DocFigure, FigureSeer and Viziometrics label figure *type*: line plot, bar, diagram, photo. A search for a dataset labeled by communicative intent found none ([ACL-Fig](https://arxiv.org/abs/2301.12293), [DocFigure](https://cvit.iiit.ac.in/usodi/Docfig.php)). PlotAtlas's intent labels would be new.
3. **The seed list mixes three axes**, and PlotAtlas should keep them apart: *message* (what the reader should conclude), *evidence/experiment type* (what was run) and *form* (marks, encodings, layout). For example, a "learning curve" is an experiment type, a "Pareto frontier" is a message, and a "multi-panel summary" is a layout.
4. **Licensing is the main legal risk.** Several datasets say arXiv content is "CC0" ([SciCap](https://arxiv.org/pdf/2110.11624), [ArxivCap](https://arxiv.org/html/2403.00231v2)). CC0 covers arXiv *metadata*. Most papers carry only arXiv's non-exclusive distribution licence. ChartMimic is careful: it filtered to CC BY 4.0 papers ([ChartMimic](https://arxiv.org/html/2406.09961v2)). CharXiv forbids training on its data ([HF card](https://huggingface.co/datasets/princeton-nlp/CharXiv/blob/main/README.md)).
5. **For code generation, use a two-level pattern.** The top level is a small declarative, Vega-Lite-like *pattern spec*: data roles, marks, encodings, facets and annotations. Each spec is paired with an executable, parameterized matplotlib template. Spec-first systems are the ones that can reason about design: Draco, CompassQL and Data Formulator all compile to Vega-Lite. ML papers, however, are almost all matplotlib, and chart-to-code benchmarks target matplotlib ([Plot2Code](https://arxiv.org/abs/2405.07990), [ChartMimic](https://arxiv.org/html/2406.09961v2)).

## 1. Visualization literature on intent and tasks

**Task typologies (the reader's side).** Amar, Eagan and Stasko ([InfoVis 2005](https://perso.telecom-paris.fr/eagan/media/papers/amar05.pdf)) built a list of ten low-level analytic tasks from about 200 analyst questions: retrieve value, filter, compute derived value, find extremum, sort, determine range, characterize distribution, find anomalies, cluster and correlate. Brehmer and Munzner ([InfoVis 2013](https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/)) split a task into *why*, *how* and *what*. The *why* runs from consume (present, discover, enjoy) or produce, through search (lookup, browse, locate, explore), down to query (identify, compare, summarize). Munzner's *Visualization Analysis & Design* (2014) pairs these *actions* with *targets*: trends, outliers and features for all the data; distribution and extremes for one attribute; dependency, correlation and similarity for several. The typology was confirmed via the project page; the exact sub-levels are recalled from the paper **[sub-levels unverified in this session]**.

For PlotAtlas, nearly every paper plot sits under **consume → present**: the author already knows the conclusion. The intent axis should therefore encode the *author's message*, not an open-ended analysis task. Amar's tasks remain useful as a lower-level attribute, the *reading operation* a viewer must perform to get the message (find extremum, compare, correlate). That attribute links intent to encoding choice.

**Intended message (the author's side).** The work closest to PlotAtlas is Elzer, Carberry and colleagues on recognizing the intended message of information graphics. A Bayesian network infers one of 12 message categories for simple bar charts from communicative signals: salience, captions and perceptual task effort. The categories are Rank-of-Entity, Rank-of-All, Increasing-Trend, Decreasing-Trend, Stable-Trend, Change-Trend, Maximum, Minimum, Contrast-Point-with-Trend, Relative-Difference-between-Entities, Relative-Difference-with-Degree and Other ([SIGIR'06](https://www.eecis.udel.edu/~carberry/Papers/SigIR-06.pdf); [IJCAI'05](https://ijcai.org/proceedings/2005/46); [UMUAI'06](https://link.springer.com/doi/10.1007/s11257-006-9002-9)). Two lessons carry over. First, a message has a *category* and *parameters*, for example Relative-Difference(ours, best baseline). Second, *design signals* such as highlighting, sorting and annotation are strong evidence of intent. Both should be extracted.

**Takeaways and captions.** Kim, Setlur and Agrawala ([CHI 2021](https://hci.stanford.edu/publications/paper.php?id=429)) ran a study with 43 line charts and 2,168 participants. When the caption and the visual emphasis agree, readers take away the emphasized feature. When the caption names a less prominent feature, readers fall back on what the chart makes salient. PlotAtlas should therefore store both the *stated* message (caption or text) and the *visually supported* message, and flag panels where the two disagree. Lundgard and Satyanarayan's four-level model of chart semantics (VIS 2021) has L1 encoding, L2 statistics, L3 perceptual trends and L4 domain context **[not re-fetched]**. It maps cleanly onto the schema: form ≈ L1, values ≈ L2, message ≈ L3, claim ≈ L4.

**Rhetoric.** Hullman and Diakopoulos ([InfoVis 2011](https://mucollective.northwestern.edu/project/vis-rhetoric)) show how choices about data, visual form, annotation and interactivity frame what viewers conclude. Kosara and Mackinlay ("Storytelling: the next step for visualization", IEEE Computer 2013) **[not re-fetched]** argue that presentation is a different goal from exploration. For ML plots, the relevant rhetorical devices are baseline selection, axis truncation, log scaling, the ordering of methods and highlighting "ours". The schema should record these devices because they matter for honest reuse.

**Encoding effectiveness.** Cleveland and McGill (JASA 1984) rank elementary perceptual tasks from most to least accurate: position on a common scale; position on non-aligned scales; length, direction and angle; area; volume and curvature; shading and saturation. Mackinlay's APT (1986) made that ranking a rule for choosing designs. Draco learned constraint weights from such perception experiments ([Draco](https://idl.uw.edu/papers/draco)). The ranking explains why ML conventions work. Scaling curves put the key variable on a common position scale on log-log axes. Ablation bars encode a *difference*, so they read better as deltas from the full model than as raw bars.

**Memorability and scientific figures.** Borkin et al. ([InfoVis 2013](https://vcg.seas.harvard.edu/publications/20130101-what-makes-a-visualization-memorable)) studied 2,070 visualizations. Human-recognizable objects, colour and unusual forms raise memorability; common bar and line charts are less memorable. The authors warn that memorable does not mean effective. This matters more for Figure 1s than for result panels. Viziometrics (Lee, West and Howe, [arXiv:1605.04951](https://arxiv.org/abs/1605.04951)) classified more than 8M PubMed figures into 5 types (another version says 6). Higher-impact papers had more diagrams. About 35% of extracted images were multi-panel, so subfigure splitting is not optional. Rougier, Droettboom and Bourne ([PLOS CB 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4161295)) give ten rules: know your audience; identify your message; adapt to the medium; captions are not optional; do not trust defaults; use colour effectively; do not mislead; avoid chartjunk; message trumps beauty; get the right tool. Rule 2 is PlotAtlas's premise. Tufte (*The Visual Display of Quantitative Information*, 1983/2001) contributes data-ink, small multiples and "compared to what?". In an ML plot, the answer to "compared to what?" is the baseline set, a first-class field.

## 2. Datasets and tools for scientific figures

| Resource | What it holds | Labels provided | License (as stated) |
|---|---|---|---|
| [SciCap](https://github.com/tingyaohsu/SciCap) (EMNLP-F 2021) | 2M+ CS arXiv figures (2010–2020); the main release keeps graph plots | caption; figure type; subfigure flag | CC BY-NC-SA 4.0 |
| [SciCap Challenge / HF](https://huggingface.co/datasets/CrowdAILab/scicap) | expanded: 8 arXiv categories plus ACL | caption, mention paragraphs, OCR | CC BY-NC-SA 4.0 |
| [ACL-Fig](https://arxiv.org/abs/2301.12293) | 112k ACL figures; 1,671 labeled (pilot) | 19 figure types (incl. Pareto, confusion matrix) | CC BY-NC ([HF](https://huggingface.co/datasets/citeseerx/ACL-fig)) |
| [DocFigure](https://cvit.iiit.ac.in/usodi/Docfig.php) | 33k figures from CV papers | 28 figure types | availability disputed |
| [FigureSeer](https://prior.allenai.org/projects/figureseer) (ECCV 2016) | result figures from papers | figure type (7), axes, legend, extracted data series | **[unverified]** |
| [Viziometrics](https://faculty.washington.edu/billhowe//projects/2015/01/15/Viziometrics.html) | 8M PubMed figures | 5–6 coarse types; multi-panel splits | **[unverified]** |
| [FigureQA](https://www.microsoft.com/en-us/research/project/figureqa-dataset/) | synthetic line, dot-line, bar and pie charts | template QA, source data, bounding boxes | Microsoft research terms **[unverified]** |
| PlotQA (Methani et al. 2020) | synthetic plots from real data | open-vocabulary QA with aggregation, source tables | **[unverified]** |
| [ChartQA](https://github.com/vis-nlp/ChartQA) | real web charts | human and machine QA, data tables | GPL-3.0 **[unverified]** |
| Chart-to-Text (Kantharaj et al., ACL 2022) | about 44k Statista and Pew charts | human summaries, data tables | **[unverified]** |
| [SciGraphQA](https://arxiv.org/abs/2308.03349) | about 295k multi-turn dialogues about arXiv CS/ML graphs | LLM-generated QA from caption and paragraph | research-only vs. MIT; conflicting |
| [ArxivCap / ArxivQA](https://mm-arxiv.github.io) | 6.4M images and 3.9M captions from 572k papers; 100k QA | caption, subfigure grouping, GPT-4V QA | HF says CC BY 4.0; project page says CC BY-NC, research-only |
| [MMC](https://huggingface.co/datasets/xywang1/MMC/blob/main/README.md) (NAACL 2024) | 600k chart instruction instances | instructions and QA over many chart types | CC BY-SA 4.0 |
| [CharXiv](https://arxiv.org/abs/2406.18521) (NeurIPS 2024) | 2,323 hand-picked arXiv charts | 4 descriptive and 1 reasoning QA per chart | QA CC BY-SA 4.0; **evaluation only, no training**; charts keep authors' copyright |
| [Paper2Fig100k](https://zenodo.org/record/7299423) | 102k figure–text pairs, mostly diagrams | caption and OCR | not stated on Zenodo |
| [ChartMimic](https://arxiv.org/html/2406.09961v2) (ICLR 2025) | 4,800 (figure, instruction, code) triplets from CC BY arXiv papers | 22 types, ~191–201 subtypes; matplotlib code | Apache-2.0 |
| [Plot2Code](https://huggingface.co/datasets/TencentARC/Plot2Code/blob/main/README.md) | 132 matplotlib-gallery plots plus plotly (368 total) | code, GPT-4 instruction | Apache-2.0 |
| [ChartCoder / Chart2Code-160k](https://huggingface.co/datasets/xxxllz/Chart2Code-160k) (ACL 2025) | 160k chart–code pairs, 27 types | Python code | **[unverified]** |

**What the labels miss.** Every resource labels *form* (type), *content* (QA, caption, data table) or *code*. None labels the communicative message, the experiment behind the plot or the linked claim. CharXiv and SciCap are the best sources of realistic arXiv chart *images* to benchmark against. Their licences forbid redistribution or training, so they should serve only as evaluation references, not as PlotAtlas content.

**Extraction tools.**
- [pdffigures2](https://index.scala-lang.org/allenai/pdffigures2/artifacts/pdffigures2) (Apache-2.0) extracts figures, tables, captions and section titles from born-digital PDFs.
- [deepfigures-open](https://github.com/allenai/deepfigures-open/) is a neural detector trained on 5.5M labels induced from LaTeX sources. It is research code and depends on pdffigures2.
- GROBID (Apache-2.0) gives figure and caption zones in TEI, plus references, which are useful for linking a panel to the text that cites it.
- MinerU parses layout well, but its licence moved from AGPL-3.0 to a custom Apache-derived licence in 2026, and its VLM weights may still be AGPL. Check the exact version before use ([summary](https://toolnavs.com/article/2457-is-mineru-worth-using-the-50k-star-pdf-to-markdown-tool-has-deployment-and-licen)) **[partly unverified]**.
- For subfigures, the Viziometrics dismantling algorithm recursively splits a figure into tokens and classifies each as auxiliary (text) or standalone. Fig1 Atlas's existing pipeline (`pipeline/s3_extract.py`) is the natural place to add panel splitting.

## 3. Products: recommendation and chart-code tools

- **Galleries** ([matplotlib](https://matplotlib.org/stable/gallery/), seaborn) are organized by *form*. They provide reusable code but no guidance on message.
- **[From Data to Viz](https://www.data-to-viz.com/)** is a decision tree keyed on *data types* (one numeric, several categoric, …) leading to forms, with caveats.
- **[FT Visual Vocabulary](https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md)** is the one widely used tool organized by *message*: deviation, correlation, ranking, distribution, change over time, magnitude, part-to-whole, spatial and flow. It derives from Schwabish and Ribeca's Graphic Continuum ([GIJN](https://gijn.org/resource/document-of-the-day-visual-vocabulary/)). PlotAtlas should model its top level on this tool and add ML-specific messages.
- **Voyager / CompassQL** (Wongsuphasawat et al. 2016–17) enumerate and rank partial Vega-Lite specs for exploration. **[Draco](https://idl.uw.edu/papers/draco)** encodes design knowledge as hard and soft Answer Set Programming constraints solved by Clingo and emits Vega-Lite. Draco 2 is pure Python ([arXiv:2308.14247](https://arxiv.org/pdf/2308.14247)).
- **[VizML](https://arxiv.org/abs/1808.04819)** learns design choices from 1M Plotly dataset–visualization pairs, reaching about 70–95% accuracy on held-out design choices.
- **[LIDA](https://arxiv.org/abs/2303.02927)** (ACL demo 2023) runs a summarizer, then a *goal explorer*, then a grammar-agnostic code generator (matplotlib, seaborn, altair, …), then an infographer. Its "goal" is a natural-language question/visualization/rationale triple, the closest product analogue to a message field.
- **[Data Formulator](https://www.microsoft.com/en-us/research/publication/data-formulator-ai-powered-concept-driven-visualization-authoring/)** (MIT licence) uses *concept binding*: high-level visualization intent is kept separate from the data transformations an AI agent writes, and the output is Vega-Lite.

**Gaps.** Recommenders map data types to forms; LIDA and Data Formulator map a natural-language goal to code. None of them knows ML conventions: seeds and error bands, log-compute axes, frontiers, "ours" highlighting, ablation deltas. None retrieves *real published examples* by message.

## 4. Synthesis

### 4.1 Critique of the seed list

| Seed item | Message | Experiment type | Form |
|---|---|---|---|
| Scaling curves | trend / extrapolation | scale sweep | log-log line plus fit |
| Pareto frontier | trade-off / dominance | multi-config sweep | scatter plus staircase |
| Learning curves | (varies: faster convergence, instability, grokking) | training dynamics | line over steps |
| Performance crossover | regime change | sweep over a condition | crossing lines |
| Distributional comparison | (compare spread or robustness) | multi-seed or per-example eval | box, violin, ECDF |
| Ablation comparison | attribution | component removal | bar, table-plot, delta bar |
| Sensitivity analysis | robustness / flatness | hyperparameter sweep | line or heatmap |
| Correlation | association / proxy validity | paired measurements | scatter plus fit |
| Qualitative comparison | (any message, shown by example) | sample generation | image grid |
| Multi-panel summary | none of its own | none | layout |

Only about half of the seed items are messages. PlotAtlas should therefore use **three orthogonal, multi-label axes**: *Message* (hierarchical, below), *Evidence* (experiment type) and *Form* (marks, encodings, layout). Retrieval should work on any combination, for example "show me *trade-off* messages built from *hyperparameter sweeps*, drawn as *anything but scatter*".

### 4.2 Draft message taxonomy (hierarchical, multi-label)

Level-1 families follow the FT, Amar and Elzer categories; level-2 entries are ML-specific. Each label takes parameters, in the Elzer style.

1. **Compare (A beats B)**: *Ranking* (ours is best among methods); *Gap* (ours beats a named baseline by Δ; Relative-Difference); *Parity* (we match a stronger or costlier method); *Consistency* (wins hold across tasks, datasets or seeds).
2. **Attribute (why it works)**: *Ablation contribution* (removing X costs Δ); *Additivity / interaction* (components stack or interact); *Decomposition* (error or compute broken into parts; part-to-whole).
3. **Trend (Y changes with a controlled X)**: *Scaling law* (smooth, often power-law, extrapolable); *Dynamics* (behaviour over training steps or time); *Monotone gain or degradation* (with data, length, noise or shift); *Saturation / diminishing returns*.
4. **Regime change**: *Crossover* (A wins below x\*, B above; Contrast-Point-with-Trend); *Phase transition / emergence* (sudden change at a threshold); *Failure onset* (breaks beyond x\*).
5. **Trade-off**: *Pareto dominance* (ours shifts the frontier); *Budget curve* (quality vs. cost, latency, memory or steps); *Operating point* (a knob moves along the curve).
6. **Robustness / sensitivity**: *Insensitivity* (flat across a hyperparameter range); *Sensitivity* (a sharp optimum must be tuned); *Variance* (spread across seeds or prompts).
7. **Association**: *Correlation / proxy validity* (metric M predicts N); *Calibration* (predicted vs. observed); *Agreement* (with humans or theory).
8. **Characterize / reveal**: *Distribution shape* (heavy tail, bimodality); *Structure* (clusters in embeddings, attention patterns, layer-wise probing); *Anomaly / failure mode*.
9. **Validate theory**: *Empirical matches prediction* (curve vs. bound or theoretical rate); *Toy confirmation* (a synthetic setting shows the mechanism).
10. **Exemplify**: *Qualitative evidence* (samples supporting any message above; always paired with another label).

Cross-cutting attributes: **claim polarity** (positive, negative or null result); **strength** (dominant or marginal); **scope** (single setting or general); **reading operation** (Amar task); **rhetorical devices** (highlight, sorting, log axis, truncated axis, annotation).

### 4.3 Per-plot extraction schema

```json
{
  "panel_id": "openreview:XXXX/fig3b",
  "paper": {"venue": "ICLR 2026", "openreview_id": "...", "arxiv_id": "...", "license": "CC-BY-4.0"},
  "figure_id": "fig3", "panel_label": "b", "bbox": [x0, y0, x1, y1], "page": 6,
  "image": {"path": "...", "source": "latex|pdf_vector|pdf_raster", "vector_available": true},
  "caption_full": "...", "caption_panel": "...", "mentions": ["paragraph text citing Fig 3b"],
  "message": {
    "labels": [{"family": "tradeoff", "type": "pareto_dominance", "confidence": 0.8}],
    "params": {"ours": "Method-X", "baselines": ["A", "B"], "x": "latency_ms", "y": "accuracy", "delta": "+2.1 at equal latency"},
    "stated_takeaway": "from caption or text", "visual_takeaway": "what the chart makes salient",
    "consistent": true, "polarity": "positive", "scope": "single_dataset"
  },
  "evidence": {"experiment_type": "hyperparameter_sweep", "linked_claim": "C2: ...", "n_seeds": 3, "uncertainty_shown": "band"},
  "form": {
    "chart_type": "scatter+frontier_line", "marks": ["point", "line"],
    "encodings": {"x": {"field": "latency", "type": "quantitative", "scale": "log"},
                  "y": {"field": "acc", "type": "quantitative"},
                  "color": {"field": "method", "highlight": "ours"}},
    "facets": null, "annotations": ["arrow: 'better'", "text label on ours"],
    "layout": {"panel_in_grid": [1, 2], "shared_axes": "y"}
  },
  "data_requirements": {"schema": [["method", "nominal"], ["latency", "q"], ["acc", "q"], ["seed", "ordinal?"]], "min_points": 5},
  "pattern_id": "pareto-scatter-v1",
  "rhetoric": ["ours_highlighted", "log_x"],
  "quality_flags": ["no_error_bars"]
}
```

### 4.4 Extracting panels: practical advice

1. **Prefer LaTeX source over the PDF.** arXiv source tarballs often hold one PDF or PNG per panel, inside `subfigure`/`subcaption` environments with subcaptions and `\label`s. This gives panel boundaries, panel captions and cross-references for free, and it is the same signal deepfigures used to induce its labels. Matplotlib PDF panels are vectors, so axis ticks, legend text and sometimes the data paths can be recovered exactly. That is cleaner than FigureSeer-style raster parsing.
2. **Fall back to the PDF.** Run pdffigures2 for figure and caption boxes. Split panels by (a) detecting "(a)", "(b)" labels with OCR or the PDF text layer; (b) whitespace projection profiles; (c) a VLM asked for panel boxes, then checking that each box holds one axis frame. Plan for about 35% of figures being multi-panel (Viziometrics).
3. **Link each panel to its text.** Match "Fig. 3b" or "Figure 3 (right)" mentions with GROBID or regex. The citing paragraph is the best evidence of the stated message, and Kim et al. show the caption alone can mislead.
4. **Respect licences.** Store images only for CC-licensed papers. For the rest, store metadata, the derived spec and a link (Fig1 Atlas already has `pipeline/s6_license.py`).

### 4.5 What representation of a "reusable pattern" supports code generation

Use **a declarative pattern spec plus an executable template**, not one or the other.

- The **pattern spec** is Vega-Lite-like JSON, a subset of section 4.3: data roles with types, mark, encoding channels with scales, facet/repeat, layers and *semantic annotations* that Vega-Lite lacks natively. Those annotations are "better" arrows, frontier computation, fit lines with extrapolation, crossover markers, delta-from-reference bars and seed bands. A spec can be checked against the user's data (types, cardinality), searched and diffed, and it can be scored by Draco-style constraints, for example "the compared quantity must use position on a common scale". The spec-first systems (Draco, CompassQL, Data Formulator) are the ones that can reason about design.
- The **template** is a parameterized matplotlib function, `plot_pareto(df, x, y, method, ours, logx=True, ax=None)`. It takes tidy long-format data, returns an `Axes`, has no hard-coded values, and uses a shared style file. Matplotlib is what ML authors use. Chart-to-code benchmarks (ChartMimic, Plot2Code, ChartCoder) measure matplotlib fidelity. LIDA shows that LLMs fill such skeletons more reliably than they write code from scratch **[last point is an inference, not a measured result]**.
- **Pipeline:** the user's message plus data goes to message classification, then retrieval of examples by message × evidence, then choice of a pattern spec, then validation of the data against the spec's roles, then the template, then an editable `.py` file. An Altair/Vega-Lite export can come from the same spec for free. When a user wants to imitate a specific published panel, chart-to-code models can produce a first draft, but the result should be mapped back onto a template so the user's data replaces the placeholder values.

## References

- Amar, Eagan, Stasko. Low-level components of analytic activity. InfoVis 2005. https://perso.telecom-paris.fr/eagan/media/papers/amar05.pdf
- Brehmer, Munzner. A multi-level typology of abstract visualization tasks. TVCG 2013. https://www.cs.ubc.ca/labs/imager/tr/2013/MultiLevelTaskTypology/
- Munzner. Visualization Analysis and Design. CRC, 2014.
- Elzer, Carberry et al. A probabilistic framework for recognizing intention in information graphics. IJCAI 2005. https://ijcai.org/proceedings/2005/46 ; SIGIR 2006 paper listing the 12 categories: https://www.eecis.udel.edu/~carberry/Papers/SigIR-06.pdf ; UMUAI 2006: https://link.springer.com/doi/10.1007/s11257-006-9002-9
- Kim, Setlur, Agrawala. Towards understanding how readers integrate charts and captions. CHI 2021. https://hci.stanford.edu/publications/paper.php?id=429
- Lundgard, Satyanarayan. Accessible visualization via natural language descriptions: a four-level model of semantic content. VIS 2021. [not re-fetched]
- Hullman, Diakopoulos. Visualization rhetoric. TVCG 2011. https://mucollective.northwestern.edu/project/vis-rhetoric
- Kosara, Mackinlay. Storytelling: the next step for visualization. IEEE Computer 2013. [not re-fetched]
- Cleveland, McGill. Graphical perception. JASA 1984; Mackinlay. APT. ACM TOG 1986.
- Borkin et al. What makes a visualization memorable? InfoVis 2013. https://vcg.seas.harvard.edu/publications/20130101-what-makes-a-visualization-memorable
- Lee, West, Howe. Viziometrics. https://arxiv.org/abs/1605.04951
- Rougier, Droettboom, Bourne. Ten simple rules for better figures. PLOS CB 2014. https://pmc.ncbi.nlm.nih.gov/articles/PMC4161295
- Tufte. The Visual Display of Quantitative Information. 2nd ed., 2001.
- SciCap: https://github.com/tingyaohsu/SciCap , https://arxiv.org/pdf/2110.11624 , https://huggingface.co/datasets/CrowdAILab/scicap
- ACL-Fig: https://arxiv.org/abs/2301.12293 , https://huggingface.co/datasets/citeseerx/ACL-fig
- DocFigure: https://cvit.iiit.ac.in/usodi/Docfig.php
- FigureSeer: https://prior.allenai.org/projects/figureseer
- FigureQA: https://www.microsoft.com/en-us/research/project/figureqa-dataset/ ; ChartQA: https://github.com/vis-nlp/ChartQA , https://arxiv.org/abs/2203.10244
- SciGraphQA: https://arxiv.org/abs/2308.03349 ; Multimodal ArXiv: https://mm-arxiv.github.io , https://arxiv.org/html/2403.00231v2
- MMC: https://huggingface.co/datasets/xywang1/MMC ; CharXiv: https://arxiv.org/abs/2406.18521 , https://huggingface.co/datasets/princeton-nlp/CharXiv
- Paper2Fig100k: https://zenodo.org/record/7299423
- ChartMimic: https://arxiv.org/html/2406.09961v2 ; Plot2Code: https://arxiv.org/abs/2405.07990 ; ChartCoder: https://arxiv.org/html/2501.06598v2 , https://huggingface.co/datasets/xxxllz/Chart2Code-160k
- pdffigures2: https://index.scala-lang.org/allenai/pdffigures2/artifacts/pdffigures2 ; deepfigures: https://github.com/allenai/deepfigures-open/ , https://arxiv.org/abs/1804.02445
- Draco: https://idl.uw.edu/papers/draco , Draco 2: https://arxiv.org/pdf/2308.14247 ; VizML: https://arxiv.org/abs/1808.04819
- LIDA: https://arxiv.org/abs/2303.02927 ; Data Formulator: https://www.microsoft.com/en-us/research/publication/data-formulator-ai-powered-concept-driven-visualization-authoring/
- FT Visual Vocabulary: https://github.com/Financial-Times/chart-doctor/blob/main/visual-vocabulary/README.md ; From Data to Viz: https://www.data-to-viz.com/
