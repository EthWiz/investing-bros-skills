"""postprod_checklist.py: missing items fail, teaser is required, waivers need Amitai, package contracts."""
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
    touch(ep / f"thumbnail-פרק-{N}.jpg")
    touch(ep / f"cover-פרק-{N}.png")
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
    assert missing == ["segments", "shorts", "shorts_covers", "past_episode_cards", "redcircle_draft",
                       "published", "spotify_links", "old_uploads"]
    _, missing = pc.check(tmp_path, N, "review")
    assert missing == ["segments", "shorts", "shorts_covers", "past_episode_cards", "redcircle_draft"]


SEGS = {"01": "סגמנט-01-צלילה-זהב", "02": "סגמנט-02-רעיון-טסלה"}
SHORTS = {"01": "שורט-01-סוויפט", "02": "שורט-02-זהב", "03": "שורט-03-טסלה"}


def segment_packages(ep: Path):
    for nn, stem in SEGS.items():
        for f in (f"{stem}.mp4", f"{stem}.txt", f"{stem}-thumb.jpg", f"youtube-סגמנט-{nn}.md"):
            touch(ep / "segments" / f)


def short_packages(ep: Path):
    for nn, stem in SHORTS.items():
        for f in (f"{stem}.m4v", f"{stem}-cover.jpg", f"{stem}.srt", f"youtube-שורט-{nn}.md"):
            touch(ep / "Shorts" / f)


def review_ready(ep: Path):
    upload_ready(ep)
    segment_packages(ep)
    short_packages(ep)
    pc.main(["mark", str(ep), "shorts_covers", "--evidence", "face format, check_cover OK"])
    touch(ep / "extras/past-episode-cards.json", "[]")
    pc.main(["mark", str(ep), "past_episode_cards", "--evidence", "no references; none set"])
    pc.main(["mark", str(ep), "redcircle_draft", "--evidence", "draft url"])


def test_review_passes_with_complete_packages_and_done_needs_publication(tmp_path):
    review_ready(tmp_path)
    assert pc.main(["check", str(tmp_path), "--episode", str(N), "--stage", "review"]) == 0
    _, missing = pc.check(tmp_path, N, "done")
    assert missing == ["published", "spotify_links", "old_uploads"]
    touch(tmp_path / "extras/publish-checklist.json",
          json.dumps({"items": [{"id": "redcircle.public", "state": "ticked"}, {"id": "short03.live", "state": "open"}]}))
    assert "short03.live" in pc.file_check(tmp_path, N, "published")


def test_four_empty_mp4_shorts_fail(tmp_path):
    for i in range(1, 5):
        touch(tmp_path / f"Shorts/שורט-0{i}-x.mp4", "")
    why = pc.file_check(tmp_path, N, "shorts")
    assert "never .mp4" in why and "short 01: no final video" in why


def test_short_package_needs_all_four_nonempty_files(tmp_path):
    short_packages(tmp_path)
    assert pc.file_check(tmp_path, N, "shorts") is None
    (tmp_path / "Shorts/שורט-02-זהב.srt").unlink()
    touch(tmp_path / "Shorts/שורט-03-טסלה-cover.jpg", "")
    why = pc.file_check(tmp_path, N, "shorts")
    assert "short 02: missing שורט-02-זהב.srt" in why and "short 03: empty שורט-03-טסלה-cover.jpg" in why
    assert "empty" in pc.file_check(tmp_path, N, "shorts_covers")


def test_wrong_short_count_fails(tmp_path):
    short_packages(tmp_path)
    for f in ("שורט-04-עוד.m4v", "שורט-04-עוד-cover.jpg"):
        touch(tmp_path / "Shorts" / f)
    assert "slot 04 is not a standing deliverable" in pc.file_check(tmp_path, N, "shorts")
    (tmp_path / "Shorts/שורט-03-טסלה.m4v").unlink()
    assert "short 03: no final video" in pc.file_check(tmp_path, N, "shorts")


