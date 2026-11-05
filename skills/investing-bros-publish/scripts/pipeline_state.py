#!/usr/bin/env python3
"""Read, fingerprint and evaluate an episode's extras/pipeline.json (investing-bros-producer ->
references/state-schema.md). No stage definitions here: everything needed to tell what is stale is
recorded in the state itself (each stage's output sha256s, its inputs' versions, the edit snapshot).

Used by pipeline.py (investing-bros-producer, the only writer) and publish_checklist.py
(investing-bros-publish, read-only). Shared as identical copies; edit them together.
"""
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = 1
STATE_NAME = "pipeline.json"
CACHE_NAME = ".pipeline-hash-cache.json"   # local only (size, mtime -> sha256); never synced
DONE = ("done", "approved", "waived")
TZ = timezone(timedelta(hours=2))           # Asia/Jerusalem (winter); times are for people, order comes from the log


def now() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def state_file(ep) -> Path:
    return Path(ep) / "extras" / STATE_NAME


def load(ep) -> "dict | None":
    p = state_file(ep)
    if not p.is_file():
        return None
    s = json.loads(p.read_text(encoding="utf-8"))
    if s.get("schema_version", 0) > SCHEMA_VERSION:
        raise ValueError(f"{p} is schema {s['schema_version']}; this script knows {SCHEMA_VERSION}: update the skills")
    return s


def save(ep, state: dict) -> Path:
    p = state_file(ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    state["revision"] = int(state.get("revision", 0)) + 1
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)
    return p


def digest(value) -> str:
    """sha256 of a JSON value with sorted keys (the crypto course's make_lesson_base.digest recipe)."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def version_of(outputs: dict, inputs: "dict | None" = None) -> str:
    """A stage's version: its outputs; a stage with no outputs (a gate) takes its inputs."""
    return "sha256:" + digest(outputs if outputs else {"inputs": inputs or {}})


class Hasher:
    """sha256 of files under ep, cached by (size, mtime) in extras/.pipeline-hash-cache.json."""

    def __init__(self, ep):
        self.ep = Path(ep)
        self.path = self.ep / "extras" / CACHE_NAME
        try:
            self.cache = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.cache = {}
        self.dirty = False

    def sha(self, rel: str) -> "str | None":
        p = self.ep / rel
        if not p.is_file():
            return None
        st = p.stat()
        key = [st.st_size, st.st_mtime_ns]
        hit = self.cache.get(rel)
        if hit and hit[:2] == key:
            return hit[2]
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        self.cache[rel] = key + [h.hexdigest()]
        self.dirty = True
        return h.hexdigest()

    def flush(self):
        if self.dirty:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
            except OSError:
                pass
            self.dirty = False


def all_marks(state: dict) -> dict:
    """Marks as {id: {"evidence": ...}}, legacy marks (from a migration) under the current ones."""
    legacy = {k: {"evidence": v} for k, v in ((state.get("legacy") or {}).get("marked") or {}).items()}
    return {**legacy, **state.get("marks", {})}


def current_outputs(ep, recorded: dict, marks: dict, hasher: "Hasher | None" = None) -> dict:
    """Recompute each recorded output: files by sha256, `mark:ID` entries by the mark's evidence."""
    hasher = hasher or Hasher(ep)
    out = {}
    for key in recorded:
        if key.startswith("mark:"):
            m = marks.get(key[5:])
            out[key] = digest(m["evidence"]) if m else None
        else:
            out[key] = hasher.sha(key)
    return out


# ---- the overlap rule: a new edit only stales renders whose raw ranges it touches -------------------

def kept(edit: dict) -> list:
    if not edit:
        return []
    ranges, cur = [], float(edit["start"])
    for a, b in sorted((float(a), float(b)) for a, b in edit.get("cuts", [])):
        ranges.append((cur, a))
        cur = b
    ranges.append((cur, float(edit["end"])))
    return ranges


def changed_spans(old: dict, new: dict) -> list:
    """Raw spans kept by one edit and not the other."""
    def minus(xs, ys):
        out = []
        for a, b in xs:
            pieces = [(a, b)]
            for c, d in ys:
                nxt = []
                for x, y in pieces:
                    if d <= x or c >= y:
                        nxt.append((x, y))
                        continue
                    if c > x:
                        nxt.append((x, c))
                    if d < y:
                        nxt.append((d, y))
                pieces = nxt
            out += [p for p in pieces if p[1] - p[0] > 1e-6]
        return out
    ko, kn = kept(old), kept(new)
    return sorted(minus(ko, kn) + minus(kn, ko))


