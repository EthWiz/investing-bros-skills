import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from find_gaps import SR, context, find_gaps, frame_db  # noqa: E402


def _tone(sec, amp=0.3):
    t = np.arange(int(SR * sec)) / SR
    return (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


def _silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def test_finds_only_the_long_silence():
    audio = np.concatenate([_tone(2), _silence(1.0), _tone(2), _silence(4.0), _tone(1)])
    gaps = find_gaps(frame_db(audio), threshold=-45, min_gap=2.5)
    assert len(gaps) == 1
    s, e = gaps[0]
    assert abs(s - 5.0) < 0.1 and abs(e - 9.0) < 0.1


def test_trailing_silence_is_reported():
    audio = np.concatenate([_tone(1), _silence(3.0)])
    assert len(find_gaps(frame_db(audio), -45, 2.5)) == 1


def test_quiet_speech_is_not_silence():
    audio = np.concatenate([_tone(1), _tone(3, amp=0.01), _tone(1)])  # about -43 dBFS
    assert find_gaps(frame_db(audio), -45, 2.5) == []


def test_context_picks_neighbouring_segments():
    segs = [{"start": 0, "end": 4.9, "text": "שאלה טובה"}, {"start": 9.1, "end": 12, "text": "אז ככה"}]
    assert context(segs, 5.0, 9.0) == ("שאלה טובה", "אז ככה")
