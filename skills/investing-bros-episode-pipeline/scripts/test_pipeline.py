import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import pipeline as pl  # noqa: E402


def test_stage_graph_is_consistent():
    ids = [s["id"] for s in pl.STAGES]
    assert len(ids) == len(set(ids))
    for i, s in enumerate(pl.STAGES):
        for d in s["deps"]:
            assert d in ids, f"{s['id']} depends on unknown {d}"
            assert ids.index(d) < i, f"{s['id']} depends on a later stage {d}"


def test_first_stage_is_intake():
    state = pl.new_state(8)
    assert pl.next_stages(state) == ["intake"]


def test_cannot_start_before_deps():
    state = pl.new_state(8)
    with pytest.raises(ValueError, match="waits for: intake"):
        pl.set_status(state, "edit", "doing")


def test_approver_needed_for_done():
    state = pl.new_state(8)
    pl.set_status(state, "intake", "done")
    pl.set_status(state, "edit", "review")
    with pytest.raises(ValueError, match="approved-by"):
        pl.set_status(state, "edit", "done")
    pl.set_status(state, "edit", "done", approved_by="Nadav")
    assert state["stages"]["edit"]["approved_by"] == "Nadav"


def test_after_edit_the_promo_stages_open_in_parallel():
    state = pl.new_state(8)
    pl.set_status(state, "intake", "done")
    pl.set_status(state, "edit", "done", approved_by="Nadav")
    assert pl.next_stages(state) == ["copy", "video", "shorts", "midform"]


def test_required_stage_cannot_be_skipped():
    state = pl.new_state(8)
    with pytest.raises(ValueError, match="not optional"):
        pl.set_status(state, "shorts", "skipped")
    pl.set_status(state, "midform", "skipped")


def _through_upload(state):
    pl.set_status(state, "intake", "done")
    pl.set_status(state, "edit", "done", approved_by="Nadav")
    pl.set_status(state, "copy", "done", approved_by="Amitai")
    for s in ("video", "midform", "thumbnail"):
        pl.set_status(state, s, "skipped")
    pl.set_status(state, "shorts", "done", approved_by="Nadav")
    pl.set_status(state, "review", "done", approved_by="Amitai")
    pl.set_status(state, "upload", "done")


def test_only_amitai_can_approve_publish():
    state = pl.new_state(8)
    _through_upload(state)
    with pytest.raises(ValueError, match="only be approved by Amitai"):
        pl.set_status(state, "publish", "done", approved_by="Nadav")
    pl.set_status(state, "publish", "done", approved_by="amitai")
    assert pl.next_stages(state) == ["share"]


def test_review_waits_for_every_promo_stage():
    state = pl.new_state(8)
    pl.set_status(state, "intake", "done")
    pl.set_status(state, "edit", "done", approved_by="Nadav")
    pl.set_status(state, "copy", "done", approved_by="Amitai")
    pl.set_status(state, "shorts", "done", approved_by="Nadav")
    with pytest.raises(ValueError, match="video, midform, thumbnail"):
        pl.set_status(state, "review", "doing")


def test_missing_outputs_warn_not_block(tmp_path):
    state = pl.new_state(8)
    pl.set_status(state, "intake", "done")
    w = pl.set_status(state, "edit", "done", approved_by="Nadav", ep=tmp_path)
    assert any("edit.json" in x for x in w)
    (tmp_path / "edit.json").write_text("{}")
    (tmp_path / "investing-bros-episode-edited.mp3").write_text("x")
    (tmp_path / "transcript").mkdir()
    (tmp_path / "transcript" / "segments.json").write_text("[]")
    assert pl.missing_outputs(tmp_path, "edit") == []


def test_cli_roundtrip(tmp_path, capsys):
    assert pl.main(["init", str(tmp_path), "--episode", "8", "--no-video"]) == 0
    state = json.loads((tmp_path / "pipeline.json").read_text(encoding="utf-8"))
    assert state["episode"] == 8 and state["stages"]["video"]["status"] == "skipped"
    assert pl.main(["init", str(tmp_path), "--episode", "8"]) == 1   # no silent overwrite
    assert pl.main(["set", str(tmp_path), "intake", "done", "--note", "2 parts"]) == 0
    assert pl.main(["set", str(tmp_path), "publish", "doing"]) == 1
    capsys.readouterr()
    assert pl.main(["report", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "פרק 8" in out and "2 parts" in out and "Next: edit" in out
