#!/usr/bin/env python3
"""(Re)build features.json from the eval images with face_score.analyze (needs mediapipe).

  build_features.py --images DIR --model face_landmarker.task
DIR holds <ID>.jpg (one host's 960x1080 half-frame each, as made by extract_frames.py).
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skills", "investing-bros-brand", "scripts"))
import face_score  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--images", required=True)
ap.add_argument("--model")
a = ap.parse_args()
import cv2  # noqa: E402
labels = json.load(open(os.path.join(HERE, "labels.json")))["items"]
out = {}
for k in labels:
    f = face_score.analyze(cv2.imread(os.path.join(a.images, k + ".jpg")), a.model)
    if f is None:
        sys.exit(f"{k}: no face found")
    out[k] = f
json.dump(out, open(os.path.join(HERE, "features.json"), "w"), indent=1, sort_keys=True)
print(f"wrote features for {len(out)} images")
