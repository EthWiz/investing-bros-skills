"""Tests for brand.py logo cutting and frame layout. Run: python3 -m pytest skills/investing-bros-shorts/scripts"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from brand import LOGO_BOXES, LOGO_MAX_H, VERTICAL, extract_logo, fit_logo  # noqa: E402


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
