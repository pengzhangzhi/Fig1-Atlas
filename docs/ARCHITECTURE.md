# Architecture: Fig1 Atlas and the shared paper corpus

Fig1 Atlas is the first of four atlases built from one corpus of accepted ICLR, ICML and NeurIPS 2026 papers:

| Atlas | Unit | Repo |
|---|---|---|
| Fig1 Atlas | a paper's Figure 1 | [pengzhangzhi/Fig1-Atlas](https://github.com/pengzhangzhi/Fig1-Atlas) |
| StoryAtlas | a paper's scientific narrative | [pengzhangzhi/StoryAtlas](https://github.com/pengzhangzhi/StoryAtlas) |
| ExperimentAtlas | one experiment | [pengzhangzhi/ExperimentAtlas](https://github.com/pengzhangzhi/ExperimentAtlas) |
| PlotAtlas | one plot panel | [pengzhangzhi/PlotAtlas](https://github.com/pengzhangzhi/PlotAtlas) |

The corpus and the stages that read papers live here, in `pipeline/`. Each atlas repo contains only its own
publish step, website, skill and published data, and it refers to papers by the same ids (`iclr26-0001`).

## Data flow

```
s1_collect       accepted-paper lists from <conf>.cc virtual-site JSON              -> work/papers_<key>.jsonl
s2a/s2/s2c       arXiv match (OAI-PMH harvest, title + author match, renamed-paper rematch) -> matched_<key>.jsonl
s2b_proceedings  official proceedings PDFs (PMLR, proceedings.iclr.cc)               -> proc_<key>.jsonl
s3_extract       download PDF + LaTeX source once; find and crop Figure 1             -> pdf/, src/, figs/
s4_annotate      Figure 1 role, claim, layout, tags, description (vision model)       -> annotated_<key>.jsonl
s5_qc / s6_license / s7_publish  quality flags, license -> hosting, data/ + Hugging Face images

c1_parse         every paper once: sections, all figures (cropped), all tables         -> corpus/<id>.json, corpus_figs/<id>/
k1_read          one text call per paper: story + claims + experiments (StoryAtlas, ExperimentAtlas) -> knowledge/<id>.json
k2_plots         one vision call per paper: result figures by panel (PlotAtlas)        -> plots/<id>.json
```

Everything is cached under `$FIG1_ATLAS_CACHE` (on DCC: `/work/zp70/fig1-atlas-cache`); no stage re-downloads or
re-parses a paper another stage already handled.

## Paper identity and traceability

- **Paper id**: `<venue><yy>-<nnnn>` (e.g. `icml26-2016`), assigned in s1 from the venue's accepted list.
- **Artifact ids** extend it: `icml26-2016` (story), `icml26-2016/c2` (claim), `icml26-2016/e3` (experiment),
  `icml26-2016/f5a` (figure 5, panel a). Fig1 Atlas entries are the paper id.
- Every artifact points back to its location: section heading, figure or table number, page.
- **Source vs. interpretation.** Fields ending in `_quote` are verbatim from the paper and are checked by string
  match after extraction (`{"text", "verified"}`). Fields described as interpretation (templates, threats, arcs,
  critiques) are the model's and are shown as such on the sites. "not stated" is a valid value and the prompts
  forbid filling in missing details.

## Licensing

Text records (roles, claims, templates, descriptions) are written by the project. Images are hosted only for
papers whose arXiv license is CC BY, CC BY-SA, CC0, CC BY-NC or CC BY-NC-SA (s6). Quotes are short and attributed.

## Websites and skills

Each atlas is a static GitHub Pages site built from its `data/` by `scripts/build_site.py`, with the same visual
identity, plus an agent skill (`SKILL.md`, standard-library search scripts that fall back to the live site's
JSON when the repo is not cloned). See [SCHEMA.md](SCHEMA.md) for the records.
