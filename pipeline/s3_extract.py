"""Stage 3: extract Figure 1 (image crop + verbatim caption).

For each matched paper:
  * download arXiv PDF + LaTeX source (cached; >=3 s between arXiv requests)
  * caption: first figure-like environment in the LaTeX source in document order (figure,
    figure*, wrapfigure, \\captionof{figure}, teaser blocks above the abstract); verbatim
    \\caption{} text, brace-matched
  * image: crop of the compiled PDF around the "Figure 1" caption. Rendering from the PDF
    handles TikZ, vector PDFs, EPS and multi-file subfigures uniformly.
  * fallback when there is no LaTeX: caption text read from the PDF
  * papers without an arXiv match use the OpenReview PDF (needs a network that OpenReview
    does not challenge; otherwise they are recorded as status=no_pdf)
Outputs CACHE/figs/<id>.png (1600 px wide), <id>.webp (480 px thumb) and
CACHE/work/extracted_<key>.jsonl
"""
import argparse, gzip, io, re, tarfile, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pymupdf as fitz
import requests
from PIL import Image
from common import CACHE, UA, read_jsonl, write_jsonl, polite_get

FIG_W, THUMB_W = 1600, 480
# label then punctuation ("Figure 1:", "Fig. 1.") or a bold-style label followed by a capital/paren ("Figure 1 Video-As-Prompt …")
CAP_RE = re.compile(r"^\s*(?:Figure|Fig\.?)\s*(?:1|I)(?:\s*[:.|\-–—]|\s+(?=[A-Z(\[]))")


# ---------------------------------------------------------------- downloads
import threading
_rate = {"last": 0.0, "gap": 1.0, "lock": threading.Lock()}


def _throttle():
    """Shared limiter: request *starts* are spaced >= gap seconds apart across all workers."""
    with _rate["lock"]:
        wait = _rate["gap"] - (time.time() - _rate["last"])
        if wait > 0:
            time.sleep(wait)
        _rate["last"] = time.time()


