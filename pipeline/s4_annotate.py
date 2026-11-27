"""Stage 4: annotate each extracted Figure 1 with a vision-language model.

Input: the image, the caption and the abstract. Output (strict JSON): role, role2, role_confidence,
claim, layout, tags, style, description.

Backends (--backend):
  claude-api  Anthropic Messages API (needs ANTHROPIC_API_KEY)           [default per design]
  claude-cli  headless Claude Code (`claude -p`), uses the local login   [no key needed]
  openai      any OpenAI-compatible server, e.g. vLLM serving Qwen-VL    (--base-url, --model)
Output: CACHE/work/annotated_<key>.jsonl (resumable)
"""
import argparse, base64, json, os, re, subprocess, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from common import CACHE, REPO, read_jsonl, write_jsonl

ROLES = ["pipeline", "prior-vs-ours", "before-after", "teaser-result", "problem-setup",
         "concept", "overview-framework", "analysis-finding"]
STYLES = ["minimal", "icon-heavy", "math-heavy", "photo/real data", "plot", "text-heavy",
          "colorful", "3d-render", "screenshot"]

PROMPT = """You are annotating Figure 1 of an accepted ML paper for a library that helps researchers find Figure 1 *templates*.
Retrieval is by what the figure ARGUES (its rhetorical role), not by topic.

Role taxonomy (pick exactly one primary role; optionally a secondary role2 if the figure clearly does two jobs, else null):
{roles}

Paper title: {title}
Abstract: {abstract}
Figure 1 caption: {caption}

Look at the figure image{image_hint}. Return ONLY a JSON object, no prose, with keys:
  "role": one of {role_list}
  "role2": one of the roles or null
  "role_confidence": number 0-1, how sure you are of "role"
  "claim": ONE sentence (<= 25 words) stating what the figure argues, phrased abstractly enough to transfer across topics (e.g. "Prior samplers need many steps; ours maps noise to data in one.")
  "layout": short phrase describing the layout: panel count, arrangement, reading direction, notable devices (e.g. "2 panels, left-to-right, math under arrows")
  "tags": 3-7 lowercase keywords mixing method-type and argument-type words useful for cross-topic search (e.g. "one-step", "distillation", "efficiency", "discrete", "generative"); hyphenate multiword tags
  "style": 1-4 of {style_list}
  "description": 80-150 words describing the figure concretely for someone who cannot see it: panels, flow, visual elements, notation, color use, where the eye goes first
  "is_figure": false only if the image is not a real figure (e.g. a table, a blank/garbled crop, or only text); else true
  "crop_ok": false if the crop looks cut off, includes unrelated body text, or misses part of the figure; else true
"""


def roles_block():
    t = (REPO / "references" / "roles.md").read_text()
    rows = [l for l in t.splitlines() if l.startswith("| `")]
    rules = t.split("## Disambiguation rules", 1)[1].split("##", 1)[0].strip()
    return "\n".join(rows) + "\nDisambiguation:\n" + rules


def build_prompt(p, ex, image_hint=""):
    return PROMPT.format(roles=roles_block(), title=p["title"], abstract=(p.get("abstract") or "")[:2500],
                         caption=(ex.get("caption") or ex.get("caption_pdf") or "(none)")[:2000],
                         role_list=ROLES, style_list=STYLES, image_hint=image_hint)


def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no json in output: " + text[:200])
    d = json.loads(m.group(0))
    assert d.get("role") in ROLES, f"bad role {d.get('role')}"
    if d.get("role2") not in ROLES or d.get("role2") == d["role"]:
        d["role2"] = None
    d["style"] = [s for s in d.get("style", []) if s in STYLES]
    d["tags"] = [re.sub(r"\s+", "-", t.strip().lower()) for t in d.get("tags", [])][:7]
    return d


def call_claude_cli(prompt, img, model):
    full = prompt.replace("Look at the figure image", f"First use the Read tool to view the figure image at {img}. Then look at it")
    r = subprocess.run(["claude", "-p", full, "--model", model, "--allowedTools", "Read", "--output-format", "json"],
                       capture_output=True, text=True, timeout=600, cwd=str(CACHE / "figs"))
    out = json.loads(r.stdout)
    return out["result"], {"cost_usd": out.get("total_cost_usd")}


def call_claude_api(prompt, img, model):
    import anthropic
    c = anthropic.Anthropic()
    data = base64.b64encode(Path(img).read_bytes()).decode()
    msg = c.messages.create(model=model, max_tokens=1200, messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
        {"type": "text", "text": prompt}]}])
    return msg.content[0].text, {"in": msg.usage.input_tokens, "out": msg.usage.output_tokens}


def call_openai(prompt, img, model, base_url):
    import requests
    data = base64.b64encode(Path(img).read_bytes()).decode()
    r = requests.post(base_url.rstrip("/") + "/chat/completions", timeout=600, json={
        "model": model, "max_tokens": 1200, "temperature": 0,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}},
            {"type": "text", "text": prompt}]}]})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"], {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("key")
    ap.add_argument("--ids")
    ap.add_argument("--backend", default="claude-api", choices=["claude-api", "claude-cli", "openai"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--redo", action="store_true")
    a = ap.parse_args()
    model = a.model or {"claude-api": "claude-sonnet-5-5", "claude-cli": "sonnet", "openai": "Qwen/Qwen2.5-VL-72B-Instruct"}[a.backend]
    meta = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"matched_{a.key}.jsonl")}
    ext = [r for r in read_jsonl(CACHE / "work" / f"extracted_{a.key}.jsonl") if r["status"] == "ok"]
    if a.ids:
        keep = set(Path(a.ids).read_text().split()); ext = [r for r in ext if r["id"] in keep]
    out_p = CACHE / "work" / f"annotated_{a.key}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_p)}
    # re-annotate when the crop changed since annotation (records carry the bbox they were made from)
    stale = lambda e: "bbox" in done[e["id"]] and done[e["id"]]["bbox"] != e.get("bbox")
    todo = [e for e in ext if a.redo or e["id"] not in done or "error" in done[e["id"]] or stale(e)]
    lock = threading.Lock()
    print(f"{len(todo)} to annotate with {a.backend}:{model}", flush=True)

    def work(e):
        img = str(CACHE / "figs" / f"{e['id']}.png")
        prompt = build_prompt(meta[e["id"]], e)
        last = None
        for _ in range(3):
            try:
                if a.backend == "claude-cli":
                    txt, usage = call_claude_cli(prompt, img, model)
                elif a.backend == "claude-api":
                    txt, usage = call_claude_api(prompt, img, model)
                else:
                    txt, usage = call_openai(prompt, img, model, a.base_url)
                d = parse_json(txt)
                d.update(id=e["id"], annotator=f"{a.backend}:{model}", usage=usage, bbox=e.get("bbox"))
                return d
            except Exception as ex:
                last = repr(ex)[:300]
        return {"id": e["id"], "error": last}

    n = 0
    with ThreadPoolExecutor(a.workers) as pool:
        for fut in as_completed([pool.submit(work, e) for e in todo]):
            d = fut.result(); n += 1
            with lock:
                done[d["id"]] = d
                if n % 5 == 0 or n == len(todo):
                    write_jsonl(out_p, sorted(done.values(), key=lambda r: r["id"]))
                    print(f"{n}/{len(todo)} errors={sum(1 for r in done.values() if 'error' in r)}", flush=True)


if __name__ == "__main__":
    main()
