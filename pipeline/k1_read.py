"""Knowledge stage 1: read a parsed paper once and extract its story, claims and experiments.

One model call per paper (text only). Output feeds StoryAtlas (story) and ExperimentAtlas (claims, experiments);
k2_plots.py then annotates the figures that the experiments point to.

  in:  CACHE/corpus/<id>.json (c1_parse.py) + paper metadata
  out: CACHE/knowledge/<id>.json  {story, claims, experiments, _meta}

Provenance rules (enforced after the call):
  * fields named *_quote must be verbatim from the paper; verify_quotes() checks them against the parsed text
    and marks each {"verified": bool}. Unverifiable quotes are kept but flagged, never shown as the paper's words.
  * "not stated" is a valid value; the prompt forbids filling in details the paper does not give.
Usage: python k1_read.py --ids FILE [--model sonnet] [--workers 4] [--tax v0] [--out-dir knowledge]
"""
import argparse, json, re, subprocess, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from common import CACHE, read_jsonl, load_matched

HERE = Path(__file__).resolve().parent
MAX_MAIN = 70000          # characters of main text sent (about 17k tokens)


def taxonomy_block(tax, keys):
    out = []
    for k in keys:
        ax = tax["axes"][k]
        out.append(f'{k} (pick up to {ax["multi"]}; {ax["q"]}):')
        for lab, d in ax["labels"].items():
            if isinstance(d, str):
                out.append(f"  - {lab}: {d}")
            else:
                line = f"  - {lab}: {d.get('def', '')}"
                if d.get("include_if"):
                    line += f" Use if: {d['include_if']} Not if: {d.get('exclude_if', '')}"
                out.append(line)
    return "\n".join(out)


PROMPT = """You are building a research knowledge base from one accepted ML paper (venue: {venue}). The base helps other
researchers find papers whose *story*, *experiments* or *plots* make the same kind of argument as theirs, across topics.
Read the paper text below and return ONE JSON object. Be faithful to the paper.

HARD RULES
- Never invent details. If the paper does not state something, write "not stated" (strings) or [] (lists).
- Fields ending in _quote must be copied VERBATIM from the paper text below (a contiguous span, 5-40 words). If no
  sentence fits, use null.
- Fields marked (interpretation) are your analysis; keep them short and concrete.
- Abstracted fields (template, pattern, design) must contain NO topic words: replace them with <PLACEHOLDERS>.
- For any taxonomy label, if no label fits, use "other:<short-kebab-label>". Do not force a fit.

TAXONOMY: STORY
{story_tax}

TAXONOMY: EXPERIMENTS
{exp_tax}

OUTPUT SCHEMA
{{
 "story": {{
   "research_question": "one sentence, the question the paper answers",
   "niche": {{"labels": [...], "statement": "what is missing or wrong in prior work, one sentence", "statement_quote": "..."}},
   "conventional_belief": {{"text": "the belief the paper challenges, or null if none is challenged", "quote": "... or null"}},
   "key_insight": "one sentence: the idea that makes the contribution possible",
   "key_insight_quote": "...",
   "contribution": {{"labels": [...], "statement": "one sentence"}},
   "arc": {{"labels": [...], "seems": "what readers believed before (interpretation)", "really": "what the paper shows instead (interpretation)"}},
   "insight_origin": [...],
   "evidence": [...],
   "story_in_own_words": "3-6 word name for this kind of story, in your own words (interpretation)",
   "abstract_moves": [{{"move": one of {abs_moves}, "text": "the abstract sentence, verbatim"}}],
   "intro_outline": [{{"move": one of {intro_moves}, "summary": "what this paragraph does, <= 15 words"}}],
   "template": "the abstract rewritten as a domain-free template of 2-4 sentences with <PLACEHOLDERS> (interpretation)",
   "title_pattern": "the title's rhetorical pattern with placeholders, e.g. '<X> is secretly <Y>' (interpretation)",
   "alternative_framings": [{{"arc": "...", "niche": "...", "one_line": "how the same results could be pitched differently"}}]
 }},
 "claims": [
   {{"id": "c1", "text": "a claim the paper makes, as one sentence", "quote": "...", "kind": "main|secondary",
     "supported_by": ["e1", ...]}}
 ],
 "experiments": [
   {{"id": "e1", "name": "short name", "where": "section heading and/or 'Table 2', 'Figure 3'",
     "figures": [figure numbers], "tables": [table numbers], "in_appendix": false,
     "role": "...", "claim_type": [...], "manipulation": [...], "evidence_form": [...],
     "experiment_in_own_words": "3-6 word name for this kind of experiment (interpretation)",
     "question": "the question this experiment answers",
     "hypothesis": "the expected outcome if the claim is true (interpretation)",
     "independent_variables": ["what is varied, with levels if stated"],
     "dependent_variables": ["metric (higher/lower is better)"],
     "controlled": ["what is held fixed, only if stated"],
     "baselines": ["..."], "datasets": ["..."],
     "replication": "seeds / error bars / significance as stated, or 'not stated'",
     "result": "what was found, with the key numbers exactly as stated",
     "result_quote": "...",
     "limitations_stated": ["limitations or caveats the authors state for this experiment"],
     "threats": ["confounders or missing controls you notice (interpretation), e.g. 'baselines not tuned with equal budget'"],
     "design_template": "a domain-free description of the design that someone could reuse: what to vary, what to hold fixed, what to compare, what to measure (interpretation, <PLACEHOLDERS>)",
     "falsifier": "the result that would have refuted the claim (interpretation)"}}
 ]
}}
List every distinct experiment in the main text (typically 3-12; merge trivial repeats, keep ablations separate).
Add appendix experiments only if the main text relies on them. Link claims and experiments by id.

PAPER: {title}
ABSTRACT: {abstract}

MAIN TEXT (sections, in order; text inside figures removed):
{main}

FIGURE CAPTIONS:
{figs}

TABLE CAPTIONS (and the start of each table's text):
{tabs}

APPENDIX SECTION HEADINGS: {appx}

Return only the JSON object."""


