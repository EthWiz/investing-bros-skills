#!/usr/bin/env python3
"""Re-extract the eval stills from the raw episode recording by timestamp (needs ffmpeg).

  extract_frames.py RECORDING.mp4 OUT_DIR
Writes OUT_DIR/<ID>.jpg: the host's 960x1080 half of the side-by-side frame. The images
are not committed (public repo, see README).
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rec, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
L = json.load(open(os.path.join(HERE, "labels.json")))
for k, v in L["items"].items():
    side = L["source"][v["host"] + "_side"]
    x0 = "0" if side == "left" else "iw/2"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(v["t_sec"]), "-i", rec, "-frames:v", "1",
                    "-vf", f"crop=iw/2:ih:{x0}:0", "-q:v", "1", os.path.join(out, k + ".jpg")], check=True)
    print(k, v["t_sec"])
