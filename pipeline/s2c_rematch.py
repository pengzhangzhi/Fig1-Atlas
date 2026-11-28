"""Stage 2c: find arXiv versions the title matcher missed (papers renamed between arXiv and camera-ready).

1. Local: same authors + similar abstract in the OAI harvest (no network).
2. OpenAlex (--openalex): search by title / abstract opening, accept a work that has an arXiv location
   and shares authors + abstract with ours.
Writes CACHE/work/rematch_<key>.jsonl {id, arxiv_id, license, how, score}; later stages overlay it via
common.load_matched().
"""
import argparse, json, re, time, unicodedata
from common import CACHE, UA, read_jsonl, write_jsonl, polite_get

STOP = set("a an the of for and in on to with via from by is are we our this that as at be or its it can which these into".split())


def full_name(n):
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    w = re.sub(r"[^a-z ]", " ", n).split()
    return (w[0][0] + " " + w[-1]) if len(w) >= 2 else (w[0] if w else "")


def words(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return {w for w in re.findall(r"[a-z][a-z0-9]+", t) if w not in STOP and len(w) > 2}


def jacc(a, b):
    return len(a & b) / max(1, len(a | b))


def prep(p):
    if "_a" not in p:
        p["_a"] = {full_name(x) for x in p["authors"]} - {""}
        p["_w"] = words(p.get("abstract")); p["_t"] = words(p["title"])
    return p


def accept(p, cand_authors, cand_abs, cand_title, theirs=None):
    prep(p)
    theirs = theirs if theirs is not None else {full_name(x) for x in cand_authors} - {""}
    if len(p["_a"] & theirs) < (1 if len(p["_a"]) <= 2 else 2):
        return 0
    a = jacc(p["_w"], words(cand_abs) if isinstance(cand_abs, str) or cand_abs is None else cand_abs)
    t = jacc(p["_t"], words(cand_title))
    sc = max(a, 0.8 * t) if (a >= 0.35 or (t >= 0.5 and a >= 0.2)) else 0
    return sc if sc >= 0.43 else 0       # eyeballed on NeurIPS: below ~0.43, often an earlier paper by the same group


def local_pass(todo):
    by_author = {}
    for p in todo:
        for x in prep(p)["_a"]:
            by_author.setdefault(x, []).append(p)
    best = {}
    for f in sorted((CACHE / "arxiv_oai").glob("*.jsonl")):
        with open(f) as fh:
            for l in fh:
                if l[14:16] < "24":               # '{"arxiv_id": "YYMM...': pre-2024 can't be a 2026 paper
                    continue
                r = json.loads(l)
                theirs = {full_name(x) for x in r["authors"]} - {""}
                cands = {p["id"]: p for x in theirs for p in by_author.get(x, ())}
                cands = [p for p in cands.values() if len(p["_a"] & theirs) >= (1 if len(p["_a"]) <= 2 else 2)]
                if not cands:
                    continue
                cw = words(r.get("abstract"))
                for p in cands:
                    sc = accept(p, None, cw, r["title"], theirs)
                    if sc and sc > best.get(p["id"], (0,))[0]:
                        best[p["id"]] = (sc, r)
    return {pid: {"id": pid, "arxiv_id": r["arxiv_id"], "license": r.get("license"), "arxiv_title": r["title"],
                  "how": "local-author-abstract", "score": round(sc, 3)} for pid, (sc, r) in best.items()}


def oa_abstract(inv):
    if not inv:
        return ""
    pos = sorted((i, w) for w, ii in inv.items() for i in ii)
    return " ".join(w for _, w in pos)


def oa_arxiv(work):
    for loc in work.get("locations") or []:
        u = (loc.get("landing_page_url") or "") + " " + (loc.get("pdf_url") or "")
        m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", u)
        if m:
            return m.group(1)
    d = (work.get("ids") or {}).get("doi") or work.get("doi") or ""
    m = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5})", d.lower())
    return m.group(1) if m else None


def openalex_pass(todo, s, oai_license):
    out = {}
    for i, p in enumerate(todo):
        queries = [("title.search", re.sub(r"[^\w\s-]", " ", p["title"])[:200])]
        ab = " ".join((p.get("abstract") or "").split()[:30])
        if ab:
            queries.append(("abstract.search", re.sub(r"[^\w\s-]", " ", ab)))
        for field, q in queries:
            r = polite_get(s, "https://api.openalex.org/works", params={
                "filter": f"{field}:{q},from_publication_date:2024-01-01", "per_page": 10,
                "select": "id,title,doi,ids,locations,authorships,abstract_inverted_index"})
            time.sleep(0.15)
            if r is None or r.status_code != 200:
                continue
            hit = None
            for w in r.json().get("results", []):
                aid = oa_arxiv(w)
                if not aid:
                    continue
                names = [a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")]
                sc = accept(p, names, oa_abstract(w.get("abstract_inverted_index")), w.get("title") or "")
                if sc:
                    hit = {"id": p["id"], "arxiv_id": aid, "license": oai_license.get(aid), "arxiv_title": w.get("title"),
                           "how": f"openalex-{field.split('.')[0]}", "score": round(sc, 3)}
                    break
            if hit:
                out[p["id"]] = hit
                break
        if (i + 1) % 100 == 0:
            print(f"  openalex {i+1}/{len(todo)}: {len(out)} found", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--openalex", action="store_true")
    a = ap.parse_args()
    rows = read_jsonl(CACHE / "work" / f"matched_{a.key}.jsonl")
    out_p = CACHE / "work" / f"rematch_{a.key}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_p)}
    todo = [r for r in rows if not r.get("arxiv_id") and r["id"] not in done]
    print(f"{a.key}: {len(todo)} papers without arXiv")
    found = local_pass(todo)
    print(f"  local author+abstract: {len(found)}")
    done.update(found)
    if a.openalex:
        lic = {}
        rest = [p for p in todo if p["id"] not in found]
        for f in sorted((CACHE / "arxiv_oai").glob("*.jsonl")):
            with open(f) as fh:
                for l in fh:
                    r = json.loads(l)
                    lic[r["arxiv_id"]] = r.get("license")
        import requests
        s = requests.Session(); s.headers["User-Agent"] = UA
        oa = openalex_pass(rest, s, lic)
        print(f"  openalex: {len(oa)}")
        done.update(oa)
    write_jsonl(out_p, sorted(({k: v for k, v in d.items() if not k.startswith("_")} for d in done.values()), key=lambda r: r["id"]))
    print(f"done: {len(done)} rematched")


if __name__ == "__main__":
    main()
