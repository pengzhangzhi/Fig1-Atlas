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
        W = page.rect.width
        if r.height > 4 * r.width and (r.x1 < 0.1 * W or r.x0 > 0.9 * W):   # arXiv stamp in the margin
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


SECTION_RE = re.compile(r"^\s*(?:[1-9]\d?(?:\.\d+){0,2}|[A-H](?:\.\d+)?)\s+[A-Z](?:[a-z]{2,}|\s?[A-Z])")
AFFIL_RE = re.compile(r"@|universit|institut|laborator|college|school of|department|\bcorresponding\b|equal contribution|github\.io|project page", re.I)


def figure_region(page, cap: fitz.Rect, pno=1, body=None):
    """Find Figure 1's bounding box on the page, given its caption block.

    Graphics (images + vector drawings) define the region. Text only bridges gaps while walking away
    from the caption, and joins the final region only when it sits inside/next to the graphics and is
    figure-sized (not headings, titles, author blocks or body paragraphs)."""
    P = page.rect
    margin_top = P.height * 0.055
    blocks = text_blocks(page)
    body = body or body_font_size(blocks)
    dense = [b["rect"] for b in blocks if b["n"] >= 150 and b["size"] >= body - 0.6]
    tx0 = min([r.x0 for r in dense] + [cap.x0]); tx1 = max([r.x1 for r in dense] + [cap.x1])
    tw = tx1 - tx0
    # Column-width figure only on a two-column page, or when the caption is off-centre (wrapfigure).
    # A short one-line caption under a full-width figure is narrow but centred.
    dense_w = [r.width for r in dense]
    two_col = len(dense_w) >= 2 and sum(w < 0.55 * tw for w in dense_w) > 0.5 * len(dense_w)
    off_centre = abs((cap.x0 + cap.x1) / 2 - (tx0 + tx1) / 2) > 0.12 * tw
    column = cap.width < 0.6 * tw and (two_col or off_centre)
    colw = cap.width if column else tx1 - tx0
    gfx_rects = [fitz.Rect(i["bbox"]) for i in page.get_image_info()] + \
                [fitz.Rect(d["rect"]) for d in page.get_drawings() if fitz.Rect(d["rect"]).width < 0.9 * P.width and not _invisible(d)]
    # body paragraph: dense body-size text spanning most of the column (figure text panels are narrower)
    is_para = lambda b: b["n"] >= 150 and b["size"] >= body - 0.6 and b["rect"].height > 18 and b["rect"].width > 0.7 * colw
    # headings / titles: large AND wide (big math labels inside figures are short)
    is_head = lambda b: (b["size"] >= body + 1.5 and b["n"] >= 12 and b["rect"].width > 0.4 * colw) or \
        (pno == 0 and b["size"] >= body + 1.5 and b["n"] >= 4
         and not any(g.contains(b["rect"]) for g in gfx_rects))  # title fragments (small caps lines)
    # first page: author / affiliation lines above a teaser
    # first page: author / affiliation lines above a teaser (centred on the page, outside graphics)
    centred = lambda r: abs((r.x0 + r.x1) / 2 - (tx0 + tx1) / 2) < 0.06 * tw and r.width > 0.3 * tw
    is_front = lambda b: pno == 0 and (AFFIL_RE.search(b["text"]) or (
        b["size"] >= body - 0.3 and b["n"] >= 12 and centred(b["rect"])
        and not any(g.contains(b["rect"]) for g in gfx_rects)))
    # numbered section headings ("4 LIMITATIONS OF …", small caps measure smaller than body text)
    para_x0 = [r.x0 for r in dense]
    is_section = lambda b: b["n"] < 120 and SECTION_RE.match(b["text"]) is not None and b["size"] >= body - 1 \
        and any(abs(b["rect"].x0 - x) < 6 for x in para_x0) \
        and not any(g.contains(b["rect"]) for g in gfx_rects)
    is_stop = lambda b: is_para(b) or is_head(b) or is_front(b) or is_section(b)
    paras = [b["rect"] for b in blocks if is_para(b)]
    # full-width figures may run past the text block (\hspace{-…}, oversized includegraphics)
    x0, x1 = (cap.x0 - 8, cap.x1 + 8) if column else (min(tx0 - 12, P.width * 0.03), max(tx1 + 12, P.width * 0.97))

    def inside(r, lo=x0, hi=x1):
        ov = min(r.x1, hi) - max(r.x0, lo)
        return ov > 0.5 * max(r.width, 1) or (ov > 0 and r.width > 0.5 * (hi - lo))

    items = []  # (rect, kind, size)
    for info in page.get_image_info():
        r = fitz.Rect(info["bbox"]) & P
        if r.width > 3 and r.height > 3:
            items.append((r, "img", 0))
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"]) & P
        if r.width < 1 and r.height < 1:
            continue
        if r.width > 0.9 * P.width and r.height < 2:   # page rules
            continue
        if _invisible(d):                              # white/blank background fills inflate the box
            continue
        items.append((r, "draw", 0))
    nchars = {}
    for b in blocks:
        r = b["rect"]
        if r.intersects(cap) or ANY_CAP_RE.match(b["text"]):
            continue
        items.append((r, "stop" if is_stop(b) else "text", b["size"]))
        nchars[tuple(r)] = b["n"]
    # a drawn frame that encloses body text (boxed abstract, theorem box) is text, not figure
    items = [(r, "stop" if k == "draw" and any(r.contains(p) for p in paras) else k, z) for r, k, z in items]
    GFX = ("img", "draw")
    items_n = [(r, k, z, nchars.get(tuple(r), 0)) for r, k, z in items]

    def grow(cand, start, upward):
        cand.sort(key=(lambda t: -t[0].y1) if upward else (lambda t: t[0].y0))
        front, gfx, gap, barrier = start, None, 28, None
        span = fitz.Rect(x0, 0, x1, 1)
        for r, k, _ in cand:
            if (r.y1 < front - gap) if upward else (r.y0 > front + gap):
                break
            if k == "stop":
                # a paragraph beside the figure (wrapfigure text) doesn't end the walk
                ref = gfx if gfx is not None else span
                if min(r.x1, ref.x1) - max(r.x0, ref.x0) > 0.3 * r.width:
                    barrier = r.y1 + 1 if upward else r.y0 - 1   # hard clip line for the region
                    break
                continue
            front = min(front, r.y0) if upward else max(front, r.y1)
            if k in GFX:
                gfx = r if gfx is None else gfx | r
        return gfx, barrier

    def finish(g, clip_y0=None, clip_y1=None):
        # add figure-sized text inside / right next to the graphics (labels, panel titles, subcaptions)
        reg = fitz.Rect(g)
        # chainable text: smaller than body text, or a short label (axis names, a^pre); not body lines
        texts = [r for r, k, z, n in items_n if k == "text" and (z < body - 0.5 or n <= 20)]
        for _ in range(3):                       # labels can chain (tick labels, then axis title)
            near = fitz.Rect(reg.x0 - 14, reg.y0 - 14, reg.x1 + 14, reg.y1 + 14)
            add = [r for r in texts if near.intersects(r) and not reg.contains(r)
                   and (clip_y0 is None or r.y0 >= clip_y0 - 1) and (clip_y1 is None or r.y1 <= clip_y1 + 1)]
            if not add:
                break
            for r in add:
                reg |= r
        # trim body paragraphs that overlap the region from the side
        for r, k, _ in items:
            if k == "stop" and r.intersects(reg) and not r.contains(g):
                if r.x1 <= g.x0 + 4:
                    reg.x0 = max(reg.x0, r.x1 + 1)
                elif r.x0 >= g.x1 - 4:
                    reg.x1 = min(reg.x1, r.x0 - 1)
        # column / wrapfigure: nothing left or right of graphics+caption (that is body text)
        hx0 = min(g.x0, cap.x0) - 12 if column else -1e9
        hx1 = max(g.x1, cap.x1) + 12 if column else 1e9
        reg = fitz.Rect(max(reg.x0, x0 - 4, hx0), reg.y0 if clip_y0 is None else max(reg.y0, clip_y0),
                        min(reg.x1, x1 + 4, hx1), reg.y1 if clip_y1 is None else min(reg.y1, clip_y1)) & P
        if reg.width < 0.6 * g.width or reg.height < 10:      # trimming went wrong: keep the graphics box
            reg = fitz.Rect(g.x0, g.y0 if clip_y0 is None else max(g.y0, clip_y0),
                            g.x1, g.y1 if clip_y1 is None else min(g.y1, clip_y1)) & P
        return reg

    # 1) figure above the caption (common case); items may overlap the caption top a little
    above = [t for t in items if (inside(t[0]) or t[1] == "stop") and t[0].y0 < cap.y0 - 2 and t[0].y1 <= cap.y1 and t[0].y0 >= margin_top]
    g, bar = grow(above, cap.y0, True)
    if g is not None:
        return finish(g, clip_y0=bar, clip_y1=cap.y0 - 1) + (-3, -3 if bar is None else 0, 3, 0)
    # 2) side caption (SCfigure / sidecap): graphics beside the caption, overlapping it vertically
    side = [t for t in items if t[1] in GFX and not inside(t[0], cap.x0, cap.x1)
            and t[0].y1 > cap.y0 - 40 and t[0].y0 < cap.y1 + 40 and t[0].x0 >= tx0 - 12 and t[0].x1 <= tx1 + 12]
    if side:
        g = None
        for r, _, _ in side:
            g = r if g is None else g | r
        return finish(g) + (-3, -3, 3, 3)
    # 3) caption above the figure
    below = [t for t in items if (inside(t[0]) or t[1] == "stop") and t[0].y0 >= cap.y1 - 2 and t[0].y1 <= P.height * 0.94]
    g, bar = grow(below, cap.y1, False)
    if g is not None:
        return finish(g, clip_y0=cap.y1 + 1, clip_y1=bar) + (-3, 0, 3, 3 if bar is None else 0)
    return None


def _invisible(d):
    """A fill-only path painted white (or fully transparent) - typically a figure's background box."""
    if d.get("type") != "f" or d.get("color") is not None:
        return False
    f = d.get("fill")
    return f is None or (min(f) > 0.97) or (d.get("fill_opacity") or 1) < 0.02


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
    body = body_font_size([b for i in range(min(len(doc), 6)) for b in text_blocks(doc[i])])  # doc-level
    reg = figure_region(page, cap, pno, body)
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
