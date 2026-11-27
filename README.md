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
