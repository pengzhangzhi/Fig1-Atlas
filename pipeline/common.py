"""Shared paths and helpers for the build pipeline."""
import json, os, re, time, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("FIG1_CACHE", "/work/zp70/fig1-atlas-cache"))
UA = "Fig1-Atlas/0.1 (research dataset builder)"
for d in ["raw", "arxiv_oai", "src", "pdf", "figs", "work"]:
    (CACHE / d).mkdir(parents=True, exist_ok=True)


def norm_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    t = re.sub(r"\$[^$]*\$", " ", t)          # drop inline math
    t = re.sub(r"\\[a-zA-Z]+", " ", t)        # latex commands
    t = re.sub(r"[^a-z0-9]+", " ", t.lower())
    return " ".join(t.split())


def norm_name(n: str) -> str:
    n = unicodedata.normalize("NFKD", n or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", n.split()[-1]) if n.split() else ""


def read_jsonl(p):
    p = Path(p)
    if not p.exists():
        return []
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


def write_jsonl(p, rows):
    tmp = Path(str(p) + ".tmp")
    with open(tmp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def polite_get(session, url, tries=5, delay=3.0, **kw):
    """GET with retry/backoff that honors Retry-After (arXiv asks for >=3s between calls)."""
    for i in range(tries):
        try:
            r = session.get(url, timeout=120, **kw)
        except Exception as e:  # network hiccup
            time.sleep(delay * (i + 1)); last = e; continue
        if r.status_code == 200:
            return r
        if r.status_code in (429, 503):
            wait = int(r.headers.get("Retry-After", 10 * (i + 1)))
            if wait > 300:                          # a daily quota, not a burst limit: give up
                return r
            time.sleep(wait); continue
        if r.status_code in (401, 403, 404, 410):   # permanent: don't retry
            return r
        time.sleep(delay * (i + 1))
    return None


def load_matched(key):
    """matched_<key>.jsonl with rematch_<key>.jsonl (s2c: renamed papers found on arXiv) overlaid."""
    rows = read_jsonl(CACHE / "work" / f"matched_{key}.jsonl")
    re_ = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"rematch_{key}.jsonl")}
    for r in rows:
        m = re_.get(r["id"])
        if m and not r.get("arxiv_id"):
            r.update(arxiv_id=m["arxiv_id"], license=m.get("license"), match_how=m.get("how"))
    return rows


_CAP_PREFIX = re.compile(r"^\s*(?:Figure|Fig\.?|FIGURE|FIG\.)\s*(?:[0-9]+(?:\.[0-9]+)?|[IVX]+)\s*[:.|\-–—]?\s*")
_TEX_LEFT = re.compile(r"[\\${}]")


def _detex(c):
    """Formatting commands out, text kept. Math and paper-specific macros stay as written."""
    c = re.sub(r"\\(?:label|labelcref|cref|Cref|ref|eqref|autoref|cite[a-z]*)\*?\{[^}]*\}", "[ref]", c)
    c = re.sub(r"\\(?:textcolor|color)\{[^}]*\}", "", c)
    c = re.sub(r"\\(?:large|bfseries|itshape|bf|it|em|newline|linebreak|par)(?![a-zA-Z])\s*", " ", c)
    for _ in range(3):
        c = re.sub(r"\\(?:text[a-z]{2}|emph|underline|mbox)\{([^{}]*)\}", r"\1", c)
        c = re.sub(r"(?<![\\a-zA-Z^_}])\{([^{}$\\]*)\}", r"\1", c)       # bare grouping braces
    return " ".join(c.split())


def final_caption(e):
    """The caption to publish for an extracted record. The LaTeX caption is kept when it cleans up to plain
    text; if macros or math are left over, the caption text of the PDF (what the reader sees) is used."""
    cap, pdf = e.get("caption") or "", e.get("caption_pdf_full") or e.get("caption_pdf") or ""
    cap = re.sub(r"\\(?:small|footnotesize|scriptsize|tiny|normalsize|centering|noindent)(?![a-zA-Z])\s*", "", cap)
    cap = re.sub(r"\\(?:vspace|hspace)\*?\{[^}]*\}|\\looseness=?-?\d+", "", cap)
    cap = re.sub(r"^\{([^{}]*)\}$", r"\1", cap.strip())
    cap = _detex(cap)
    if e.get("caption_source") == "pdf" or not _TEX_LEFT.search(cap):
        return cap or None, e.get("caption_source")
    body = _CAP_PREFIX.sub("", " ".join(pdf.split()), count=1)
    body = re.sub(r"([a-z]{2})- ([a-z]{2})", r"\1\2", body)      # words hyphenated across lines
    plain = re.sub(r"\$[^$]*\$|\\[a-zA-Z]+|[{}]", " ", cap)      # the words of the LaTeX caption, to judge completeness
    if len(body) >= 0.6 * len(" ".join(plain.split())) and len(body) >= 20:
        return body, "pdf"
    return cap or None, e.get("caption_source")
