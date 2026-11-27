"""Stage 2b: map papers to their official proceedings page + PDF (camera-ready, openly downloadable).

  ICML -> PMLR volume (lists OpenReview ids: exact match)
  ICLR / NeurIPS -> proceedings.<conf>.cc (title match, exact then fuzzy)
Papers without an arXiv version are extracted from these PDFs (no OpenReview download needed).
Output: CACHE/work/proc_<key>.jsonl  {id, proc_page, proc_pdf}
"""
import argparse, difflib, html, json, re
import requests
from common import CACHE, UA, REPO, read_jsonl, write_jsonl, norm_title


def parse_pmlr(text):
    out = []
    for blk in text.split('<div class="paper">')[1:]:
        t = re.search(r'<p class="title">(.*?)</p>', blk, re.S)
        pdf = re.search(r'href="(https://[^"]+\.pdf)"', blk)
        page = re.search(r'href="(https://proceedings\.mlr\.press/[^"]+\.html)"', blk)
        orid = re.search(r'openreview\.net/forum\?id=([\w-]+)', blk)
        if t and pdf:
            out.append({"title": html.unescape(" ".join(re.sub("<[^>]+>", "", t.group(1)).split())),
                        "pdf": pdf.group(1), "page": page.group(1) if page else None,
                        "orid": orid.group(1) if orid else None})
    return out


def parse_cc(text, base):
    out = []
    for m in re.finditer(r'href="(/paper_files/paper/\d+/hash/([0-9a-f]+)-Abstract-(\w+)\.html)">(.*?)</a>', text, re.S):
        root = base.split("/paper_files")[0]
        out.append({"title": html.unescape(" ".join(re.sub("<[^>]+>", "", m.group(4)).split())),
                    "page": root + m.group(1),
                    "pdf": f"{root}/paper_files/paper/{m.group(1).split('/')[3]}/file/{m.group(2)}-Paper-{m.group(3)}.pdf",
                    "orid": None})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("venue", help="venue config name, e.g. icml2026")
    a = ap.parse_args()
    cfg = json.load(open(REPO / "pipeline" / "venues" / f"{a.venue}.json"))
    pc = cfg.get("proceedings")
    r = requests.get(pc["url"], headers={"User-Agent": UA}, timeout=300)
    if r.status_code != 200:
        raise SystemExit(f"proceedings not available yet: {pc['url']} -> {r.status_code}")
    entries = parse_pmlr(r.text) if pc["type"] == "pmlr" else parse_cc(r.text, pc["url"])
    print(len(entries), "proceedings entries")
    papers = read_jsonl(CACHE / "work" / f"papers_{cfg['key']}.jsonl")
    by_or = {e["orid"]: e for e in entries if e["orid"]}
    by_t = {norm_title(e["title"]): e for e in entries}
    buckets = {}
    for t, e in by_t.items():
        w = t.split()
        for k in (("h",) + tuple(w[:3]), ("t",) + tuple(w[-3:])):
            buckets.setdefault(k, []).append((t, e))
    rows, how = [], {"orid": 0, "title": 0, "fuzzy": 0, "none": 0}
    for p in papers:
        e = by_or.get(p["openreview_id"]); kind = "orid"
        if e is None:
            e = by_t.get(norm_title(p["title"])); kind = "title"
        if e is None:
            t = norm_title(p["title"]); w = t.split(); best, sc = None, 0
            for k in (("h",) + tuple(w[:3]), ("t",) + tuple(w[-3:])):
                for ct, ce in buckets.get(k, []):
                    s = difflib.SequenceMatcher(None, t, ct).ratio()
                    if s > sc:
                        best, sc = ce, s
            e, kind = (best, "fuzzy") if sc >= 0.88 else (None, "none")
        how[kind] += 1
        if e:
            rows.append({"id": p["id"], "proc_page": e["page"], "proc_pdf": e["pdf"]})
    write_jsonl(CACHE / "work" / f"proc_{cfg['key']}.jsonl", rows)
    print(cfg["key"], how)


if __name__ == "__main__":
    main()
