"""One-off: for records whose published caption would still contain LaTeX, read the whole caption from the PDF
(the stored caption_pdf can be just the first text block) and save it as caption_pdf_full."""
import re, sys, shutil
import fitz
from common import CACHE, read_jsonl, write_jsonl, load_matched, final_caption
from s3_extract import full_caption_text, clean_caption

for key in sys.argv[1:]:
    path = CACHE / "work" / f"extracted_{key}.jsonl"
    rows = read_jsonl(path); papers = {p["id"]: p for p in load_matched(key)}
    n = fixed = 0
    for e in rows:
        if e.get("status") != "ok" or not e.get("caption_pdf") or e.get("caption_source") == "pdf":
            continue
        cap, src = final_caption(e)
        if src == "pdf" or not re.search(r"[\\${}]", cap or ""):
            continue
        n += 1
        p = papers.get(e["id"], {}); aid = e.get("arxiv_id") or p.get("arxiv_id")
        cands = [CACHE / "pdf" / f"{aid}.pdf"] if aid else [CACHE / "pdf" / f"proc-{e['id']}.pdf", CACHE / "pdf" / f"or-{p.get('openreview_id')}.pdf"]
        pdf = next((c for c in cands if c.exists()), None)
        if not pdf:
            continue
        try:
            doc = fitz.open(pdf)
            full = full_caption_text(doc[e["page"]], e["caption_pdf"], len(clean_caption(e.get("caption_latex")) or ""))
        except Exception:
            continue
        if full != e["caption_pdf"]:
            e["caption_pdf_full"] = full
            if final_caption(e)[1] == "pdf":
                fixed += 1
            else:
                del e["caption_pdf_full"]
    shutil.copy(path, str(path) + ".before_capfix")
    write_jsonl(path, rows)
    print(key, "with residue", n, "fixed from PDF", fixed)