def overlaps(ranges, spans) -> bool:
    return any(a < d and c < b for a, b in ranges for c, d in spans)


# ---- evaluation -----------------------------------------------------------------------------------

def evaluate(ep, state: dict, hasher: "Hasher | None" = None) -> dict:
    """{stage_key: {"status": "current"|"stale"|"failed", "why": str}} for every recorded stage."""
    hasher = hasher or Hasher(ep)
    stages, marks = state.get("stages", {}), all_marks(state)
    memo = {}

    def ev(key, seen=()):
        if key in memo:
            return memo[key]
        rec = stages.get(key)
        if rec is None:
            return {"status": "missing", "why": "not passed yet"}
        if key in seen:
            return {"status": "current", "why": ""}
        seen = seen + (key,)
        if rec.get("state") == "failed":
            res = {"status": "failed", "why": rec.get("why", "")}
        elif rec.get("state") == "waived":
            res = {"status": "current", "why": ""}
        else:
            res = {"status": "current", "why": ""}
            if rec.get("outputs"):
                cur = current_outputs(ep, rec["outputs"], marks, hasher)
                changed = [k for k, v in rec["outputs"].items() if cur.get(k) != v]
                if changed:
                    res = {"status": "stale", "why": "changed since it passed: " + ", ".join(
                        ("missing " if cur.get(k) is None else "") + k for k in changed)}
            if res["status"] == "current" and rec.get("state") == "approved" and rec.get("of"):
                of = ev(rec["of"], seen)
                of_rec = stages.get(rec["of"])
                approved_ver = rec.get("of_version", rec.get("version"))
                if of["status"] != "current":
                    res = {"status": "stale", "why": f"{rec['of']} is {of['status']}"}
                elif rec.get("of_keys"):
                    now_ver = version_of({k: (of_rec.get("outputs") or {}).get(k) for k in rec["of_keys"]})
                    if now_ver != approved_ver:
                        res = {"status": "stale", "why": f"{', '.join(rec['of_keys'])} changed after the approval"}
                elif of_rec.get("version") != approved_ver:
                    res = {"status": "stale", "why": f"{rec['of']} changed after the approval"}
            if res["status"] == "current":
                for inp, ver in (rec.get("inputs") or {}).items():
                    i = ev(inp, seen)
                    irec = stages.get(inp) or {}
                    if i["status"] == "current" and irec.get("version") == ver:
                        continue
                    data = rec.get("data") or {}
                    if (i["status"] == "current" and data.get("raw_ranges") is not None and data.get("edit")
                            and (irec.get("data") or {}).get("edit") is not None):
                        spans = changed_spans(data["edit"], irec["data"]["edit"])
                        if not overlaps(data["raw_ranges"], spans):
                            continue          # the new edit doesn't touch this render
                        res = {"status": "stale", "why": f"{inp} changed inside its raw range "
                               + ", ".join(f"{a:.1f}-{b:.1f}" for a, b in spans)}
                        break
                    res = {"status": "stale", "why": f"{inp} " + ("is " + i["status"] if i["status"] != "current"
                                                                  else "changed after it passed")}
                    break
        memo[key] = res
        return res

    out = {k: ev(k) for k in stages}
    hasher.flush()
    return out


def is_current(ep, state: dict, key: str, evaluation: "dict | None" = None) -> bool:
    ev = evaluation if evaluation is not None else evaluate(ep, state)
    return key in state.get("stages", {}) and ev.get(key, {}).get("status") == "current"


def add_event(state: dict, kind: str, track: str = "", stage: str = "", detail: str = "") -> dict:
    e = {"at": now(), "kind": kind, "track": track, "stage": stage, "detail": detail}
    state.setdefault("events", []).append(e)
    return e


def find_state_near(path) -> "Path | None":
    """extras/pipeline.json next to a file in extras/ (e.g. publish-checklist.json) or in an episode dir."""
    p = Path(path)
    for c in ([p / "extras" / STATE_NAME] if p.is_dir() else []) + [p.parent / STATE_NAME,
                                                                   p.parent / "extras" / STATE_NAME]:
        if c.is_file():
            return c
    return None


def episode_dir_of(state_path: Path) -> Path:
    return Path(state_path).parent.parent


if __name__ == "__main__":
    import sys
    ep = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.getcwd())
    s = load(ep)
    if s is None:
        print(f"no {state_file(ep)}")
        sys.exit(1)
    for k, v in evaluate(ep, s).items():
        print(f"{v['status']:8} {k} {v['why']}")
