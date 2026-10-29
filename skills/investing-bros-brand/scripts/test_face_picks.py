"""make_face_grid.py and record_face_picks.py: the per-episode face-pick loop."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import make_face_grid as mg  # noqa: E402
import record_face_picks as rp  # noqa: E402


def test_parse_time():
    assert mg.parse_time("34:51.3") == pytest.approx(2091.3)
    assert mg.parse_time("1:00:02") == 3602
    assert mg.parse_time("75.5") == 75.5


def test_pick_times_spreads_and_orders():
    js = {"frames": {"a": {"t": 100, "score": 3}, "b": {"t": 110, "score": 2.9},
                     "c": {"t": 400, "score": 1}, "d": {"t": 20, "score": 0.5}}}
    assert mg.pick_times(js, 3, 30) == [20, 100, 400]
    assert mg.pick_times(js, 2, 30) == [100, 400]


def test_grid_shape():
    assert mg.grid_shape(10) == (5, 2)
    assert mg.grid_shape(3) == (3, 1)


def test_build_grid(tmp_path):
    from PIL import Image
    paths = []
    for k in range(3):
        p = tmp_path / f"A{k + 1}.jpg"
        Image.new("RGB", (96, 108), (40 * k, 80, 120)).save(p)
        paths.append(str(p))
    out = tmp_path / "grid.jpg"
    mg.build_grid(paths, ["A1  00:01.0", "A2", "A3"], str(out), tile_w=96)
    assert Image.open(out).size == (3 * 96, 108 + 44)


MANS = [{"recording": "rec.mp4", "host": "amitai", "side": "left",
         "items": {"A1": {"host": "amitai", "t_sec": 10.0}, "A2": {"host": "amitai", "t_sec": 50.0}}},
        {"recording": "rec.mp4", "host": "nadav", "side": "right",
         "items": {"N1": {"host": "nadav", "t_sec": 20.0}}}]


def test_record_labels():
    items, rec = rp.merge_manifests(MANS)
    lab = rp.build_labels(9, items, rec, ["A2", "N1"], rp.parse_bad(["A1=eyes look weird"]), "2026-10-29")
    assert lab["items"]["A1"] == {"host": "amitai", "t_sec": 10.0, "label": "bad", "reason": "eyes look weird"}
    assert lab["items"]["N1"]["label"] == "good"
    assert lab["source"] == {"episode": 9, "recording": "rec.mp4", "amitai_side": "left", "nadav_side": "right"}


def test_record_refuses_bad_input():
    items, rec = rp.merge_manifests(MANS)
    with pytest.raises(ValueError):
        rp.parse_bad(["A1"])  # a reject needs the operator's reason
    with pytest.raises(ValueError):
        rp.build_labels(9, items, rec, ["A1"], {"A1": "x"}, "d")
    with pytest.raises(ValueError):
        rp.build_labels(9, items, rec, ["Z9"], {}, "d")
    with pytest.raises(ValueError):
        rp.build_labels(9, items, rec, [], {}, "d")


def test_round_files_are_named_by_host_and_prefix():
    a, b = mg.out_names("amitai", "A"), mg.out_names("amitai", "B")
    assert a == {"grid": "grid-amitai-A.jpg", "manifest": "manifest-amitai-A.json"}
    assert a["grid"] != b["grid"] and a["manifest"] != b["manifest"]


def test_second_round_does_not_overwrite_the_first(tmp_path, monkeypatch):
    from PIL import Image

    def fake_extract(recording, t, side, out):
        Image.new("RGB", (64, 72), (int(t) % 255, 80, 120)).save(out)

    monkeypatch.setattr(mg, "extract", fake_extract)
    out = tmp_path / "faces"
    assert mg.main(["rec.mp4", str(out), "--host", "amitai", "--side", "left", "--prefix", "A",
                    "--times", "00:10", "00:50"]) == 0
    assert mg.main(["rec.mp4", str(out), "--host", "amitai", "--side", "left", "--prefix", "B",
                    "--times", "01:10"]) == 0
    files = sorted(p.name for p in out.iterdir())
    assert {"grid-amitai-A.jpg", "grid-amitai-B.jpg", "manifest-amitai-A.json", "manifest-amitai-B.json"} <= set(files)
    with pytest.raises(SystemExit):  # same round again: refused
        mg.main(["rec.mp4", str(out), "--host", "amitai", "--side", "left", "--prefix", "A", "--times", "00:20"])
    # record_face_picks reads both rounds from the directory, with the right times
    lab_path = tmp_path / "ep.json"
    assert rp.main(["--episode", "9", "--manifest", str(out), "--good", "B1",
                    "--bad", "A1=eyes shut", "--date", "2026-10-29", "--out", str(lab_path)]) == 0
    import json
    items = json.loads(lab_path.read_text())["items"]
    assert items["A1"]["t_sec"] == 10 and items["A2"]["t_sec"] == 50 and items["B1"]["t_sec"] == 70
    assert items["B1"]["label"] == "good" and items["A1"]["label"] == "bad"


def test_manifest_ids_must_match_their_round():
    bad = [dict(MANS[0], prefix="B")]  # ids A1/A2 in a manifest that says round B
    with pytest.raises(ValueError):
        rp.merge_manifests(bad)
    with pytest.raises(ValueError):  # the same round passed twice
        rp.merge_manifests(MANS + [MANS[0]])


def test_empty_manifest_dir_is_refused(tmp_path):
    with pytest.raises(ValueError):
        rp.manifest_paths([str(tmp_path)])
