#!/usr/bin/env python3
"""Assemble the GitHub Pages site into _site/: static files from site/, plus index.json,
p/<id>.json and llms.txt generated from data/. Standard library only (runs in CI)."""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default=str(ROOT / "_site"))
ap.add_argument("--local-images", help="preview build: copy <id>.webp/.png from this dir and link them relatively")
A = ap.parse_args()
OUT = Path(A.out)
REPO_URL = "https://github.com/pengzhangzhi/Fig1-Atlas"
SITE_URL = "https://pengzhangzhi.github.io/Fig1-Atlas"

if OUT.exists():
    shutil.rmtree(OUT)
shutil.copytree(ROOT / "site", OUT)
(OUT / "p").mkdir()
recs = []
for line in open(ROOT / "data" / "index.jsonl"):
    r = json.loads(line)
    m = json.loads((ROOT / "data" / "papers" / r["id"] / "meta.json").read_text())
    if A.local_images and m["image_url"]:
        (OUT / "img").mkdir(exist_ok=True)
        for ext, key in ((".webp", "thumb_url"), (".png", "image_url")):
            src = Path(A.local_images) / f"{r['id']}{ext}"
            if src.exists():
                if ext == ".png":   # keep the preview small: re-encode the full image as WebP
                    from_ = src
                    dst = OUT / "img" / f"{r['id']}_full.webp"
                    try:
                        from PIL import Image
                        Image.open(from_).save(dst, quality=85)
                        m[key] = f"img/{dst.name}"
                    except ImportError:
                        shutil.copy(from_, OUT / "img" / from_.name); m[key] = f"img/{from_.name}"
                else:
                    shutil.copy(src, OUT / "img" / src.name); m[key] = f"img/{src.name}"
    (OUT / "p" / f"{r['id']}.json").write_text(json.dumps(m, ensure_ascii=False))
    recs.append({**r, "style": m["style"], "thumb_url": m["thumb_url"], "image_url": m["image_url"], "conf": m.get("role_confidence")})
(OUT / "index.json").write_text(json.dumps(recs, ensure_ascii=False, separators=(",", ":")))
(OUT / "llms.txt").write_text(f"""# Fig1 Atlas

> Figure 1s from accepted ICLR, ICML and NeurIPS 2026 papers, annotated by what each figure argues
> (role, one-sentence claim, layout, tags, style, written description). Use it to find Figure 1 templates
> for a paper being written. {len(recs)} figures.

Repo (preferred; contains SKILL.md and search scripts): {REPO_URL}
Index (all records, JSON array): {SITE_URL}/index.json
One paper's full metadata: {SITE_URL}/p/<id>.json
Role definitions: {REPO_URL}/blob/main/references/roles.md

## Workflow
1. Read the user's draft; write in two lines what Figure 1 must argue; pick 1-2 roles:
   pipeline, prior-vs-ours, before-after, teaser-result, problem-setup, concept, overview-framework, analysis-finding.
2. If you can run code, clone the repo and follow SKILL.md (scripts/search.py --role ... --tags ...).
   Otherwise fetch index.json and filter: exact role match first, then tag overlap, then title/claim keywords.
3. Fetch p/<id>.json for ~20 shortlisted ids; read description, caption, layout; cut to ~8.
4. Look at image_url where present (openly licensed papers only); otherwise use the description or the arXiv link.
5. Return 3-5 templates: paper + link, why it fits, a panel-by-panel mapping of the user's content; end with one recommended pick.
""")
(OUT / ".nojekyll").write_text("")
print(f"built {OUT} with {len(recs)} records")
