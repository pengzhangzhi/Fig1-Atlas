"""Evaluation: does retrieval find structurally analogous items (the same kind of story / experiment / plot) rather
than only topically similar ones?

For each atlas, a set of realistic user queries is run through four rankers:
  bm25-all     keyword ranking over all text incl. title (a topical baseline)
  emb-all      embedding of title + all text
  emb-struct   embedding of the abstracted, topic-free fields only (what the sites embed)
  hybrid       0.35 * normalized bm25-all + emb-struct (what the sites run)
The top-5 of every ranker are pooled and judged blind by an LLM on two separate 0-2 scales:
  useful  : would this item serve the user as a template/example for what they asked?
  topical : is it about the same research topic as the query?
Reported: mean useful@5 and topical@5 per ranker, plus nDCG@5 on usefulness.
Usage: python e2_retrieval.py   (reads the three atlas repos next to Fig1-Atlas)
"""
import json, math, re, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = Path(__file__).resolve().parent.parent / "docs" / "eval"

QUERIES = {
 "StoryAtlas": [
  "We found that you can drop the KL penalty in RLHF entirely and training is just as stable and twice as fast.",
  "Our new benchmark of real hospital notes shows that clinical LLMs that score 90% on QA exams fail most realistic tasks.",
  "We show that three popular graph neural network oversmoothing fixes are all special cases of one normalization.",
  "We noticed attention sinks in vision transformers, explain why they appear, and use them to prune tokens.",
  "Our protein design method gets both high diversity and high designability, which people thought trade off.",
  "We prove a lower bound showing that a widely used heuristic for learning-rate warmup cannot be avoided.",
  "We apply ideas from database query optimization to schedule LLM agent tool calls.",
  "Speech models trained with our method are more robust to accents because we traced errors to the tokenizer and fixed it.",
  "We release the first large dataset of satellite images of glaciers with expert annotations.",
  "Careful re-evaluation shows that recent gains of new optimizers over Adam disappear with equal tuning.",
  "We introduce a new attack where a malicious user poisons a shared memory of a multi-user chatbot.",
  "Our theory explains why in-context learning emerges only after a specific training phase.",
 ],
 "ExperimentAtlas": [
  "I need to show that my speedup does not just come from using more GPU memory.",
  "How do I prove that each of the three loss terms in my objective is necessary?",
  "I want to show my model's gains hold on other backbones, not just Llama.",
  "How can I test whether my LLM judge agrees with humans before using it as the main metric?",
  "I claim my method scales better with model size than the baseline. How should I test that?",
  "I want to show a phenomenon causally depends on a specific attention head, not just correlates.",
  "Reviewers say my improvement could be within seed noise. What experiment addresses that?",
  "I want to check that my benchmark results are not due to test-set contamination.",
  "I want a toy setting where the ground truth is known to show my estimator is unbiased.",
  "How do I show my method is robust to label noise in the training data?",
  "I need to show the method helps more on harder examples than easy ones.",
  "I want to show my theory's predicted convergence rate matches what happens in practice.",
 ],
 "PlotAtlas": [
  "Show that our method reaches the same accuracy with far fewer inference steps than baselines.",
  "Show validation loss falls as a power law with compute for our models.",
  "Show which components of our system contribute the most to the final score.",
  "Show that our small model is better than the large one only when data is scarce.",
  "Show our results are stable across a wide range of learning rates.",
  "Show that the model trained on one domain fails on others.",
  "Show the distribution of confidence scores for correct versus wrong answers.",
  "Show our method wins on every one of eight datasets.",
  "Show that our cheap proxy metric correlates with human ratings.",
  "Show training reward curves over steps with variance across seeds.",
  "Show measured error against the theoretical bound as sample size grows.",
  "Show a qualitative comparison of generated images from several methods.",
 ],
}
FULL = {"StoryAtlas": ["title", "question", "seems", "really", "insight", "own", "template"],
        "ExperimentAtlas": ["title", "name", "question", "varies", "measures", "design", "falsifier", "own"],
        "PlotAtlas": ["title", "takeaway", "pattern_name", "spec", "x", "y", "encoding"]}
PURPOSE = {"StoryAtlas": "a paper whose story/framing they could borrow for their own paper",
           "ExperimentAtlas": "an experiment whose design they could adapt to test their own claim",
           "PlotAtlas": "a plot whose design they could adapt to show their own result"}

tok = lambda s: re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", (s or "").lower())


def bm25(docs, q):
    D = [tok(d) for d in docs]; N = len(D); avg = sum(map(len, D)) / N; df = Counter(w for d in D for w in set(d))
    out = []
    for d in D:
        c = Counter(d); s = 0
        for w in set(tok(q)):
            f = c.get(w, 0)
            if f:
                s += math.log(1 + (N - df[w] + .5) / (df[w] + .5)) * f * 2.2 / (f + 1.2 * (.25 + .75 * len(d) / avg))
        out.append(s)
    return np.array(out)


