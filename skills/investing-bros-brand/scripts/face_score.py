#!/usr/bin/env python3
"""Score host-face stills for thumbnails and covers.

Two layers:
- ``analyze(bgr_image)`` runs MediaPipe FaceLandmarker (blendshapes + 478 landmarks
  with irises) on one host's crop and returns a flat feature dict. Needs ``mediapipe``
  and ``opencv-python`` plus the ``face_landmarker.task`` model (``--model`` or
  ``$FACE_LANDMARKER_TASK``).
- ``score(features, baseline)`` is pure Python: higher is a better thumbnail face.
  ``baseline`` holds the host's own medians (eye openness, head pitch) over the
  candidate frames, so the rules travel across hosts and camera setups.

The rules (learned from Amitai's episode 9 picks, see evals/face-picks in the repo):
reward a real smile (mouth corners up, teeth showing); penalise eyes turned away from
the lens (iris off-centre), a wide-open unsmiling "stare", blinks or nearly shut eyes,
lowered brows / head dropped toward the desk, grimaces (stretched lips), lopsided
mouths, puckered or funnel (mid-word) mouths, a jaw dropped mid-sentence, turned heads and blur.

CLI:
  face_score.py FRAMES_DIR --side left|right|full [--pick 9 --gap 30] [--json out.json]
Frame files should be named so the seconds can be read from them
(``t0123.4.jpg`` or ``c_0001.jpg`` with ``--step 4``).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics

VERSION = 2

BLEND_KEYS = (
    "browDownLeft browDownRight browInnerUp eyeBlinkLeft eyeBlinkRight "
    "eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft "
    "eyeLookOutRight eyeSquintLeft eyeSquintRight jawOpen mouthFunnel mouthPucker "
    "mouthRollLower mouthRollUpper mouthSmileLeft mouthSmileRight mouthStretchLeft "
    "mouthStretchRight mouthUpperUpLeft mouthUpperUpRight mouthPressLeft mouthPressRight"
).split()


# ---------------------------------------------------------------- analysis (needs mediapipe)
_LANDMARKER = None


def _landmarker(model: str | None = None):
    global _LANDMARKER
    if _LANDMARKER is None:
        from mediapipe.tasks.python import BaseOptions, vision

        path = model or os.environ.get("FACE_LANDMARKER_TASK", "face_landmarker.task")
        _LANDMARKER = vision.FaceLandmarker.create_from_options(
            vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=path),
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
                num_faces=1,
            )
        )
    return _LANDMARKER


def analyze(img, model: str | None = None) -> dict | None:
    """Feature dict for the largest face in a BGR image, or None if no face."""
    import cv2
    import mediapipe as mp
    import numpy as np

    rgb = np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    r = _landmarker(model).detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
    if not r.face_blendshapes:
        return None
    b = {c.category_name: c.score for c in r.face_blendshapes[0]}
    f = {k: round(float(b[k]), 4) for k in BLEND_KEYS}
    M = np.array(r.facial_transformation_matrixes[0])
    f["yaw"] = round(float(np.degrees(np.arctan2(M[0, 2], M[2, 2]))), 2)
    f["pitch"] = round(float(np.degrees(np.arcsin(-M[1, 2]))), 2)
    h, w = img.shape[:2]
    lm = r.face_landmarks[0]
    P = lambda i: np.array([lm[i].x * w, lm[i].y * h])  # noqa: E731
    # Eyes, both measured left-to-right in the image: corner A, corner B, upper lid, lower lid, iris.
    for side, (a, c, u, d, iris) in {"R": (33, 133, 159, 145, 468), "L": (362, 263, 386, 374, 473)}.items():
        A, C, U, D, I = P(a), P(c), P(u), P(d), P(iris)
        ew = float(np.linalg.norm(C - A))
        f["ear" + side] = round(float(np.linalg.norm(U - D)) / ew, 4)
        f["irisX" + side] = round(float((I - A).dot(C - A)) / ew**2, 4)
    face_w = float(np.linalg.norm(P(454) - P(234)))
    mw = float(np.linalg.norm(P(291) - P(61)))
    f["mouthOpenRatio"] = round(float(np.linalg.norm(P(14) - P(13))) / mw, 4)
    f["mouthWidth"] = round(mw / face_w, 4)
    xs = [p.x * w for p in lm]
    ys = [p.y * h for p in lm]
    x0, x1, y0, y1 = int(max(0, min(xs))), int(min(w, max(xs))), int(max(0, min(ys))), int(min(h, max(ys)))
    g = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    f["sharp"] = round(float(cv2.Laplacian(cv2.resize(g, (300, 360)), cv2.CV_64F).var()), 1)
    f["box"] = [x0, y0, x1, y1]
    return f


# ---------------------------------------------------------------- scoring (pure python)
def _avg(f, k):
    return (f[k + "Left"] + f[k + "Right"]) / 2


def baseline(features: list[dict]) -> dict:
    """The host's own medians over a set of candidate frames."""
    fs = [f for f in features if f]
    return {
        "ear": statistics.median((f["earL"] + f["earR"]) / 2 for f in fs),
        "pitch": statistics.median(f["pitch"] for f in fs),
    }


