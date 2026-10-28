#!/usr/bin/env python3
"""Check a lesson's takes the moment they arrive, while a beat can still be recorded again.

Usage:
    python3 check_takes.py lesson-N/lesson-N-video.json --takes-dir DIR [--words-dir WORDS] [--faces]

Per take: the picture (1920x1080 at 30 fps expected; less is upscaled, so punch-ins stay small), clipping (samples
at full scale: the mic gain is too high and levelling can't undo it), the noise floor (the quietest stretches;
above -50 dB it turns into audible hiss once the lesson is levelled to -14 LUFS), and with --words-dir how long
the take runs before the first word and after the last. With --faces (macOS, Apple Vision) the face's width and
position in each take: when they differ by more than a few percent, line them up with `make_lesson_base.py frame`
(it needs a background) or re-record. Prints one line per finding and exits 1 when something should be fixed
before cutting. Nothing is written.
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

CLIP_SAMPLES = 20       # a click or two at full scale is the record button; more is the voice clipping
NOISE_FLOOR = -50.0     # dB RMS of the quietest tenth of the take
WAIT = 5.0              # seconds before the first word or after the last worth a mention
FACE_WIDTH = 0.05       # faces wider or narrower than the median by this share: framing drifted
FACE_X = 40             # px between face centres


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    st = data["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"width": st["width"], "height": st["height"], "fps": round(int(num) / int(den), 2),
            "duration": float(data["format"]["duration"])}


def audio_log(path: Path) -> str:
    """astats per window (RMS) and overall (peaks), as ffmpeg logs them."""
    return subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(path), "-vn", "-af",
                           "asplit[a][b];[a]astats=metadata=1:reset=15,ametadata=print:key=lavfi.astats.Overall.RMS_level,"
                           "anullsink;[b]astats=measure_perchannel=none", "-f", "null", "-"],
                          capture_output=True, text=True).stderr


def parse_audio(log: str) -> dict:
    """{floor: dB RMS of the quietest tenth of the windows, peak: dB, at_peak: samples at the peak level}."""
    rms = sorted(float(x) for x in re.findall(r"RMS_level=(-?[\d.]+)", log))
    peak = re.findall(r"Peak level dB: (-?[\d.]+|-inf)", log)
    count = re.findall(r"Peak count: ([\d.]+)", log)
    return {"floor": rms[len(rms) // 10] if rms else None,
            "peak": float(peak[-1]) if peak and peak[-1] != "-inf" else None,
            "at_peak": int(float(count[-1])) if count else 0}


def take_findings(beat: int, pic: dict, audio: dict, words=None) -> list:
    """[(level, text)] for one take; level 'fix' (before cutting) or 'note'."""
    out = []
    if (pic["width"], pic["height"]) != (1920, 1080) or pic["fps"] != 30:
        lvl = "fix" if pic["height"] < 1080 else "note"
        out.append((lvl, f"beat {beat}: {pic['width']}x{pic['height']} at {pic['fps']} fps, not 1920x1080 at 30"))
    if audio["peak"] is not None and audio["peak"] > -0.1 and audio["at_peak"] > CLIP_SAMPLES:
        out.append(("fix", f"beat {beat}: clips ({audio['at_peak']} samples at full scale): turn the mic gain down "
                           "until speech peaks around -10 to -6 dB and record it again"))
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
        findings += take_findings(t["beat"], probe(take), parse_audio(audio_log(take)), words)
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
