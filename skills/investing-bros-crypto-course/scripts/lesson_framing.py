"""Line up the framing of a lesson's takes (make_lesson_base.py frame): the same face size in the same place.

Takes recorded on different days, or after the phone reconnected, are framed differently: in lesson 1's OBS
takes the face was 617-714 px wide and its centre 784-969 px across. With a background replacement the takes can
be lined up in post. Each take is scaled so the face has one width and moved so it sits at one x, anchored on the
bottom edge, so the cut-off shoulders stay on the frame's edge. Two rules keep it invisible:
- a take whose head is cut off at the top is never shrunk: the flat cut would show on the background;
- a take is only moved down, never up: moving up opens a gap under the shoulders.
The faces are measured with Apple Vision (face_box.swift, macOS). The result goes into each take of the config as
`frame` {scale, x, y} and into the config's `face` (the point the template's punch-ins and bubble centre on), so a
rebuild from the Drive package needs no measuring.
"""
import json
import statistics
import subprocess
from pathlib import Path

import lesson_background

W, H = 1920, 1080
FACE_X = 840            # the template's face x (Lesson.tsx), between the left wall space and the centre
HEAD_CUT = 0.18         # a face box starting this close to the top: the head is cut off by the frame
SCALES = (0.8, 1.25)    # beyond these the take is too soft or too small; re-record instead
EYES_MOUTH = 0.55       # the template's face point, as a share of the face box height from its top
SWIFT = Path(__file__).resolve().parent / "face_box.swift"


def measure(take: Path, tool: Path) -> dict:
    """The take's median face box: {samples, cx, top, w, h, width, height} in the take's pixels."""
    out = subprocess.run([str(tool), str(take)], capture_output=True, text=True, check=True).stdout
    face = json.loads(out)
    if face["samples"] == 0:
        raise SystemExit(f"error: no face found in {take}")
    return face


def to_base(face: dict) -> dict:
    """A face box measured in the take's pixels, in the 1920x1080 base the take is scaled to."""
    k = W / face.get("width", W)
    return {key: face[key] * k for key in ("cx", "top", "w", "h")}


def plan(faces: dict, width=None, x=FACE_X) -> dict:
    """faces {beat: box in base pixels} -> {"width", "takes": {beat: {scale, x, y}}, "face": {x, y}}.
    The face width defaults to the smallest one, so no take is enlarged, except that takes with the head cut off
    keep at least their own width (they can't shrink)."""
    cut = {b for b, f in faces.items() if f["top"] < HEAD_CUT * H}
    if width is None:
        width = max([min(f["w"] for f in faces.values())] + [faces[b]["w"] for b in cut])
    scales = {}
    for b, f in faces.items():
        s = width / f["w"]
        if b in cut:
            s = max(1.0, s)
        if not SCALES[0] <= s <= SCALES[1]:
            raise SystemExit(f"error: beat {b}: its face would need a scale of {s:.2f}, outside {SCALES[0]}-{SCALES[1]}; "
                             "re-record it or pick another --width")
        scales[b] = s
    tops = {b: H - scales[b] * (H - f["top"]) for b, f in faces.items()}       # after scaling from the bottom edge
    free = [t for b, t in tops.items() if b not in cut]
    line = statistics.median(free) if free else None
    takes, points = {}, []
    for b, f in sorted(faces.items()):
        s = scales[b]
        down = max(0.0, line - tops[b]) if line is not None and b not in cut else 0.0
        takes[b] = {"scale": round(s, 4), "x": round(x - s * f["cx"], 1), "y": round(H - s * H + down, 1)}
        points.append(tops[b] + down + EYES_MOUTH * s * f["h"])
    return {"width": round(width, 1), "takes": takes, "face": {"x": x, "y": round(statistics.median(points))}}


def face_tool():
    return lesson_background.swift_tool(SWIFT, "face_box")
