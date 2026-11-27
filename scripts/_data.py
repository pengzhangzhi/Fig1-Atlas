"""Locate the Fig1 Atlas data: local repo checkout first, website as fallback. Standard library only."""
import json, os, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = os.environ.get("FIG1_ATLAS_SITE", "https://pengzhangzhi.github.io/Fig1-Atlas")


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fig1-atlas-skill"}), timeout=60) as r:
        return r.read()


def load_index():
    p = ROOT / "data" / "index.jsonl"
    if p.exists():
        with open(p) as f:
            return [json.loads(l) for l in f if l.strip()]
    return json.loads(_get(f"{SITE}/index.json"))


def load_meta(pid):
    p = ROOT / "data" / "papers" / pid / "meta.json"
    if p.exists():
        return json.loads(p.read_text())
    return json.loads(_get(f"{SITE}/p/{pid}.json"))
