import json, math, subprocess, sys, numpy as np, cv2
from PIL import Image
import plan, mg, captions as cap

FPS = 30; W, H = 1080, 1920; SFPS = 25
OUT = "out.mp4"   # set by patch_reel.py
tm, content_dur = plan.timemap()
total = content_dur + (plan.SRC_END - plan.CONTENT_END)
NF = int(math.floor(total * FPS))
chunks = plan.chunks()
json.dump(chunks, open("captions_chunks.json", "w"), ensure_ascii=False, indent=1)

def wout(word, which="s"):
    for c in chunks:
        for w in c["words"]:
            if w["word"] == word: return w[which]
# Motion-graphic cues: mgs.json = [[kind, anchor_word, offset_s, dur_s], ...]; kind must exist in mg.KINDS
import os
MGS = [(k, round(wout(w) + off, 2), d) for k, w, off, d in json.load(open('mgs.json')) if wout(w) is not None] if os.path.exists('mgs.json') else []
json.dump(MGS, open("mg_schedule.json", "w"))
LEAD = 0.04
ANCHOR = (540.0, 1250.0)
TITLE_RECTS = []
TITLE_IMG = np.array(Image.open('title.png')) if os.path.exists('title.png') else None
BAR_RECT = (0, 0, 1, 1)

def seg_of(t):
    for k, (a, b, o) in enumerate(tm):
        nxt = tm[k + 1][2] if k + 1 < len(tm) else content_dur
        if t < nxt: return k, a, b, o
    return len(tm) - 1, *tm[-1]

def zoom_for(k, a, b, o, t):
    base = 1.0 if k % 2 == 0 else 1.12
    dur = b - a
    slow = 0.045 * min(1.0, (t - o) / max(dur, 1e-3)) if dur > 2.5 else 0.0
    return base + slow

def warp(fr, s):
    if abs(s - 1) < 1e-4: return fr
    M = np.array([[s, 0, ANCHOR[0] * (1 - s)], [0, s, ANCHOR[1] * (1 - s)]], np.float32)
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

FILL_RECTS = []
def clean_overlays(fr):
    """fill burned title/bar boxes with a vertical blend of the rows just outside, so the zoomed
    copy of the boxes never peeks out from behind the re-pasted originals"""
    out = fr.copy()
    for (x0, y0, x1, y1) in FILL_RECTS:
        top = fr[y0 - 3:y0 - 1, x0:x1].astype(np.float32).mean(0)
        bot = fr[y1 + 1:y1 + 3, x0:x1].astype(np.float32).mean(0)
        k = np.linspace(0, 1, y1 - y0)[:, None, None]
        out[y0:y1, x0:x1] = (top[None] * (1 - k) + bot[None] * k).astype(np.uint8)
    return out

def alpha_over(dst, src_rgba, x, y, a=1.0):
    h, w = src_rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src_rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    al = s[..., 3:4] / 255.0 * a
    d = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (s[..., :3] * al + d * (1 - al)).astype(np.uint8)

cap_cache = {}
def caption_img(ci, wi):
    key = (ci, wi)
    if key not in cap_cache:
        cap_cache[key] = np.array(cap.render_chunk([w["word"] for w in chunks[ci]["words"]], wi))
    return cap_cache[key]

def draw_captions(fr, t):
    t = t + LEAD
    for ci, c in enumerate(chunks):
        if c["s"] <= t < c["e"]:
            ws = c["words"]; wi = 0
            for j, w in enumerate(ws):
                if t >= w["s"]: wi = j
            im = caption_img(ci, wi)
            u = min(1.0, (t - c["s"]) / 0.16)
            sc = mg.ease_back(u, 2.2) * 0.25 + 0.75 if u < 1 else 1.0
            a = min(1.0, (t - c["s"]) / 0.06)
            if sc != 1.0:
                im = cv2.resize(im, (max(1, int(im.shape[1] * sc)), max(1, int(im.shape[0] * sc))), interpolation=cv2.INTER_AREA)
            alpha_over(fr, im, (W - im.shape[1]) // 2, cap.CAP_Y - im.shape[0] // 2, a)
            return

def mg_at(t):
    for kind, s, d in MGS:
        if s <= t < s + d: return kind, t - s, d
    return None

def main(limit=None):
    rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", plan.SRC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", "mix.wav", "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-pix_fmt", "yuv420p",
                           "-x264-params", "keyint=60:min-keyint=30", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                           "-movflags", "+faststart", "-shortest", OUT], stdin=subprocess.PIPE)
    cur_idx, cur = -1, None
    for n in range(NF if limit is None else limit):
        t = n / FPS
        in_content = t < content_dur
        if in_content:
            k, a, b, o = seg_of(t); ts = min(b - 1e-3, a + (t - o))
        else:
            ts = plan.CONTENT_END + (t - content_dur)
        want = int(round(ts * SFPS))
        while cur_idx < want:
            raw = rd.stdout.read(W * H * 3)
            if len(raw) < W * H * 3: break
            cur = np.frombuffer(raw, np.uint8).reshape(H, W, 3); cur_idx += 1
        src = cur
        if not in_content:
            wr.stdin.write(src.tobytes()); continue
        fr = warp(clean_overlays(src), zoom_for(k, a, b, o, t)).copy()
        m = mg_at(t)
        if m:
            kind, lt, d = m
            card, (cx, cy), ca, bgk = mg.render_card(kind, lt, d)
            if bgk > 0:
                small = cv2.resize(fr, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
                small = cv2.GaussianBlur(small, (0, 0), 3)
                bl = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
                bl = bl * 0.42 + np.array([0, 6, 40], np.float32) * 0.58
                fr = (fr.astype(np.float32) * (1 - bgk) + bl * bgk).astype(np.uint8)
            alpha_over(fr, np.array(card), cx, cy, ca)
        for (x0, y0, x1, y1) in TITLE_RECTS + [BAR_RECT]:
            fr[y0:y1, x0:x1] = src[y0:y1, x0:x1]
        if TITLE_IMG is not None: alpha_over(fr, TITLE_IMG, 0, 0)
        draw_captions(fr, t)
        wr.stdin.write(fr.tobytes())
        if n % 150 == 0: print("frame", n, "/", NF, flush=True)
    wr.stdin.close(); wr.wait(); rd.kill()
    print("done", OUT, "frames", NF, "content", round(content_dur, 3), "total", round(total, 3))

if __name__ == "__main__":
    print("MGS", MGS)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
