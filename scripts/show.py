#!/usr/bin/env python3
"""Print full metadata for shortlisted papers: description, caption, layout, links, image URL.

  python scripts/show.py iclr26-0412 neurips26-2401
  python scripts/show.py --json iclr26-0412          # raw meta.json
  python scripts/show.py --abstract iclr26-0412      # include the abstract
"""
import argparse, json, textwrap
from _data import load_meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--abstract", action="store_true")
    a = ap.parse_args()
    for pid in a.ids:
        try:
            m = load_meta(pid)
        except Exception as e:
            print(f"== {pid}: not found ({e})\n"); continue
        if a.json:
            print(json.dumps(m, ensure_ascii=False, indent=1)); continue
        w = lambda s: textwrap.fill(s or "", 110, initial_indent="  ", subsequent_indent="  ")
        L = m["links"]
        print(f"== {m['id']} | {m['venue']} {m['tier']} | {m['title']}")
        print(f"role: {m['role']}" + (f" (+{m['role2']})" if m.get("role2") else "") + f" | style: {', '.join(m['style'])} | tags: {', '.join(m['tags'])}")
        print(f"claim: {m['claim']}")
        print(f"layout: {m['layout']}")
        print("description:"); print(w(m["description"]))
        print("caption:"); print(w(m.get("caption")))
        if a.abstract:
            print("abstract:"); print(w(m.get("abstract")))
        print(f"links: arxiv={L.get('arxiv')} openreview={L.get('openreview')} pdf={L.get('pdf')}")
        print(f"image: {m['image_url'] or 'not hosted (license ' + str(m.get('img')) + '); open the arXiv/PDF link, Figure 1 is on page ' + str((m.get('figure_page') or 0) + 1)}")
        print()


if __name__ == "__main__":
    main()