def gaze_offset(f) -> float:
    """How far the irises sit from the eye centre, horizontally (0 = centred)."""
    return abs((f["irisXL"] + f["irisXR"]) / 2 - 0.5)


def parts(f: dict, base: dict) -> dict:
    """Each named term of the score, so a reviewer can see why a frame lost."""
    smile = _avg(f, "mouthSmile")
    ear_rel = (f["earL"] + f["earR"]) / 2 / base["ear"]
    p = {
        # + a real smile (capped so a forced max-grin doesn't win) and visible teeth
        "smile": 1.5 * min(smile, 0.8),
        "teeth": 0.8 * min(_avg(f, "mouthUpperUp"), 0.3),
        # - eyes turned away from the lens ("looking into the abyss" / sideways)
        "gaze_away": -10 * max(0.0, gaze_offset(f) - 0.05),
        # - eyes wider than the host's norm: an unsmiling stare / startled look
        "stare": -4 * max(0.0, ear_rel - 1.12),
        # - blink or nearly shut eyes
        #   (a real smile narrows the eyes, so allow more narrowing the bigger the smile)
        "eyes_shut": -3 * max(0.0, _avg(f, "eyeBlink") - 0.4)
        - 4 * max(0.0, 0.8 - 0.2 * min(smile, 0.8) - ear_rel),
        # - lowered brows and head dropped toward the desk (eyes look down / half shut)
        "brows_down": -5 * max(0.0, _avg(f, "browDown") - 0.12),
        #   (pitch in degrees above the host's usual; small nods are normal)
        "head_down": -0.3 * max(0.0, f["pitch"] - base["pitch"] - 4.5),
        # - odd mouth shapes: grimace, lopsided, mid-word pucker/funnel, overly gaping jaw
        "grimace": -5 * max(0.0, _avg(f, "mouthStretch") - 0.05),
        "lopsided": -3 * max(0.0, abs(f["mouthSmileLeft"] - f["mouthSmileRight"]) - 0.1),
        "mid_word": -2 * (f["mouthFunnel"] + f["mouthPucker"] + f["mouthRollLower"]),
        "talking": -2 * max(0.0, f["jawOpen"] - 0.3),
        # - turned head (a slight three-quarter turn is fine), blur
        "turned": -max(0.0, abs(f["yaw"]) - 5) / 40,
        "sharp": min(f["sharp"], 400) / 1000,
    }
    return p


def score(f: dict, base: dict) -> float:
    return round(sum(parts(f, base).values()), 4)


def score_v1(f: dict, base: dict | None = None) -> float:
    """The episode-9 scorer before the eval (kept for the before/after report)."""
    sm = _avg(f, "mouthSmile")
    bl = _avg(f, "eyeBlink")
    ld = _avg(f, "eyeLookDown")
    odd = f["mouthFunnel"] + f["mouthPucker"] + f["mouthRollLower"]
    return round(
        min(sm, 0.8) * 1.5 - bl * 3 - ld * 1.5 - odd * 1.5 - max(0, f["jawOpen"] - 0.35) * 2
        + f["sharp"] / 1000 - abs(f["yaw"]) / 30,
        4,
    )


def pick(scored: list[tuple[float, float]], n: int, gap: float) -> list[tuple[float, float]]:
    """Top-n (score, t) at least ``gap`` seconds apart."""
    out: list[tuple[float, float]] = []
    for s, t in sorted(scored, key=lambda x: -x[0]):
        if all(abs(t - u) >= gap for _, u in out):
            out.append((s, t))
        if len(out) == n:
            break
    return out


def _t_of(path: str, step: float) -> float:
    m = re.search(r"t(\d+(?:\.\d+)?)", os.path.basename(path))
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)", os.path.basename(path))
    return (int(m.group(1)) - 1) * step


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames", help="folder of .jpg frames")
    ap.add_argument("--side", choices=["left", "right", "full"], default="full",
                    help="which half of a side-by-side recording holds this host")
    ap.add_argument("--model", help="face_landmarker.task (or $FACE_LANDMARKER_TASK)")
    ap.add_argument("--step", type=float, default=1.0, help="seconds per frame for c_0001.jpg names")
    ap.add_argument("--pick", type=int, default=9)
    ap.add_argument("--gap", type=float, default=30.0, help="min seconds between picks")
    ap.add_argument("--json", help="write every frame's features and score here")
    a = ap.parse_args(argv)
    import cv2

    rows = {}
    for p in sorted(glob.glob(os.path.join(a.frames, "*.jpg"))):
        im = cv2.imread(p)
        w = im.shape[1]
        if a.side == "left":
            im = im[:, : w // 2]
        elif a.side == "right":
            im = im[:, w // 2 :]
        f = analyze(im, a.model)
        if f:
            rows[p] = f
    base = baseline(list(rows.values()))
    scored = [(score(f, base), _t_of(p, a.step)) for p, f in rows.items()]
    for s, t in pick(scored, a.pick, a.gap):
        print(f"{int(t // 60):02d}:{t % 60:04.1f}  score {s:+.2f}")
    if a.json:
        json.dump({"version": VERSION, "baseline": base,
                   "frames": {p: dict(f, score=score(f, base), t=_t_of(p, a.step)) for p, f in rows.items()}},
                  open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
