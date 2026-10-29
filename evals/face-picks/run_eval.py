#!/usr/bin/env python3
"""Does the face scorer rank every GOOD still above every BAD one?

  run_eval.py [--scorer v2|v1] [--images DIR --model face_landmarker.task]
Without --images it scores the committed features.json (no mediapipe needed, runs in CI).
With --images it re-analyses the stills first. Each host is scored against its own
baseline: labels.json "baselines" (whole-episode medians), else the medians of its stills. Reports per-image scores and pairwise
accuracy (all good-vs-bad pairs, and within each host); exits 1 below 100%.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "investing-bros-brand", "scripts"))
import face_score  # noqa: E402


def evaluate(features, labels, scorer="v2", baselines=None):
    fn = face_score.score if scorer == "v2" else face_score.score_v1
    bases = dict(baselines or {})
    for h in {v["host"] for v in labels.values()} - set(bases):
        bases[h] = face_score.baseline([features[k] for k, v in labels.items() if v["host"] == h])
    scores = {k: fn(features[k], bases[v["host"]]) for k, v in labels.items()}
    good = [k for k, v in labels.items() if v["label"] == "good"]
    bad = [k for k, v in labels.items() if v["label"] == "bad"]
    pairs = [(g, b) for g in good for b in bad]
    wrong = [(g, b) for g, b in pairs if scores[g] <= scores[b]]
    same = [(g, b) for g, b in pairs if labels[g]["host"] == labels[b]["host"]]
    wrong_same = [p for p in wrong if p in same]
    return {
        "scores": scores, "bases": bases, "wrong": wrong,
        "pairwise": 1 - len(wrong) / len(pairs),
        "pairwise_same_host": 1 - len(wrong_same) / len(same) if same else None,
        "margin": min(scores[g] for g in good) - max(scores[b] for b in bad),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorer", choices=["v1", "v2"], default="v2")
    ap.add_argument("--images")
    ap.add_argument("--model")
    a = ap.parse_args(argv)
    doc = json.load(open(os.path.join(HERE, "labels.json")))
    labels = doc["items"]
    baselines = {h: v for h, v in doc.get("baselines", {}).items() if isinstance(v, dict)}
    if a.images:
        import cv2
        features = {k: face_score.analyze(cv2.imread(os.path.join(a.images, k + ".jpg")), a.model) for k in labels}
    else:
        features = json.load(open(os.path.join(HERE, "features.json")))
    r = evaluate(features, labels, a.scorer, baselines)
    for k in sorted(labels, key=lambda k: -r["scores"][k]):
        v = labels[k]
        extra = ""
        if a.scorer == "v2":
            p = face_score.parts(features[k], r["bases"][v["host"]])
            neg = sorted(((x, y) for x, y in p.items() if y < -0.02), key=lambda x: x[1])
            extra = "  " + ", ".join(f"{x} {y:+.2f}" for x, y in neg[:3])
        print(f"{k:3} {v['host']:6} {v['label']:7} {r['scores'][k]:+.3f}{extra}")
    print(f"\nscorer {a.scorer}: pairwise good>bad {r['pairwise']:.0%} "
          f"(same host {r['pairwise_same_host']:.0%}), margin {r['margin']:+.3f}")
    for g, b in r["wrong"]:
        print(f"  misranked: {g} ({r['scores'][g]:+.3f}) <= {b} ({r['scores'][b]:+.3f})")
    return 0 if r["pairwise"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