def test_lowercase_shorts_folder_is_accepted(tmp_path):
    short_packages(tmp_path)
    (tmp_path / "Shorts").rename(tmp_path / "shorts")
    assert pc.file_check(tmp_path, N, "shorts") is None


def test_segment_packages_are_flat_complete_and_one_per_slot(tmp_path):
    segment_packages(tmp_path)
    assert pc.file_check(tmp_path, N, "segments") is None
    touch(tmp_path / "segments/סגמנט-01-צלילה-זהב-v2.mp4")
    why = pc.file_check(tmp_path, N, "segments")
    assert "2 final candidates" in why
    (tmp_path / "segments/סגמנט-01-צלילה-זהב-v2.mp4").unlink()
    touch(tmp_path / "segments/סגמנט-02-רעיון-טסלה.txt", "")
    (tmp_path / "segments/youtube-סגמנט-02.md").unlink()
    why = pc.file_check(tmp_path, N, "segments")
    assert "segment 02: missing youtube-סגמנט-02.md" in why and "segment 02: empty סגמנט-02-רעיון-טסלה.txt" in why


def test_segment_01_must_be_the_deep_dive_and_no_third_slot(tmp_path):
    segment_packages(tmp_path)
    for f in ("סגמנט-03-הסבר-x.mp4",):
        touch(tmp_path / "segments" / f)
    assert "slot 03 is not a standing deliverable" in pc.file_check(tmp_path, N, "segments")
    (tmp_path / "segments/סגמנט-03-הסבר-x.mp4").unlink()
    for f in ("mp4", "txt"):
        (tmp_path / f"segments/סגמנט-01-צלילה-זהב.{f}").rename(tmp_path / f"segments/סגמנט-01-רעיון-זהב.{f}")
    (tmp_path / "segments/סגמנט-01-צלילה-זהב-thumb.jpg").rename(tmp_path / "segments/סגמנט-01-רעיון-זהב-thumb.jpg")
    assert "deep dive" in pc.file_check(tmp_path, N, "segments")


def test_old_nested_segment_layout_is_explained(tmp_path):
    touch(tmp_path / "segments/סגמנט-01/seg.mp4")
    touch(tmp_path / "segments/סגמנט-02/seg.mp4")
    assert "flat in segments/" in pc.file_check(tmp_path, N, "segments")


def test_thumbnail_must_be_in_the_episode_root(tmp_path):
    touch(tmp_path / f"promo/thumbnail-פרק-{N}.jpg")
    touch(tmp_path / f"cover-פרק-{N}.png")
    assert "move it to the episode root" in pc.file_check(tmp_path, N, "thumbnail_cover")


def test_done_passes_with_everything(tmp_path):
    review_ready(tmp_path)
    touch(tmp_path / "extras/past-episode-cards.json", json.dumps([{"v5_timestamp": 787.9, "quote": "בפרק 8",
          "referenced_episode": 8, "youtube_video_id": "6chKVe8nQ8A"}]))
    pc.main(["mark", str(tmp_path), "past_episode_cards", "--evidence", "1 card set in Studio at 13:08"])
    touch(tmp_path / "extras/publish-checklist.json", json.dumps({"items": [{"id": "redcircle.public", "state": "ticked"},
          {"id": "short01.cover", "state": "waived"}]}))
    pc.main(["mark", str(tmp_path), "spotify_links", "--evidence", "https://open.spotify.com/episode/x on all 6"])
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


def test_waiver_must_come_from_the_episode_owner(tmp_path):
    upload_ready(tmp_path, teaser=False)
    touch(tmp_path / "extras/pipeline.json", json.dumps({"schema_version": 1, "owner": {"name": "nadav"}}))
    assert pc.main(["waive", str(tmp_path), "teaser", "--by", "Amitai 09:12: no teaser"]) == 2
    assert pc.main(["waive", str(tmp_path), "teaser", "--by", "Nadav 09:13: בלי טיזר"]) == 0
