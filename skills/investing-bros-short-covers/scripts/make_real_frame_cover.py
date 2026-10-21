"""Real-frame Short cover (v2, torn-strip hook over a real podcast frame).
Composites graphics ONLY; the photo is cropped/resized proportionally, never retouched.
CLI: python3 make_real_frame_cover.py FRAME.jpg OUT.jpg "line1" "line2" "פרק 8" [--face-cx 0.5]
Spec: investing-bros-brand/references/shorts-covers.md (section B, v2 measurements).
"""
import argparse, os
from PIL import Image
from make_torn_title import torn_strip, shadow, font

W, H = 1080, 1920
# Sampled from Amitai's ep8 references (Oct 2026)
CREAM, MUST, INK, TAB = (251, 238, 223), (252, 175, 2), (1, 21, 38), (253, 240, 226)
LOGO = os.path.join(os.path.dirname(__file__), "../../investing-bros-brand/assets/logo-solid.png")
# Layout as fractions of the 1080x1920 frame
LOGO_BOX = (0.075, 0.025, 0.20)      # x, y, width
TITLE_CY = 0.79                      # centre of the two-strip headline
TITLE_W = 0.74                       # strip width (both strips, x 0.13-0.87)
TAB_GAP = -0.004                     # tab touches/overlaps the mustard strip's lower edge


def fill_crop(frame, face_cx=0.5):
    """Scale to cover 9:16 and crop; face_cx = horizontal face centre (0..1) to keep centred."""
    s = max(W / frame.width, H / frame.height)
    im = frame.convert("RGB").resize((round(frame.width * s), round(frame.height * s)), Image.LANCZOS)
    x = min(max(int(im.width * face_cx - W / 2), 0), im.width - W)
    y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def _strip(text, color, wmax, angle, seed):
    """Both headline strips share one width (~74% of frame) like the reference; text is centred."""
    im = torn_strip(text, color, 150, angle, pad=(36, 18), seed=seed, fg=INK)
    if im.width < wmax:
        extra = (wmax - im.width) // 2
        im = torn_strip(text, color, 150, angle, pad=(36 + extra, 18), seed=seed, fg=INK)
    return _fit(im, wmax)


def _fit(im, wmax):
    return im if im.width <= wmax else im.resize((wmax, int(im.height * wmax / im.width)), Image.LANCZOS)


def real_frame_cover(frame, line1, line2, episode, face_cx=0.5, logo_path=LOGO):
    bg = fill_crop(frame, face_cx).convert("RGBA")
    wmax = int(W * TITLE_W)
    a = _strip(line1, CREAM, wmax, 0.8, 21)
    b = _strip(line2, MUST, wmax, -0.6, 22)
    ov = int(min(a.height, b.height) * 0.06)
    top = int(H * TITLE_CY - (a.height + b.height - ov) / 2)
    bg.alpha_composite(shadow(a, (4, 6), 6, 90), ((W - a.width) // 2 - 20, top - 20))
    yb = top + a.height - ov
    bg.alpha_composite(shadow(b, (4, 6), 6, 90), ((W - b.width) // 2 - 20, yb - 20))
    t = torn_strip(episode, TAB, 64, 0, pad=(34, 16), seed=23, fg=INK, fringe=3)
    bg.alpha_composite(shadow(t, (2, 3), 3, 80), ((W - t.width) // 2 - 20, yb + b.height + int(H * TAB_GAP) - 20))
    if logo_path and os.path.exists(logo_path):
        lg = Image.open(logo_path).convert("RGBA")
        lw = int(W * LOGO_BOX[2]); lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
        bg.alpha_composite(lg, (int(W * LOGO_BOX[0]), int(H * LOGO_BOX[1])))
    return bg.convert("RGB")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("frame"); p.add_argument("out"); p.add_argument("line1"); p.add_argument("line2"); p.add_argument("episode")
    p.add_argument("--face-cx", type=float, default=0.5)
    a = p.parse_args()
    real_frame_cover(Image.open(a.frame), a.line1, a.line2, a.episode, a.face_cx).save(a.out, quality=92)
