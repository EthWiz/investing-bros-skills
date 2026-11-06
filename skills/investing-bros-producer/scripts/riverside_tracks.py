#!/usr/bin/env python3
"""Pull per-speaker Riverside tracks from the web dashboard. Browser only.

The pull starts when the episode owner says in chat that the episode was recorded.
That message is recorded here (`begin --by`) and the Producer arms one temporary
polling routine. The routine checks about every 15 minutes (allowed range 10-20).
Each wake looks once. When the tracks are downloaded, or after about 6 hours, the
routine is deleted or disabled (`disarm: true`). This script does not sleep and
does not loop.

  riverside_tracks.py begin   EP --project NAME --by "Owner HH:MM: ..." [--every 15] [--now ISO]
  riverside_tracks.py due     EP [--now ISO]
  riverside_tracks.py checked EP [--now ISO]
  riverside_tracks.py commit  EP --listing FILE [--now ISO]
  riverside_tracks.py verify  EP

Sign in at https://riverside.fm (it redirects to https://riverside.com) with the
Grok Bot vault login, filled only by secure fill. This script never reads or
prints that login. It never deletes a Riverside studio, project or recording.
Disabling the polling routine is not a delete on Riverside.

Exit 0 = armed / wait / check / ready. Exit 1 = refused, not ready, or give-up.
Exit 2 = usage. On give-up, disarm is still true: remove the routine anyway.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import episode_owner as O  # noqa: E402

SIGN_IN_URL = "https://riverside.fm"   # redirects to riverside.com
STUDIO_ORIGIN = "https://riverside.com"
MANIFEST_REL = "extras/riverside-pull.json"
POLL_DEFAULT_MIN = 15
POLL_MIN_MIN = 10
POLL_MAX_MIN = 20
GIVE_UP = timedelta(hours=6)
DURATION_TOLERANCE_S = 1.0
HIGH = "high"
READY = "ready"
KINDS = ("video", "audio")
COMMANDS = ("begin", "due", "checked", "commit", "verify")
SECRET_WORDS = ("password", "secret", "token", "cookie")
ALERT = ("Riverside tracks are still not ready after about 6 hours. "
         "Alert the episode owner and stop polling.")
DISARM_LINE = "Delete or disable the temporary polling routine. Do not schedule another check."
KEEP_LINE = "Leave the temporary polling routine armed. Do not poll again in this turn."


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"{value} needs a timezone")
    return dt


def interval_minutes(value) -> int:
    """The routine's gap. About 15 minutes; 10 through 20 is the allowed range."""
    try:
        if isinstance(value, bool):
            raise ValueError
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"polling interval must be {POLL_MIN_MIN}-{POLL_MAX_MIN} minutes") from None
    if n < POLL_MIN_MIN or n > POLL_MAX_MIN:
        raise ValueError(f"polling interval must be {POLL_MIN_MIN}-{POLL_MAX_MIN} minutes (about 15)")
    return n


def manifest_path(ep) -> Path:
    return Path(ep) / MANIFEST_REL


def load(ep):
    p = manifest_path(ep)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ValueError(f"{MANIFEST_REL} unreadable") from e


def save(ep, manifest: dict) -> Path:
    p = manifest_path(ep)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(p)
    return p


def recorded_message_ok(ep, quote: str) -> "tuple[bool, str]":
    """The owner's chat message that the episode was recorded. Not an approval."""
    if O.find_state(ep) is None:
        return False, "no extras/pipeline.json yet: pipeline.py start, then begin --by the owner's words"
    owner = O.load_owner(O.find_state(ep))["name"]
    who = O.speaker(quote)
    if not (quote or "").strip() or who is None:
        return False, f'must quote the episode owner ({owner}): --by "{owner.title()} HH:MM: <their words>"'
    if who != owner:
        return False, f"{who.title()} is not this episode's owner ({owner}); only that message arms the pull"
    return True, ""


