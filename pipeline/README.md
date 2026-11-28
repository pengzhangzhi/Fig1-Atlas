# Build pipeline

Python stages; each writes to a cache directory (`$FIG1_CACHE`, default `/work/zp70/fig1-atlas-cache`) and
is resumable, so a failure in one stage doesn't restart the build. Needs `pymupdf pillow requests`
(+ `huggingface_hub` for upload, `anthropic` for the API annotator).

| stage | script | what it does |
|---|---|---|
| 1 | `s1_collect.py <venue>` | accepted papers from the conference virtual-site export (`venues/<venue>.json`): title, authors, tier, track, OpenReview id. Dedupes oral re-listings. |
| 2a | `s2a_harvest_arxiv.py --set cs` | one-time bulk harvest of arXiv metadata (title, authors, abstract, **license**) over OAI-PMH |
| 2 | `s2_match.py <key> [--api]` | title match against the harvest (then arXiv search API), author check; no match → abstract from the virtual site |
| 2b | `s2b_proceedings.py <key>` | official proceedings (PMLR for ICML, proceedings.iclr.cc, proceedings.neurips.cc): camera-ready PDF for papers not on arXiv |
| 2c | `s2c_rematch.py <key> [--openalex]` | papers renamed between arXiv and camera-ready: same authors + similar abstract (word Jaccard ≥ 0.43) in the harvest; optional OpenAlex search (free tier ≈ 100 searches/day). Later stages overlay `rematch_<key>.jsonl` via `common.load_matched` |
| 3 | `s3_extract.py <key>` | download arXiv PDF + LaTeX source; caption verbatim from the first figure environment; image = crop of the compiled PDF above the matching caption, 1600 px PNG + 480 px WebP |
| 4 | `s4_annotate.py <key> --backend claude-api\|claude-cli\|openai` | VLM returns role, claim, layout, tags, style, description as strict JSON |
| 5 | `s5_qc.py <key>` | flags tiny / page-sized crops, missing captions, low role confidence, not-a-figure, bad crops; writes a 50-paper spot-check list |
| 6 | `s6_license.py <key>` | CC-BY/BY-SA/CC0/BY-NC/BY-NC-SA → image hosted; everything else text-only |
| 7 | `s7_publish.py <keys…> [--upload]` | writes `data/index.jsonl`, `data/papers/<id>/meta.json`, `data/missing.jsonl`; pushes images to HF |

The website is built from `data/` by `scripts/build_site.py` in the Pages workflow.

## Notes
* **Why the virtual-site export, not the OpenReview API:** OpenReview challenges non-browser clients from many
  networks (including the build machine), while `https://<conf>.cc/static/virtual/data/<conf>-2026-orals-posters.json`
  lists every accepted paper. Adding a venue = one JSON in `venues/`.
* **Why the PDF crop for every image:** it handles TikZ, vector PDFs, EPS and multi-file subfigures with one code path.
  The LaTeX source supplies the verbatim caption and identifies which caption block is Figure 1.
* **Papers without arXiv** fall back to the OpenReview PDF, which only downloads from networks OpenReview does not
  challenge; elsewhere they land in `data/missing.jsonl` with reason `no_pdf`.
* Be polite to arXiv: ≥3 s between requests (built in). Sources and PDFs are cached and never redistributed.

## Trial run (gate)
```bash
python s1_collect.py iclr2026
python s2_match.py iclr26 --ids trial_ids.txt --api
python s3_extract.py iclr26 --ids trial_ids.txt
python s4_annotate.py iclr26 --ids trial_ids.txt --backend claude-cli
python s5_qc.py iclr26 && python s6_license.py iclr26 && python s7_publish.py iclr26 --upload
```
