# Figure 1 roles (v1)

A Figure 1 is classified by **what it argues**, not what it is about. Every figure gets exactly one
primary `role` (and optionally one `role2` when a figure clearly does two jobs). Use the role to
find templates that make the same *kind* of argument as your paper, across topics.

| role | The figure argues… | Typical look | Pick it for papers that… |
|---|---|---|---|
| `pipeline` | Here is how our method works, step by step | boxes and arrows left→right, stages, data flowing through modules | propose a method whose novelty is the procedure |
| `prior-vs-ours` | Existing approaches do X; we do Y | two or more side-by-side panels, "(a) prior / (b) ours", contrast colors, ✗ vs ✓ | improve on a known approach and need the reader to see the difference at a glance |
| `before-after` | Input or baseline output vs. our output | image/sample grids, input → output, baseline row vs. ours row | fix a visible failure (artifacts, hallucination, wrong answer) |
| `teaser-result` | Look at this headline result or sample quality | a big scatter / bar / Pareto plot with "ours" highlighted, or a gallery of samples | have one number or a gallery that sells the paper |
| `problem-setup` | Here is the task or failure mode we address | an illustrative example of the problem, a dialogue, an annotated failure case | introduce a new task, threat model or failure mode |
| `concept` | Here is the intuition, as a cartoon or geometric picture | abstract geometry, distributions, loss landscapes, toy 2-D sketches | have a theoretical or conceptual core idea |
| `overview-framework` | Here are the parts of a system or benchmark and how they fit | hub-and-spoke or grid of components, taxonomy trees, benchmark task mosaics | introduce a benchmark, dataset, survey/position or multi-part system |
| `analysis-finding` | We found this phenomenon | plots of an empirical trend, scaling curves, attention maps showing a surprise | are empirical/analysis papers whose contribution is an observation |

## Disambiguation rules
* Method diagram **with** a small "prior" inset → `pipeline` unless the contrast is the main visual weight.
* A results plot used to show *our* method winning → `teaser-result`; a plot used to show a *phenomenon* → `analysis-finding`.
* Benchmark/dataset papers → `overview-framework` unless the figure is a single example of the task (`problem-setup`).
* Cartoon of an idea with no concrete modules → `concept`; with concrete modules/data flow → `pipeline`.

## Layout vocabulary
`layout` is a short free-text phrase, e.g. "2 panels, left-to-right, math under arrows",
"3x4 image grid, rows = methods", "single scatter plot, ours highlighted top-left",
"top: pipeline strip; bottom: results bar chart".

## Style tags
`minimal`, `icon-heavy`, `math-heavy`, `photo/real data`, `plot`, `text-heavy`, `colorful`, `3d-render`, `screenshot`.

## Examples
Highest-confidence examples from the trial set (ICLR 2026). `python scripts/show.py <id>` for details.

* `pipeline`: `iclr26-0847` (Token-Based Audio Inpainting via Discrete Diffusion); `iclr26-4036` (FlexiCodec: A Dynamic Neural Audio Codec for Low Frame Rates); `iclr26-4565` (TangoFlux: Super Fast and Faithful Text to Audio Generation …)
* `prior-vs-ours`: `iclr26-0748` (Presenting a Paper is an Art: Self-Improvement Aesthetic Age…); `iclr26-0660` (ReDDiT: Rehashing Noise for Discrete Visual Generation); `iclr26-0996` (VITA: Vision-to-Action Flow Matching Policy)
* `before-after`: `iclr26-1810` (MotionWeaver: Holistic 4D-Anchored Framework for Multi-Human…); `iclr26-2284` (Free Lunch for Stabilizing Rectified Flow Inversion); `iclr26-2783` (VSF: Simple, Efficient, and Effective Negative Guidance in F…)
* `teaser-result`: `iclr26-0555` (One-Step Flow Q-Learning: Addressing the Diffusion Policy Bo…); `iclr26-4768` (Diffusion LLMs Can Do Faster-Than-AR Inference via Discrete …); `iclr26-0115` (SPG: Sandwiched Policy Gradient for Masked Diffusion Languag…)
* `problem-setup`: `iclr26-5152` (Meta-Adaptive Prompt Distillation for Few-Shot Visual Questi…); `iclr26-0765` (A Scalable Distributed Framework for Multimodal GigaVoxel Im…); `iclr26-1141` (Vision Language Models are Biased)
* `concept`: `iclr26-2934` (Entropic Confinement and Mode Connectivity in Overparameteri…); `iclr26-3992` (On the Design of One-step Diffusion via Shortcutting Flow Pa…); `iclr26-4968` (ADEPT: Continual Pretraining via Adaptive Expansion and Dyna…)
* `overview-framework`: `iclr26-4396` (NExT-OMNI: Towards Any-to-Any Omnimodal Foundation Models wi…); `iclr26-1545` (WARC-Bench: Web Archive based Benchmark for GUI Subtask Exec…); `iclr26-3627` (Spatial Reasoning with Vision-Language Models in Ego-Centric…)
* `analysis-finding`: `iclr26-2014` (CollectiveKV: Decoupling and Sharing Collaborative Informati…); `iclr26-3007` (Scale-wise Distillation of Diffusion Models); `iclr26-3461` (SparseD: Sparse Attention for Diffusion Language Models)
