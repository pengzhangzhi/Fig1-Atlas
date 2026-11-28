"""Evaluation: how stable are the labels? Compare two independent extraction runs on the same papers.

For each taxonomy axis: mean Jaccard of the label sets, and how often the primary (first) label matches.
Experiments are aligned across runs by the figures/tables they cite and by name similarity.
Plots are aligned by figure number and panel label.
Usage: python e1_stability.py <dir A> <dir B> [--kind knowledge|plots]
"""
import argparse, difflib, glob, json
from pathlib import Path
from common import CACHE


FAM = {k: v.get("family") for k, v in json.loads((Path(__file__).parent / "taxonomy" / "plot.v1.json").read_text())["axes"]["message"]["labels"].items()}


def jac(a, b):
    a, b = set(a or []), set(b or [])
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def first(x):
    return (x or [None])[0]


def lab(x):
    """labels may be stored as a list or as {"labels": [...]} or {"primary": .., "secondary": ..}"""
    if isinstance(x, dict):
        if "labels" in x:
            return x["labels"]
        return [v for v in (x.get("primary"), x.get("secondary")) if v]
    return x if isinstance(x, list) else ([x] if x else [])


def align(ea, eb):
    pairs, used = [], set()
    for a in ea:
        best, bs = None, 0.0
        for j, b in enumerate(eb):
            if j in used:
                continue
            s = 0.6 * jac([f"f{n}" for n in a.get("figures") or []] + [f"t{n}" for n in a.get("tables") or []],
                          [f"f{n}" for n in b.get("figures") or []] + [f"t{n}" for n in b.get("tables") or []])
            s += 0.4 * difflib.SequenceMatcher(None, (a.get("name") or "").lower(), (b.get("name") or "").lower()).ratio()
            if s > bs:
                best, bs = j, s
        if best is not None and bs >= 0.45:
            used.add(best); pairs.append((a, eb[best]))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--kind", default="knowledge")
    a = ap.parse_args()
    A, B = CACHE / a.a, CACHE / a.b
    ids = sorted({Path(f).stem for f in glob.glob(str(B / "*.json"))} & {Path(f).stem for f in glob.glob(str(A / "*.json"))})
    res = {}
    add = lambda k, j, p: res.setdefault(k, []).append((j, p))
    n_exp = [0, 0]
    for i in ids:
        x, y = json.loads((A / f"{i}.json").read_text()), json.loads((B / f"{i}.json").read_text())
        if a.kind == "knowledge":
            if "story" not in x or "story" not in y:
                continue
            for ax in ("archetype", "arc", "niche", "contribution", "insight_origin", "evidence"):
                if ax in x["story"] and ax in y["story"] and (ax != "arc" or isinstance(x["story"][ax], dict) and x["story"][ax].get("labels")):
                    la, lb = lab(x["story"][ax]), lab(y["story"][ax])
                    add("story." + ax, jac(la, lb), first(la) == first(lb))
            ea, eb = x["experiments"], y["experiments"]
            pairs = align(ea, eb); n_exp[0] += len(pairs); n_exp[1] += max(len(ea), len(eb))
            for p, q in pairs:
                for ax in ("pattern", "claim_type", "manipulation", "controls", "evidence_form", "role"):
                    if ax in p and ax in q:
                        la, lb = lab(p[ax]), lab(q[ax])
                        add("experiment." + ax, jac(la, lb), first(la) == first(lb))
        else:
            fa = {f["n"]: f for f in x.get("figures", [])}; fb = {f["n"]: f for f in y.get("figures", [])}
            for n in fa.keys() & fb.keys():
                add("figure.is_data_figure", float(fa[n].get("is_data_figure") == fb[n].get("is_data_figure")), True)
                pa = {(p.get("label") or "").strip("()").lower(): p for p in fa[n].get("panels", [])}
                pb = {(p.get("label") or "").strip("()").lower(): p for p in fb[n].get("panels", [])}
                add("figure.same_panel_split", float(set(pa) == set(pb)), True)
                for k in pa.keys() & pb.keys():
                    for ax in ("message", "family", "chart", "devices"):
                        if ax in pa[k] and ax in pb[k]:
                            la, lb = lab(pa[k][ax]), lab(pb[k][ax])
                            if ax == "family" or ax == "message":
                                fam = lambda L: [FAM.get(v, str(v).split("/")[0]) for v in L]
                                add("panel.message_family", jac(fam(la), fam(lb)), first(fam(la)) == first(fam(lb)))
                            add("panel." + ax, jac(la, lb), first(la) == first(lb))
    print(f"{len(ids)} papers compared ({a.a} vs {a.b})")
    if a.kind == "knowledge":
        print(f"experiments aligned: {n_exp[0]} of {n_exp[1]} ({n_exp[0] / max(n_exp[1], 1):.0%})")
    out = {}
    for k, v in sorted(res.items()):
        out[k] = {"n": len(v), "jaccard": round(sum(j for j, _ in v) / len(v), 3), "primary_agree": round(sum(p for _, p in v) / len(v), 3)}
        print(f"{k:32s} n={len(v):4d}  jaccard={out[k]['jaccard']:.2f}  primary agrees={out[k]['primary_agree']:.0%}")
    Path(CACHE / "work" / f"stability_{a.a}_vs_{a.b}.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
