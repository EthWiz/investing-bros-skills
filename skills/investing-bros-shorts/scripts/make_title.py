"""make_title.py "TITLE" out.png  - navy rounded title box, Heebo Black white text, gold underline. PIL+raqm (no libass).
Box fits inside TITLE_BOX (x0,y0,x1,y1) on the 1080x1920 frame; shorts.sh keeps that region unzoomed."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, features
assert features.check("raqm"), "Pillow built without raqm - Hebrew shaping/bidi would be wrong"
FONT = os.environ.get("HEEBO_FONT", "fonts/Heebo-Variable.ttf")  # Heebo variable font (wght axis; 900 = Black). Not in the repo.
NAVY = (12, 27, 58, 235); GOLD = (245, 183, 31, 255)  # house accent #F5B71F
TITLE_BOX = (90, 150, 990, 380)
def main(txt, out):
    x0, y0, x1, y1 = TITLE_BOX; W = x1 - x0; size = 92
    while True:
        f = ImageFont.truetype(FONT, size); f.set_variation_by_axes([900])
        d0 = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        bb = d0.multiline_textbbox((0, 0), txt, font=f, direction="rtl", language="he", align="center", spacing=8)
        if bb[2] - bb[0] <= W - 80 or size <= 48: break
        size -= 4
    tw, th = int(bb[2] - bb[0]), int(bb[3] - bb[1])
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bw, bh = tw + 80, th + 60; bx = (1080 - bw) // 2
    d.rounded_rectangle((bx, y0, bx + bw, y0 + bh), 26, fill=NAVY)
    d.rectangle((bx + 40, y0 + bh - 12, bx + bw - 40, y0 + bh - 6), fill=GOLD)
    d.multiline_text((540, y0 + bh / 2 - 4), txt, font=f, fill=(255, 255, 255, 255), anchor="mm", direction="rtl",
                     language="he", align="center", spacing=8)
    im.save(out); print(f"{bx},{y0},{bx+bw},{y0+bh}")
if __name__ == "__main__": main(sys.argv[1].replace("\\n", "\n"), sys.argv[2])
