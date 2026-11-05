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
        touch(ep / "extras/teaser-check.log", "CAPTIONS OK\n")
        pc.main(["mark", str(ep), "teaser_quality", "--evidence", "3 moments re-read cold; payoffs kept"])
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
    touch(ep / "extras/cover-check.log",
          f"OK thumbnail-פרק-{N}.jpg: 1920x1080 episode-wide\nOK cover-פרק-{N}.png: 3000x3000 episode-square\n")
    pc.main(["mark", str(ep), "cover_checks", "--evidence", "Codex on the Mac, prompts in extras/codex/"])
    pc.main(["mark", str(ep), "face_identity", "--evidence", "Amitai left until 41:10, swap verified"])


def test_empty_dir_fails_listing_everything(tmp_path):
    rows, missing = pc.check(tmp_path, N, "done")
    assert set(missing) == set(pc.IDS)
    assert pc.main(["check", str(tmp_path), "--episode", str(N)]) == 1


def test_missing_teaser_blocks_upload(tmp_path):
    upload_ready(tmp_path, teaser=False)
    _, missing = pc.check(tmp_path, N)
    assert missing == ["teaser", "teaser_quality"]


def test_upload_stage_passes_but_done_needs_downstream(tmp_path):
    upload_ready(tmp_path)
    assert pc.main(["check", str(tmp_path), "--episode", str(N)]) == 0
    _, missing = pc.check(tmp_path, N, "done")
    assert missing == ["segments", "shorts", "shorts_covers", "past_episode_cards", "redcircle_draft", "old_uploads"]


def test_done_passes_with_everything(tmp_path):
    upload_ready(tmp_path)
    for s in ("סגמנט-01", "סגמנט-02"):
        touch(tmp_path / "segments" / s / "seg.mp4")
    for i in range(3):
        touch(tmp_path / f"Shorts/short-0{i+1}/s.mp4")
        touch(tmp_path / f"Shorts/short-0{i+1}/שורט-0{i+1}-x-cover.jpg")
    pc.main(["mark", str(tmp_path), "shorts_covers", "--evidence", "face format, check_cover OK"])
    touch(tmp_path / "extras/past-episode-cards.json", json.dumps([{"v5_timestamp": 787.9, "quote": "בפרק 8",
          "referenced_episode": 8, "youtube_video_id": "6chKVe8nQ8A"}]))
    pc.main(["mark", str(tmp_path), "past_episode_cards", "--evidence", "1 card set in Studio at 13:08"])
    pc.main(["mark", str(tmp_path), "redcircle_draft", "--evidence", "draft url"])
    pc.main(["mark", str(tmp_path), "old_uploads", "--evidence", "deleted Private abc123 (old full episode)"])
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


def test_teaser_captions_must_pass_and_moments_be_reviewed(tmp_path):
    upload_ready(tmp_path)
    touch(tmp_path / "extras/teaser-check.log", "FAIL caption @ 3 leaves the safe area\n1 caption problem(s)\n")
    assert pc.check(tmp_path, N)[1] == ["teaser_quality"]
    touch(tmp_path / "extras/teaser-check.log", "CAPTIONS OK\n")
    state = pc.load(tmp_path)
    del state["marked"]["teaser_quality"]
    pc.save(tmp_path, state)
    rows, missing = pc.check(tmp_path, N)
    assert missing == ["teaser_quality"] and "needs mark" in dict((r[1], r[2]) for r in rows)["teaser_quality"]


def test_cover_checks_need_ok_for_both_covers_and_no_fail(tmp_path):
    upload_ready(tmp_path)
    touch(tmp_path / "extras/cover-check.log", f"OK thumbnail-פרק-{N}.jpg\nFAIL headline: U+061F\n")
    assert pc.check(tmp_path, N)[1] == ["cover_checks"]
    touch(tmp_path / "extras/cover-check.log", f"OK thumbnail-פרק-{N}.jpg\n")
    assert pc.check(tmp_path, N)[1] == ["cover_checks"]


def test_face_identity_and_old_uploads_are_mark_only(tmp_path):
    upload_ready(tmp_path)
    state = pc.load(tmp_path)
    del state["marked"]["face_identity"]
    pc.save(tmp_path, state)
    assert pc.check(tmp_path, N)[1] == ["face_identity"]
    assert "old_uploads" in pc.check(tmp_path, N, "done")[1]


def test_waived_teaser_also_clears_teaser_quality(tmp_path):
    upload_ready(tmp_path, teaser=False)
    pc.main(["waive", str(tmp_path), "teaser", "--by", "Amitai 09:12: no teaser this time"])
    rows, missing = pc.check(tmp_path, N)
    assert missing == [] and dict((r[1], r[0]) for r in rows)["teaser_quality"] == "WAIVED"


def test_past_episode_cards_rejects_unknown_id(tmp_path):
    touch(tmp_path / "extras/past-episode-cards.json", json.dumps([{"v5_timestamp": 1, "quote": "q",
          "referenced_episode": 8, "youtube_video_id": "XXXXXXXXXXX"}]))
    assert "not in episode index" in (pc.file_check(tmp_path, N, "past_episode_cards") or "")
