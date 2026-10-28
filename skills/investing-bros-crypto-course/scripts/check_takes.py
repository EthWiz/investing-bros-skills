#!/usr/bin/env python3
"""Check a lesson's takes the moment they arrive, while a beat can still be recorded again.

Usage:
    python3 check_takes.py lesson-N/lesson-N-video.json --takes-dir DIR [--words-dir WORDS] [--faces]

Per take: the picture (1920x1080 at 30 fps expected; less is upscaled, so punch-ins stay small); the sound, which
must be there and audible (a take with no audio track, or only silence, can't be cut); clipping, measured as the
share of samples within 1 dB of full scale, which survives AAC encoding where an exact-peak count doesn't (more
than 0.05% is a voice clipping: the mic gain is too high and levelling can't undo it); the noise floor (the quietest
stretches; above -50 dB it turns into audible hiss once the lesson is levelled to -14 LUFS); and with --words-dir
how long the take runs before the first word and after the last. With --faces (macOS, Apple Vision) the face's
width and position in each take: when they differ by more than a few percent, line them up with
`make_lesson_base.py frame` (it needs a background) or re-record. Prints one line per finding and exits 1 when
something should be fixed before cutting. Nothing is written.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lesson_framing  # noqa: E402
from make_lesson_base import take_path, word_times, words_name  # noqa: E402

CLIPPED = 5e-4          # share of samples within 1 dB of full scale: lesson 1's takes 0.001-0.007%, a clipped voice
NEAR_CLIP = 1e-4        # far more (a deliberately clipped signal, AAC-encoded: 50%)
SILENT = -60.0          # mean dB: nothing audible (digital silence measures -91)
NOISE_FLOOR = -50.0     # dB RMS of the quietest tenth of the take
WAIT = 5.0              # seconds before the first word or after the last worth a mention
FACE_WIDTH = 0.05       # faces wider or narrower than the median by this share: framing drifted
FACE_X = 40             # px between face centres


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = [st for st in data["streams"] if st["codec_type"] == "video"][0]
    num, den = video["r_frame_rate"].split("/")
    return {"width": video["width"], "height": video["height"], "fps": round(int(num) / int(den), 2),
            "duration": float(data["format"]["duration"]),
            "audio": any(st["codec_type"] == "audio" for st in data["streams"])}


def audio_log(path: Path) -> str:
    """astats per window (RMS, for the noise floor) and volumedetect (level and the samples near full scale)."""
    return subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-vn", "-af",
                           "asplit[a][b];[a]astats=metadata=1:reset=15,ametadata=print:key=lavfi.astats.Overall.RMS_level,"
                           "anullsink;[b]volumedetect", "-f", "null", "-"],
                          capture_output=True, text=True).stderr


def parse_audio(log: str) -> dict:
    """{samples, mean, max: dB, near_full: samples within 1 dB of full scale, floor: dB RMS of the quietest tenth
    of the windows}; None for what the log doesn't have (the analysis failed)."""
    rms = sorted(float(x) for x in re.findall(r"RMS_level=(-?[\d.]+)", log))
    samples = [int(x) for x in re.findall(r"n_samples: (\d+)", log)]
    mean = re.findall(r"mean_volume: (-?[\d.]+) dB", log)
    peak = re.findall(r"max_volume: (-?[\d.]+) dB", log)
    near = re.findall(r"histogram_0db: (\d+)", log)
    return {"samples": max(samples) if samples else 0, "mean": float(mean[-1]) if mean else None,
            "max": float(peak[-1]) if peak else None, "near_full": int(near[-1]) if near else 0,
            "floor": rms[len(rms) // 10] if rms else None}


def take_findings(beat: int, pic: dict, audio, words=None) -> list:
    """[(level, text)] for one take; level 'fix' (before cutting) or 'note'. audio None = no audio track."""
    out = []
    if (pic["width"], pic["height"]) != (1920, 1080) or pic["fps"] != 30:
        lvl = "fix" if pic["height"] < 1080 else "note"
        out.append((lvl, f"beat {beat}: {pic['width']}x{pic['height']} at {pic['fps']} fps, not 1920x1080 at 30"))
    if audio is None:
        return out + [("fix", f"beat {beat}: no audio track: check the mic source in OBS and record it again")]
    if not audio["samples"] or audio["mean"] is None:
        return out + [("fix", f"beat {beat}: its sound couldn't be measured: open the take and listen")]
    if audio["mean"] < SILENT:
        return out + [("fix", f"beat {beat}: no audible sound (mean {audio['mean']:.0f} dB): wrong or muted mic; "
                              "record it again")]
    share = audio["near_full"] / audio["samples"]
    if share > CLIPPED:
        out.append(("fix", f"beat {beat}: clips ({share:.2%} of samples within 1 dB of full scale): turn the mic gain "
                           "down until speech peaks around -10 to -6 dB and record it again"))
    elif share > NEAR_CLIP:
        out.append(("note", f"beat {beat}: peaks touch full scale ({share:.3%} of samples): a little less gain next time"))
    if audio["floor"] is not None and audio["floor"] > NOISE_FLOOR:
        out.append(("note", f"beat {beat}: noise floor {audio['floor']:.0f} dB: audible hiss after levelling; "
                            "quieter room or less gain next time"))
    if words:
        lead, tail = words[0][0], pic["duration"] - words[-1][1]
        if lead > WAIT:
            out.append(("note", f"beat {beat}: {lead:.1f} s before the first word (trimmed away)"))
        if tail > WAIT:
            out.append(("note", f"beat {beat}: {tail:.1f} s after the last word (trimmed away)"))
    return out


def check_take(beat: int, take: Path, words=None) -> list:
    pic = probe(take)
    return take_findings(beat, pic, parse_audio(audio_log(take)) if pic["audio"] else None, words)


def face_findings(faces: dict) -> list:
    """faces {beat: box in base pixels} -> findings when the framing drifted between takes."""
    if len(faces) < 2:
        return []
    widths = sorted(f["w"] for f in faces.values())
    mid = widths[len(widths) // 2]
    xs = [f["cx"] for f in faces.values()]
    lines = [f"beat {b}: face {f['w']:.0f} px wide, centre x {f['cx']:.0f}, top {f['top']:.0f}" for b, f in sorted(faces.items())]
    if max(abs(w - mid) for w in widths) > FACE_WIDTH * mid or max(xs) - min(xs) > FACE_X:
        return [("note", line) for line in lines] + [
            ("fix", f"framing drifted: faces {widths[0]:.0f}-{widths[-1]:.0f} px wide, centres {min(xs):.0f}-{max(xs):.0f} px "
                    "across; run make_lesson_base.py frame (needs a background) or re-record")]
    return [("note", line) for line in lines]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--takes-dir", required=True)
    ap.add_argument("--words-dir")
    ap.add_argument("--faces", action="store_true", help="measure the face in every take (macOS)")
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8"))
    findings, faces = [], {}
    tool = lesson_framing.face_tool() if a.faces else None
    for t in cfg["takes"]:
        take = take_path(t, Path(a.takes_dir))
        wf = Path(a.words_dir) / words_name(t["beat"]) if a.words_dir else None
        words = word_times(wf) if wf and wf.is_file() else None
        findings += check_take(t["beat"], take, words)
        if tool:
            faces[t["beat"]] = lesson_framing.to_base(lesson_framing.measure(take, tool))
    findings += face_findings(faces)
    for level, text in findings:
        print(f"{'FIX ' if level == 'fix' else 'note'}  {text}")
    fixes = sum(1 for level, _ in findings if level == "fix")
    print(f"takes: {'ok' if not fixes else f'{fixes} to fix before cutting'}")
    return 1 if fixes else 0


if __name__ == "__main__":
    sys.exit(main())
