"""facetrack_split.py IN_CLIP.mp4 OUT_9x16.mp4 [--turns turns.json --offset SEC] [--yunet yunet.onnx]
Two-shot / split-screen source (two speakers side by side) -> 1080x1920 crop that follows the ACTIVE speaker,
instead of a centre crop that cuts both faces in half.
 - YuNet face per half (OpenCV FaceDetectorYN; model: face_detection_yunet_2023mar.onnx from opencv_zoo)
 - active speaker = mouth-motion energy with hysteresis (min hold 1.6 s), optionally overridden by speaker turns
   turns.json = [[t_sec_in_full_episode, "L"|"R"], ...] (e.g. exported from Riverside), --offset = clip start in episode
 - crop x smoothed (median + gaussian), clamped inside the speaker's half. Audio is stream-copied.
Writes OUT and OUT.facetrack.json (per-5fps speaker + x0) for inspection."""
import argparse, cv2, json, subprocess, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--turns"); ap.add_argument("--offset", type=float, default=0.0)
ap.add_argument("--yunet", default="yunet.onnx"); a = ap.parse_args()
def probe(k): return subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",f"stream={k}","-of","csv=p=0",a.src],capture_output=True,text=True).stdout.strip()
SW, SH = int(probe("width")), int(probe("height")); FR = probe("r_frame_rate"); SFPS = eval(FR)
FW, FH = 960, int(960 * SH / SW) // 2 * 2
raw = subprocess.run(["ffmpeg","-v","error","-i",a.src,"-vf",f"fps=5,scale={FW}:{FH}","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, FH, FW, 3)
det = cv2.FaceDetectorYN.create(a.yunet, "", (FW // 2, FH), 0.6)
n = len(fr); cx = np.full((n, 2), np.nan); en = np.zeros((n, 2)); prevm = [None, None]
for i, g in enumerate(fr):
    for h in range(2):
        half = np.ascontiguousarray(g[:, h*FW//2:(h+1)*FW//2]); _, f = det.detect(half)
        if f is None or len(f) == 0: prevm[h] = None; continue
        f = max(f, key=lambda r: r[-1]); cx[i, h] = f[0] + f[2]/2 + h*FW//2
        mx = int((f[10]+f[12])/2); my = int((f[11]+f[13])/2); w = int(f[2]*0.35)
        m = cv2.cvtColor(half[max(0,my-w//2):my+w//2, max(0,mx-w):mx+w], cv2.COLOR_BGR2GRAY)
        m = cv2.resize(m, (32, 16)).astype(np.float32) if m.size else None
        if m is not None and prevm[h] is not None: en[i, h] = np.abs(m - prevm[h]).mean()
        prevm[h] = m
sm = np.stack([np.convolve(en[:, h], np.ones(9)/9, mode="same") for h in range(2)], 1)
spk = np.zeros(n, int); cur = int(sm[:10, 1].mean() > sm[:10, 0].mean()); last = 0
for i in range(n):
    o = 1 - cur
    if sm[i, o] > sm[i, cur] * 1.35 and i - last >= 8: cur = o; last = i
    spk[i] = cur
if a.turns:
    T = json.load(open(a.turns))
    for i in range(n):
        tt = a.offset + i/5 + 0.3; prev = [s for t_, s in T if t_ <= tt]
        if prev: spk[i] = 1 if prev[-1] == "R" else 0
CROPW = int(round(SH * 9 / 16)) // 2 * 2; scale = SW / FW; x0 = np.zeros(n)
for h in range(2):
    xs = cx[:, h]; idx = np.arange(n); ok = ~np.isnan(xs)
    xs = np.interp(idx, idx[ok], xs[ok]) if ok.any() else np.full(n, FW/4 + h*FW/2)
    med = np.array([np.median(xs[max(0,i-3):i+4]) for i in range(n)])
    g = np.exp(-0.5*(np.arange(-10, 11)/3.0)**2); g /= g.sum()
    xs = np.convolve(np.pad(med, 10, mode="edge"), g, mode="valid") * scale
    x0 = np.where(spk == h, np.clip(xs - CROPW/2, h*SW/2, (h+1)*SW/2 - CROPW), x0)
json.dump({"fps": 5, "x0": [round(float(v), 1) for v in x0], "spk": spk.tolist()}, open(a.out + ".facetrack.json", "w"))
rd = subprocess.Popen(["ffmpeg","-v","error","-i",a.src,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","1080x1920","-r",FR,"-i","-","-i",a.src,
                       "-map","0:v","-map","1:a?","-c:v","libx264","-preset","veryfast","-crf","14","-pix_fmt","yuv420p","-c:a","copy","-shortest",a.out],stdin=subprocess.PIPE)
k = 0
while True:
    b = rd.stdout.read(SW*SH*3)
    if len(b) < SW*SH*3: break
    im = np.frombuffer(b, np.uint8).reshape(SH, SW, 3); x = int(x0[min(n-1, int(k / SFPS * 5))]) if n else (SW-CROPW)//2
    wr.stdin.write(cv2.resize(im[:, x:x+CROPW], (1080, 1920), interpolation=cv2.INTER_LANCZOS4).tobytes()); k += 1
wr.stdin.close(); wr.wait()
print("speaker switches", int((np.diff(spk) != 0).sum()), "frames", k, "->", a.out)
