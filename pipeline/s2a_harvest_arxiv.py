"""Stage 2a: bulk-harvest arXiv cs/stat metadata (title, authors, abstract, license) via OAI-PMH.

One-time, resumable. Writes CACHE/arxiv_oai/<set>.jsonl. Much politer and faster than
~20k title searches against the arXiv API.
"""
import argparse, json, time, xml.etree.ElementTree as ET
import requests
from common import CACHE, UA, polite_get

OAI = "https://oaipmh.arxiv.org/oai"
NS = {"o": "http://www.openarchives.org/OAI/2.0/", "a": "http://arxiv.org/OAI/arXiv/"}


def parse(xml_text):
    root = ET.fromstring(xml_text)
    out = []
    for rec in root.iterfind(".//o:record", NS):
        m = rec.find(".//a:arXiv", NS)
        if m is None:
            continue
        g = lambda k: (m.findtext(f"a:{k}", default="", namespaces=NS) or "").strip()
        authors = []
        for a in m.iterfind("a:authors/a:author", NS):
            authors.append(" ".join(x for x in [a.findtext("a:forenames", "", NS), a.findtext("a:keyname", "", NS)] if x).strip())
        out.append({"arxiv_id": g("id"), "title": " ".join(g("title").split()), "authors": authors,
                    "abstract": " ".join(g("abstract").split()), "license": g("license") or None,
                    "created": g("created"), "categories": g("categories")})
    tok = root.find(".//o:resumptionToken", NS)
    return out, (tok.text if tok is not None and tok.text else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="cs")
    ap.add_argument("--from", dest="frm", default="2024-03-01")
    a = ap.parse_args()
    out_p = CACHE / "arxiv_oai" / f"{a.set}.jsonl"
    state_p = CACHE / "arxiv_oai" / f"{a.set}.state"
    s = requests.Session(); s.headers["User-Agent"] = UA
    tok = state_p.read_text().strip() if state_p.exists() else None
    if tok == "DONE":
        print("already done"); return
    n = 0
    while True:
        url = f"{OAI}?verb=ListRecords&resumptionToken={tok}" if tok else \
              f"{OAI}?verb=ListRecords&metadataPrefix=arXiv&set={a.set}&from={a.frm}"
        r = polite_get(s, url, tries=10)
        if r is None:
            raise SystemExit("harvest failed; re-run to resume")
        recs, tok = parse(r.text)
        with open(out_p, "a") as f:
            for x in recs:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        n += len(recs)
        state_p.write_text(tok or "DONE")
        print(f"{a.set}: +{len(recs)} total {n} token={'yes' if tok else 'END'}", flush=True)
        if not tok:
            break
        time.sleep(3)


if __name__ == "__main__":
    main()
