# Fig1 Atlas

> **AI agents: read [SKILL.md](SKILL.md) first.** It is the workflow for finding Figure 1 templates in this library.

An open library of Figure 1s from accepted **ICLR, ICML and NeurIPS 2026** papers, built so coding agents
(Claude Code, Codex, …) can find Figure 1 templates for a paper being written.

**Retrieve by what the figure argues, not by topic.** Every figure is annotated with its rhetorical
*role* (pipeline, prior-vs-ours, before-after, teaser-result, problem-setup, concept,
overview-framework, analysis-finding), the one-sentence *claim* it makes, its *layout*, tags, style and a
written description. There is no embedding search: an agent filters a compact text index with small scripts.

## Use it

**With an agent** — paste this into Claude Code / Codex together with your draft or idea:

> Clone https://github.com/pengzhangzhi/Fig1-Atlas, read its SKILL.md, and find Figure 1 templates for my paper.

**As a Claude Code skill** — copy or symlink this repo into your skills folder:
```bash
git clone https://github.com/pengzhangzhi/Fig1-Atlas ~/.claude/skills/fig1-atlas
```
Then ask "design my Figure 1".

**By hand**
```bash
python3 scripts/search.py --role prior-vs-ours --tags one-step,distillation --limit 20
python3 scripts/show.py <id> <id>
python3 scripts/fetch_fig.py <id> <id>
```

## Coverage (full run, 2026-11-28)

| venue | accepted | in the atlas | image hosted | missing: no PDF yet | missing: other |
|---|---:|---:|---:|---:|---:|
| ICLR 2026 | 5,353 | 5,177 | 2,596 | 2 | 174 |
| ICML 2026 | 6,554 | 6,237 | 3,143 | 0 | 317 |
| NeurIPS 2026 | 9,002 | 6,149 | 4,009 | 2,494 | 359 |
| **total** | **20,909** | **17,563** | **9,748** | **2,496** | **850** |

PDFs come from arXiv (including papers renamed since arXiv, matched by authors and abstract) and the official
ICLR and ICML proceedings. The 2,494 NeurIPS papers with no PDF are not on arXiv; they will be added when the
NeurIPS 2026 proceedings are published. "Other" means the PDF has no captioned Figure 1, or it could not be
cropped cleanly. `data/missing.jsonl` lists every missing paper with its reason.

Roles across the atlas: pipeline 4,376 · prior-vs-ours 3,035 · analysis-finding 2,821 · teaser-result 2,659 ·
concept 1,506 · problem-setup 1,428 · overview-framework 1,379 · before-after 359.

## What's inside

| path | what |
|---|---|
| `SKILL.md` | agent workflow |
| `references/roles.md` | role taxonomy, disambiguation rules, examples |
| `scripts/` | `search.py`, `show.py`, `fetch_fig.py` (stdlib only) |
| `data/index.jsonl` | one ~60-token line per paper: id, title, venue, tier, role, claim, layout, tags, img |
| `data/papers/<id>/meta.json` | abstract, caption, description, style, links, license, image URL |
| `data/missing.jsonl` | accepted papers without a usable Figure 1 yet, and why |
| `pipeline/` | the build pipeline (not needed by agents) |
| `site/` | website source (GitHub Pages) |

Images live in the Hugging Face dataset [`fredzzp/fig1-atlas`](https://huggingface.co/datasets/fredzzp/fig1-atlas).

## Licensing and takedown

Images are hosted only for papers whose arXiv version is CC-BY, CC-BY-SA, CC0, CC-BY-NC or CC-BY-NC-SA,
with attribution; NC images are non-commercial only, and this project is non-commercial. Every other paper gets a
text entry (project-written description, role, claim, a short quoted caption with attribution) and links.
**Authors** who want a figure removed, or want to opt a paper in, can open an issue — we act on it promptly.

## Build pipeline

See [pipeline/README.md](pipeline/README.md).
