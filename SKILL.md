---
name: fig1-atlas
description: Find Figure 1 templates for an ML paper being written. Searches a library of Figure 1s from accepted ICLR, ICML and NeurIPS 2026 papers by what the figure argues (its rhetorical role) rather than by topic, then proposes 3-5 concrete layouts mapped onto the user's content. Use when the user asks to design, sketch, plan or find inspiration/templates for a Figure 1, teaser figure, or overview/method figure of a paper.
---

# Fig1 Atlas: find Figure 1 templates

Each Figure 1 in the library is annotated with its **role** (what kind of argument it makes),
a one-sentence **claim**, its **layout**, **tags**, **style** and an 80-150 word written **description**.
Retrieve by role first, topic second: a one-step discrete generation paper should see consistency-model
and distillation Figure 1s ("many steps → one step"), not just other discrete diffusion papers.

All commands run from the repo root, need only Python 3 (standard library), and no API keys.
If the repo is not cloned, the scripts fall back to the website data automatically.

## Workflow

1. **Decide what Figure 1 must argue.** Read the user's draft, method or idea. Write two lines:
   (a) the single claim Figure 1 must make, (b) one or two candidate roles from the table below.
   Also pick 2-5 *argument-level* tags (e.g. `one-step`, `distillation`, `efficiency`, `unification`,
   `failure-mode`, `scaling`) plus at most 1-2 topic tags.

2. **Search.**
   ```bash
   python scripts/search.py --role prior-vs-ours,concept --tags one-step,distillation,discrete --limit 30
   ```
   One line per hit: `id | venue tier | role | title | claim`. Run 2-3 searches with different
   role/tag combinations rather than one big one. `--q "free text"` adds keyword matching;
   `--hosted` keeps only papers with downloadable images; `--roles` lists roles with counts.

3. **Read the shortlist.** `python scripts/show.py <id> <id> ...` prints description, caption, layout and
   links. Read them and cut to about 8 candidates whose *argument and layout* would fit the user's claim.

4. **Look at the figures.** `python scripts/fetch_fig.py <8 ids>` downloads hosted images to
   `fig1_atlas_figs/`; view them. Papers marked `[text-only]` have no hosted image (license): open the arXiv
   link if you can browse (the figure page is printed), otherwise judge from the description.

5. **Return 3-5 templates.** For each:
   - paper title, venue, link (arXiv or OpenReview), and the image path if fetched
   - why it fits: which argument it makes and why that is the user's argument too
   - a mapping sketch: what goes in each panel/region for the user's paper (concrete labels, arrows, plots)
   End with **one recommended pick** and why. Optionally offer a rough ASCII/TikZ sketch of the recommended layout.

## Roles

| role | the figure argues… |
|---|---|
| `pipeline` | here is how our method works, step by step |
| `prior-vs-ours` | existing approaches do X; we do Y |
| `before-after` | input or baseline output vs. our output |
| `teaser-result` | look at this headline result or sample quality |
| `problem-setup` | here is the task or failure mode we address |
| `concept` | here is the intuition, as a cartoon or geometric picture |
| `overview-framework` | here are the parts of a system or benchmark and how they fit |
| `analysis-finding` | we found this phenomenon (empirical paper) |

Definitions, disambiguation rules and example ids: [references/roles.md](references/roles.md).

## Tips
- Role choice matters most. Method papers whose novelty is a *contrast* with prior work → try `prior-vs-ours`
  and `concept`, not only `pipeline`. Benchmarks → `overview-framework` or `problem-setup`.
- Tags are free-form lowercase hyphenated words; partial word matches count, so `one-step` also hits `one-step-generation`.
- Images are hosted only for openly licensed papers. Always cite the source paper when adapting a layout.
