---
name: fig1-atlas
description: Find Figure 1 templates for an ML paper being written. Searches a library of Figure 1s from accepted ICLR, ICML and NeurIPS 2026 papers by what the figure argues (its rhetorical role) rather than by topic, then proposes 3-5 concrete layouts mapped onto the user's content and drafts the one the user picks. Use when the user asks to design, sketch, plan or find inspiration/templates for a Figure 1, teaser figure, or overview/method figure of a paper.
---

# Fig1 Atlas: find Figure 1 templates

Each Figure 1 in the library is annotated with its **role** (what kind of argument it makes),
a one-sentence **claim**, its **layout**, **tags**, **style** and an 80-150 word written **description**.
Retrieve by role first, topic second: a one-step discrete generation paper should see consistency-model
and distillation Figure 1s ("many steps → one step"), not just other discrete diffusion papers.

All commands run from the repo root with `python3` (standard library only, no API keys).
If the repo is not cloned, the scripts fall back to the website data automatically.

## Workflow

1. **Decide what Figure 1 must argue.** Read the user's draft, method or idea. Write two lines:
   (a) the single claim Figure 1 must make, (b) one or two candidate roles from the table below.
   If the paper has several contributions (e.g. an objective, a benchmark and a decoding result), pick the one
   the title/abstract leads with for Figure 1; the others can become insets.
   Also list 3-5 tags: a few *argument-level* words (`one-step`, `distillation`, `efficiency`, `failure-mode`,
   `scaling`, `unification`) plus 1-2 *topic* words. `python3 scripts/search.py --list-tags <substr>` shows the
   real tag vocabulary (e.g. `--list-tags step` → one-step, few-step, few-step-generation, …).

2. **Search** — run these three kinds of query (each prints `id | venue tier | role | title | claim`):
   ```bash
   # a) role + topic: same argument, related subject (the main shortlist)
   python3 scripts/search.py --role prior-vs-ours,concept --tags one-step,distillation,discrete --limit 30
   # b) topic only: closest papers regardless of how their figure argues (catches role mislabels)
   python3 scripts/search.py --tags self-correction,remasking --q "remask wrong tokens" --limit 20
   # c) role only, cross-topic: the same kind of figure from any field (layout ideas)
   python3 scripts/search.py --role prior-vs-ours --role-only --hosted --limit 40
   ```
   With `--tags`/`--q` a paper must match at least one of them. `--hosted` keeps papers with downloadable
   images, `--venue`/`--tier` filter, `--roles` prints role and venue counts (check coverage first).

3. **Read the shortlist.** `python3 scripts/show.py <id> <id> ...` prints description, caption, layout and
   links. Cut to about 8 candidates whose *argument and layout* would fit the user's claim.

4. **Look at the figures.** `python3 scripts/fetch_fig.py <ids> [--out DIR]` downloads hosted images (default
   `<system temp>/fig1_atlas_figs/`, outside the repo) and prints each path; view them. Papers marked
   `[text-only]` have no hosted image (license): open the arXiv link if you can browse (the figure page is
   printed), otherwise judge from the description. Close prior work makes a weak template to copy: say so.

5. **Return 3-5 templates.** For each:
   - paper title, venue, link (arXiv or OpenReview), and the image path if fetched
   - why it fits: which argument it makes and why that is the user's argument too
   - a mapping sketch: what goes in each panel/region for the user's paper (concrete labels, arrows, plots)
   End with **one recommended pick** and why, with a rough ASCII sketch of that layout filled with the user's content.
   Then stop and let the user choose.

6. **Draft the figure once the user picks.** Build it in the format they work in (TikZ, matplotlib, SVG, or a
   slide; ask if the draft does not make it obvious) and keep it editable. Borrow the template's layout and
   argument, never its artwork, and tell the user which paper the layout came from so they can credit it.

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
