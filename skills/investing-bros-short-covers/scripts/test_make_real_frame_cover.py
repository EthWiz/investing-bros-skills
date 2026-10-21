import os, sys
import pytest
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import make_torn_title
pytestmark = pytest.mark.skipif(not os.path.exists(make_torn_title.RUBIK), reason="Rubik font missing")
from make_real_frame_cover import real_frame_cover, fill_crop, W, H


def frame(w=1920, h=1080):
    return Image.new("RGB", (w, h), (90, 120, 150))


def test_fill_crop_is_9x16_without_distortion():
    assert fill_crop(frame()).size == (W, H)
    assert fill_crop(frame(941, 1672)).size == (W, H)


def test_cover_size_and_photo_untouched_at_top_centre():
    out = real_frame_cover(frame(), "כשהריבית", "עולה", "פרק 8")
    assert out.size == (W, H)
    assert out.getpixel((W // 2, int(H * 0.35))) == (90, 120, 150)  # face zone: no overlay


def test_headline_strips_in_lower_third():
    out = real_frame_cover(frame(), "כשהריבית", "עולה", "פרק 8", logo_path=None)
    changed = [y for y in range(0, H, 8) if out.getpixel((W // 2, y)) != (90, 120, 150)]
    assert changed and min(changed) > H * 0.6
