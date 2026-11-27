"""Stage 2: match each paper to arXiv (title, then author check); record arXiv id, license, abstract.

Lookup order:
  1. local OAI-PMH harvest (stage 2a) - exact normalized-title hit, then author check
  2. arXiv search API (--api) - title query, fuzzy title + author check, then OAI GetRecord for license
  3. no arXiv match -> abstract scraped from the conference virtual-site page; PDF falls back to OpenReview
Output: CACHE/work/matched_<key>.jsonl  (resumable: already-matched ids are skipped)
"""
import argparse, difflib, html, json, random, re, time, xml.etree.ElementTree as ET
from pathlib import Path
import requests
from common import CACHE, UA, read_jsonl, write_jsonl, norm_title, norm_name, polite_get

ATOM = {"a": "http://www.w3.org/2005/Atom"}
OAI_NS = {"o": "http://www.openarchives.org/OAI/2.0/", "x": "http://arxiv.org/OAI/arXiv/"}


def load_local_index():
    idx = {}
    for p in sorted((CACHE / "arxiv_oai").glob("*.jsonl")):
        with open(p) as f:
            for l in f:
                r = json.loads(l)
                idx.setdefault(norm_title(r["title"]), {})[r["arxiv_id"]] = r
    return idx


def author_ok(ours, theirs):
    if not ours or not theirs:
        return True
    a, b = {norm_name(x) for x in ours}, {norm_name(x) for x in theirs}
    a.discard(""); b.discard("")
    return len(a & b) >= 1


def oai_get(s, aid):
    r = polite_get(s, f"https://oaipmh.arxiv.org/oai?verb=GetRecord&identifier=oai:arXiv.org:{aid}&metadataPrefix=arXiv")
    time.sleep(3)
    if r is None or r.status_code != 200:
        return None
    m = ET.fromstring(r.text).find(".//x:arXiv", OAI_NS)
    if m is None:
        return None
    g = lambda k: " ".join((m.findtext(f"x:{k}", "", OAI_NS) or "").split())
    return {"arxiv_id": g("id"), "title": g("title"), "abstract": g("abstract"), "license": g("license") or None}


STOP = set("the and for that with from into via are can does how what when why which this its our not but you your all any over under than then toward towards using use more less only also".split())


def api_search(s, title):
    q = re.sub(r"[^A-Za-z0-9 ]+", " ", title)
    words = [w for w in q.split() if len(w) > 2 and w.lower() not in STOP][:12]
    q = " AND ".join(f"ti:{w}" for w in words)
    r = polite_get(s, "https://export.arxiv.org/api/query", params={"search_query": q, "max_results": 10})
    time.sleep(3)
    if r is None:
        return []
    out = []
    for e in ET.fromstring(r.text).iterfind("a:entry", ATOM):
        aid = e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1]
        aid = re.sub(r"v\d+$", "", aid)
        out.append({"arxiv_id": aid, "title": " ".join(e.findtext("a:title", "", ATOM).split()),
                    "authors": [a.findtext("a:name", "", ATOM) for a in e.iterfind("a:author", ATOM)]})
    return out


def scrape_abstract(s, url):
    if not url:
        return None
    r = polite_get(s, url, delay=1)
    if r is None or r.status_code != 200:
        return None
    m = re.search(r'class="abstract-text-inner">(.*?)</div>', r.text, re.S)
    if not m:
        return None
    t = re.sub(r"<[^>]+>", " ", m.group(1))
    return " ".join(html.unescape(t).split()) or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key", help="venue key, e.g. iclr26")
    ap.add_argument("--ids", help="file with one paper id per line (subset, e.g. the trial sample)")
    ap.add_argument("--api", action="store_true", help="use arXiv search API for papers not in the local harvest")
    a = ap.parse_args()
    papers = read_jsonl(CACHE / "work" / f"papers_{a.key}.jsonl")
    if a.ids:
        keep = set(Path(a.ids).read_text().split())
        papers = [p for p in papers if p["id"] in keep]
    out_p = CACHE / "work" / f"matched_{a.key}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_p)}
    idx = load_local_index()
    s = requests.Session(); s.headers["User-Agent"] = UA
    n_new = 0
    for i, p in enumerate(papers):
        if p["id"] in done and done[p["id"]].get("match_method") != "none":
            continue
        rec, method = None, "none"
        for cand in idx.get(norm_title(p["title"]), {}).values():
            if author_ok(p["authors"], cand["authors"]):
                rec, method = cand, "oai-title"; break
        if rec is None and a.api:
            best, score = None, 0
            for c in api_search(s, p["title"]):
                sc = difflib.SequenceMatcher(None, norm_title(p["title"]), norm_title(c["title"])).ratio()
                if sc > score and author_ok(p["authors"], c["authors"]):
                    best, score = c, sc
            if best and score >= 0.9:
                full = oai_get(s, best["arxiv_id"])
                if full:
                    rec, method = full, f"api-title({score:.2f})"
        row = dict(p)
        if rec:
            row.update(arxiv_id=rec["arxiv_id"], license=rec.get("license"), abstract=rec.get("abstract"),
                       abstract_source="arxiv", match_method=method)
        else:
            row.update(arxiv_id=None, license=None, abstract=scrape_abstract(s, p.get("virtual_url")),
                       abstract_source="virtual-site", match_method="none")
        done[p["id"]] = row; n_new += 1
        if n_new % 20 == 0:
            write_jsonl(out_p, sorted(done.values(), key=lambda r: r["id"]))
            print(f"[{i+1}/{len(papers)}] matched so far: {sum(1 for r in done.values() if r['arxiv_id'])}/{len(done)}", flush=True)
    write_jsonl(out_p, sorted(done.values(), key=lambda r: r["id"]))
    print(f"done: {sum(1 for r in done.values() if r['arxiv_id'])}/{len(done)} with arXiv")


if __name__ == "__main__":
    main()
