"""Tests for make_lesson_base.py (trim suggestions, the join, the extras names, the lesson configs)."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_lesson_base import (build_cmd, copy_words, digest, extras_name, filter_graph, fingerprint,  # noqa: E402
                              finalize_base, latest_record, manifest, parse_silences, stamp, status, take_path, trims_from_silences)

EXAMPLE = Path(__file__).resolve().parent.parent / "references" / "example-lesson-video.json"


def test_trims_skip_camera_clicks_at_both_ends():
    # lesson 1 beat 1: a click at 0-0.26 s, speech from 2.31 s to 42.48 s, a click at the very end
    assert trims_from_silences([(0.258, 0.879), (1.082, 2.31), (42.477, 44.245)], 44.497) == (2.01, 42.93)
    # beat 4: a 0.5 s noise before a long silence still counts as the take's start
    assert trims_from_silences([(0.544, 1.569), (1.704, 2.619), (47.653, 50.176)], 50.431) == (2.32, 48.1)


def test_trims_keep_the_whole_take_when_speech_touches_the_edges():
    assert trims_from_silences([(10.0, 11.0)], 30.0) == (0.0, 30.0)
    assert trims_from_silences([], 12.5) == (0.0, 12.5)


def test_parse_silences_closes_a_silence_running_to_the_end():
    log = "silence_start: 0.2\nsilence_end: 1.5 | silence_duration: 1.3\nsilence_start: 9.1\n"
    assert parse_silences(log, 10.0) == [(0.2, 1.5), (9.1, 10.0)]


def test_join_trims_scales_and_levels_every_take_in_order(tmp_path):
    takes = [{"beat": 1, "file": "a.mov", "from": 2.0, "to": 43.0}, {"beat": 2, "file": "b.mov", "from": 0.55, "to": 19.2}]
    g = filter_graph(takes)
    assert "[0:v]trim=2.0:43.0" in g and "[1:a]atrim=0.55:19.2" in g
    assert "scale=1920:1080:flags=lanczos,fps=30" in g
    assert "afade=t=out:st=40.94:d=0.06" in g                      # 41 s take, fade in its last 60 ms
    assert "[v0][a0][v1][a1]concat=n=2:v=1:a=1" in g
    assert "loudnorm=I=-14" in g and "setpts" in g and "atempo" not in g   # no speed change
    for name in ("a.mov", "קטע-02.mp4"):                           # beat 2 only under its Drive name
        (tmp_path / name).write_text("v")
    cmd = build_cmd(takes, tmp_path, tmp_path / "base.mp4")
    inputs = [cmd[i + 1] for i, x in enumerate(cmd) if x == "-i"]
    assert inputs == [str(tmp_path / "a.mov"), str(tmp_path / "קטע-02.mp4")]
    with pytest.raises(SystemExit):
        filter_graph([{"beat": 3, "file": "c.mov", "from": 5.0, "to": 5.0}])


def test_extras_names_follow_the_drive_convention():
    assert extras_name(1) == "קטע-01.mp4" and extras_name(12) == "קטע-12.mp4"


def test_small_concat_padding_is_trimmed_without_reencoding(tmp_path):
    base = tmp_path / 'base.mp4'
    base.write_bytes(b'original')
    takes = [{'from': 0, 'to': 419.28 / 6}] * 6
    calls = []
    def probe(path):
        return 419.4 if path == base else 419.366667
    def run(cmd, check):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b'fixed')
    assert finalize_base(base, takes, probe=probe, run=run) == 419.366667
    cmd = calls[0]
    assert cmd[cmd.index('-t') + 1] == '419.28'
    assert cmd[cmd.index('-c') + 1] == 'copy'
    assert base.read_bytes() == b'fixed'
    assert not list(tmp_path.glob('*.part.mp4'))


@pytest.mark.parametrize('actual', [418.8, 420.0])
def test_finalize_refuses_missing_content_or_large_excess(tmp_path, actual):
    base = tmp_path / 'base.mp4'
    base.write_bytes(b'original')
    with pytest.raises(SystemExit, match='not small concat tail padding'):
        finalize_base(base, [{'from': 0, 'to': 419.28 / 6}] * 6, probe=lambda _: actual)
    assert base.read_bytes() == b'original'


def test_failed_duration_remux_keeps_the_original(tmp_path):
    base = tmp_path / 'base.mp4'
    base.write_bytes(b'original')
    def run(cmd, check):
        Path(cmd[-1]).write_bytes(b'bad')
    with pytest.raises(SystemExit, match='original kept'):
        finalize_base(base, [{'from': 0, 'to': 419.28 / 6}] * 6,
                      probe=lambda p: 419.4 if p == base else 419.0, run=run)
    assert base.read_bytes() == b'original'
    assert not list(tmp_path.glob('*.part.mp4'))


def test_a_take_is_found_by_its_own_name_then_its_drive_name(tmp_path):
    t = {"beat": 3, "file": "Beat 3 - take 1.mov"}
    with pytest.raises(SystemExit, match="neither"):
        take_path(t, tmp_path)
    (tmp_path / "קטע-03.mp4").write_text("v")
    assert take_path(t, tmp_path).name == "קטע-03.mp4"
    (tmp_path / "Beat 3 - take 1.mov").write_text("v")
    assert take_path(t, tmp_path).name == "Beat 3 - take 1.mov"


def test_the_manifest_is_a_config_that_rebuilds_from_drive():
    cfg = {"lesson": 1, "takes": [{"beat": 1, "file": "Beat 1 - take 1.mov", "from": 2.0, "to": 43.0}],
           "assets": {"whitepaper": {"file": "assets/bitcoin-whitepaper-p1.png", "source": "https://bitcoin.org"}}}
    text = json.dumps(cfg)
    m = manifest(cfg, text, "שיעור-1-בסיס.mp4", 196.1234, "abc1234", "2026-10-27T10:00:00+00:00")
    assert m["takes"] == cfg["takes"] and m["assets"]["whitepaper"]["file"] == "bitcoin-whitepaper-p1.png"
    assert cfg["assets"]["whitepaper"]["file"].startswith("assets/")      # the config itself is untouched
    pkg = m["package"]
    assert pkg["skills_version"] == "abc1234" and pkg["base_seconds"] == 196.123 and len(pkg["config_sha256"]) == 64
    assert pkg["takes"] == {"1": {"drive": "קטע-01.mp4", "recorded_as": "Beat 1 - take 1.mov"}}
    assert pkg["words"] == ["קטע-01.json"] and pkg["captions"] == "שיעור-1-כתוביות.srt"
    assert "build שיעור-1-מניפסט.json --takes-dir ." in pkg["rebuild"]
    cfg["script"] = {"doc": "D", "revision": "r", "snapshot": "script/תסריט-שיעור-1-v1.md"}
    m = manifest(cfg, text, "b.mp4", 1.0, "v", "t")
    assert m["script"]["snapshot"] == "תסריט-שיעור-1-v1.md"           # the package holds it beside the manifest


def test_no_real_lesson_config_is_kept_in_the_repo():
    """Real configs live in each lesson's own folder and its Drive package, not in the skill."""
    refs = EXAMPLE.parent
    assert not (refs / "lessons").exists()
    assert not list(refs.rglob("lesson-*-video.json"))


