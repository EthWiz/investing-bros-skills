"""Per-episode face-pick label files (evals/face-picks/episodes/epNN.json) stay complete."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_episode_label_files_are_complete():
    files = sorted((REPO / "evals" / "face-picks" / "episodes").glob("ep*.json"))
    assert files
    for f in files:
        d = json.loads(f.read_text())
        assert d["source"]["recording"] and d["picked_on"]
        labels = [i["label"] for i in d["items"].values()]
        assert "good" in labels
        for sid, i in d["items"].items():
            assert i["host"] in ("amitai", "nadav") and i["t_sec"] >= 0, sid
            assert i["label"] in ("good", "bad", "unknown"), sid
            if i["label"] == "bad":
                assert i.get("reason") and i["reason"] != "picked", sid
