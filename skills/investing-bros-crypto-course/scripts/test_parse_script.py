"""Tests for parse_script.py (the script Doc's text into the video config's `script`)."""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from parse_script import changed_beats, main, parse  # noqa: E402

DOC = """# תסריט שיעור 1

## **קטע 1: הפתיחה (כ-40 שניות)**

*על המסך: רק אתה, פנים למצלמה.*

שלום לכולם.
והיום נלמד מה זה קריפטו.

## קטע 2: גילוי נאות (כ-15 שניות)

*על המסך: אתה, עם פס בתחתית.*

1. זה תוכן לימודי.
- לא ייעוץ השקעות.

### קטע 3: בלי זמן

שורה בלי על המסך.

## מקורות

- https://bitcoin.org/bitcoin.pdf
"""


def test_beats_titles_lengths_and_on_screen_lines():
    beats = parse(DOC)
    assert list(beats) == ["1", "2", "3"]
    assert beats["1"] == {"title": "הפתיחה", "seconds": 40, "on_screen": "רק אתה, פנים למצלמה.",
                          "text": "שלום לכולם. והיום נלמד מה זה קריפטו."}
    assert beats["2"]["text"] == "זה תוכן לימודי. לא ייעוץ השקעות."      # list markers dropped
    assert beats["3"]["seconds"] is None and beats["3"]["on_screen"] == ""
    assert "bitcoin.org" not in beats["3"]["text"]                       # the sources heading ends the beats


def test_update_keeps_the_departures(tmp_path):
    doc, cfg = tmp_path / "script.md", tmp_path / "lesson-1-video.json"
    doc.write_text(DOC, encoding="utf-8")
    cfg.write_text(json.dumps({"lesson": 1, "script": {"doc": "OLD", "departures": {"1": "card added"}}}),
                   encoding="utf-8")
    assert main([str(doc), "--doc", "NEW", "--revision", "2026-10-26T20:12:34Z", "--update", str(cfg)]) == 0
    s = json.loads(cfg.read_text(encoding="utf-8"))["script"]
    assert (s["doc"], s["revision"], s["departures"]) == ("NEW", "2026-10-26T20:12:34Z", {"1": "card added"})
    assert s["revision_kind"] == "modified_time"                         # the default when only Drive metadata is read
    assert set(s["beats"]) == {"1", "2", "3"}


def test_the_snapshot_is_recorded_by_path_and_hash(tmp_path):
    lesson = tmp_path / "lesson-1"
    (lesson / "script").mkdir(parents=True)
    doc, cfg = lesson / "script" / "תסריט-שיעור-1-v1.md", lesson / "lesson-1-video.json"
    doc.write_text(DOC, encoding="utf-8")
    cfg.write_text(json.dumps({"lesson": 1}), encoding="utf-8")
    main([str(doc), "--doc", "D", "--revision", "AHj4e", "--revision-kind", "revision_id", "--update", str(cfg)])
    s = json.loads(cfg.read_text(encoding="utf-8"))["script"]
    assert s["snapshot"] == "script/תסריט-שיעור-1-v1.md"                 # relative to the config: the folder can move
    assert s["snapshot_sha256"] == hashlib.sha256(doc.read_bytes()).hexdigest()
    assert (s["revision"], s["revision_kind"]) == ("AHj4e", "revision_id")


def test_a_new_revision_names_the_beats_that_changed(tmp_path, capsys):
    doc, cfg = tmp_path / "script.md", tmp_path / "lesson-1-video.json"
    doc.write_text(DOC, encoding="utf-8")
    cfg.write_text(json.dumps({"lesson": 1}), encoding="utf-8")
    main([str(doc), "--doc", "D", "--revision", "r1", "--update", str(cfg)])
    doc.write_text(DOC.replace("רק אתה, פנים למצלמה.", "כרטיס ליד הפנים.").replace("שורה בלי על המסך.", "שורה אחרת."),
                   encoding="utf-8")
    capsys.readouterr()
    main([str(doc), "--doc", "D", "--revision", "r2", "--update", str(cfg)])
    assert "changed since r1: 1, 3" in capsys.readouterr().out
    old = {"1": {"title": "a", "on_screen": "x", "text": "t", "seconds": 10}}
    assert changed_beats(old, {"1": dict(old["1"], seconds=20)}) == []   # a new length estimate is not a change to review


def test_text_without_beats_is_refused(tmp_path):
    doc = tmp_path / "x.md"
    doc.write_text("# Something else\n\nNo beats here.\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="no 'קטע N"):
        main([str(doc), "--doc", "D", "--revision", "R"])
