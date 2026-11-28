"""Corpus stage 1: parse each paper's PDF once into a shared, atlas-independent record.

Every atlas (Fig1, Story, Experiment, Plot) reads these records instead of re-opening PDFs.

  CACHE/corpus/<id>.json
    sections  [{h, page, text}]   main text in reading order, cut at References; appendix kept separately
    figures   [{n, page, caption, bbox, crop}]  every numbered figure, cropped with the Fig1 cropper
    tables    [{n, page, caption, text}]        every numbered table: caption and the text under it
  CACHE/corpus_figs/<id>/fig<n>.png|.webp       crops (hosting is decided later, per paper license)

Usage: python c1_parse.py <venue key> [--ids FILE] [--redo] [--workers N]
Reads only local PDFs (the ones s3 downloaded); no network.
"""
import argparse, json, re, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import fitz
from common import CACHE, read_jsonl, load_matched
from s3_extract import (text_blocks, body_font_size, figure_region, render, full_caption_text, SECTION_RE)

OUT = CACHE / "corpus"
FIGS = CACHE / "corpus_figs"
FIG_RE = re.compile(r"^\s*(?:Figure|Fig\.?|FIGURE|FIG\.)\s*(\d+)(?:\s*[:.|\-–—]\s*\S|\s+(?=[A-Z(]))")
TAB_RE = re.compile(r"^\s*(?:Table|TABLE|Tab\.)\s*(\d+)(?:\s*[:.|\-–—]\s*\S|\s+(?=[A-Z(]))")
SEP_RE = re.compile(r"^\s*\S+\.?\s*\d+\s*[:.|\-–—]")
HEAD_RE = re.compile(r"^\s*(?:[1-9]\d?(?:\.\d+){0,3}\.?|[A-H](?:\.\d+)*\.?)\s+[A-Z&]")
REFS_RE = re.compile(r"^\s*(?:\d+\s+)?(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$")
APPX_RE = re.compile(r"^\s*(?:Appendix|APPENDIX|Appendices|Supplementary Material)\b|^\s*A\s+[A-Z][A-Za-z]")
NAMED_HEAD = re.compile(r"^\s*(?:Abstract|ABSTRACT|Acknowledge?ments?|ACKNOWLEDGE?MENTS?|Impact Statement|Broader Impact|Limitations|Conclusions?)\s*$")


def pdf_path(p):
    aid = p.get("arxiv_id")
    cands = [CACHE / "pdf" / f"{aid}.pdf"] if aid else []
    cands += [CACHE / "pdf" / f"proc-{p['id']}.pdf", CACHE / "pdf" / f"or-{p.get('openreview_id')}.pdf"]
    return next((c for c in cands if c.exists() and c.stat().st_size > 1000), None)


def _bold_label(page, rect):
    """True if the first span of the block at rect is bold (caption labels are; body references are not)."""
    for b in page.get_text("dict", clip=rect)["blocks"]:
        for l in b.get("lines", []):
            for sp in l["spans"]:
                if sp["text"].strip():
                    return bool(sp["flags"] & 16) or "Bold" in sp["font"] or "Medi" in sp["font"]
    return False


def is_caption(page, b, t):
    return SEP_RE.match(t) is not None or _bold_label(page, b["rect"])


