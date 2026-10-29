"""The face scorer must rank every still Amitai picked above every one he rejected."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "evals" / "face-picks"
sys.path.insert(0, str(EVAL))
sys.path.insert(0, str(ROOT / "skills" / "investing-bros-brand" / "scripts"))

import run_eval  # noqa: E402


def _load():
    doc = json.loads((EVAL / "labels.json").read_text(encoding="utf-8"))
    feats = json.loads((EVAL / "features.json").read_text(encoding="utf-8"))
    bases = {h: v for h, v in doc.get("baselines", {}).items() if isinstance(v, dict)}
    return feats, doc["items"], bases


def test_every_good_above_every_bad():
    feats, labels, bases = _load()
    r = run_eval.evaluate(feats, labels, "v2", bases)
    assert r["pairwise"] == 1, r["wrong"]
    assert r["margin"] > 0.1


def test_labels_are_complete():
    feats, labels, _ = _load()
    assert set(feats) == set(labels)
    for k, v in labels.items():
        assert v["label"] in {"good", "bad", "unknown"}
        assert v["host"] in {"amitai", "nadav"} and v["t_sec"] > 0
        if v["label"] == "bad":
            assert v.get("reason"), k
