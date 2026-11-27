"""Stage 5: quality flags. A figure is flagged for review when the crop is tiny, the caption is
missing, the model's role confidence is low, the model says it is not a figure (e.g. a table) or
the crop looks wrong, or the crop covers most of a page.
Writes CACHE/work/qc_<key>.jsonl and prints a 50-per-venue random spot-check list.
"""
import argparse, random
from collections import Counter
from common import CACHE, read_jsonl, write_jsonl


def flags_for(e, a):
    f = []
    if e.get("status") != "ok":
        return [f"extract:{e.get('status')}"]
    w, h = e.get("crop_pt") or (0, 0)
    if w < 150 or h < 50:
        f.append("tiny-crop")
    if (e.get("page_frac") or 0) > 0.75:
        f.append("page-sized-crop")
    if not e.get("caption"):
        f.append("no-caption")
    if a is None or "error" in a:
        f.append("not-annotated")
        return f
    if (a.get("role_confidence") or 0) < 0.5:
        f.append("low-role-confidence")
    if a.get("is_figure") is False:
        f.append("not-a-figure")
    if a.get("crop_ok") is False:
        f.append("bad-crop")
    return f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("key"); ap.add_argument("--spot", type=int, default=50)
    a = ap.parse_args()
    ext = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"extracted_{a.key}.jsonl")}
    ann = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"annotated_{a.key}.jsonl")}
    rows = [{"id": i, "flags": flags_for(e, ann.get(i))} for i, e in sorted(ext.items())]
    write_jsonl(CACHE / "work" / f"qc_{a.key}.jsonl", rows)
    c = Counter(f for r in rows for f in r["flags"])
    print(f"{len(rows)} extracted; {sum(1 for r in rows if not r['flags'])} clean; flags: {dict(c)}")
    ok = [r["id"] for r in rows if ext[r["id"]].get("status") == "ok"]
    random.seed(0)
    spot = sorted(random.sample(ok, min(a.spot, len(ok))))
    (CACHE / "work" / f"spotcheck_{a.key}.txt").write_text("\n".join(spot) + "\n")
    print("spot-check list:", CACHE / "work" / f"spotcheck_{a.key}.txt")


if __name__ == "__main__":
    main()
