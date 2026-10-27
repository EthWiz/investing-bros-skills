"""Tests for check_lesson.py (media, loudness, sync, dead air at cuts, captions)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from check_lesson import (check_captions, check_loudness, check_media, check_silences, lag_seconds,  # noqa: E402
                          parse_ebur128, wrap_lines)

PROPS = {"duration": 60.0,
         "beats": [{"start": 0.0, "end": 30.0}, {"start": 30.0, "end": 60.0}],
         "segments": [{"start": 0.0, "end": 20.0, "mode": "full"}, {"start": 20.0, "end": 60.0, "mode": "side"}]}


def media(width=1920, height=1080, codec="h264", rate="30/1", audio=True):
    streams = [{"codec_type": "video", "codec_name": codec, "width": width, "height": height, "r_frame_rate": rate}]
    return {"streams": streams + ([{"codec_type": "audio", "codec_name": "aac"}] if audio else [])}


def test_media_must_be_1080p_h264_30fps_with_sound():
    assert check_media(media()) == []
    errs = check_media(media(1280, 720, "hevc", "30000/1001", audio=False))
    assert len(errs) == 4 and any("1280x720" in e for e in errs) and any("29.970" in e for e in errs)
    assert check_media({"streams": []}) == ["video: no video stream"]


def test_loudness_reads_the_ebur128_summary():
    log = ("[Parsed_ebur128_0] t: 1.0 M: -20.1 S: -20.3 I: -19.0 LUFS\n"
           "Summary:\n  Integrated loudness:\n    I:         -14.2 LUFS\n  True peak:\n    Peak:       -1.6 dBFS\n")
    assert parse_ebur128(log) == (-14.2, -1.6)
    assert check_loudness(-14.2, -1.6) == []
    assert len(check_loudness(-18.0, -0.4)) == 2
    assert check_loudness(None, None)                                   # no reading is a failure


def test_lag_finds_a_shifted_copy_of_the_sound():
    np = pytest.importorskip("numpy")
    rate = 8000
    a = np.random.default_rng(1).standard_normal(rate * 3).astype(np.float32)
    late = np.concatenate([np.zeros(344, np.float32), a])[: len(a)]     # 43 ms late
    assert lag_seconds(a, late, rate) == pytest.approx(0.043, abs=1 / rate)
    assert lag_seconds(a, a, rate) == 0.0
    assert lag_seconds(a[:100], a[:100], rate) is None                  # too short to tell


def test_a_long_silence_across_a_cut_is_dead_air():
    errs, warns = check_silences([(29.0, 31.0)], PROPS)
    assert errs and "cut" in errs[0] and not warns
    errs, warns = check_silences([(29.5, 30.5), (40.0, 43.0)], PROPS)   # a short pause at the cut is fine
    assert errs == [] and warns == ["silence: 3.0 s at 40.0 s"]
    assert check_silences([(58.0, float("inf"))], PROPS) == ([], [])    # trailing silence ends at the end


def cap(start, end, text, first=None, last=None):
    ws = text.split()
    step = (end - start) / len(ws)
    words = [{"w": w, "start": start + i * step, "end": start + (i + 1) * step} for i, w in enumerate(ws)]
    if first is not None:
        words[0]["start"] = first
    if last is not None:
        words[-1]["end"] = last
    return {"start": start, "end": end, "words": words}


def test_good_captions_pass():
    props = {**PROPS, "captions": [cap(0.5, 2.5, "שלום לכולם"), cap(2.5, 4.0, "והיום נלמד")]}
    assert check_captions(props) == ([], [])


@pytest.mark.parametrize("caps, message", [
    ([cap(1.0, 1.4, "קצר")], "under 0.7"),
    ([cap(59.0, 61.0, "בסוף")], "past the end"),
    ([cap(1.0, 3.0, "אחד"), cap(2.5, 4.0, "שתיים")], "overlaps"),
    ([cap(3.0, 4.0, "אחד"), cap(1.0, 2.0, "שתיים")], "out of order"),
    ([cap(1.0, 3.0, "אחד שתיים", first=0.6)], "after its first word"),
    ([cap(1.0, 3.0, "אחד שתיים", last=3.4)], "leaves before its last"),
])
def test_bad_captions_fail(caps, message):
    errs, _ = check_captions({**PROPS, "captions": caps})
    assert any(message in e for e in errs), errs


def test_fast_captions_warn_and_long_ones_fail_in_the_narrow_layout():
    fast = {**PROPS, "captions": [cap(1.0, 2.0, "מילה ארוכה מאוד שנקראת מהר מדי בשנייה")]}
    assert check_captions(fast)[1] and "characters a second" in check_captions(fast)[1][0]
    measure = lambda text: 100.0 * len(text.split())                   # every word 100 px wide
    text = " ".join(["מילה"] * 12)
    assert len(wrap_lines(text, 1300, measure)) == 1 and len(wrap_lines(text, 860, measure)) == 2
    long = " ".join(["מילה"] * 20)                                       # 2 lines full, 3 lines side
    errs, _ = check_captions({**PROPS, "captions": [cap(5.0, 9.0, long)]}, measure)
    assert errs == []
    errs, _ = check_captions({**PROPS, "captions": [cap(25.0, 29.0, long)]}, measure)
    assert errs and "side layout" in errs[0]
