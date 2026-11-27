#!/usr/bin/env python3
"""Filter the Fig1 Atlas index and print a compact shortlist (one line per hit: id | venue tier | role | title | claim).

Scoring: exact role match first (primary role 10, secondary role 6), then tag overlap (2 per tag,
partial-word matches 1), then keyword hits in title / claim / layout (1 each), plus a small boost for
oral (0.5) and spotlight (0.3) papers. Topic keywords are optional and weigh less than role.

Examples:
  python scripts/search.py --role prior-vs-ours --tags one-step,discrete --limit 30
  python scripts/search.py --role pipeline,concept --q "distillation teacher student"
  python scripts/search.py --role teaser-result --hosted --venue ICLR
  python scripts/search.py --roles        # list roles with counts
"""
import argparse, re, sys
from collections import Counter
from _data import load_index

ROLES = ["pipeline", "prior-vs-ours", "before-after", "teaser-result", "problem-setup",
         "concept", "overview-framework", "analysis-finding"]


def words(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--role", default="", help=f"comma-separated roles: {', '.join(ROLES)}")
    ap.add_argument("--tags", default="", help="comma-separated tags, e.g. one-step,distillation")
    ap.add_argument("--q", default="", help="free-text keywords matched against title, claim, layout")
    ap.add_argument("--venue", default="", help="substring filter, e.g. ICLR or 'NeurIPS 2026'")
    ap.add_argument("--tier", default="", help="comma-separated: oral,spotlight,poster")
    ap.add_argument("--hosted", action="store_true", help="only papers whose image is hosted")
    ap.add_argument("--require-role", action="store_true", help="drop hits that match no requested role")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--roles", action="store_true", help="print role counts and exit")
    a = ap.parse_args()
    idx = load_index()
    if a.roles:
        c = Counter(r["role"] for r in idx)
        for k in ROLES:
            print(f"{k:20s} {c.get(k, 0)}")
        print(f"{'total':20s} {len(idx)}"); return
    roles = [r.strip() for r in a.role.split(",") if r.strip()]
    bad = [r for r in roles if r not in ROLES]
    if bad:
        sys.exit(f"unknown role(s) {bad}; choose from {ROLES}")
    tags = [t.strip().lower() for t in a.tags.split(",") if t.strip()]
    tag_words = set().union(*[words(t) for t in tags]) if tags else set()
    q = words(a.q)
    tiers = {t.strip() for t in a.tier.split(",") if t.strip()}
    hits = []
    for r in idx:
        if a.venue and a.venue.lower() not in r["venue"].lower():
            continue
        if tiers and r["tier"] not in tiers:
            continue
        if a.hosted and r.get("img", "none") == "none":
            continue
        s = 0.0
        if roles:
            if r["role"] in roles:
                s += 10
            elif r.get("role2") in roles:
                s += 6
            elif a.require_role:
                continue
        rtags = [t.lower() for t in r.get("tags", [])]
        exact = len(set(tags) & set(rtags))
        s += 2 * exact
        if tag_words:
            s += len(tag_words & set().union(*[words(t) for t in rtags] or [set()]))  # partial word overlap
            s += 0.5 * len(tag_words & (words(r["title"]) | words(r["claim"])))
        if q:
            s += len(q & (words(r["title"]) | words(r["claim"]) | words(r.get("layout"))))
        s += {"oral": 0.5, "spotlight": 0.3}.get(r["tier"], 0)
        if s > 0.5 or not (roles or tags or q):
            hits.append((s, r))
    hits.sort(key=lambda t: -t[0])
    for s, r in hits[:a.limit]:
        role = r["role"] + (f"/{r['role2']}" if r.get("role2") else "")
        img = "" if r.get("img", "none") != "none" else " [text-only]"
        print(f"{r['id']} | {r['venue']} {r['tier']} | {role} | {r['title'][:90]} | {r['claim']}{img}")
    print(f"# {len(hits)} hits, showing {min(len(hits), a.limit)}", file=sys.stderr)


if __name__ == "__main__":
    main()
