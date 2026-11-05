"""episode_owner.py: the owner comes from extras/pipeline.json; Amitai when there is none."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import episode_owner as eo  # noqa: E402


def test_no_state_means_amitai(tmp_path):
    assert eo.check_quote("Amitai 10:00: ok", tmp_path)[0]
    ok, owner, msg = eo.check_quote("Nadav 10:00: ok", tmp_path)
    assert not ok and owner == "amitai" and "not this episode's owner" in msg


def test_state_owner_found_from_any_path_in_the_episode(tmp_path):
    (tmp_path / "extras").mkdir()
    (tmp_path / "extras/pipeline.json").write_text(json.dumps({"owner": {"name": "nadav", "confirmed": False}}))
    (tmp_path / "Shorts").mkdir()
    for p in (tmp_path, tmp_path / "extras", tmp_path / "extras/artwork-register.json",
              tmp_path / "Shorts/שורט-01-x-cover.jpg", tmp_path / "thumbnail-פרק-9.jpg"):
        assert eo.load_owner(eo.find_state(p))["name"] == "nadav"
    assert eo.check_quote("נדב 10:00: מאשר", tmp_path)[0]
    assert not eo.check_quote("agent: ok", tmp_path)[0]
    assert not eo.check_quote("", tmp_path)[0]
    assert eo.main([str(tmp_path)]) == 0
