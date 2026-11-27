#!/usr/bin/env python3
"""Download Figure 1 images for shortlisted papers (only papers with openly licensed, hosted images).

  python scripts/fetch_fig.py iclr26-0412 neurips26-2401 --out fig1_atlas_figs [--thumb]
Prints the local path per id, or why there is no image (then judge from the description, or open the arXiv link).
"""
import argparse, urllib.request
from pathlib import Path
from _data import load_meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--out", default="fig1_atlas_figs")
    ap.add_argument("--thumb", action="store_true", help="480px WebP thumbnails instead of 1600px PNG")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for pid in a.ids:
        try:
            m = load_meta(pid)
        except Exception as e:
            print(f"{pid}: not found ({e})"); continue
        url = m.get("thumb_url" if a.thumb else "image_url")
        if not url:
            print(f"{pid}: no hosted image (license: {m.get('img')}); see {m['links'].get('arxiv') or m['links']['pdf']} "
                  f"(Figure 1 on page {(m.get('figure_page') or 0) + 1})"); continue
        dest = out / (pid + (".webp" if a.thumb else ".png"))
        if not dest.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "fig1-atlas-skill"})
            with urllib.request.urlopen(req, timeout=120) as r:
                dest.write_bytes(r.read())
        print(f"{pid}: {dest}")


if __name__ == "__main__":
    main()
