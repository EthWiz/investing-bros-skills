import importlib.util
import json
from pathlib import Path

from PIL import Image

spec = importlib.util.spec_from_file_location("check_cover", Path(__file__).with_name("check_cover.py"))
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)


def img(tmp_path, name, size, fmt="JPEG", mode="RGB"):
    p = tmp_path / name
    Image.new(mode, size, (9, 36, 59) if mode == "RGB" else (9, 36, 59, 255)).save(p, fmt)
    return p


def register(tmp_path, **row):
    p = tmp_path / "artwork-register.json"
    p.write_text(json.dumps({"artifacts": [row]}, ensure_ascii=False), encoding="utf-8")
    return p


def test_good_files_pass(tmp_path):
    assert cc.main([str(img(tmp_path, "thumbnail-פרק-8.jpg", (1920, 1080))), "--kind", "episode-wide", "--episode", "8"]) == 0
    assert cc.main([str(img(tmp_path, "cover-פרק-8.png", (3000, 3000), "PNG")), "--kind", "episode-square"]) == 0
    assert cc.main([str(img(tmp_path, "סגמנט-01-צלילה-זהב-thumb.jpg", (1280, 720))), "--kind", "segment-wide"]) == 0
    assert cc.main([str(img(tmp_path, "שורט-01-סוויפט-cover.jpg", (1080, 1920))), "--kind", "shorts-vertical"]) == 0


def test_wrong_name_episode_and_format(tmp_path):
    errs, _, _ = cc.check_file(img(tmp_path, "thumbnail-פרק-7.jpg", (1920, 1080)), "episode-wide", 8)
    assert errs == ["name says episode 7, expected 8"]
    errs, _, _ = cc.check_file(img(tmp_path, "thumb.jpg", (1920, 1080)), "episode-wide")
    assert len(errs) == 1 and "does not match" in errs[0]
    p = tmp_path / "thumbnail-פרק-8.jpg"
    Image.new("RGB", (1920, 1080)).save(p, "PNG")                       # PNG bytes behind a .jpg name
    errs, _, _ = cc.check_file(p, "episode-wide")
    assert errs == ["is PNG, episode-wide must be JPEG"]


def test_geometry(tmp_path):
    errs, _, _ = cc.check_file(img(tmp_path, "thumbnail-פרק-8.jpg", (1672, 941)), "episode-wide")
    assert errs == []                                                  # within 1% of 16:9, above the minimum
    errs, warns, _ = cc.check_file(img(tmp_path, "thumbnail-פרק-8.jpg", (1254, 1254)), "episode-wide")
    assert any("not 16:9" in e for e in errs)                          # a square padded as a thumbnail
    errs, _, _ = cc.check_file(img(tmp_path, "שורט-01-x-cover.jpg", (941, 1672)), "shorts-vertical")
    assert any("exactly 1080x1920" in e for e in errs)                 # not upscaled yet
    errs, warns, _ = cc.check_file(img(tmp_path, "cover-פרק-8.png", (1254, 1254), "PNG"), "episode-square")
    assert any("1400x1400 minimum" in e for e in errs)
    errs, warns, _ = cc.check_file(img(tmp_path, "cover-פרק-8.png", (2048, 2048), "PNG"), "episode-square")
    assert errs == [] and warns and "target is 3000x3000" in warns[0]


def test_transparency_and_not_an_image(tmp_path):
    errs, _, _ = cc.check_file(img(tmp_path, "cover-פרק-8.png", (3000, 3000), "PNG", "RGBA"), "episode-square")
    assert errs == ["has transparency; covers must be flat RGB"]
    p = tmp_path / "thumbnail-פרק-8.jpg"
    p.write_text("<html>quota</html>")
    errs, _, dims = cc.check_file(p, "episode-wide")
    assert dims is None and "not a readable image" in errs[-1]


def test_youtube_size_limit(tmp_path, monkeypatch):
    p = img(tmp_path, "thumbnail-פרק-8.jpg", (1920, 1080))
    monkeypatch.setitem(cc.KINDS["episode-wide"], "max_bytes", 10)
    errs, _, _ = cc.check_file(p, "episode-wide")
    assert any("2 MB" in e for e in errs)


def test_register_rules(tmp_path):
    seg = img(tmp_path, "סגמנט-01-צלילה-זהב-thumb.jpg", (1280, 720))
    ok = register(tmp_path, output_path=f"segments/{seg.name}", format="segment-wide",
                  width=1280, height=720, episode_tab=False)
    assert cc.check_register(seg, ok, "segment-wide", (1280, 720)) == []
    bad = register(tmp_path, output_path=seg.name, format="episode-wide", width=1920, height=1080, episode_tab=True)
    errs = cc.check_register(seg, bad, "segment-wide", (1280, 720))
    assert len(errs) == 3 and "no episode tab" in errs[-1]
    missing = register(tmp_path, output_path="other.jpg", format="segment-wide")
    assert "no artifact" in cc.check_register(seg, missing, "segment-wide", (1280, 720))[0]
    ep = img(tmp_path, "thumbnail-פרק-8.jpg", (1920, 1080))
    no_tab = register(tmp_path, output_path=ep.name, format="episode-wide", width=1920, height=1080, episode_tab=None)
    assert "must be true" in cc.check_register(ep, no_tab, "episode-wide", (1920, 1080))[0]