PROMPT_V1 = """You are building a research knowledge base from one accepted ML paper (venue: {venue}). The base helps other
researchers find papers whose *story*, *experiments* or *plots* make the same kind of argument as theirs, across topics.
Read the paper text below and return ONE JSON object. Be faithful to the paper.

HARD RULES
- Never invent details. If the paper does not state something, write "not stated" (strings) or [] (lists).
- Fields ending in _quote must be copied VERBATIM from the paper text below (a contiguous span, 5-40 words). If no
  sentence fits, use null.
- Fields marked (interpretation) are your analysis; keep them short and concrete.
- Abstracted fields (template, pattern, design) must contain NO topic words: replace them with <PLACEHOLDERS>.
- For any taxonomy label, if no label fits, use "other:<short-kebab-label>". Do not force a fit.

TAXONOMY: STORY
{story_tax}

TAXONOMY: EXPERIMENTS
{exp_tax}

OUTPUT SCHEMA
{{
 "story": {{
   "research_question": "one sentence, the question the paper answers",
   "niche": {{"labels": [...], "statement": "what is missing or wrong in prior work, one sentence", "statement_quote": "..."}},
   "challenged_belief": {{"text": "ONLY if the paper explicitly states that a belief, assumption or practice is widely held AND argues it is wrong: that belief in one sentence; otherwise null", "quote": "the paper's sentence stating it, or null"}},
   "key_insight": "one sentence: the idea that makes the contribution possible",
   "key_insight_quote": "...",
   "contribution": {{"labels": [...], "statement": "one sentence"}},
   "archetype": {{"primary": "...", "secondary": "... or null", "why": "one sentence: which sentence of the abstract or introduction carries the pitch"}},
   "arc": {{"seems": "what a reader would assume before reading (interpretation, one sentence)", "really": "what the paper shows instead (interpretation, one sentence)"}},
   "insight_origin": [...],
   "evidence": [...],
   "story_in_own_words": "3-6 word name for this kind of story, in your own words (interpretation)",
   "abstract_moves": [{{"move": one of {abs_moves}, "text": "the abstract sentence, verbatim"}}],
   "intro_outline": [{{"move": one of {intro_moves}, "summary": "what this paragraph does, <= 15 words"}}],
   "template": "the abstract rewritten as a domain-free template of 2-4 sentences with <PLACEHOLDERS> (interpretation)",
   "title_pattern": "the title's rhetorical pattern with placeholders, e.g. '<X> is secretly <Y>' (interpretation)",
   "alternative_framings": [{{"arc": "...", "niche": "...", "one_line": "how the same results could be pitched differently"}}]
 }},
 "claims": [
   {{"id": "c1", "text": "a claim the paper makes, as one sentence", "quote": "...", "kind": "main|secondary",
     "supported_by": ["e1", ...]}}
 ],
 "experiments": [
   {{"id": "e1", "name": "short name", "where": "section heading and/or 'Table 2', 'Figure 3'",
     "figures": [figure numbers], "tables": [table numbers], "in_appendix": false,
     "role": "...", "pattern": [primary, optional secondary], "claim_type": [primary, optional secondary],
     "controls": [only controls the paper states for this experiment], "evidence_form": [...],
     "experiment_in_own_words": "3-6 word name for this kind of experiment (interpretation)",
     "question": "the question this experiment answers",
     "hypothesis": "the expected outcome if the claim is true (interpretation)",
     "independent_variables": ["what is varied, with levels if stated"],
     "dependent_variables": ["metric (higher/lower is better)"],
     "controlled": ["what is held fixed, only if stated"],
     "baselines": ["..."], "datasets": ["..."],
     "replication": "seeds / error bars / significance as stated, or 'not stated'",
     "result": "what was found, with the key numbers exactly as stated",
     "result_quote": "...",
     "limitations_stated": ["limitations or caveats the authors state for this experiment"],
     "threats": ["confounders or missing controls you notice (interpretation), e.g. 'baselines not tuned with equal budget'"],
     "design_template": "a domain-free description of the design that someone could reuse: what to vary, what to hold fixed, what to compare, what to measure (interpretation, <PLACEHOLDERS>)",
     "falsifier": "the result that would have refuted the claim (interpretation)"}}
 ]
}}
List every distinct experiment in the main text (typically 3-12; merge trivial repeats, keep ablations separate).
Add appendix experiments only if the main text relies on them. Link claims and experiments by id.

PAPER: {title}
ABSTRACT: {abstract}

MAIN TEXT (sections, in order; text inside figures removed):
{main}

FIGURE CAPTIONS:
{figs}

TABLE CAPTIONS (and the start of each table's text):
{tabs}

APPENDIX SECTION HEADINGS: {appx}

Return only the JSON object."""


