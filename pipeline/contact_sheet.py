"""Render labeled contact sheets of extracted figures for the by-eye spot check.
  python contact_sheet.py ids.txt out_prefix [--per 12]
Writes out_prefix_<n>.png, 3 columns, each tile labeled with id + QC status."""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw
from common import CACHE, read_jsonl


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("ids"); ap.add_argument("out"); ap.add_argument("--per", type=int, default=12)
    ap.add_argument("--key", default="iclr26")
    a = ap.parse_args()
    ids = Path(a.ids).read_text().split()
    qc = {r["id"]: r["flags"] for r in read_jsonl(CACHE / "work" / f"qc_{a.key}.jsonl")}
    W, cols = 520, 3
    for s in range(0, len(ids), a.per):
        tiles = []
        for pid in ids[s:s + a.per]:
            p = CACHE / "figs" / f"{pid}.webp"
            im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (480, 120), "#ddd")
            im = im.resize((W - 20, max(1, round(im.height * (W - 20) / im.width))))
            if im.height > 600:
                im = im.crop((0, 0, im.width, 600))
            t = Image.new("RGB", (W, im.height + 34), "#888"); t.paste(im, (10, 28))
            ImageDraw.Draw(t).text((10, 8), f"{pid}  {','.join(qc.get(pid, [])) or 'ok'}", fill="white")
            tiles.append(t)
        rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
        H = sum(max(t.height for t in r) for r in rows)
        sheet = Image.new("RGB", (W * cols, H), "#555"); y = 0
        for r in rows:
            for j, t in enumerate(r):
                sheet.paste(t, (j * W, y))
            y += max(t.height for t in r)
        sheet.save(f"{a.out}_{s // a.per}.png")
        print(f"{a.out}_{s // a.per}.png")


if __name__ == "__main__":
    main()