def fake_hash(path):
    return "h:" + Path(path).read_text()


def lesson(tmp_path):
    cfg = {"lesson": 1, "takes": [{"beat": 1, "file": "a.mov", "from": 1.0, "to": 9.0},
                                  {"beat": 2, "file": "b.mov", "from": 0.5, "to": 7.0}],
           "proofread": {"1": "שלום.", "2": "להתראות."}, "anchors": {}, "segments": [], "title": ["x"],
           "script": {"doc": "D", "revision": "r1", "snapshot_sha256": "s1"}}
    takes, words = tmp_path / "takes", tmp_path / "words"
    takes.mkdir()
    words.mkdir()
    (takes / "a.mov").write_text("take-a")
    (takes / "b.mov").write_text("take-b")
    for n in (1, 2):
        (words / f"קטע-0{n}.json").write_text("[]")
    return cfg, takes, words


def test_stamp_records_the_take_and_never_overwrites(tmp_path):
    cfg, takes, words = lesson(tmp_path)
    assert stamp(cfg, takes, words, hasher=fake_hash) == [(1, "stamped"), (2, "stamped")]
    side = json.loads((words / "קטע-01.take.json").read_text(encoding="utf-8"))
    assert (side["take"], side["sha256"]) == ("a.mov", "h:take-a")
    (takes / "a.mov").write_text("a new take-a")
    assert stamp(cfg, takes, words, hasher=fake_hash)[0] == (1, "STALE: the take changed")
    assert json.loads((words / "קטע-01.take.json").read_text(encoding="utf-8"))["sha256"] == "h:take-a"
    assert stamp(cfg, takes, words, force=True, hasher=fake_hash)[0] == (1, "stamped")


