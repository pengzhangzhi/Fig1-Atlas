"""Knowledge stage 2: annotate a paper's result figures, panel by panel, by what they communicate.

One model call per paper. The model views every figure crop that an experiment points to (plus other main-text
data figures), with its caption, the sentences that cite it, and the experiments k1_read.py linked to it.

  in:  CACHE/corpus/<id>.json, CACHE/corpus_figs/<id>/fig<n>.png, CACHE/knowledge/<id>.json
  out: CACHE/plots/<id>.json  {figures: [{n, is_data_figure, layout, panels: [...]}], _meta}
Usage: python k2_plots.py --ids FILE [--model sonnet] [--workers 4] [--tax v0]
"""
import argparse, json, re, shutil, subprocess, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from common import CACHE, load_matched
from k1_read import taxonomy_block, verify_quotes, source_text, parse_json, _norm

HERE = Path(__file__).resolve().parent
MAX_FIGS = 10

PROMPT = """You are annotating the result figures of an accepted ML paper ({venue}) for PlotAtlas, a library that helps
researchers decide how to plot their own results. Plots are classified by WHAT THEY COMMUNICATE, not only by chart type.

First use the Read tool to view each figure image listed below (all of them). Then return ONE JSON object.

HARD RULES
- Describe only what is visible or stated. Do not invent axis names, values or methods you cannot read; write "unreadable".
- *_quote fields: verbatim from the caption or the citing text given below (5-40 words), or null.
- Abstracted fields (pattern, spec) contain NO topic words; use <PLACEHOLDERS>.
- Panels: split a figure into panels only where the figure itself has separate plots (subplots, (a)/(b) labels). A
  figure with one plot has one panel with label "".
- If no taxonomy label fits, use "other:<short-kebab-label>".

TAXONOMY
{plot_tax}

PAPER: {title}

FIGURES TO ANNOTATE:
{figs}

OUTPUT SCHEMA
{{"figures": [
  {{"n": <figure number>,
    "is_data_figure": true if it plots experimental data or results (false for diagrams, schematics, pipelines, example inputs),
    "layout": "panel arrangement, e.g. '1x3 small multiples, shared y'",
    "experiment": "e<k> from the list or null",
    "panels": [
      {{"label": "a" or "",
        "message": [primary, optional secondary], "modifier": [...], "chart": [...], "devices": [...],
        "takeaway_stated_quote": "...",
        "takeaway_visual": "what the plot itself makes salient, one sentence (interpretation)",
        "consistent": true if the visual takeaway matches the stated one,
        "x": {{"label": "as printed", "scale": "linear|log|categorical|time|unreadable"}},
        "y": {{"label": "as printed", "scale": "..."}},
        "encoding": "what color / marker / line style / facet stand for, e.g. 'color = method, ours in red; marker = dataset'",
        "series": ["the legend entries or compared groups as printed, max 8"],
        "data_requirements": "the tidy table needed to redraw it: columns with types, e.g. 'method (nominal), compute (quantitative, log), accuracy (quantitative), seed (for band)'",
        "pattern_name": "3-6 word name for this reusable plot pattern (interpretation), e.g. 'Pareto scatter with ours highlighted'",
        "pattern_spec": "a compact, domain-free Vega-Lite-like description: mark, x, y, color, facet, layers (fit line, band, reference line, annotations), using <PLACEHOLDERS>",
        "critique": "one sentence: what makes it effective, or what would make it clearer (interpretation)"}}
    ]}}
]}}
Return only the JSON object."""


MENTION_RE = lambda n: re.compile(rf"(?:Fig(?:ure|\.)?s?\.?\s*{n}(?![0-9])[^.]{{0,300}}\.)", re.I)


def mentions(c, n, k=3):
    out = []
    for s in c["sections"]:
        for m in MENTION_RE(n).finditer(s["text"]):
            a = s["text"].rfind(". ", 0, m.start()) + 2
            out.append(s["text"][max(a, m.start() - 300):m.end()].strip())
            if len(out) >= k:
                return out
    return out


