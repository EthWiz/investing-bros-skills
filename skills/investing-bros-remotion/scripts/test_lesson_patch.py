"""Tests for lesson_patch.py: what a --patch re-renders, and the splice itself (with ffmpeg, when it has libx264)."""
import copy
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
import lesson_patch as lp  # noqa: E402
from lesson_patch import FPS  # noqa: E402


def props():
    return {
        "duration": 120.0, "beats": [{"n": 1, "start": 0, "end": 120.0}], "face": {"x": 960, "y": 717},
        "title": ["שיעור"], "lesson": 1, "parts": [], "partStarts": [], "assets": {},
        "disclaimer": {"start": 80.0, "end": 90.0},
        "captions": [{"start": 10.0, "end": 12.0, "words": [{"w": "פי", "start": 10.0, "end": 10.4},
                                                            {"w": "3.5.", "start": 10.4, "end": 11.0}]},
                     {"start": 50.0, "end": 52.0, "words": [{"w": "שלום", "start": 50.0, "end": 51.0}]}],
        "segments": [{"start": 0, "end": 30.0, "mode": "full", "zoom": 1.0},
                     {"start": 30.0, "end": 52.0, "mode": "bubble", "scene": "growth-bars", "content": {"bars": []}},
                     {"start": 52.0, "end": 120.0, "mode": "full", "zoom": 1.0}],
        "at": {"name": 5.0, "f_coin": 40.0},
    }


FP = {"template": "t", "base": "b", "assets": {}}


def test_nothing_changed_means_nothing_to_render():
    assert lp.changed_ranges(props(), props()) == []


def test_a_changed_caption_is_re_rendered_around_its_words_only():
    new = props()
    new["captions"][0]["words"][1]["w"] = "3.5"
    assert lp.changed_ranges(props(), new) == [(9.5, 12.5)]


def test_a_changed_scene_is_re_rendered_over_its_whole_segment_and_the_glide_out():
    new = props()
    new["segments"][1]["content"] = {"bars": [{"label": "ביטקוין"}]}
    assert lp.changed_ranges(props(), new) == [(29.0, 53.5)]


def test_a_moved_anchor_reaches_to_the_end_of_the_scene_that_uses_it():
    new = props()
    new["at"]["f_coin"] = 41.0
    assert lp.changed_ranges(props(), new) == [(39.0, 53.5)]


def test_a_moved_disclaimer_covers_both_strips_and_close_ranges_merge():
    new = props()
    new["disclaimer"] = {"start": 81.0, "end": 90.0}
    assert lp.changed_ranges(props(), new) == [(79.0, 91.5)]


def test_lesson_wide_changes_base_and_images_always_need_a_full_render():
    new = props()
    new["duration"] = 121.0
    assert lp.why_full(props(), new, FP, FP, explicit=True) == ["props 'duration' changed"]
    assert lp.why_full(props(), props(), FP, {**FP, "base": "x"}, explicit=True) == ["the base changed"]
    assert lp.why_full(props(), props(), FP, {**FP, "assets": {"a": "1"}}, explicit=True) == ["a scene image changed"]


def test_a_template_change_is_patched_only_over_a_range_the_caller_names():
    changed = {**FP, "template": "t2"}
    assert "the template changed" in lp.why_full(props(), props(), FP, changed, explicit=False)[0]
    assert lp.why_full(props(), props(), FP, changed, explicit=True) == []


def test_ranges_widen_to_whole_gops_of_the_previous_export():
    kf, total = [0, 250, 500], 750
    spans = lp.snap([(10.0, 12.0)], kf, total)
    assert spans == [(250, 500)]
    assert lp.plan(spans, total) == [("copy", 0, 250), ("render", 250, 500), ("copy", 500, 750)]
    spans = lp.snap([(1.0, 2.0), (20.0, 24.9)], kf, total)       # the second runs to the end
    assert spans == [(0, 250), (500, 750)]
    assert lp.plan(spans, total) == [("render", 0, 250), ("copy", 250, 500), ("render", 500, 750)]
    assert lp.snap([(5.0, 9.0), (8.0, 10.0)], kf, total) == [(0, 500)]   # overlapping GOPs merge


