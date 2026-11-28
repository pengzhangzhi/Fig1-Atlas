"""Taxonomy discovery: propose data-driven categories from a batch of extracted records.

The extraction prompts ask for a free-text name ("story_in_own_words", "experiment_in_own_words", "pattern_name")
next to the literature-based labels. This script shows a strong model those names plus the v0 labels and asks it to
induce categories from the data: definitions, inclusion/exclusion rules, examples, and which v0 labels are
overlapping, missing or unused. A human (or the next iteration) then edits taxonomy/<kind>.v<n>.json.

Usage: python t1_discover.py story|experiment|plot [--model opus] [--know-dir knowledge] [--plot-dir plots]
Output: taxonomy/discovery_<kind>.json and .md
"""
import argparse, glob, json, subprocess
from pathlib import Path
from common import CACHE
from k1_read import parse_json

HERE = Path(__file__).resolve().parent

ASK = {
 "story": """Below are {n} accepted ML papers, each summarised by its narrative: a free-text name for its story, the
belief change (seems -> really), the niche, the contribution and the v0 labels another annotator assigned.

Induce a taxonomy of STORY ARCHETYPES from this data: the recurring ways papers frame their work, at the level a
researcher would use to decide how to pitch a paper ("new benchmark exposes a hidden failure", "diagnose then fix",
...). Aim for 8-14 archetypes that together cover >= 90% of papers, are mutually distinguishable, and transfer across
research topics.""",
 "experiment": """Below are {n} experiments from accepted ML papers, each with a free-text name, its question and the
v0 labels another annotator assigned (claim_type = what is claimed; manipulation = what is varied).

Induce a taxonomy of EXPERIMENT DESIGN PATTERNS from this data: recurring, reusable designs a researcher could copy to
test a claim ("leave-one-out ablation at matched budget", "synthetic task with known ground truth", ...), grouped
into 6-10 families with 2-6 patterns each. Also judge the v0 claim_type and manipulation axes.""",
 "plot": """Below are {n} plot panels from accepted ML papers, each with a free-text pattern name, the message labels
(v0) and chart type another annotator assigned, and its stated takeaway.

Induce a taxonomy of PLOT MESSAGES (what the panel makes the reader conclude) from this data, grouped into 6-12
families with subtypes, and list the most reusable concrete plot PATTERNS (message + form) with how often they occur.
Also judge the v0 message axis.""",
}

TAIL = """
Return ONE JSON object:
{{"categories": [{{"id": "kebab-case", "name": "short human name", "parent": "family id or null",
   "definition": "one sentence", "include_if": "decision rule", "exclude_if": "how to tell it from its nearest neighbour",
   "examples": ["item ids, 2-5"], "count": <items that fit>}}],
 "uncovered": ["item ids that fit no category"],
 "v0_review": {{"unused_or_rare": [...], "overlapping_pairs": [["a","b","why"]], "missing": ["what v0 lacks"],
               "axis_problems": ["e.g. a label that annotators over-assign, with evidence"]}},
 "notes": "anything else that would improve the taxonomy (3-6 sentences)"}}
Assign each item to its best category when counting. Return only the JSON object.

ITEMS:
{items}"""


def items(kind, a):
    out = []
    if kind == "story":
        for f in sorted(glob.glob(str(CACHE / a.know_dir / "*.json"))):
            k = json.loads(Path(f).read_text())
            if "story" not in k:
                continue
            s = k["story"]
            out.append(f"[{k['_meta']['id']}] name: {s.get('story_in_own_words')} | seems: {s['arc'].get('seems')} -> really: {s['arc'].get('really')}"
                       f" | niche: {s['niche'].get('statement')} | contribution: {s['contribution'].get('statement')}"
                       f" | v0 niche={s['niche'].get('labels')} arc={s['arc'].get('labels')} contribution={s['contribution'].get('labels')}")
    elif kind == "experiment":
        for f in sorted(glob.glob(str(CACHE / a.know_dir / "*.json"))):
            k = json.loads(Path(f).read_text())
            for e in k.get("experiments", []):
                out.append(f"[{k['_meta']['id']}/{e['id']}] {e.get('experiment_in_own_words')} | Q: {e.get('question')}"
                           f" | v0 claim={e.get('claim_type')} manip={e.get('manipulation')} form={e.get('evidence_form')} role={e.get('role')}")
    else:
        for f in sorted(glob.glob(str(CACHE / a.plot_dir / "*.json"))):
            d = json.loads(Path(f).read_text())
            pid = d.get("_meta", {}).get("id")
            for fg in d.get("figures", []):
                if not fg.get("is_data_figure"):
                    continue
                for p in fg.get("panels", []):
                    q = (p.get("takeaway_stated_quote") or {}).get("text") or ""
                    out.append(f"[{pid}/f{fg['n']}{p.get('label') or ''}] {p.get('pattern_name')} | message={p.get('message')} chart={p.get('chart')}"
                               f" | x={p.get('x', {}).get('label')} y={p.get('y', {}).get('label')} | visual: {p.get('takeaway_visual')} | stated: {q[:160]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["story", "experiment", "plot"])
    ap.add_argument("--model", default="opus")
    ap.add_argument("--know-dir", default="knowledge")
    ap.add_argument("--plot-dir", default="plots")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    it = items(a.kind, a)
    prompt = ASK[a.kind].format(n=len(it)) + TAIL.format(items="\n".join(it))
    r = subprocess.run(["claude", "-p", "--model", a.model, "--output-format", "json", "--allowedTools", ""],
                       input=prompt, capture_output=True, text=True, timeout=3600, cwd=str(CACHE))
    out = json.loads(r.stdout)
    d = parse_json(out["result"])
    d["_meta"] = {"kind": a.kind, "items": len(it), "model": a.model, "cost_usd": out.get("total_cost_usd")}
    p = HERE / "taxonomy" / f"discovery_{a.kind}{a.tag}.json"
    p.write_text(json.dumps(d, indent=1, ensure_ascii=False))
    print(p, len(d.get("categories", [])), "categories;", len(d.get("uncovered", [])), "uncovered; $", out.get("total_cost_usd"))


if __name__ == "__main__":
    main()