def pick_figures(c, k):
    linked = {}
    for e in (k or {}).get("experiments", []):
        for n in e.get("figures") or []:
            if isinstance(n, int):
                linked.setdefault(n, []).append(e)
    figs = [f for f in c["figures"] if "crop" in f and f.get("part") != "appendix" and (f["n"] in linked or f["n"] > 1)]
    figs.sort(key=lambda f: (f["n"] not in linked, f["n"]))
    return figs[:MAX_FIGS], linked


def build(p, c, k, tax, workdir):
    figs, linked = pick_figures(c, k)
    blocks = []
    for f in figs:
        img = workdir / f"fig{f['n']}.png"
        shutil.copy(CACHE / "corpus_figs" / p["id"] / f"fig{f['n']}.png", img)
        exps = "; ".join(f"{e['id']} '{e.get('name')}': {e.get('question')} -> {str(e.get('result'))[:300]}" for e in linked.get(f["n"], []))
        men = " | ".join(mentions(c, f["n"]))
        blocks.append(f"- Figure {f['n']} — image: {img}\n  caption: {f['caption'][:900]}\n  cited as: {men[:900] or 'none found'}\n"
                      f"  linked experiments: {exps or 'none'}")
    keys = ["message", "modifier", "chart", "devices"] if tax["version"] != "v0" else ["message", "chart"]
    tb = taxonomy_block(tax, keys) + ("" if tax["version"] != "v0" else f"\ndevices (any number): {tax['devices']}")
    prompt = PROMPT.format(venue=p["venue"], plot_tax=tb,
                           title=p["title"], figs="\n".join(blocks))
    return prompt, figs


def call(prompt, model, cwd, timeout=1800):
    r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--allowedTools", "Read"],
                       input=prompt, capture_output=True, text=True, timeout=timeout, cwd=str(cwd))
    out = json.loads(r.stdout)
    if out.get("is_error"):
        raise RuntimeError(str(out.get("result"))[:300])
    return out["result"], {"cost_usd": out.get("total_cost_usd"), "ms": out.get("duration_ms"), "turns": out.get("num_turns")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tax", default="v0")
    ap.add_argument("--out-dir", default="plots")
    ap.add_argument("--know-dir", default="knowledge")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    tax = json.loads((HERE / "taxonomy" / f"plot.{a.tax}.json").read_text())
    meta = {p["id"]: p for key in ("iclr26", "icml26", "neurips26") for p in load_matched(key)}
    out = CACHE / a.out_dir; out.mkdir(exist_ok=True)
    ids = [i for i in Path(a.ids).read_text().split() if a.redo or not (out / f"{i}.json").exists()]
    print(f"{len(ids)} papers with {a.model}", flush=True)

    def work(pid):
        p = meta[pid]; c = json.loads((CACHE / "corpus" / f"{pid}.json").read_text())
        kp = CACHE / a.know_dir / f"{pid}.json"
        k = json.loads(kp.read_text()) if kp.exists() else None
        wd = CACHE / "tmp_k2" / pid; wd.mkdir(parents=True, exist_ok=True)
        prompt, figs = build(p, c, k, tax, wd)
        if not figs:
            return pid, {"figures": [], "_meta": {"id": pid, "note": "no figures to annotate"}}
        last = None
        for _ in range(3):
            try:
                txt, usage = call(prompt, a.model, wd)
                d = parse_json(txt)
                stats = {"quotes": 0, "verified": 0}
                verify_quotes(d, source_text(p, c), stats)
                seen = {f["n"] for f in figs}
                d["figures"] = [f for f in d.get("figures", []) if f.get("n") in seen]
                d["_meta"] = {"id": pid, "model": a.model, "taxonomy": a.tax, "figures_sent": sorted(seen), **usage,
                              "quotes": stats, "date": time.strftime("%Y-%m-%d")}
                return pid, d
            except Exception as e:
                last = repr(e)[:300]
        return pid, {"id": pid, "error": last}

    with ThreadPoolExecutor(a.workers) as pool:
        for i, fut in enumerate(as_completed([pool.submit(work, x) for x in ids])):
            pid, d = fut.result()
            (out / f"{pid}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
            m = d.get("_meta", {})
            n_p = sum(len(f.get("panels", [])) for f in d.get("figures", []))
            print(i + 1, pid, d.get("error") or f"figs={len(d.get('figures', []))} panels={n_p} quotes={m.get('quotes')} ${m.get('cost_usd')}", flush=True)


if __name__ == "__main__":
    main()
