#!/usr/bin/env python3
"""Filter the Fig1 Atlas index and print a compact shortlist (one line per hit: id | venue tier | role | title | claim).

Scoring: role match (primary 4, secondary 2.5) + topic match (exact tag 3, shared tag word 1,
tag word in title/claim 0.5, --q keyword 1.5) + small oral/spotlight boost. When --tags/--q are given a
paper must match at least one of them, so the output is a filtered, ranked shortlist. Use --role-only
for a pure cross-topic browse of one role (same argument, any subject).

Examples:
  python scripts/search.py --role prior-vs-ours --tags one-step,discrete --limit 30
  python scripts/search.py --role pipeline,concept --q "distillation teacher student"
  python scripts/search.py --role teaser-result --hosted --venue ICLR
  python scripts/search.py --role prior-vs-ours --role-only --hosted --limit 40   # cross-topic browse
  python scripts/search.py --roles        # role + venue counts
  python scripts/search.py --list-tags step   # tag vocabulary containing "step"
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
    ap.add_argument("--tags", default="", help="comma-separated tags, e.g. one-step,distillation (see --list-tags)")
    ap.add_argument("--q", default="", help="free-text keywords matched against title, claim, layout, tags")
    ap.add_argument("--venue", default="", help="substring filter, e.g. ICLR or 'NeurIPS 2026'")
    ap.add_argument("--tier", default="", help="comma-separated: oral,spotlight,poster")
    ap.add_argument("--hosted", action="store_true", help="only papers whose image is hosted")
    ap.add_argument("--role-only", action="store_true",
                    help="cross-topic browse: rank by role alone, ignoring topic matches (use with --role)")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--roles", action="store_true", help="print role and venue counts and exit")
    ap.add_argument("--list-tags", nargs="?", const="", metavar="SUBSTR",
                    help="print the tag vocabulary with counts (optionally only tags containing SUBSTR) and exit")
    a = ap.parse_args()
    idx = load_index()
    if a.roles:
        c = Counter(r["role"] for r in idx)
        for k in ROLES:
            print(f"{k:20s} {c.get(k, 0)}")
        print(f"{'total':20s} {len(idx)}")
        for v, n in sorted(Counter(r["venue"] for r in idx).items()):
            print(f"venue: {v} ({n})")
        return
    if a.list_tags is not None:
        c = Counter(t for r in idx for t in r.get("tags", []) if a.list_tags.lower() in t)
        print(" ".join(f"{t}({n})" for t, n in c.most_common(300)))
        return
    roles = [r.strip() for r in a.role.split(",") if r.strip()]
    bad = [r for r in roles if r not in ROLES]
    if bad:
        sys.exit(f"unknown role(s) {bad}; choose from {ROLES}")
    venues = sorted({r["venue"] for r in idx})
    if a.venue and not any(a.venue.lower() in v.lower() for v in venues):
        sys.exit(f"no papers from venue '{a.venue}' in this index; available: {', '.join(venues)}")
    tags = [t.strip().lower() for t in a.tags.split(",") if t.strip()]
    tag_words = set().union(*[words(t) for t in tags]) if tags else set()
    q = words(a.q) - STOP
    tiers = {t.strip() for t in a.tier.split(",") if t.strip()}
    topic_query = bool(tags or q) and not a.role_only
    hits = []
    for r in idx:
        if a.venue and a.venue.lower() not in r["venue"].lower():
            continue
        if tiers and r["tier"] not in tiers:
            continue
        if a.hosted and r.get("img", "none") == "none":
            continue
        role_s = 0.0
        if roles:
            role_s = 4 if r["role"] in roles else 2.5 if r.get("role2") in roles else 0
            if role_s == 0 and a.role_only:
                continue
        rtags = [t.lower() for t in r.get("tags", [])]
        rtag_words = set().union(*[words(t) for t in rtags]) if rtags else set()
        text_words = words(r["title"]) | words(r["claim"]) | words(r.get("layout"))
        topic = 3 * len(set(tags) & set(rtags))                      # exact tag
        topic += 1 * len(tag_words & rtag_words)                     # tag word overlap
        topic += 0.5 * len(tag_words & text_words)
        topic += 1.5 * len(q & (text_words | rtag_words))
        if topic_query and topic == 0:
            continue                                                 # topic given: it must match something
        s = role_s + topic + {"oral": 0.5, "spotlight": 0.3}.get(r["tier"], 0)
        if roles and role_s == 0 and not topic_query:
            continue
        hits.append((s, r))
    hits.sort(key=lambda t: -t[0])
    print(f"# {len(hits)} hits of {len(idx)} papers ({', '.join(venues)}), showing {min(len(hits), a.limit)}")
    for s, r in hits[:a.limit]:
        role = r["role"] + (f"/{r['role2']}" if r.get("role2") else "")
        img = "" if r.get("img", "none") != "none" else " [text-only]"
        print(f"{r['id']} | {r['venue']} {r['tier']} | {role} | {r['title']} | {r['claim']}{img}")


STOP = set("a an the of for and or to in on with via by from is are we our".split())


if __name__ == "__main__":
    main()