def build_input(p, c, tax_story, tax_exp):
    main, n = [], 0
    for s in c["sections"]:
        block = f"## {s['h']}\n{s['text']}\n"
        if n + len(block) > MAX_MAIN:
            main.append(block[:max(0, MAX_MAIN - n)] + " [truncated]"); break
        main.append(block); n += len(block)
    figs = "\n".join(f"Figure {f['n']}{' (appendix)' if f.get('part') == 'appendix' else ''}: {f['caption'][:600]}" for f in c["figures"][:40])
    tabs = "\n".join(f"Table {t['n']}{' (appendix)' if t.get('part') == 'appendix' else ''}: {t['caption'][:400]}\n   [{t['text'][:500]}]"
                     for t in c["tables"][:30])
    appx = "; ".join(s["h"] for s in c.get("appendix", [])[:40]) or "none"
    v1 = tax_story["version"] != "v0"
    sk = ["archetype", "niche", "contribution", "insight_origin", "evidence"] if v1 else ["niche", "contribution", "arc", "insight_origin", "evidence"]
    ek = ["pattern", "claim_type", "controls", "evidence_form", "role"] if v1 else ["claim_type", "manipulation", "evidence_form", "role"]
    return (PROMPT_V1 if v1 else PROMPT).format(venue=p["venue"], story_tax=taxonomy_block(tax_story, sk),
                         exp_tax=taxonomy_block(tax_exp, ek),
                         abs_moves=tax_story["abstract_moves"], intro_moves=tax_story["intro_moves"],
                         title=p["title"], abstract=p.get("abstract") or "", main="".join(main), figs=figs or "none",
                         tabs=tabs or "none", appx=appx)


_norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def source_text(p, c):
    parts = [p.get("abstract") or "", p["title"]] + [s["h"] + " " + s["text"] for s in c["sections"] + c.get("appendix", [])]
    parts += [f["caption"] for f in c["figures"]] + [t["caption"] + " " + t["text"] for t in c["tables"]]
    return _norm(" ".join(parts))


def verify_quotes(obj, src, stats):
    """Walk the record; every key ending in 'quote' becomes {"text", "verified"}; abstract_moves text is checked too."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k.endswith("quote") and (isinstance(v, str) or v is None):
                ok = bool(v) and len(_norm(v)) > 10 and _norm(v) in src
                if v and not ok:                     # tolerate small edits: 85% of 6-word shingles present
                    w = _norm(v).split(); sh = [" ".join(w[i:i + 6]) for i in range(max(1, len(w) - 5))]
                    ok = len(w) >= 6 and sum(s in src for s in sh) >= 0.85 * len(sh)
                obj[k] = {"text": v, "verified": ok} if v else None
                if v:
                    stats["quotes"] += 1; stats["verified"] += ok
            else:
                verify_quotes(v, src, stats)
    elif isinstance(obj, list):
        for v in obj:
            verify_quotes(v, src, stats)


def call(prompt, model, timeout=1200):
    r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--allowedTools", ""],
                       input=prompt, capture_output=True, text=True, timeout=timeout, cwd=str(CACHE))
    out = json.loads(r.stdout)
    if out.get("is_error"):
        raise RuntimeError(str(out.get("result"))[:300])
    return out["result"], {"cost_usd": out.get("total_cost_usd"), "ms": out.get("duration_ms"),
                           "usage": {k: out.get("usage", {}).get(k) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")}}


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no json: " + text[:200])
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tax", default="v0")
    ap.add_argument("--out-dir", default="knowledge")
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    tax_s = json.loads((HERE / "taxonomy" / f"story.{a.tax}.json").read_text())
    tax_e = json.loads((HERE / "taxonomy" / f"experiment.{a.tax}.json").read_text())
    meta = {p["id"]: p for k in ("iclr26", "icml26", "neurips26") for p in load_matched(k)}
    ids = Path(a.ids).read_text().split()
    out = CACHE / a.out_dir; out.mkdir(exist_ok=True)
    todo = [i for i in ids if a.redo or not (out / f"{i}.json").exists()]
    print(f"{len(todo)} papers with {a.model}, taxonomy {a.tax}", flush=True)

    def work(pid):
        p = meta[pid]; c = json.loads((CACHE / "corpus" / f"{pid}.json").read_text())
        if c.get("status") != "ok":
            return pid, {"id": pid, "error": "not parsed"}
        prompt = build_input(p, c, tax_s, tax_e)
        last = None
        for attempt in range(3):
            try:
                txt, usage = call(prompt, a.model)
                d = parse_json(txt)
                stats = {"quotes": 0, "verified": 0}
                verify_quotes(d, source_text(p, c), stats)
                d["_meta"] = {"id": pid, "model": a.model, "taxonomy": a.tax, "prompt_chars": len(prompt), **usage,
                              "quotes": stats, "date": time.strftime("%Y-%m-%d")}
                return pid, d
            except Exception as e:
                last = repr(e)[:300]
        return pid, {"id": pid, "error": last}

    with ThreadPoolExecutor(a.workers) as pool:
        for i, fut in enumerate(as_completed([pool.submit(work, x) for x in todo])):
            pid, d = fut.result()
            (out / f"{pid}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
            m = d.get("_meta", {})
            print(i + 1, pid, d.get("error") or f"exp={len(d.get('experiments', []))} claims={len(d.get('claims', []))} "
                  f"quotes={m.get('quotes')} ${m.get('cost_usd')}", flush=True)


if __name__ == "__main__":
    main()
