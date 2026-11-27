#!/usr/bin/env python3
"""Download OpenReview PDFs for accepted papers that have no arXiv version.

Run this on a machine OpenReview does not challenge (e.g. a laptop); the build machine can't.
Standard library only.

  python3 fetch_openreview_pdfs.py openreview_ids.txt --out or_pdfs/
  rsync -av or_pdfs/ <build-host>:/work/zp70/fig1-atlas-cache/pdf/

Files are saved as or-<openreview_id>.pdf, the name stage 3 looks for. Resumable; ~2 s between requests.
"""
import argparse, os, sys, time, urllib.request
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", help="file with one OpenReview forum id per line")
    ap.add_argument("--out", default="or_pdfs")
    ap.add_argument("--delay", type=float, default=2.0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ids = [l.strip() for l in open(a.ids) if l.strip()]
    ok = bad = 0
    for i, oid in enumerate(ids, 1):
        dest = out / f"or-{oid}.pdf"
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        req = urllib.request.Request(f"https://openreview.net/pdf?id={oid}",
                                     headers={"User-Agent": "Mozilla/5.0 (fig1-atlas)"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if data[:4] == b"%PDF":
                tmp = dest.with_suffix(".part"); tmp.write_bytes(data); os.replace(tmp, dest); ok += 1
            else:
                bad += 1
        except Exception as e:
            bad += 1
            print(f"{oid}: {e}", file=sys.stderr)
        if i % 50 == 0:
            print(f"[{i}/{len(ids)}] ok={ok} failed={bad}", flush=True)
        time.sleep(a.delay)
    print(f"done: ok={ok} failed={bad}")


if __name__ == "__main__":
    main()