def refuse_destructive(action: str) -> None:
    """The dashboard is read and download only. The polling routine is not a Riverside object."""
    text = (action or "").lower()
    if any(w in text for w in ("delete", "trash", "remove", "destroy")) and any(
            n in text for n in ("studio", "project", "recording")):
        raise ValueError("refusing to delete a Riverside studio, project or recording")


def secret_fields(obj, prefix="") -> list:
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k)
            here = f"{prefix}{key}"
            if any(w in key.lower() for w in SECRET_WORDS):
                found.append(here)
            else:
                found.extend(secret_fields(v, here + "."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(secret_fields(v, f"{prefix}[{i}]."))
    return found


def _pos_int(n) -> bool:
    return isinstance(n, int) and not isinstance(n, bool) and n > 0


def part_no(value) -> int:
    if isinstance(value, bool) or isinstance(value, float) or (isinstance(value, int) and value < 1):
        raise ValueError("part must be a positive integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit() and int(value) >= 1:
        return int(value)
    raise ValueError("part must be a positive integer")


def normalize_rel(path: str) -> str:
    raw = str(path).replace("\\", "/").strip()
    if not raw or raw.startswith(("/", "~")) or ".." in Path(raw).parts:
        raise ValueError(f"path must stay inside riverside/: {path}")
    parts = Path(raw).parts
    if not parts or parts[0] != "riverside":
        raise ValueError(f"path must stay inside riverside/: {path}")
    return Path(*parts).as_posix()


def listing_problems(listing: dict) -> list:
    if not isinstance(listing, dict):
        return ["listing must be an object"]
    blocked = secret_fields(listing)
    if blocked:
        return ["listing contains a secret field: " + ", ".join(blocked)]
    tracks = listing.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        return ["listing needs a tracks list"]
    problems, grouped, speakers = [], {}, []
    for t in tracks:
        if not isinstance(t, dict):
            problems.append("track entry is not an object")
            continue
        name = str(t.get("speaker") or "").strip()
        kind = t.get("kind")
        try:
            part = part_no(t.get("part", 1))
        except ValueError:
            problems.append(f"{name or '?'}: part must be a positive integer")
            continue
        if not name or kind not in KINDS:
            problems.append("each track needs a speaker and kind video or audio")
            continue
        key = (name, part, kind)
        if key in grouped:
            problems.append(f"duplicate {kind} for {name} part {part}")
            continue
        grouped[key] = t
        if name not in speakers:
            speakers.append(name)
    for name in listing.get("participants") or []:
        name = str(name).strip()
        if name and name not in speakers:
            speakers.append(name)
    if not speakers:
        problems.append("no speakers")
    parts = {}
    for name, part, _kind in grouped:
        parts.setdefault(name, set()).add(part)
    for name in speakers:
        if name not in parts:
            problems.append(f"{name}: no tracks")
            continue
        for part in sorted(parts[name]):
            for kind in KINDS:
                t = grouped.get((name, part, kind))
                if t is None:
                    problems.append(f"{name} part {part}: missing high-quality {kind}")
                    continue
                if t.get("quality") != HIGH or t.get("status") != READY:
                    problems.append(f"{name} part {part}: {kind} is not a ready high-quality track "
                                    f"(quality={t.get('quality')!r}, status={t.get('status')!r})")
                    continue
                if not _pos_int(t.get("bytes")):
                    problems.append(f"{name} part {part}: {kind} needs a positive integer bytes")
                dur = t.get("duration_s")
                if isinstance(dur, bool) or not isinstance(dur, (int, float)) or float(dur) <= 0:
                    problems.append(f"{name} part {part}: {kind} needs duration_s")
                if not t.get("path"):
                    problems.append(f"{name} part {part}: {kind} needs a path")
    return problems


def build_speakers(listing: dict) -> list:
    by, order = {}, []
    for t in listing["tracks"]:
        if t.get("quality") != HIGH or t.get("status") != READY:
            continue
        name = str(t["speaker"]).strip()
        part = part_no(t.get("part", 1))
        if name not in order:
            order.append(name)
        by.setdefault(name, {}).setdefault(part, {})[t["kind"]] = {
            "path": normalize_rel(t["path"]), "bytes": int(t["bytes"]),
            "duration_s": float(t["duration_s"]), "quality": HIGH}
    return [{"name": name, "parts": [
        {"part": n, "video": by[name][n]["video"], "audio": by[name][n]["audio"]}
        for n in sorted(by[name])]} for name in order]


def probe_duration(path) -> "float | None":
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return float((r.stdout or "").strip())
    except ValueError:
        return None


def file_problems(ep, speakers, probe) -> list:
    out, seen = [], set()
    root = Path(ep).resolve()
    for sp in speakers:
        for part in sp["parts"]:
            for kind in KINDS:
                f = part[kind]
                try:
                    rel = normalize_rel(f["path"])
                except ValueError as e:
                    out.append(str(e))
                    continue
                if rel in seen:
                    out.append(f"duplicate path {rel}")
                    continue
                seen.add(rel)
                path = Path(ep) / rel
                if not path.is_file():
                    out.append(f"missing {rel}")
                    continue
                try:
                    path.resolve().relative_to(root)
                except ValueError:
                    out.append(f"path leaves the episode folder: {rel}")
                    continue
                size = path.stat().st_size
                if size != int(f["bytes"]):
                    out.append(f"{rel}: size {size} != {f['bytes']}")
                got = probe(path)
                want = float(f["duration_s"])
                if got is None:
                    out.append(f"{rel}: duration could not be read")
                elif abs(float(got) - want) > DURATION_TOLERANCE_S:
                    out.append(f"{rel}: duration {got} != {want} (tolerance {DURATION_TOLERANCE_S}s)")
    return out


def verify_manifest(ep, manifest: dict, probe=None) -> list:
    probe = probe or probe_duration
    problems = []
    if manifest.get("via") != "browser":
        problems.append("tracks are pulled in the browser on the Riverside web dashboard")
    if manifest.get("drive_upload") is not False:
        problems.append("raw footage is not uploaded to Drive when Riverside is accessible")
    if manifest.get("status") != "ready":
        problems.append(f"status is {manifest.get('status')!r}, not ready")
    speakers = manifest.get("speakers") or []
    if not speakers:
        problems.append("no speakers")
        return problems
    structural = False
    for sp in speakers:
        name = sp.get("name") or "?"
        parts = sp.get("parts") or []
        if not parts:
            structural = True
            problems.append(f"{name}: no parts")
            continue
        for part in parts:
            for kind in KINDS:
                f = part.get(kind) or {}
                if f.get("quality") != HIGH or not f.get("path"):
                    structural = True
                    problems.append(f"{name} part {part.get('part')}: missing high-quality {kind}")
    if not structural:
        problems.extend(file_problems(ep, speakers, probe))
    return problems


def verify_episode(ep, probe=None) -> list:
    """Problems that keep main.riverside from passing. Empty means the files are recorded."""
    try:
        m = load(ep)
    except ValueError as e:
        return [str(e)]
    if m is None:
        return [f"no {MANIFEST_REL} (riverside_tracks.py begin, after the owner says it was recorded)"]
    if m.get("status") != "ready":
        return [f"Riverside pull is {m.get('status')!r}. The temporary polling routine checks the web "
                "dashboard about every 15 minutes (10-20). Give up after about 6 hours. Do not busy-loop."]
    return verify_manifest(ep, m, probe)


def media_paths(manifest: dict) -> list:
    out = []
    for sp in manifest.get("speakers") or []:
        for part in sp.get("parts") or []:
            for kind in KINDS:
                f = part.get(kind) or {}
                if f.get("path"):
                    out.append(f["path"])
    return out


def stage_data(manifest: dict) -> dict:
    tracks = []
    for sp in manifest.get("speakers") or []:
        for part in sp.get("parts") or []:
            for kind in KINDS:
                f = part.get(kind) or {}
                if not f:
                    continue
                tracks.append({"speaker": sp.get("name"), "part": part.get("part"), "kind": kind,
                               "path": f.get("path"), "bytes": f.get("bytes"),
                               "duration_s": f.get("duration_s")})
    return {"via": "browser", "project": manifest.get("project"), "drive_upload": False,
            "interval_minutes": manifest.get("interval_minutes"), "armed_by": manifest.get("armed_by"),
            "started_at": manifest.get("started_at"), "ready_at": manifest.get("ready_at"),
            "tracks": tracks}


def poll_decision(started_at, now, last_check_at, status, every) -> dict:
    """One decision. The caller schedules a routine or stops. This function does not wait."""
    every = interval_minutes(every)
    base = {"interval_minutes": every, "alert": "", "error": ""}
    if status == "ready":
        return {**base, "action": "ready", "next_check_at": None, "disarm": True}
    if status == "gave_up" or now >= started_at + GIVE_UP:
        return {**base, "action": "give_up", "next_check_at": None, "disarm": True, "alert": ALERT}
    gap = timedelta(minutes=every)
    if last_check_at is None or now >= last_check_at + gap:
        nxt = now + gap
        deadline = started_at + GIVE_UP
        if nxt > deadline:
            nxt = deadline
        return {**base, "action": "check", "next_check_at": nxt, "disarm": False}
    return {**base, "action": "wait", "next_check_at": last_check_at + gap, "disarm": False}


def _clock(manifest, now):
    now = now or datetime.now(timezone.utc)
    started = parse_time(manifest["started_at"])
    last = parse_time(manifest["last_check_at"]) if manifest.get("last_check_at") else None
    every = interval_minutes(manifest.get("interval_minutes") or POLL_DEFAULT_MIN)
    return now, poll_decision(started, now, last, manifest.get("status"), every)


def _need(ep):
    m = load(ep)
    if m is None:
        raise ValueError(f"no {MANIFEST_REL}: begin after the owner says the episode was recorded")
    return m


def begin(ep, project: str, by: str, every=POLL_DEFAULT_MIN, now=None) -> dict:
    ok, msg = recorded_message_ok(ep, by)
    if not ok:
        raise ValueError(msg)
    project = (project or "").strip()
    if not project:
        raise ValueError("project name is required")
    every = interval_minutes(every)
    existing = load(ep)
    if existing:
        return existing
    now = now or datetime.now(timezone.utc)
    m = {"project": project, "started_at": iso(now), "last_check_at": None, "status": "waiting",
         "via": "browser", "drive_upload": False, "interval_minutes": every, "armed_by": by.strip(),
         "ready_at": None, "checks": [], "speakers": []}
    save(ep, m)
    return m


def due(ep, now=None) -> dict:
    m = _need(ep)
    now, decision = _clock(m, now)
    if decision["action"] == "give_up" and m.get("status") != "gave_up":
        m["status"] = "gave_up"
        save(ep, m)
    if decision.get("next_check_at") is not None:
        decision["next_check_at"] = iso(decision["next_check_at"])
    return decision


def checked(ep, now=None) -> dict:
    """Record one dashboard look. Refuses to move the clock when a check is not due."""
    m = _need(ep)
    now, decision = _clock(m, now)
    if decision["action"] == "wait":
        decision["next_check_at"] = iso(decision["next_check_at"])
        decision["error"] = "a check is not due; leave the routine armed and stop"
        return decision
    if decision["action"] == "ready":
        return decision
    if decision["action"] == "give_up":
        m["status"] = "gave_up"
        m["last_check_at"] = iso(now)
        save(ep, m)
        decision["next_check_at"] = None
        return decision
    m["last_check_at"] = iso(now)
    m.setdefault("checks", []).append({"at": iso(now), "ready": False})
    save(ep, m)
    nxt = poll_decision(parse_time(m["started_at"]), now, now, "waiting", m["interval_minutes"])
    nxt["next_check_at"] = iso(nxt["next_check_at"])
    nxt["action"] = "scheduled"
    return nxt


def commit(ep, listing: dict, now=None) -> list:
    now = now or datetime.now(timezone.utc)
    try:
        m = _need(ep)
    except ValueError as e:
        return [str(e)]
    blocked = secret_fields(listing)
    if blocked:
        return ["listing contains a secret field: " + ", ".join(blocked)]
    problems = listing_problems(listing)
    if problems:
        return problems
    try:
        speakers = build_speakers(listing)
    except ValueError as e:
        return [str(e)]
    ready = dict(m)
    ready.update(status="ready", via="browser", drive_upload=False, ready_at=iso(now),
                 speakers=speakers, last_check_at=iso(now))
    problems = verify_manifest(ep, ready)
    if problems:
        return problems
    save(ep, ready)
    return []


def render(decision: dict) -> str:
    lines = [f"action: {decision['action']}",
             f"disarm: {'true' if decision.get('disarm') else 'false'}",
             f"interval_minutes: {decision.get('interval_minutes', '')}"]
    if decision.get("next_check_at"):
        lines.append(f"next_check_at: {decision['next_check_at']}")
    if decision.get("alert"):
        lines.append(f"alert: {decision['alert']}")
    lines.append(DISARM_LINE if decision.get("disarm") else KEEP_LINE)
    if decision.get("error"):
        lines.append(f"error: {decision['error']}")
    return "\n".join(lines) + "\n"


def _now_arg(value):
    return parse_time(value) if value else None


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("begin")
    p.add_argument("ep")
    p.add_argument("--project", required=True)
    p.add_argument("--by", required=True)
    p.add_argument("--every", type=int, default=POLL_DEFAULT_MIN)
    p.add_argument("--now")
    p = sub.add_parser("due")
    p.add_argument("ep")
    p.add_argument("--now")
    p = sub.add_parser("checked")
    p.add_argument("ep")
    p.add_argument("--now")
    p = sub.add_parser("commit")
    p.add_argument("ep")
    p.add_argument("--listing", required=True)
    p.add_argument("--now")
    p = sub.add_parser("verify")
    p.add_argument("ep")
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        if a.cmd == "begin":
            existed = load(Path(a.ep)) is not None
            m = begin(Path(a.ep), a.project, a.by, a.every, _now_arg(a.now))
            print(f"action: {'already_armed' if existed else 'armed'}")
            print(f"interval_minutes: {m['interval_minutes']}")
            print(f"started_at: {m['started_at']}")
            print("Arm one temporary polling routine at this interval if it is not armed yet. "
                  "Run the first dashboard check in this turn. Delete or disable the routine "
                  "when a later run prints disarm: true.")
            return 0
        if a.cmd == "due":
            d = due(Path(a.ep), _now_arg(a.now))
            print(render(d), end="")
            return 1 if d["action"] == "give_up" else 0
        if a.cmd == "checked":
            d = checked(Path(a.ep), _now_arg(a.now))
            print(render(d), end="")
            return 0 if d["action"] in ("scheduled", "ready") and not d.get("error") else 1
        if a.cmd == "commit":
            listing = json.loads(Path(a.listing).read_text(encoding="utf-8"))
            problems = commit(Path(a.ep), listing, _now_arg(a.now))
            if problems:
                print("\n".join(problems), file=sys.stderr)
                return 1
            print("action: ready\ndisarm: true\n" + DISARM_LINE)
            return 0
        if a.cmd == "verify":
            problems = verify_episode(Path(a.ep))
            if problems:
                print("\n".join(problems), file=sys.stderr)
                return 1
            print("OK")
            return 0
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
