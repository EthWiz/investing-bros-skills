import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import find_past_episode_refs as f  # noqa: E402

IDX = json.loads((Path(__file__).parents[2] / "investing-bros-show/references/episode-index.json").read_text(encoding="utf-8"))


def seg(t, text):
    return {"start": t, "end": t + 2, "text": text}


def test_number_and_topic_refs():
    s = [seg(10, "פתיחת רגולציה בתחום הגרעין שדיברנו עליו"), seg(50, "דיברנו על זה בפרק 8 מומלץ"),
         seg(90, "דיברנו על זה גם בפרק שמונה"), seg(120, "אם דיברנו פעם על זהב"), seg(130, "בפרק 12 נדבר")]
    cards = f.pick(f.find(s, 10, IDX), IDX)
    eps = [c["referenced_episode"] for c in cards]
    assert eps == [5, 8, 7]
    c8 = [c for c in cards if c["referenced_episode"] == 8][0]
    assert c8["v5_timestamp"] == 50 and c8["youtube_video_id"] == "6chKVe8nQ8A" and "x2" in c8["detection"]
    assert f.validate(cards, IDX) == []


def test_topic_needs_backref_cue_and_max_four():
    assert f.find([seg(1, "מחיר הזהב עלה היום")], 10, IDX) == {}
    s = [seg(i, f"דיברנו בפרק {n}") for i, n in enumerate([1, 3, 4, 5, 6, 7])]
    assert len(f.pick(f.find(s, 10, IDX), IDX)) == 4


def test_validate_rejects_bad():
    bad = [{"referenced_episode": 8, "youtube_video_id": "XXXXXXXXXXX", "quote": "q", "v5_timestamp": 1}] * 2
    errs = f.validate(bad, IDX)
    assert any("twice" in e for e in errs) and any("not in episode index" in e for e in errs)


def test_edit_cuts_and_offset_map_to_delivered_time():
    # Episode 12: raw mention 964.17, start 55.375, cut 418.208-554.5,
    # offset (teaser+intro) 35.916667 → delivered 13:28 (808.42), not 16:40.
    s = [seg(964.17, "מי שרוצה, דיברנו על זה בפרק 3 על ספייסקס,")]
    edit = (55.375, 3275.0, [[418.208, 554.5]])
    cards = f.pick(f.find(s, 12, IDX), IDX, offset=35.916667, edit=edit)
    c3 = [c for c in cards if c["referenced_episode"] == 3][0]
    assert c3["v5_timestamp"] == 808.42
    # offset alone (the old behaviour) is the wrong 16:40 / 1000.09
    wrong = f.pick(f.find(s, 12, IDX), IDX, offset=35.916667)
    assert [c for c in wrong if c["referenced_episode"] == 3][0]["v5_timestamp"] == 1000.09


def test_mention_inside_a_cut_uses_the_next_kept_mention():
    s = [seg(500.0, "דיברנו על זה בפרק 3"), seg(700.0, "עוד פעם, בפרק 3")]
    edit = (0.0, 1000.0, [[400.0, 600.0]])
    cards = f.pick(f.find(s, 12, IDX), IDX, offset=10.0, edit=edit)
    c3 = [c for c in cards if c["referenced_episode"] == 3][0]
    assert c3["v5_timestamp"] == 510.0  # 700 - 200 cut + 10 offset
    assert "עוד פעם" in c3["quote"]
