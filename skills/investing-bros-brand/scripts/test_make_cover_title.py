import glob
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("make_cover_title", Path(__file__).with_name("make_cover_title.py"))
mct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mct)


def test_cover_crop_never_stretches():
    assert mct.cover_crop((1254, 1254)) == (274, 0, 979, 1254)      # square art: trim the sides
    assert mct.cover_crop((941, 1672)) == (0, 0, 940, 1672)        # imagegen 9:16: a 1 px trim, no squash
    assert mct.cover_crop((1080, 2400)) == (0, 240, 1080, 2160)    # too tall: trim top and bottom


def test_title_must_stay_in_centre_square():
    assert mct.title_position((900, 400)) == (90, mct.TITLE_TOP)
    with pytest.raises(ValueError):
        mct.title_position((900, 1100))                             # runs past y 1500
    with pytest.raises(ValueError):
        mct.title_position((900, 300), top=300)                     # starts above y 420
    with pytest.raises(ValueError):
        mct.title_position((1200, 300))


def test_type_scale_refuses_tiny_type():
    assert mct.type_scale([800, 600]) == 1.0
    assert mct.type_scale([1200, 900]) == pytest.approx(mct.MAX_TITLE_W / 1200)
    with pytest.raises(ValueError, match="too long"):
        mct.type_scale([2500, 900])


def test_logo_bottom_right():
    x, y = mct.logo_position((260, 157))
    assert (x + 260, y + 157) == (mct.W - mct.LOGO_MARGIN, mct.H - mct.LOGO_MARGIN)


def test_renders_1080x1920(tmp_path):
    from PIL import Image, features
    fonts = glob.glob("/usr/share/fonts/**/Heebo*.ttf", recursive=True)
    if not features.check("raqm") or not fonts:
        pytest.skip("needs Pillow with raqm and Heebo")
    art = tmp_path / "art.png"
    Image.new("RGB", (1254, 1254), mct.NAVY).save(art)
    out = tmp_path / "cover.jpg"
    logo = Path(__file__).resolve().parent.parent / "assets" / "logo-solid.png"
    mct.make_cover(str(art), str(out), "מי ינצח", "במרוץ הרובוטקסי?", fonts[0], "פרק 1", str(logo))
    im = Image.open(out)
    assert (im.format, im.size) == ("JPEG", (1080, 1920))