def arxiv_get(s, url, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    _throttle()
    r = polite_get(s, url)
    if r is None or r.status_code != 200:
        return None
    tmp = dest.with_suffix(dest.suffix + ".part")
    tmp.write_bytes(r.content); tmp.replace(dest)
    return dest


# ---------------------------------------------------------------- LaTeX side
def read_source(src: Path):
    """Return {relative_path: text} for .tex files in an arXiv e-print (tar.gz, gz or pdf)."""
    raw = src.read_bytes()
    files = {}
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
            for m in tf.getmembers():
                if m.isfile() and m.name.lower().endswith((".tex", ".ltx")) and m.size < 5_000_000:
                    files[m.name] = tf.extractfile(m).read().decode("utf-8", "replace")
        return files
    except tarfile.TarError:
        pass
    try:
        txt = gzip.decompress(raw).decode("utf-8", "replace")
        if "\\begin{document}" in txt or "\\documentclass" in txt:
            files["main.tex"] = txt
    except OSError:
        pass  # PDF-only submission
    return files


def strip_comments(t):
    return re.sub(r"(?<!\\)%.*", "", t)


def expand_inputs(text, files, depth=0):
    if depth > 6:
        return text
    def rep(m):
        name = m.group(2).strip()
        for cand in (name, name + ".tex"):
            for k in files:
                if k == cand or k.endswith("/" + cand) or k == "./" + cand:
                    return expand_inputs(strip_comments(files[k]), files, depth + 1)
        return ""
    return re.sub(r"\\(input|include|subfile)\s*\{([^}]+)\}", rep, text)


def find_main(files):
    cands = [k for k, v in files.items() if "\\begin{document}" in strip_comments(v)]
    if not cands:
        return None
    return max(cands, key=lambda k: len(files[k]))


def brace_arg(t, i):
    """t[i] is at/just before '{'; return (content, end_index)."""
    while i < len(t) and t[i] in " \t\n":
        i += 1
    if i < len(t) and t[i] == "[":           # optional short caption [..]
        d = 0
        while i < len(t):
            d += t[i] == "["; d -= t[i] == "]"; i += 1
            if d == 0:
                break
        while i < len(t) and t[i] in " \t\n":
            i += 1
    if i >= len(t) or t[i] != "{":
        return None, i
    d, j = 0, i
    while j < len(t):
        c = t[j]
        if c == "\\":
            j += 2; continue
        d += c == "{"; d -= c == "}"
        j += 1
        if d == 0:
            return t[i + 1:j - 1], j
    return None, j


FIG_ENV = re.compile(r"\\begin\{(figure\*?|wrapfigure|SCfigure\*?|teaserfigure)\}|\\captionof\{figure\}")


def latex_fig1(files):
    main = find_main(files)
    if not main:
        return None
    doc = expand_inputs(strip_comments(files[main]), files)
    pre, _, body = doc.partition("\\begin{document}")
    # teaser figures defined in the preamble via \teaser{...} / \twocolumn[...] land in body anyway
    m = FIG_ENV.search(body)
    if not m:
        return None
    if m.group(0).startswith("\\captionof"):
        cap, _ = brace_arg(body, m.end())
        env_text = body[max(0, m.start() - 1500):m.end() + len(cap or "") + 2]
    else:
        env = m.group(1)
        end = body.find(f"\\end{{{env}}}", m.end())
        env_text = body[m.start(): end if end > 0 else m.end() + 4000]
        k = env_text.find("\\caption")
        cap = None
        while k >= 0:
            # skip \captionsetup / \caption* of subfigures: take the last top-level \caption
            nxt = env_text[k + 8:k + 9]
            if nxt in ("{", "[", " "):
                c, _ = brace_arg(env_text, k + 8)
                if c is not None:
                    cap = c  # keep last (main caption follows subcaptions)
            k = env_text.find("\\caption", k + 8)
        sub = re.findall(r"\\subcaption\{|\\subfloat|\\begin\{subfigure", env_text)
    return {"caption_latex": (cap or "").strip() or None, "graphics": re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", env_text)}


def clean_caption(c):
    if not c:
        return c
    c = re.sub(r"\\label\{[^}]*\}", "", c)
    c = re.sub(r"\\(?:cite[tp]?|citep|citet|citealp|ref|eqref|autoref|cref|Cref)\*?(\[[^\]]*\])?\{[^}]*\}", "[ref]", c)
    for _ in range(3):
        c = re.sub(r"\\(?:textbf|textit|emph|texttt|textsc|underline|mathbf|textrm|textsf|text|mbox|footnotesize|small|bf|it)\{([^{}]*)\}", r"\1", c)
    c = re.sub(r"\\(?:textcolor|color)\{[^}]*\}\{([^{}]*)\}", r"\1", c)
    c = re.sub(r"\\(?:small|footnotesize|scriptsize|bf|it|centering|vspace\{[^}]*\}|hspace\{[^}]*\})\b", "", c)
    c = c.replace("~", " ").replace("\\%", "%").replace("\\&", "&").replace("``", '"').replace("''", '"')
    return " ".join(c.split())


# ---------------------------------------------------------------- PDF side
ANY_CAP_RE = re.compile(r"^\s*(?:Figure|Fig\.?|FIGURE|FIG\.)\s*(?:[0-9]+(?:\.[0-9]+)?|[IVX]+)(?:\s*[:.|\-–—]|\s+(?=[A-Z(\[]))")


def _plain(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def find_caption_block(doc, latex_caption=None, max_pages=10):
    """Locate Figure 1's caption in the PDF. Prefer the block matching the LaTeX caption; otherwise
    the first figure caption in reading order (handles 'Figure 1:', 'Fig. 1.', 'Figure 3.1:' …)."""
    import difflib
    want = _plain(clean_caption(latex_caption))[:80] if latex_caption else None
    first = None
    for pno in range(min(max_pages, len(doc))):
        for b in doc[pno].get_text("blocks"):
            if b[6] != 0:
                continue
            m = ANY_CAP_RE.match(b[4])
            if not m:
                continue
            hit = (pno, fitz.Rect(b[:4]), " ".join(b[4].split()))
            if first is None:
                first = hit
            if want:
                got = _plain(b[4][m.end():])[:len(want)]
                if difflib.SequenceMatcher(None, want, got).ratio() > 0.6:
                    return hit
            elif CAP_RE.match(b[4]):
                return hit
    return first if first else (None, None, None)


def text_blocks(page):
    """Text blocks with char count and median font size; vertical text (arXiv stamp) dropped."""
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        r = fitz.Rect(b["bbox"])
        if r.height > 4 * r.width:
            continue
        spans = [sp for l in b["lines"] for sp in l["spans"] if sp["text"].strip()]
        if not spans:
            continue
        txt = " ".join(sp["text"] for sp in spans)
        sizes = sorted(sp["size"] for sp in spans)
        out.append({"rect": r, "text": txt, "n": len(txt.strip()), "size": sizes[len(sizes) // 2]})
    return out


def body_font_size(blocks):
    from collections import Counter
    c = Counter()
    for b in blocks:
        c[round(b["size"] * 2) / 2] += b["n"]
    return c.most_common(1)[0][0] if c else 10.0


def figure_region(page, cap: fitz.Rect):
    P = page.rect
    margin_top = P.height * 0.055
    blocks = text_blocks(page)
    body = body_font_size(blocks)
    is_para = lambda b: b["n"] >= 150 and b["size"] >= body - 0.6 and b["rect"].height > 18
    paras = [b["rect"] for b in blocks if is_para(b)]
    tx0 = min([r.x0 for r in paras] + [cap.x0]); tx1 = max([r.x1 for r in paras] + [cap.x1])
    if cap.width < 0.6 * (tx1 - tx0):        # column-width caption: two-column layout or wrapfigure
        x0, x1 = cap.x0 - 12, cap.x1 + 12
    else:
        x0, x1 = tx0 - 12, tx1 + 12
    def inside(r, lo=x0, hi=x1):
        ov = min(r.x1, hi) - max(r.x0, lo)
        return ov > 0.5 * max(r.width, 1) or (ov > 0 and r.width > 0.5 * (hi - lo))
    items = []  # (rect, kind)
    for info in page.get_image_info():
        r = fitz.Rect(info["bbox"]) & P
        if r.width > 3 and r.height > 3:
            items.append((r, "img"))
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"]) & P
        if r.width < 1 and r.height < 1:
            continue
        if r.width > 0.9 * P.width and r.height < 2:   # page rules
            continue
        items.append((r, "draw"))
    for b in blocks:
        r = b["rect"]
        if r.intersects(cap) or ANY_CAP_RE.match(b["text"]):
            continue
        items.append((r, "para" if is_para(b) else "text"))

    # a drawn frame/box that encloses body-text paragraphs (e.g. a boxed abstract) is text, not figure
    para_rects = [r for r, k in items if k == "para"]
    items = [(r, "para" if k == "draw" and any(r.contains(p) for p in para_rects) else k) for r, k in items]

    def grow(cand, start, key, edge):
        """Walk outward from the caption through contiguous non-paragraph items."""
        cand.sort(key=key)
        front, region, gap = start, None, 28
        for r, k in cand:
            if edge(r, front, gap):
                break
            if k == "para":
                break
            front = min(front, r.y0) if key is _by_bottom else max(front, r.y1)
            region = r if region is None else region | r
        if region is None or not any(k in ("img", "draw") and region.contains(r) for r, k in cand):
            return None
        return region

    # 1) figure above the caption (the common case). Items may overlap the caption top a little
    #    (images often carry whitespace), so accept anything that starts above it.
    above = [(r, k) for r, k in items if inside(r) and r.y0 < cap.y0 - 2 and r.y1 <= cap.y1 and r.y0 >= margin_top]
    region = grow(above, cap.y0, _by_bottom, lambda r, f, g: r.y1 < f - g)
    if region is not None:
        region = fitz.Rect(max(region.x0, x0 - 10), region.y0, min(region.x1, x1 + 10), cap.y0 - 1) & P
        return region + (-4, -4, 4, 0)
    # 2) side caption (SCfigure / sidecap): graphics beside the caption, overlapping it vertically
    side = [(r, k) for r, k in items if k in ("img", "draw", "text") and not inside(r, cap.x0, cap.x1)
            and r.y1 > cap.y0 - 40 and r.y0 < cap.y1 + 40 and r.x0 >= tx0 - 12 and r.x1 <= tx1 + 12]
    if any(k in ("img", "draw") for r, k in side):
        region = None
        for r, k in side:
            region = r if region is None else region | r
        return (region & P) + (-4, -4, 4, 4)
    # 3) caption above the figure
    below = [(r, k) for r, k in items if inside(r) and r.y0 >= cap.y1 - 2 and r.y1 <= P.height * 0.94]
    region = grow(below, cap.y1, _by_top, lambda r, f, g: r.y0 > f + g)
    if region is not None:
        region = fitz.Rect(max(region.x0, x0 - 10), cap.y1 + 1, min(region.x1, x1 + 10), region.y1) & P
        return region + (-4, 0, 4, 4)
    return None


def _by_bottom(t):
    return -t[0].y1


def _by_top(t):
    return t[0].y0


def render(page, clip, out_png, out_webp):
    zoom = FIG_W / max(clip.width, 1)
    zoom = min(zoom, 12)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if img.width != FIG_W:
        img = img.resize((FIG_W, round(img.height * FIG_W / img.width)), Image.LANCZOS)
    img.save(out_png, optimize=True)
    th = img.resize((THUMB_W, round(img.height * THUMB_W / img.width)), Image.LANCZOS)
    th.save(out_webp, quality=82)
    return img.size


def process(p, s):
    out = {"id": p["id"], "status": None}
    aid = p.get("arxiv_id")
    if aid:
        pdf = arxiv_get(s, f"https://arxiv.org/pdf/{aid}", CACHE / "pdf" / f"{aid}.pdf")
        src = arxiv_get(s, f"https://arxiv.org/e-print/{aid}", CACHE / "src" / f"{aid}.src")
    else:
        pdf = arxiv_get(s, f"https://openreview.net/pdf?id={p['openreview_id']}", CACHE / "pdf" / f"or-{p['openreview_id']}.pdf")
        src = None
        if pdf and not pdf.read_bytes()[:4] == b"%PDF":
            pdf.unlink(); pdf = None
    if not pdf:
        out["status"] = "no_pdf"; return out
    lt = None
    if src:
        try:
            lt = latex_fig1(read_source(src))
        except Exception as e:
            out["latex_error"] = repr(e)[:200]
    try:
        doc = fitz.open(pdf)
    except Exception:
        out["status"] = "bad_pdf"; return out
    pno, cap, cap_pdf = find_caption_block(doc, (lt or {}).get("caption_latex"))
    out["caption_pdf"] = cap_pdf
    if lt and lt.get("caption_latex"):
        out["caption_latex"] = lt["caption_latex"]
        out["caption"] = clean_caption(lt["caption_latex"])
        out["caption_source"] = "latex"
    elif cap_pdf:
        out["caption"] = ANY_CAP_RE.sub("", cap_pdf, count=1).strip()
        out["caption_source"] = "pdf"
    out["n_graphics"] = len(lt["graphics"]) if lt else None
    if cap is None:
        out["status"] = "no_caption_in_pdf"; return out
    page = doc[pno]
    reg = figure_region(page, cap)
    if reg is None or reg.height < 20:
        out["status"] = "no_region"; out["page"] = pno; return out
    size = render(page, reg, CACHE / "figs" / f"{p['id']}.png", CACHE / "figs" / f"{p['id']}.webp")
    out.update(status="ok", page=pno, bbox=[round(v, 1) for v in reg], crop_pt=[round(reg.width), round(reg.height)],
               img_size=list(size), page_frac=round(reg.width * reg.height / (page.rect.width * page.rect.height), 3))
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--ids")
    ap.add_argument("--redo", action="store_true", help="re-run extraction (downloads stay cached)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--gap", type=float, default=1.0, help="min seconds between arXiv request starts (all workers)")
    a = ap.parse_args()
    rows = read_jsonl(CACHE / "work" / f"matched_{a.key}.jsonl")
    if a.ids:
        keep = set(Path(a.ids).read_text().split()); rows = [r for r in rows if r["id"] in keep]
    out_p = CACHE / "work" / f"extracted_{a.key}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_p)}
    _rate["gap"] = a.gap
    todo = [p for p in rows if a.redo or p["id"] not in done or done[p["id"]]["status"] in ("no_pdf",)]
    local = threading.local()

    def work(p):
        if not hasattr(local, "s"):
            local.s = requests.Session(); local.s.headers["User-Agent"] = UA
        try:
            return process(p, local.s)
        except Exception as e:
            return {"id": p["id"], "status": "error", "error": repr(e)[:300]}

    from collections import Counter
    with ThreadPoolExecutor(a.workers) as pool:
        for i, r in enumerate(pool.map(work, todo)):
            done[r["id"]] = r
            if i % 20 == 0:
                write_jsonl(out_p, sorted(done.values(), key=lambda r: r["id"]))
                print(i, len(todo), Counter(r["status"] for r in done.values()), flush=True)
    write_jsonl(out_p, sorted(done.values(), key=lambda r: r["id"]))
    from collections import Counter
    print("done", Counter(r["status"] for r in done.values()))


if __name__ == "__main__":
    main()
