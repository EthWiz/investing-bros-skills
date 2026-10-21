import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from align_tracks import offset_seconds  # noqa: E402


def _speech(n, seed=1):
    rng = np.random.default_rng(seed)
    return np.repeat(rng.random(n // 50), 50)[:n] - 0.5


def test_combined_behind_track_ep8():
    track = _speech(60000)
    combined = np.concatenate([np.zeros(167), track])[:60000]  # 1 ms units: 0.167 s late
    assert abs(offset_seconds(combined, track) - 0.167) < 0.002


def test_combined_ahead_is_negative():
    track = _speech(60000, 2)
    combined = track[250:]
    assert abs(offset_seconds(combined, track) + 0.25) < 0.002
