#!/usr/bin/env python3
"""Record the operator's face picks and rejects for one episode, as an eval label file.

  record_face_picks.py --episode 9 --manifest OUT/manifest-amitai.json OUT/manifest-nadav.json \
      --good B1,B9,B2,A4,N1,N2,N4 \
      --bad "A1=my eyes look weird" --bad "A3=eyes looking down, almost shut" \
      --out evals/face-picks/episodes/ep09.json

--good: the stills the operator wants. --bad ID=REASON: a still he doesn't want, in his
words; a reject without a reason is refused. Every other still shown is stored as
"unknown". Ids must come from the manifests make_face_grid.py wrote.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os


def merge_manifests(manifests: list[dict]) -> tuple[dict, str]:
    items, recs = {}, set()
    for m in manifests:
        recs.add(m["recording"])
        for sid, it in m["items"].items():
            if sid in items:
                raise ValueError(f"id {sid} appears in two manifests")
            items[sid] = dict(it, side=m["side"])
    if len(recs) != 1:
        raise ValueError(f"manifests come from different recordings: {sorted(recs)}")
    return items, recs.pop()


def parse_bad(specs: list[str]) -> dict[str, str]:
    out = {}
    for s in specs:
        sid, _, reason = s.partition("=")
        sid, reason = sid.strip(), reason.strip()
        if not reason:
            raise ValueError(f"reject {sid or s!r} needs a reason: --bad 'ID=why'")
        out[sid] = reason
    return out


def build_labels(episode: int, items: dict, recording: str, good: list[str], bad: dict[str, str],
                 picked_on: str) -> dict:
    unknown_ids = [s for s in list(good) + list(bad) if s not in items]
    if unknown_ids:
        raise ValueError(f"not in the manifests: {', '.join(unknown_ids)}")
    both = set(good) & set(bad)
    if both:
        raise ValueError(f"marked both good and bad: {', '.join(sorted(both))}")
    if not good:
        raise ValueError("no picks: the operator must choose at least one still")
    out_items = {}
    for sid, it in items.items():
        row = {"host": it["host"], "t_sec": it["t_sec"]}
        if sid in good:
            row.update(label="good", reason="picked")
        elif sid in bad:
            row.update(label="bad", reason=bad[sid])
        else:
            row["label"] = "unknown"
        out_items[sid] = row
    sides = {f"{it['host']}_side": it["side"] for it in items.values()}
    return {"episode": episode, "picked_on": picked_on, "operator": "amitai",
            "source": {"episode": episode, "recording": recording, **sides}, "items": out_items}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--episode", type=int, required=True)
    ap.add_argument("--manifest", nargs="+", required=True)
    ap.add_argument("--good", default="", help="comma-separated ids")
    ap.add_argument("--bad", action="append", default=[], help="ID=reason (repeatable)")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    mans = []
    for p in a.manifest:
        with open(p) as fh:
            mans.append(json.load(fh))
    items, rec = merge_manifests(mans)
    good = [s.strip() for s in a.good.split(",") if s.strip()]
    labels = build_labels(a.episode, items, rec, good, parse_bad(a.bad), a.date)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(labels, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    n = {k: sum(1 for i in labels["items"].values() if i["label"] == k) for k in ("good", "bad", "unknown")}
    print(f"{a.out}: {n['good']} good, {n['bad']} bad, {n['unknown']} unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