def test_the_sidecar_keeps_the_props_and_the_fingerprint(tmp_path):
    out = tmp_path / "lesson.mp4"
    lp.write_sidecar(out, props(), FP)
    assert lp.sidecar_path(out).name == "lesson.mp4.render.json"
    assert lp.json.loads(lp.sidecar_path(out).read_text(encoding="utf-8")) == {"fingerprint": FP, "props": props()}


def test_range_parsing():
    assert lp.parse_range("30-72.5") == (30.0, 72.5)
    with pytest.raises(ValueError):
        lp.parse_range("72-30")


def has_x264():
    if not shutil.which("ffmpeg"):
        return False
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return "libx264" in r.stdout


def encode(dst, source, frames, extra=(), audio=False, gop=30):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{source}=size=320x180:rate={FPS}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-c:a", "aac", "-shortest"]
    x264 = ["-c:v", "libx264", "-crf", "18", "-g", str(gop), "-pix_fmt", "yuv420p"]   # B-frames on, as Remotion's
    subprocess.run([*cmd, "-frames:v", str(frames), *x264, *extra, str(dst)], check=True)


def packets(video, stream):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", stream, "-count_packets",
                        "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True, check=True)
    return int(r.stdout.strip().strip(","))


@pytest.mark.skipif(not has_x264(), reason="ffmpeg with libx264 needed")
@pytest.mark.parametrize("gop, parts", [
    (30, [("copy", 0, 30), ("render", 30, 60), ("copy", 60, 120)]),     # keyframes on whole seconds
    (25, [("copy", 0, 25), ("render", 25, 75), ("copy", 75, 120)]),     # and between them (0.8333 s, 2.5 s)
])
def test_splice_keeps_the_frame_count_and_the_sound_and_decodes_cleanly(tmp_path, gop, parts):
    prev = tmp_path / "prev.mp4"
    encode(prev, "testsrc", 120, audio=True, gop=gop)                # 4 s
    total = lp.frame_count(prev)
    assert lp.plan(lp.snap([(1.2, 1.8)], lp.keyframes(prev), total), total) == parts
    rendered = []

    def render(first, last, dst):
        rendered.append((first, last))
        encode(dst, "testsrc2", last - first + 1, gop=gop)

    out = tmp_path / "out.mp4"
    assert lp.splice(prev, out, parts, render, tmp_path / "work") == [parts[1][1] / FPS, parts[2][1] / FPS]
    assert rendered == [(parts[1][1], parts[1][2] - 1)]
    assert lp.frame_count(out) == total
    times = lp.subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time",
                               "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.split()
    pts = [round(float(x.strip(",")) * FPS) for x in times]
    assert pts == list(range(total))                                  # every frame once, in order
    assert packets(out, "a:0") == packets(prev, "a:0")              # the sound is the previous export's
    assert not (tmp_path / "work").exists()


@pytest.mark.skipif(not has_x264(), reason="ffmpeg with libx264 needed")
def test_splice_refuses_frames_encoded_differently(tmp_path):
    prev = tmp_path / "prev.mp4"
    encode(prev, "testsrc", 90, audio=True)
    parts = [("copy", 0, 30), ("render", 30, 60), ("copy", 60, 90)]

    def render(first, last, dst):
        encode(dst, "testsrc2", last - first + 1, extra=["-profile:v", "baseline"])

    with pytest.raises(SystemExit, match="other H.264 parameters"):
        lp.splice(prev, tmp_path / "out.mp4", parts, render, tmp_path / "work")


def test_the_render_command_for_a_range_is_the_full_one_plus_frames_and_muted():
    from pathlib import Path
    from render_lesson import range_cmd, render_cmd
    full = render_cmd(Path("/o/x.mp4"), Path("/p.json"), None, 8)
    part = range_cmd(Path("/o/x.mp4"), Path("/p.json"), 900, 1199, None, 8)
    assert part == [*full, "--frames=900-1199", "--muted"]
    assert copy.deepcopy(part) == part
