"""Tests for lesson_background.py and the background in make_lesson_base.py build."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import lesson_background  # noqa: E402
from make_lesson_base import build_cmd, filter_graph, fingerprint, manifest, status  # noqa: E402

TAKES = [{"beat": 1, "file": "a.mov", "from": 2.0, "to": 43.0}, {"beat": 2, "file": "b.mov", "from": 0.5, "to": 19.2}]
VISION = {"method": "vision", "image": "assets/bg.jpg"}


def test_a_background_block_is_checked_and_gets_its_key_defaults():
    with pytest.raises(SystemExit, match="method"):
        lesson_background.check({"method": "magic", "image": "x.jpg"})
    with pytest.raises(SystemExit, match="image"):
        lesson_background.check({"method": "vision"})
    bg = lesson_background.check({"method": "chroma", "image": "x.jpg", "key": {"similarity": 0.2}})
    assert bg["key"] == {"color": "0x00B140", "similarity": 0.2, "blend": 0.06}


def test_vision_puts_each_take_on_its_own_copy_of_the_image_with_its_own_matte():
    g = filter_graph(TAKES, lesson_background.check(VISION))
    # inputs: takes 0-1, the image 2-3, the mattes 4-5
    assert "[2:v]scale=1920:1080,setsar=1,format=rgba[bg0]" in g and "[3:v]" in g
    assert "[4:v]trim=2.0:43.0,setpts=PTS-STARTPTS" in g and "[5:v]trim=0.5:19.2" in g   # matte trimmed like its take
    assert "[c0][m0]alphamerge[fg0]" in g and "[bg1][fg1]overlay=shortest=1,format=yuv420p[v1]" in g
    assert "[v0][a0][v1][a1]concat=n=2" in g and "chromakey" not in g


def test_chroma_keys_the_take_and_needs_no_matte():
    g = filter_graph(TAKES, lesson_background.check({"method": "chroma", "image": "bg.jpg"}))
    assert "chromakey=color=0x00B140:similarity=0.12:blend=0.06,format=rgba,despill=type=green[fg0]" in g
    assert "alphamerge" not in g and "[4:v]" not in g


def test_the_build_command_adds_the_image_per_take_then_the_mattes(tmp_path):
    for name in ("a.mov", "b.mov"):
        (tmp_path / name).write_text("v")
    cmd = build_cmd(TAKES, tmp_path, tmp_path / "base.mp4", background=lesson_background.check(VISION),
                    image=tmp_path / "bg.jpg", mattes=[tmp_path / "m1.mkv", tmp_path / "m2.mkv"])
    inputs = [cmd[i + 1] for i, x in enumerate(cmd) if x == "-i"]
    assert inputs == [str(tmp_path / n) for n in ("a.mov", "b.mov", "bg.jpg", "bg.jpg", "m1.mkv", "m2.mkv")]
    assert cmd.count("-loop") == 2
    with pytest.raises(SystemExit, match="matte"):
        lesson_background.take_chain(0, 0.0, 1.0, "[0:v]trim=0.0:1.0", lesson_background.check(VISION), 1)


def test_the_manifest_carries_the_background_by_its_package_name():
    cfg = {"lesson": 1, "takes": TAKES[:1], "background": dict(VISION)}
    m = manifest(cfg, json.dumps(cfg), "b.mp4", 1.0, "v", "t")
    assert m["background"] == {"method": "vision", "image": "bg.jpg"} and cfg["background"]["image"] == "assets/bg.jpg"


def test_a_new_background_means_base_props_and_render_again(tmp_path):
    cfg = {"lesson": 1, "takes": TAKES[:1], "proofread": {}, "script": {"revision": "r"}}
    (tmp_path / "a.mov").write_text("v")
    (tmp_path / "קטע-01.json").write_text("[]")
    record = {"made": "t", "fingerprint": fingerprint(cfg), "takes": []}
    assert "background" not in fingerprint(cfg)                 # records made before backgrounds still match
    cfg["background"] = dict(VISION)
    lines, todo = status(cfg, tmp_path, tmp_path, record, hasher=lambda p: "h")
    assert "the background changed" in lines and todo == ["base", "props", "render"]


def test_check_lesson_fingerprints_the_background_the_same_way():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "investing-bros-remotion" / "scripts"))
    import check_lesson
    cfg = {"lesson": 1, "takes": TAKES, "proofread": {"1": "x"}, "background": dict(VISION)}
    assert check_lesson.fingerprint(cfg) == fingerprint(cfg)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_the_chroma_key_turns_green_into_the_background_and_keeps_the_rest(tmp_path):
    take = tmp_path / "green.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "color=0x00B140:s=1920x1080:d=1:r=30,drawbox=x=760:y=340:w=400:h=400:color=0x808080:t=fill",
                    "-f", "lavfi", "-i", "sine=frequency=220:sample_rate=48000", "-t", "1", "-c:v", "libx264", "-qp", "0",
                    "-c:a", "aac", str(take)], check=True)
    bg = tmp_path / "bg.png"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=0x09243B:s=1920x1080:d=1", "-frames:v", "1",
                    str(bg)], check=True)
    out = tmp_path / "base.mp4"
    takes = [{"beat": 1, "file": "green.mp4", "from": 0.0, "to": 1.0}]
    subprocess.run(build_cmd(takes, tmp_path, out, background=lesson_background.check({"method": "chroma", "image": "bg"}),
                             image=bg), check=True)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    px = lambda x, y: raw[(y * 1920 + x) * 3:(y * 1920 + x) * 3 + 3]  # noqa: E731
    corner, centre = px(40, 40), px(960, 540)
    assert abs(corner[0] - 0x09) < 12 and abs(corner[1] - 0x24) < 12 and abs(corner[2] - 0x3B) < 12   # navy
    assert all(abs(c - 0x80) < 12 for c in centre)                                                      # grey kept
