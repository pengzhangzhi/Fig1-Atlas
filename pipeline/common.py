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
            time.sleep(int(r.headers.get("Retry-After", 10 * (i + 1)))); continue
        if r.status_code == 404:
            return r
        time.sleep(delay * (i + 1))
    return None
