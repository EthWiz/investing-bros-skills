#!/usr/bin/env python3
"""Who may approve and waive for an episode: its episode owner (investing-bros-show -> Episode owner).

The owner is recorded in the episode's extras/pipeline.json (investing-bros-producer ->
references/state-schema.md). With no state file (an older episode, the crypto course,
other non-episode work) the approver is Amitai.

A quote names its speaker first: "Nadav 21:02: ..." or "נדב 21:02: ...".

    python3 episode_owner.py PATH            # prints the owner for the episode PATH belongs to

Shared by investing-bros-producer, -post-production, -publish and -brand (identical copies;
edit them together).
"""
import json
import sys
from pathlib import Path

DEFAULT = "amitai"
NAMES = {"amitai": ("amitai", "אמיתי"), "nadav": ("nadav", "נדב")}
STATE = "pipeline.json"


def find_state(path) -> "Path | None":
    """extras/pipeline.json for an episode dir, its extras/, or any file in either."""
    p = Path(path)
    cands = []
    for base in ([p] if p.is_dir() else []) + [p.parent, p.parent.parent]:
        cands += [base / "extras" / STATE, base / STATE] if base.name != "extras" else [base / STATE]
    for c in cands:
        if c.is_file():
            return c
    return None


def load_owner(state_file) -> dict:
    """{'name': 'amitai'|'nadav', 'confirmed': bool, 'source': str}"""
    if state_file is None:
        return {"name": DEFAULT, "confirmed": True, "source": "no episode state: Amitai approves"}
    data = json.loads(Path(state_file).read_text(encoding="utf-8"))
    owner = data.get("owner") or {}
    name = owner.get("name", DEFAULT)
    if name not in NAMES:
        raise ValueError(f"{state_file}: unknown owner {name!r}")
    return {"name": name, "confirmed": bool(owner.get("confirmed", True)), "source": str(state_file)}


def speaker(quote: str) -> "str | None":
    q = (quote or "").strip().lower()
    for name, spellings in NAMES.items():
        if any(q.startswith(s) for s in spellings):
            return name
    return None


def check_quote(quote: str, path) -> "tuple[bool, str, str]":
    """(ok, owner, message). ok when the quote is in the episode owner's own words."""
    owner = load_owner(find_state(path))["name"]
    who = speaker(quote)
    if not (quote or "").strip() or who is None:
        return False, owner, f'must quote the episode owner ({owner}): --by "{owner.title()} HH:MM: <their words>"'
    if who != owner:
        return False, owner, (f"{who.title()} is not this episode's owner ({owner}); only the owner approves or "
                              "waives (investing-bros-show -> Episode owner)")
    return True, owner, "ok"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    o = load_owner(find_state(argv[0]))
    print(f"{o['name']}{'' if o['confirmed'] else ' (unconfirmed)'}  [{o['source']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