def describe(atlas, r):
    if atlas == "StoryAtlas":
        return f"{r['title']}. Seems: {r['seems']} Really: {r['really']}"
    if atlas == "ExperimentAtlas":
        return f"{r['title']}. Experiment: {r['question']} Varies: {r.get('varies')}. Measures: {r.get('measures')}. Design: {r['design']}"
    return f"{r['title']}. Plot: {r['takeaway']} x={r.get('x')}, y={r.get('y')}. Form: {r.get('pattern_name')}"


def judge(atlas, q, cands):
    items = "\n".join(f"[{i}] {describe(atlas, r)}" for i, r in enumerate(cands))
    prompt = f"""A researcher asked: "{q}"
They want {PURPOSE[atlas]}. Rate each candidate below on two separate scales.
useful (0-2): 2 = a strong template for what they asked (same kind of argument/design/message, adaptable to their work);
  1 = partly useful; 0 = not useful. Judge usefulness for their PURPOSE, regardless of research topic.
topical (0-2): 2 = same research topic; 1 = related area; 0 = different topic.
Candidates:
{items}
Return only JSON: {{"ratings": [{{"i": 0, "useful": 0, "topical": 0}}, ...]}} covering every candidate."""
    r = subprocess.run(["claude", "-p", "--model", "sonnet", "--output-format", "json", "--allowedTools", ""], input=prompt,
                       capture_output=True, text=True, timeout=900)
    out = json.loads(r.stdout)
    d = json.loads(re.search(r"\{.*\}", out["result"], re.S).group(0))
    return {x["i"]: (x["useful"], x["topical"]) for x in d["ratings"]}, out.get("total_cost_usd") or 0


def main():
    sys.path.insert(0, str(ROOT / "StoryAtlas" / "pipeline"))
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5")
    prefix = "Represent this sentence for searching relevant passages: "
    report, cost = {}, 0
    for atlas, qs in QUERIES.items():
        R = ROOT / atlas
        rows = [json.loads(l) for l in open(R / "data" / "index.jsonl")]
        vec = np.frombuffer((R / "data" / "vectors.bin").read_bytes(), dtype=np.int8).reshape(len(rows), -1).astype(np.float32) / 127
        full_text = [" ".join(str(r.get(f) or "") for f in FULL[atlas]) for r in rows]
        vfull = m.encode(full_text, batch_size=64, normalize_embeddings=True)
        group = (lambda r: r["paper"] + "/" + str(r["fig"])) if atlas == "PlotAtlas" else (lambda r: r["id"])
        res = {k: {"useful": [], "topical": [], "ndcg": []} for k in ("bm25-all", "emb-all", "emb-struct", "hybrid")}
        for q in qs:
            qv = m.encode([prefix + q], normalize_embeddings=True)[0]
            b = bm25(full_text, q); bn = b / max(b.max(), 1e-9)
            scores = {"bm25-all": b, "emb-all": vfull @ qv, "emb-struct": vec @ qv,
                      "hybrid": 0.35 * bn + np.maximum(0, (vec @ qv - 0.45) / 0.4)}
            tops = {}
            for k, s in scores.items():
                seen, t = set(), []
                for i in np.argsort(-s):
                    g = group(rows[i])
                    if g in seen:
                        continue
                    seen.add(g); t.append(int(i))
                    if len(t) == 5:
                        break
                tops[k] = t
            pool = sorted({i for t in tops.values() for i in t})
            rat, c = judge(atlas, q, [rows[i] for i in pool]); cost += c
            for k, t in tops.items():
                u = [rat.get(pool.index(i), (0, 0))[0] for i in t]; tp = [rat.get(pool.index(i), (0, 0))[1] for i in t]
                ideal = sorted([v[0] for v in rat.values()], reverse=True)[:5]
                dcg = lambda xs: sum((2 ** x - 1) / math.log2(j + 2) for j, x in enumerate(xs))
                res[k]["useful"].append(np.mean(u)); res[k]["topical"].append(np.mean(tp)); res[k]["ndcg"].append(dcg(u) / max(dcg(ideal), 1e-9))
            print(atlas, q[:60], {k: round(float(np.mean([rat.get(pool.index(i), (0, 0))[0] for i in t])), 2) for k, t in tops.items()}, flush=True)
        report[atlas] = {k: {m_: round(float(np.mean(v)), 3) for m_, v in d.items()} for k, d in res.items()}
        report[atlas]["n_queries"] = len(qs); report[atlas]["n_items"] = len(rows)
    report["_judge"] = {"model": "sonnet", "cost_usd": round(cost, 2)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "retrieval.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