def parse(p, crops=True):
    pdf = pdf_path(p)
    if not pdf:
        return {"id": p["id"], "status": "no_pdf"}
    doc = fitz.open(pdf)
    npages = min(len(doc), 40)
    pages = [text_blocks(doc[i]) for i in range(npages)]
    body = body_font_size([b for bl in pages[:8] for b in bl])
    sections, figs, tabs = [], {}, {}
    cur = {"h": "Front matter", "page": 0, "text": []}
    part = "main"                      # main -> refs -> appendix
    appendix = []
    for pno in range(npages):
        page = doc[pno]; H = page.rect.height
        fig_boxes = []
        for b in pages[pno]:
            t = " ".join(b["text"].split())
            m = FIG_RE.match(t)
            if m and int(m.group(1)) not in figs and len(t) > 12 and is_caption(page, b, t):
                n = int(m.group(1))
                cap = full_caption_text(page, t)
                rec = {"n": n, "page": pno, "caption": re.sub(r"([a-z]{2})- ([a-z]{2})", r"\1\2", cap), "part": part}
                try:
                    reg = figure_region(page, b["rect"], pno, body)
                except Exception:
                    reg = None
                if reg is not None and reg.width > 40 and reg.height > 25:
                    rec["bbox"] = [round(v, 1) for v in reg]
                    fig_boxes.append(reg)
                    if crops:
                        d = FIGS / p["id"]; d.mkdir(parents=True, exist_ok=True)
                        try:
                            w, h = render(page, reg, d / f"fig{n}.png", d / f"fig{n}.webp")
                            rec["crop"] = [w, h]
                        except Exception:
                            pass
                figs[n] = rec
                continue
            m = TAB_RE.match(t)
            if m and int(m.group(1)) not in tabs and len(t) > 12 and is_caption(page, b, t):
                n = int(m.group(1))
                cap = full_caption_text(page, t)
                # table body: blocks directly below the caption (most templates put captions above tables)
                below = sorted([o for o in pages[pno] if o["rect"].y0 >= b["rect"].y1 - 2 and o["rect"].y0 < b["rect"].y1 + 260
                                and min(o["rect"].x1, b["rect"].x1 + 200) - max(o["rect"].x0, b["rect"].x0 - 200) > 0
                                and o["size"] < body + 0.2], key=lambda o: (o["rect"].y0, o["rect"].x0))
                txt = " | ".join(" ".join(o["text"].split()) for o in below[:60])
                tabs[n] = {"n": n, "page": pno, "caption": cap, "text": txt[:2500], "part": part}
        for b in pages[pno]:
            r, t = b["rect"], " ".join(b["text"].split())
            if r.y1 < H * 0.06 or r.y0 > H * 0.94 or ((FIG_RE.match(t) or TAB_RE.match(t)) and is_caption(page, b, t)):
                continue                                   # running header/footer, captions
            if any(fb.intersects(r) and (fb & r).get_area() > 0.6 * r.get_area() for fb in fig_boxes):
                continue                                   # text inside a figure
            if REFS_RE.match(t) and part == "main":
                sections.append(cur); part = "refs"; cur = None; continue
            if part == "refs":
                if b["n"] < 120 and APPX_RE.match(t) and b["size"] >= body - 0.3:
                    part = "appendix"; cur = {"h": t[:120], "page": pno, "text": []}
                continue
            is_head = b["n"] < 120 and (HEAD_RE.match(t) or NAMED_HEAD.match(t)) and b["size"] >= body - 1 and not t.endswith(".")
            if is_head:
                (sections if part == "main" else appendix).append(cur)
                cur = {"h": t[:120], "page": pno, "text": []}
            else:
                cur["text"].append(t)
    if cur:
        (sections if part == "main" else appendix).append(cur)
    fix = lambda ss: [{"h": s["h"], "page": s["page"], "text": re.sub(r"([a-z]{2})- ([a-z]{2})", r"\1\2", " ".join(s["text"]))}
                      for s in ss if s and (s["text"] or s["h"])]
    return {"id": p["id"], "status": "ok", "pdf": pdf.name, "pages": len(doc), "body_size": body,
            "sections": fix(sections), "appendix": fix(appendix),
            "figures": [figs[k] for k in sorted(figs)], "tables": [tabs[k] for k in sorted(tabs)]}


def work(args):
    p, crops = args
    try:
        r = parse(p, crops)
    except Exception as e:
        r = {"id": p["id"], "status": "error", "error": repr(e)[:300]}
    (OUT / f"{p['id']}.json").write_text(json.dumps(r, ensure_ascii=False))
    return p["id"], r["status"], len(r.get("figures", [])), len(r.get("tables", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+")
    ap.add_argument("--ids")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--no-crops", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    keep = set(Path(a.ids).read_text().split()) if a.ids else None
    rows = []
    for key in a.keys:
        proc = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"proc_{key}.jsonl")}
        rows += [{**r, "proc_pdf": proc.get(r["id"], {}).get("proc_pdf")} for r in load_matched(key)]
    rows = [r for r in rows if (keep is None or r["id"] in keep) and (a.redo or not (OUT / f"{r['id']}.json").exists())]
    from collections import Counter
    c = Counter()
    with ProcessPoolExecutor(a.workers) as pool:
        for i, (pid, st, nf, nt) in enumerate(pool.map(work, [(r, not a.no_crops) for r in rows], chunksize=4)):
            c[st] += 1
            if i % 200 == 0:
                print(i, len(rows), dict(c), flush=True)
    print("done", dict(c))


if __name__ == "__main__":
    main()
