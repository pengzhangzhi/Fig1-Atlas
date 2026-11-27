"""Stage 1: collect accepted papers for a venue.

Source: the conference "miniconf" virtual-site export (one JSON per venue). It lists every
accepted paper with title, authors, decision and OpenReview forum link. (The OpenReview API
works too, but it challenges non-browser clients from many networks.)
Adding a venue = adding pipeline/venues/<name>.json.
Output: CACHE/work/papers_<key>.jsonl
"""
import argparse, ast, json, re
import requests
from common import CACHE, UA, write_jsonl, REPO


SKIP_TRACKS = {"BlogPosts"}  # blog posts have no paper PDF / Figure 1


def tier_of(decision, eventtype):
    if (eventtype or "").lower() == "oral":   # an oral slot beats the decision string
        return "oral"
    d = (decision or "").lower()
    for t in ("oral", "spotlight"):
        if t in d:
            return t
    if (eventtype or "").lower() == "oral":
        return "oral"
    return "poster"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("venue", help="venue config name, e.g. iclr2026")
    a = ap.parse_args()
    cfg = json.load(open(REPO / "pipeline" / "venues" / f"{a.venue}.json"))
    raw_p = CACHE / "raw" / f"{a.venue}.json"
    if not raw_p.exists():
        r = requests.get(cfg["url"], headers={"User-Agent": UA}, timeout=300); r.raise_for_status()
        raw_p.write_bytes(r.content)
    res = json.load(open(raw_p))["results"]
    rank = {"oral": 0, "spotlight": 1, "poster": 2}
    papers = {}
    for e in res:
        m = re.search(r"forum\?id=([\w-]+)", e.get("paper_url") or "")
        if not m:
            continue
        orid = m.group(1)
        au = e.get("authors") or []
        if isinstance(au, str):
            try:
                au = ast.literal_eval(au)
            except Exception:
                au = []
        auth = [x["fullname"] for x in au if isinstance(x, dict)]
        track = (e.get("sourceurl") or "").split("/")[-1].replace("group?id=", "")
        if track in SKIP_TRACKS:
            continue
        p = {"openreview_id": orid, "title": " ".join(e["name"].split()), "authors": auth,
             "venue": cfg["venue"], "tier": tier_of(e.get("decision"), e.get("eventtype")),
             "track": track if track and track != "Conference" else "main",
             "topic": e.get("topic") if e.get("topic") not in (None, "None") else None,
             "virtual_url": cfg["site"] + e["virtualsite_url"] if e.get("virtualsite_url") else None,
             "code_url": e.get("url") if (e.get("url") or "None") != "None" else None}
        old = papers.get(orid)
        if old is None or rank[p["tier"]] < rank[old["tier"]]:
            papers[orid] = p
    # ids: <venue>-<4-digit seq> over the final accepted list sorted by OpenReview id (stable;
    # avoids case-only differences that break case-insensitive filesystems)
    rows = sorted(papers.values(), key=lambda p: p["openreview_id"])
    for i, p in enumerate(rows, 1):
        p["id"] = f"{cfg['key']}-{i:04d}"
    rows = [{"id": p.pop("id"), **p} for p in rows]
    out = CACHE / "work" / f"papers_{cfg['key']}.jsonl"
    write_jsonl(out, rows)
    from collections import Counter
    print(out, len(rows), Counter(p["tier"] for p in rows), Counter(p["track"] for p in rows).most_common(4))


if __name__ == "__main__":
    main()
