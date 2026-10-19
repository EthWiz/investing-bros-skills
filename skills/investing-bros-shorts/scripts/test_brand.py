"""Tests for brand.py logo cutting and frame layout. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from brand import LOGO_BOXES, LOGO_MAX_H, VERTICAL, extract_logo, extract_solid_logo, fit_logo, make_fonts  # noqa: E402


def _cover(path):
    """1400x1400 navy cover: a big white 'wordmark' block inside the navy box, plus a few star specks."""
    img = np.zeros((1400, 1400, 3), np.uint8) + np.array([12, 24, 60], np.uint8)
    x0, y0, x1, y1 = (int(v * 1400) for v in LOGO_BOXES["navy"])
    img[y0 + 60:y0 + 200, x0 + 80:x1 - 80] = 255           # wordmark
    for y, x in ((y0 + 260, x0 + 40), (y0 + 300, x1 - 50), (y0 + 30, x1 - 30)):
        img[y:y + 4, x:x + 4] = 255                           # 16 px stars
    Image.fromarray(img).save(path)


def test_logo_cut_drops_star_specks(tmp_path):
    cover, out = tmp_path / "cover.png", tmp_path / "logo.png"
    _cover(cover)
    extract_logo(str(cover), str(out))
    logo = np.asarray(Image.open(out))
    alpha = logo[:, :, 3] > 40
    # after cropping to the visible bbox only the wordmark block remains: a solid rectangle
    assert alpha.mean() > 0.95
    assert logo.shape[1] > 3 * logo.shape[0]


def test_vertical_logo_clears_the_headline():
    tall = Image.new("RGBA", (751, 395))                     # the two-line navy wordmark's proportions
    logo = fit_logo(tall, VERTICAL["logo_w"], LOGO_MAX_H["vertical"])
    assert logo.height <= LOGO_MAX_H["vertical"] and logo.width <= VERTICAL["logo_w"]
    assert VERTICAL["logo_y"] + logo.height + 20 <= VERTICAL["headline_margin_v"]


def test_solid_logo_keeps_dark_letters_opaque(tmp_path):
    source, out = tmp_path / "newspaper.png", tmp_path / "solid.png"
    navy = np.array([9, 36, 59], np.uint8)
    pixels = np.zeros((125, 125, 3), np.uint8) + navy
    pixels[5:42, 5:120] = np.array([245, 235, 213], np.uint8)   # cream torn-paper strip
    pixels[35:70, 10:115] = np.array([245, 185, 36], np.uint8)  # connected yellow strip
    pixels[15:30, 35:55] = navy                                # dark letter inside the paper
    Image.fromarray(pixels).save(source)

    extract_solid_logo(str(source), str(out))
    logo = np.asarray(Image.open(out))
    dark = (logo[:, :, :3] == navy).all(axis=2)
    assert dark.any()
    assert (logo[:, :, 3][dark] > 240).any()  # letter pixels are not keyed transparent


def test_make_fonts_instances_all_static_weights(monkeypatch, tmp_path):
    import fontTools.ttLib
    import fontTools.varLib.instancer

    weights = []

    class Names:
        def setName(self, *_args):
            pass

    class Font:
        def __getitem__(self, key):
            assert key == "name"
            return Names()

        def save(self, path):
            path.write_bytes(b"font")

    monkeypatch.setattr(fontTools.ttLib, "TTFont", lambda _path: Font())

    def instance(font, axes, inplace=False):
        assert not inplace
        weights.append(axes["wght"])
        return font

    monkeypatch.setattr(fontTools.varLib.instancer, "instantiateVariableFont", instance)
    made = make_fonts("Heebo[wght].ttf", str(tmp_path / "fonts"))
    assert weights == [600, 800, 900]
    assert [os.path.basename(path) for path in made] == [
        "Heebo-SemiBold.ttf", "Heebo-ExtraBold.ttf", "Heebo-Black.ttf",
    ]


def test_hook_strips_cream_then_mustard_navy_type(tmp_path):
    import glob
    import pytest
    from PIL import Image, features
    from brand import HOOK_Y_BOUNDS, JOURNAL_CREAM, JOURNAL_MUSTARD, hook_strips
    fonts = glob.glob("/usr/share/fonts/**/Heebo*.ttf", recursive=True) + glob.glob("/usr/share/fonts/**/DejaVuSans.ttf", recursive=True)
    if not features.check("raqm") or not fonts:
        pytest.skip("needs Pillow with raqm and a Hebrew font")
    out = tmp_path / "hook.png"
    top, bottom = hook_strips(["למה לסייברקאב", "אין הגה?"], str(out), fonts[0], 960)
    assert 317 < top < 960 < bottom < 1470 - 58 - 40          # centred, clear of logo and captions
    im = Image.open(out).convert("RGBA")
    assert im.size == (1080, 1920) and im.getpixel((5, 5))[3] == 0          # transparent outside the strips
    px = set(im.crop((0, top, 1080, bottom)).getdata())
    near = lambda c: any(abs(p[0] - c[0]) < 14 and abs(p[1] - c[1]) < 14 and abs(p[2] - c[2]) < 14 and p[3] > 250 for p in px)
    assert near(JOURNAL_CREAM) and near(JOURNAL_MUSTARD) and near((9, 36, 59))
    assert HOOK_Y_BOUNDS[0] <= 960 <= HOOK_Y_BOUNDS[1]
