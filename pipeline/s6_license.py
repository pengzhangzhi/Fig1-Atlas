"""Stage 6: image-hosting policy from the arXiv license.

  CC-BY, CC-BY-SA, CC0          -> full image + thumbnail hosted, attribution on the paper page
  CC-BY-NC, CC-BY-NC-SA         -> hosted, non-commercial terms noted (project stays non-commercial)
  *-ND (no-derivatives)         -> not hosted by default (a crop may count as an adaptation);
                                   pass --host-nd to change
  arXiv default / unknown / none-> no hosted image; text entry + links only
"""
import argparse
from common import CACHE, read_jsonl, write_jsonl

def short(lic):
    if not lic:
        return "none"
    l = lic.lower()
    if "publicdomain/zero" in l:
        return "cc0"
    if "creativecommons.org/licenses/" in l:
        kind = l.split("/licenses/")[1].split("/")[0]       # by, by-sa, by-nc-nd, ...
        return "cc-" + kind
    if "arxiv.org/licenses/nonexclusive" in l:
        return "arxiv"
    return "other"


def hosted(code, host_nd=False):
    if code in ("cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"):
        return True
    return host_nd and code in ("cc-by-nd", "cc-by-nc-nd")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("key"); ap.add_argument("--host-nd", action="store_true")
    a = ap.parse_args()
    rows = []
    for m in read_jsonl(CACHE / "work" / f"matched_{a.key}.jsonl"):
        code = short(m.get("license"))
        rows.append({"id": m["id"], "license": m.get("license"), "img": code, "host": hosted(code, a.host_nd)})
    write_jsonl(CACHE / "work" / f"license_{a.key}.jsonl", rows)
    from collections import Counter
    print(Counter(r["img"] for r in rows), "hosted:", sum(r["host"] for r in rows))


if __name__ == "__main__":
    main()
