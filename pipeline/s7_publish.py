"""Stage 7: publish.

  * data/index.jsonl                 one short line per paper (what search scans)
  * data/papers/<id>/meta.json       full metadata
  * data/missing.jsonl               accepted papers with no usable Figure 1 yet (and why)
  * Hugging Face dataset             images/<id>.png + thumbs/<id>.webp for license-hosted papers
The website's index.json / p/<id>.json / llms.txt are generated from data/ by
scripts/build_site.py inside the GitHub Pages workflow.
"""
import argparse, json, shutil
from pathlib import Path
from common import CACHE, REPO, read_jsonl, write_jsonl

HF_REPO = "fredzzp/fig1-atlas"
HF_BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"
INDEX_KEYS = ["id", "title", "venue", "tier", "role", "role2", "claim", "layout", "tags", "img"]


def build(keys):
    papers, missing = [], []
    for key in keys:
        m = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"matched_{key}.jsonl")}
        ext = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"extracted_{key}.jsonl")}
        ann = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"annotated_{key}.jsonl")}
        qc = {r["id"]: r["flags"] for r in read_jsonl(CACHE / "work" / f"qc_{key}.jsonl")}
        lic = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"license_{key}.jsonl")}
        proc = {r["id"]: r for r in read_jsonl(CACHE / "work" / f"proc_{key}.jsonl")}
        for pid, p in sorted(m.items()):
            e, a, L = ext.get(pid), ann.get(pid), lic.get(pid, {})
            flags = qc.get(pid, [])
            if not e or e.get("status") != "ok":
                missing.append({"id": pid, "title": p["title"], "venue": p["venue"],
                                "reason": (e or {}).get("status", "not-extracted")}); continue
            if not a or "error" in a:
                missing.append({"id": pid, "title": p["title"], "venue": p["venue"], "reason": "not-annotated"}); continue
            if "not-a-figure" in flags:
                missing.append({"id": pid, "title": p["title"], "venue": p["venue"], "reason": "not-a-figure"}); continue
            host = bool(L.get("host"))
            aid = p.get("arxiv_id")
            pr = proc.get(pid, {})
            meta = {
                "id": pid, "title": p["title"], "authors": p["authors"], "venue": p["venue"], "tier": p["tier"],
                "track": p["track"], "topic": p.get("topic"),
                "role": a["role"], "role2": a.get("role2"), "claim": a["claim"], "layout": a["layout"],
                "tags": a["tags"], "style": a["style"],
                "description": a["description"], "caption": e.get("caption"), "caption_source": e.get("caption_source"),
                "abstract": p.get("abstract"),
                "links": {"openreview": f"https://openreview.net/forum?id={p['openreview_id']}",
                          "arxiv": f"https://arxiv.org/abs/{aid}" if aid else None,
                          "pdf": pr.get("proc_pdf") or (f"https://arxiv.org/pdf/{aid}" if aid else f"https://openreview.net/pdf?id={p['openreview_id']}"),
                          "proceedings": pr.get("proc_page"),
                          "virtual": p.get("virtual_url"), "code": p.get("code_url")},
                "license": L.get("license"), "img": L.get("img", "none") if host else "none",
                "image_url": f"{HF_BASE}/images/{pid}.png" if host else None,
                "thumb_url": f"{HF_BASE}/thumbs/{pid}.webp" if host else None,
                "figure_page": e.get("page"), "qc_flags": flags,
                "annotator": a.get("annotator"), "role_confidence": a.get("role_confidence"),
            }
            papers.append(meta)
    return papers, missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+", help="venue keys to publish, e.g. iclr26 icml26 neurips26")
    ap.add_argument("--upload", action="store_true", help="push hosted images to the HF dataset")
    a = ap.parse_args()
    papers, missing = build(a.keys)
    data = REPO / "data"
    if (data / "papers").exists():
        shutil.rmtree(data / "papers")
    for m in papers:
        d = data / "papers" / m["id"]; d.mkdir(parents=True, exist_ok=True)
        (d / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
    rank = {"oral": 0, "spotlight": 1, "poster": 2}
    papers.sort(key=lambda m: m["id"])
    write_jsonl(data / "index.jsonl", [{k: m[k] for k in INDEX_KEYS if not (k == "role2" and not m[k])} for m in papers])
    write_jsonl(data / "missing.jsonl", missing)
    print(f"published {len(papers)} papers ({sum(1 for m in papers if m['image_url'])} with hosted images); {len(missing)} missing")
    if a.upload:
        upload([m for m in papers if m["image_url"]])


def upload(hosted):
    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(HF_REPO, repo_type="dataset", private=True, exist_ok=True)
    stage = CACHE / "hf_stage"
    if stage.exists():
        shutil.rmtree(stage)
    (stage / "images").mkdir(parents=True); (stage / "thumbs").mkdir()
    rows = []
    for m in hosted:
        shutil.copy(CACHE / "figs" / f"{m['id']}.png", stage / "images" / f"{m['id']}.png")
        shutil.copy(CACHE / "figs" / f"{m['id']}.webp", stage / "thumbs" / f"{m['id']}.webp")
        rows.append({"file_name": f"{m['id']}.png", "id": m["id"], "title": m["title"], "venue": m["venue"],
                     "role": m["role"], "claim": m["claim"], "caption": m["caption"], "license": m["license"],
                     "authors": ", ".join(m["authors"]), "arxiv": m["links"]["arxiv"]})
    write_jsonl(stage / "images" / "metadata.jsonl", rows)
    shutil.copy(REPO / "pipeline" / "hf_README.md", stage / "README.md")
    api.upload_folder(repo_id=HF_REPO, repo_type="dataset", folder_path=str(stage),
                      commit_message=f"Update {len(rows)} figures")
    print("uploaded", len(rows), "figures to", HF_REPO)


if __name__ == "__main__":
    main()
