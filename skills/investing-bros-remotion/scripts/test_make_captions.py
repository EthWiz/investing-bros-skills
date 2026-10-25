"""Tests for make_captions.py (proofread words + whisper timings -> word-timed captions)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_captions import align, build, chunk, snap_to_speech, to_output, tokens  # noqa: E402

HEARD = [{"w": "ורואים", "s": 10.0, "e": 10.3}, {"w": "צניחה", "s": 10.3, "e": 10.8},
         {"w": "של", "s": 10.8, "e": 11.0}, {"w": "שלושים", "s": 11.0, "e": 11.3},
         {"w": "אחוז", "s": 11.3, "e": 11.6}, {"w": "בבית", "s": 11.6, "e": 11.9},
         {"w": "שלהם", "s": 11.9, "e": 12.3}]


def test_tokens_mark_bracketed_keywords_across_words():
    assert tokens("ורואים [צניחה של] 30%") == [("ורואים", False), ("צניחה", True), ("של", True), ("30%", False)]


def test_alignment_survives_whisper_spelling_and_number_words():
    proof = ["ורואים", "צניחה", "של", "30%", "בבית", "שלהם,"]
    pairs = align(proof, [h["w"] for h in HEARD])
    assert pairs[0] == 0 and pairs[1] == 1 and pairs[4] == 5 and pairs[5] == 6
    assert align(["לפורטפוליו"], ["לפרוטפוליוס"]) == {0: 0}


def test_words_get_whisper_times_on_the_output_timeline():
    timemap = [[9.0, 13.0, 0.0]]
    caps = build([{"from": 9.0, "to": 13.0, "text": "ורואים [צניחה] של 30% בבית שלהם."}], HEARD, timemap, speed=1.25)
    words = [w for c in caps for w in c["words"]]
    assert [w["w"] for w in words] == ["ורואים", "צניחה", "של", "30%", "בבית", "שלהם."]
    assert words[0]["start"] == pytest.approx((10.0 - 9.0) / 1.25)
    assert words[4]["start"] == pytest.approx((11.6 - 9.0) / 1.25)
    assert all(a["start"] < b["start"] for a, b in zip(words, words[1:]))
    assert any(c["highlight"] == ["צניחה"] for c in caps)
    assert caps[-1]["end"] <= (13.0 - 9.0) / 1.25 + 1e-6            # never past the end of the video


def test_chunks_are_short_single_lines_broken_at_punctuation_and_pauses():
    ws = [{"w": w, "s": i * 0.3, "e": i * 0.3 + 0.25, "key": False} for i, w in
          enumerate(["אחת", "שתיים,", "שלוש", "ארבע", "חמש", "שש", "שבע"])]
    ws[6]["s"], ws[6]["e"] = 5.0, 5.3                                  # long pause before the last word
    groups = [[w["w"] for w in g] for g in chunk(ws)]
    assert groups[0] == ["אחת", "שתיים,"]
    assert all(1 <= len(g) <= 4 and len(" ".join(g)) <= 18 for g in groups)
    assert groups[-1] == ["שבע"]


def test_captions_never_overlap_and_hold_through_short_gaps():
    timemap = [[0.0, 10.0, 0.0]]
    heard = [{"w": "אחת,", "s": 1.0, "e": 1.3}, {"w": "שתיים", "s": 1.5, "e": 1.8}]
    caps = build([{"from": 0.0, "to": 10.0, "text": "אחת, שתיים"}], heard, timemap, speed=1.0, lines=1)
    assert caps[0]["end"] == pytest.approx(caps[1]["start"])
    assert len(build([{"from": 0.0, "to": 10.0, "text": "אחת, שתיים"}], heard, timemap, speed=1.0)) == 1   # house: one caption


def test_start_in_silence_snaps_to_the_speech():
    env = [0.0] * 100 + [5.0] * 50                                     # 100 Hz: speech starts at 1.0 s
    words = snap_to_speech([{"w": "וזה", "s": 0.4, "e": 1.4}], env, 100, 0.0, 1.0)
    assert words[0]["s"] == pytest.approx(1.0)
    kept = snap_to_speech([{"w": "עוד", "s": 1.1, "e": 1.3}], env, 100, 0.0, 1.0)
    assert kept[0]["s"] == pytest.approx(1.1)


def test_to_output_maps_through_the_kept_pieces():
    tm = [[10.0, 20.0, 0.0], [30.0, 34.0, 8.0]]
    assert to_output(15.0, tm, 1.25) == pytest.approx(4.0)
    assert to_output(32.0, tm, 1.25) == pytest.approx(9.6)
    assert to_output(25.0, tm, 1.25) is None                           # dropped between pieces


def test_two_line_captions_are_longer_and_never_flash():
    from make_captions import LAYOUTS
    fast = [{"w": w, "s": i * 0.25, "e": i * 0.25 + 0.22, "key": False} for i, w in
            enumerate(["אחת,", "שתיים", "שלוש,", "ארבע", "חמש", "שש,", "שבע", "שמונה", "תשע."])]
    one = chunk(fast, **LAYOUTS[1])
    two = chunk(fast, **LAYOUTS[2])
    assert len(two) < len(one)
    assert all(len(g) <= 8 and len(" ".join(w["w"] for w in g)) <= 36 for g in two)
    assert [w["w"] for w in two[0]][:2] == ["אחת,", "שתיים"]          # no break at the first comma
    for a, b in zip(two, two[1:]):                                     # a short one only stays if joining overflows
        if a[-1]["e"] - a[0]["s"] < 1.2:
            assert len(a + b) > 8 or len(" ".join(w["w"] for w in a + b)) > 36


def test_short_leftover_joins_its_neighbour():
    from make_captions import merge_short
    g1 = [{"w": "אחת", "s": 0.0, "e": 0.3}]
    g2 = [{"w": "שתיים", "s": 0.3, "e": 1.0}, {"w": "שלוש", "s": 1.0, "e": 2.0}]
    assert merge_short([g1, g2], 8, 36, 1.2) == [g1 + g2]