def test_status_names_what_to_run_again(tmp_path):
    cfg, takes, words = lesson(tmp_path)
    stamp(cfg, takes, words, hasher=fake_hash)
    lines, todo = status(cfg, takes, words, None, hasher=fake_hash)
    assert "no export record" in lines[-1] and todo == ["base", "props", "render"]
    record = {"made": "t", "fingerprint": fingerprint(cfg),
              "takes": [{"beat": 1, "sha256": "h:take-a"}, {"beat": 2, "sha256": "h:take-b"}]}
    assert status(cfg, takes, words, record, hasher=fake_hash) == (["nothing changed since the export of t"], [])
    cfg["proofread"]["2"] = "להתראות לכולם."
    assert status(cfg, takes, words, record, hasher=fake_hash)[1] == ["props", "render"]       # Whisper is kept
    cfg["takes"][0]["to"] = 8.5
    assert status(cfg, takes, words, record, hasher=fake_hash)[1] == ["base", "props", "render"]
    (takes / "b.mov").write_text("another take-b")
    lines, todo = status(cfg, takes, words, record, hasher=fake_hash)
    assert "beat 2: the take changed since its words were made" in lines and "whisper" in todo
    cfg["script"]["snapshot_sha256"] = "s2"
    assert "review the script" in status(cfg, takes, words, record, hasher=fake_hash)[1]


def test_the_latest_record_in_a_folder_is_used(tmp_path):
    assert latest_record(tmp_path) is None
    for stamp_ in ("20261027T100000Z", "20261027T120000Z"):
        (tmp_path / f"שיעור-1-ייצוא-{stamp_}.json").write_text(json.dumps({"made": stamp_}))
    assert latest_record(tmp_path)["made"] == "20261027T120000Z"


def test_the_package_gets_the_words_and_their_drive_hash(tmp_path):
    cfg, takes, words = lesson(tmp_path)
    stamp(cfg, takes, words, hasher=fake_hash)
    extras = tmp_path / "extras"
    extras.mkdir()
    for n in (1, 2):
        (extras / f"קטע-0{n}.mp4").write_text(f"remux-{n}")
    copy_words(cfg["takes"], words, extras, hasher=fake_hash)
    side = json.loads((extras / "קטע-02.take.json").read_text(encoding="utf-8"))
    assert (side["sha256"], side["package_sha256"]) == ("h:take-b", "h:remux-2")
    assert (extras / "קטע-01.json").is_file()
    (words / "קטע-02.json").unlink()
    with pytest.raises(SystemExit, match="no words"):
        copy_words(cfg["takes"], words, extras, hasher=fake_hash)


def test_the_digest_recipe_matches_check_lesson():
    # the same value and digest are pinned in investing-bros-remotion's test_check_lesson.py
    assert digest({"b": [1, 2.5], "a": "שקל"}) == "3bdd54540bcd88c26abe23472687f25b8a072bf43395a8e16f9c6d7e92828e97"


@pytest.mark.parametrize("path", [EXAMPLE], ids=lambda p: p.name)
def test_lesson_configs_are_complete(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    beats = [t["beat"] for t in cfg["takes"]]
    script = cfg["script"]
    assert script["doc"] and script["revision"], "the config says which Doc revision it follows"
    assert all(script["beats"].get(str(b), {}).get("on_screen") for b in beats), "an על המסך line per take"
    assert set(script.get("departures", {})) <= {str(b) for b in beats}
    assert beats == sorted(beats) and len(set(beats)) == len(beats)
    assert all(t["to"] > t["from"] >= 0 for t in cfg["takes"])
    assert set(cfg["proofread"]) == {str(b) for b in beats}, "proofread text for every take"
    assert len(cfg["part_starts"]) == len(cfg["parts"])
    assert cfg["segments"][0]["at"][:2] == [beats[0], None], "the lesson opens on Amitai's face"
    assert all(s["mode"] == "full" or s.get("scene") for s in cfg["segments"])
