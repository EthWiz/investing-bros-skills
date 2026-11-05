"""postprod_checklist.py: missing items fail, teaser is required, waivers need Amitai."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import postprod_checklist as pc  # noqa: E402

N = 10


def touch(p: Path, text: str = "x"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def upload_ready(ep: Path, teaser=True):
    touch(ep / f"הקלטה-ערוכה-פרק-{N}.m4a")
    touch(ep / "extras/transcript/segments.json", "[]")
    touch(ep / "extras/edit.json", json.dumps({"start": 0, "end": 9, "cuts": [[1, 2]]}))
    touch(ep / "extras/cuts-review/cuts-list.txt")
    touch(ep / "extras/cuts-review/cut-01.mp4")
    if teaser:
        touch(ep / "promo/cold-open-teaser.mp4")
    touch(ep / "extras/investing-bro-intro-with-beat.mp4")
    touch(ep / f"video/פרק-{N}-וידאו.mp4")
    touch(ep / f"video/תיאור-פרק-{N}-youtube.txt", "0:00 טיזר\n1:05 חדשות\n20:00 עומק\n")
    touch(ep / "extras/verify_sync.log", "SYNC OK\n")
    touch(ep / f"כותרות-פרק-{N}.txt")
    touch(ep / f"תיאור-פרק-{N}.txt")
    touch(ep / f"art/thumbnail-פרק-{N}.jpg")
    touch(ep / f"art/cover-פרק-{N}.png")
    pc.main(["mark", str(ep), "transcript_doc", "--evidence", "https://docs.google.com/x"])
    pc.main(["mark", str(ep), "chapters", "--evidence", "shifted +65s"])


def test_empty_dir_fails_listing_everything(tmp_path):
    rows, missing = pc.check(tmp_path, N, "done")
    assert set(missing) == set(pc.IDS)
    assert pc.main(["check", str(tmp_path), "--episode", str(N)]) == 1


def test_missing_teaser_blocks_upload(tmp_path):
    upload_ready(tmp_path, teaser=False)
    _, missing = pc.check(tmp_path, N)
    assert missing == ["teaser"]


def test_upload_stage_passes_but_done_needs_downstream(tmp_path):
    upload_ready(tmp_path)
    assert pc.main(["check", str(tmp_path), "--episode", str(N)]) == 0
    _, missing = pc.check(tmp_path, N, "done")
    assert missing == ["segments", "shorts", "redcircle_draft"]


def test_done_passes_with_everything(tmp_path):
    upload_ready(tmp_path)
    for s in ("סגמנט-01", "סגמנט-02"):
        touch(tmp_path / "segments" / s / "seg.mp4")
    for i in range(3):
        touch(tmp_path / f"Shorts/short-0{i+1}/s.mp4")
    pc.main(["mark", str(tmp_path), "redcircle_draft", "--evidence", "draft url"])
    assert pc.main(["check", str(tmp_path), "--episode", str(N), "--stage", "done"]) == 0


def test_waiver_needs_amitai_and_clears_item(tmp_path):
    upload_ready(tmp_path, teaser=False)
    assert pc.main(["waive", str(tmp_path), "teaser", "--by", "agent: skip it"]) == 2
    assert pc.main(["waive", str(tmp_path), "teaser", "--by", "Amitai 09:12: no teaser this time"]) == 0
    assert pc.main(["check", str(tmp_path), "--episode", str(N)]) == 0


def test_sync_fail_and_too_few_review_clips(tmp_path):
    upload_ready(tmp_path)
    touch(tmp_path / "extras/verify_sync.log", "SYNC OK\nseg 3 SYNC FAIL\n")
    touch(tmp_path / "extras/edit.json", json.dumps({"cuts": [[1, 2], [3, 4]]}))
    _, missing = pc.check(tmp_path, N)
    assert set(missing) == {"verify_sync", "cut_list"}
