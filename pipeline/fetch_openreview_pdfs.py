#!/usr/bin/env python3
"""Download OpenReview PDFs for accepted papers that have no arXiv version.

Anonymous requests are usually refused (OpenReview challenges scripted clients). Use the official,
authenticated API instead:  pip install openreview-py, then set OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD
(your own account) and pass --api.

  python3 fetch_openreview_pdfs.py openreview_ids.txt --out or_pdfs/ --api
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
    ap.add_argument("--api", action="store_true", help="use the authenticated openreview-py API client")
    a = ap.parse_args()
    client = None
    if a.api:
        import openreview  # pip install openreview-py
        client = openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net",
                                                 username=os.environ["OPENREVIEW_USERNAME"],
                                                 password=os.environ["OPENREVIEW_PASSWORD"])
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ids = [l.strip() for l in open(a.ids) if l.strip()]
    ok = bad = 0
    for i, oid in enumerate(ids, 1):
        dest = out / f"or-{oid}.pdf"
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        try:
            if client is not None:
                data = client.get_attachment(field_name="pdf", id=oid)
            else:
                req = urllib.request.Request(f"https://openreview.net/pdf?id={oid}",
                                             headers={"User-Agent": "fig1-atlas"})
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
