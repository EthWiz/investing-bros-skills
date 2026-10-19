#!/usr/bin/env python3
"""Render the approved Investing Bros full-frame 16:9 teaser.

The per-episode JSON format is documented in
references/teaser-fullframe.example.json. Relative paths are resolved from the
JSON file, so configs are portable and contain no machine-specific paths.
When `assembly_audio` is set, the same normalized PCM samples used for the
standalone AAC output are retained for sample-accurate episode assembly.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from brand import ACCENT, TEASER, TITLE_NAVY, WHITE, ass_colour  # noqa: E402

FADE_FIRST_IN = 0.35
FADE_JOIN = 0.12
AFADE_IN = 0.03
AFADE_OUT = 0.04
TITLE_FADE_MS = 500
LOUDNESS = {"I": -14, "TP": -1.5, "LRA": 11}
RLM = "\u200f"


def resolve_path(config_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def probe_duration(path: Path, selector: str | None = None) -> float:
    cmd = ["ffprobe", "-v", "error"]
    if selector:
        cmd += ["-select_streams", selector, "-show_entries", "stream=duration"]
    else:
        cmd += ["-show_entries", "format=duration"]
    cmd += ["-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    value = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    if not value or value == "N/A":
        raise ValueError(f"could not read duration for {path}")
    return float(value.splitlines()[0])


def probe_fps(path: Path) -> str:
    cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    value = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    if float(Fraction(value)) <= 0:
        raise ValueError(f"could not read frame rate for {path}")
    return value


def validate_audio_clock(source: Path, audio: Path, fps: float) -> None:
    """Reject a gap-collapsed WAV before it can put speech ahead of picture."""
    source_duration = probe_duration(source, "a:0")
    audio_duration = probe_duration(audio)
    tolerance = max(0.05, 1.0 / fps)
    drift = abs(source_duration - audio_duration)
    if drift > tolerance:
        raise ValueError(
            f"audio clock mismatch: source stream {source_duration:.3f}s, "
            f"WAV {audio_duration:.3f}s ({drift:.3f}s; allowed {tolerance:.3f}s). "
            "Rebuild it with make_pts_audio.sh."
        )


class Timeline:
    def __init__(self, pieces: list[dict], fps: float):
        self.segments = []
        output_start = 0.0
        for piece in pieces:
            duration = round((float(piece["end"]) - float(piece["start"])) * fps) / fps
            if duration <= 0:
                raise ValueError(f"empty teaser piece: {piece}")
            cards = [
                (float(start) - float(piece["start"]), float(end) - float(piece["start"]), text)
                for start, end, text in piece["cards"]
            ]
            for start, end, text in cards:
                if start < -0.05 or end > duration + 0.05 or end <= start:
                    raise ValueError(f"caption card outside its piece: {text!r}")
            self.segments.append({
                "host": piece["host"],
                "source_start": float(piece["start"]),
                "duration": duration,
                "output_start": output_start,
                "cards": cards,
            })
            output_start += duration
        self.duration = output_start


def _soft_mask(boxes: list[tuple], blur: int, size: tuple[int, int]) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for x0, y0, x1, y1, alpha in boxes:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=60, fill=alpha)
    return mask.filter(ImageFilter.GaussianBlur(blur))


def make_overlays(logo_path: Path, work_dir: Path) -> tuple[Path, Path]:
    width, height = TEASER["size"]
    dark = _soft_mask(
        [TEASER["caption_plate"], TEASER["title_plate"], TEASER["bottom_plate"]],
        55,
        (width, height),
    )
    plate = Image.new("RGBA", (width, height), (6, 10, 22, 0))
    plate.putalpha(dark)

    logo = Image.open(logo_path).convert("RGBA")
    layout = TEASER["logo"]
    logo_width = layout["width"]
    logo = logo.resize((logo_width, round(logo.height * logo_width / logo.width)), Image.Resampling.LANCZOS)
    alpha = logo.getchannel("A")

    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_logo = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    shadow_logo.putalpha(alpha.point(lambda value: round(value * 0.8)))
    shadow.paste(shadow_logo, (layout["x"] + 4, layout["y"] + 8), shadow_logo)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))

    rim = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    rim_logo = Image.new("RGBA", logo.size, (10, 16, 34, 0))
    rim_logo.putalpha(alpha.filter(ImageFilter.MaxFilter(5)).point(lambda value: round(value * 0.7)))
    rim.paste(rim_logo, (layout["x"], layout["y"]), rim_logo)
    plate = Image.alpha_composite(plate, Image.alpha_composite(shadow, rim.filter(ImageFilter.GaussianBlur(1))))
    plate.alpha_composite(logo, (layout["x"], layout["y"]))

    overlay = work_dir / "overlay.png"
    blur_mask = work_dir / "blurmask.png"
    plate.save(overlay)
    _soft_mask([TEASER["blur_plate"]], 35, (width, height)).save(blur_mask)
    return overlay, blur_mask


def ass_time(value: float) -> str:
    value = max(0.0, value)
    hours = int(value // 3600)
    minutes = int(value % 3600 // 60)
    seconds = value % 60
    return f"{hours}:{minutes:02d}:{seconds:05.2f}"


def caption_text(text: str) -> str:
    gold = ass_colour(ACCENT)
    white = ass_colour(WHITE)
    highlighted = re.sub(
        r"\[(.+?)\]",
        lambda match: rf"{{\c{gold}}}{match.group(1)}{{\c{white}}}",
        text,
    )
    return RLM + highlighted + RLM


def build_ass(config: dict, timeline: Timeline) -> str:
    caption = TEASER["caption"]
    kicker = TEASER["kicker"]
    title = TEASER["title"]
    gold = ass_colour(ACCENT)
    navy = ass_colour(TITLE_NAVY)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {TEASER['size'][0]}
PlayResY: {TEASER['size'][1]}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{caption['font']},{caption['size']},&H00FFFFFF,&H00FFFFFF,&H64000000,&H8C000000,0,0,0,0,100,100,0,0,1,1.2,3,2,0,0,0,-1
Style: Kick,{kicker['font']},{kicker['size']},{gold},{gold},{navy},&H64000000,0,0,0,0,100,100,0,0,1,{kicker['outline']},{kicker['shadow']},9,0,0,0,-1
Style: Title,{title['font']},{title['size']},&H00FFFFFF,&H00FFFFFF,{navy},&H64000000,0,0,0,0,100,100,0,0,1,{title['outline']},{title['shadow']},9,0,0,0,-1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def event(layer, start, end, style, text):
        return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{text}\n"

    body = event(
        2, 0, timeline.duration, "Kick",
        rf"{{\pos({kicker['x']},{kicker['y']})\fad({TITLE_FADE_MS},0)\4a&H50&\blur1}}"
        + RLM + config["kicker"] + RLM,
    )
    body += event(
        2, 0, timeline.duration, "Title",
        rf"{{\pos({title['x']},{title['y']})\fad({TITLE_FADE_MS},0)\4a&H50&\blur0.8}}"
        + RLM + config["title"] + RLM,
    )
    for segment in timeline.segments:
        segment_end = segment["output_start"] + segment["duration"]
        for start, end, text in segment["cards"]:
            body += event(
                0,
                segment["output_start"] + start,
                min(segment["output_start"] + end, segment_end),
                "Cap",
                rf"{{\an2\pos({caption['x']},{caption['y']})\blur0.7\shad3\4a&H60&}}"
                + caption_text(text),
            )
    return head + body


def build_filter(config: dict, timeline: Timeline, fps_expression: str, ass: Path) -> str:
    width, height = TEASER["size"]
    count = len(timeline.segments)
    filters = []
    for index, segment in enumerate(timeline.segments):
        try:
            x, y, crop_width, crop_height = config["crops"][segment["host"]]
        except KeyError as exc:
            raise ValueError(f"missing crop for host {segment['host']!r}") from exc
        duration = segment["duration"]
        fade_in = FADE_FIRST_IN if index == 0 else FADE_JOIN
        filters.append(
            f"[{index}:v]trim=duration={duration:.4f},setpts=PTS-STARTPTS,fps={fps_expression},"
            f"crop={crop_width}:{crop_height}:{x}:{y},scale={width}:{height}:flags=lanczos,"
            "eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.4,"
            f"fade=t=in:st=0:d={fade_in},fade=t=out:st={max(0, duration - FADE_JOIN):.4f}:d={FADE_JOIN},"
            f"format=yuv420p[v{index}]"
        )
        filters.append(
            f"[{count + index}:a]atrim=duration={duration:.4f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d={AFADE_IN},afade=t=out:st={max(0, duration - AFADE_OUT):.4f}:d={AFADE_OUT}[a{index}]"
        )
    filters.append("".join(f"[v{i}][a{i}]" for i in range(count)) + f"concat=n={count}:v=1:a=1[vc][ac]")
    filters += [
        f"[{2 * count}:v]format=rgba,trim=duration={timeline.duration:.4f}[overlay]",
        f"[{2 * count + 1}:v]format=gray,trim=duration={timeline.duration:.4f}[mask]",
        "[vc]split[sharp][blur]",
        "[blur]gblur=sigma=22,eq=brightness=-0.06,format=yuva420p[blurred]",
        "[blurred][mask]alphamerge[blurplate]",
        "[sharp][blurplate]overlay=0:0[banded]",
        f"[banded][overlay]overlay=0:0:format=auto,ass={ass}:fontsdir={config['fonts']},format=yuv420p[vout]",
    ]
    return ";".join(filters)


def measured_loudnorm(raw_path: Path) -> str:
    base = f"loudnorm=I={LOUDNESS['I']}:TP={LOUDNESS['TP']}:LRA={LOUDNESS['LRA']}"
    result = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(raw_path), "-vn", "-af", base + ":print_format=json", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"\{[^{}]*input_i[^{}]*\}", result.stderr)
    if not match:
        raise RuntimeError("ffmpeg loudnorm did not return measurements")
    data = json.loads(match.group(0))
    measured = (
        f":measured_I={data['input_i']}:measured_TP={data['input_tp']}"
        f":measured_LRA={data['input_lra']}:measured_thresh={data['input_thresh']}"
        f":offset={data['target_offset']}:linear=true"
    )
    return base + measured


def render(config: dict, config_path: Path, force: bool = False, ass_only: bool = False) -> Path:
    source = resolve_path(config_path, config["source"])
    audio = resolve_path(config_path, config["audio"])
    logo = resolve_path(config_path, config["logo"])
    fonts = resolve_path(config_path, config["fonts"])
    output = resolve_path(config_path, config["out"])
    assembly_audio = (
        resolve_path(config_path, config["assembly_audio"])
        if config.get("assembly_audio") else None
    )
    if output.exists() and not force and not ass_only:
        raise FileExistsError(f"{output} exists; use --force to overwrite")
    if assembly_audio and assembly_audio.exists() and not force and not ass_only:
        raise FileExistsError(f"{assembly_audio} exists; use --force to overwrite")
    for label, path in (("source", source), ("audio", audio), ("logo", logo), ("fonts", fonts)):
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")

    fps_expression = str(config.get("fps") or probe_fps(source))
    fps = float(Fraction(fps_expression))
    timeline = Timeline(config["pieces"], fps)
    if not 30 <= timeline.duration <= 60:
        print(f"warning: combined teaser should be 30-60 s (is {timeline.duration:.2f} s)", file=sys.stderr)
    validate_audio_clock(source, audio, fps)

    with tempfile.TemporaryDirectory(prefix="investing-bros-teaser-") as temp:
        work_dir = Path(temp)
        overlay, blur_mask = make_overlays(logo, work_dir)
        ass = work_dir / "teaser.ass"
        ass.write_text(build_ass(config, timeline), encoding="utf-8")
        if ass_only:
            destination = output.with_suffix(".ass")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(ass.read_text(encoding="utf-8"), encoding="utf-8")
            return destination

        runtime_config = dict(config, fonts=str(fonts))
        args = ["ffmpeg", "-v", "error", "-y"]
        for segment in timeline.segments:
            args += [
                "-ss", f"{segment['source_start']:.4f}",
                "-t", f"{segment['duration'] + 0.5:.4f}",
                "-i", str(source),
            ]
        for segment in timeline.segments:
            args += [
                "-ss", f"{segment['source_start']:.4f}",
                "-t", f"{segment['duration']:.4f}",
                "-i", str(audio),
            ]
        args += ["-loop", "1", "-i", str(overlay), "-loop", "1", "-i", str(blur_mask)]
        raw = work_dir / "raw.mov"
        args += [
            "-filter_complex", build_filter(runtime_config, timeline, fps_expression, ass),
            "-map", "[vout]", "-map", "[ac]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-r", fps_expression,
            "-c:a", "pcm_s16le", "-ar", "48000", str(raw),
        ]
        subprocess.run(args, check=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        normalized_audio = assembly_audio or (work_dir / "assembly-audio.wav")
        normalized_audio.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(raw), "-map", "0:a",
            "-af", measured_loudnorm(raw) + ",aresample=48000",
            "-c:a", "pcm_s16le", str(normalized_audio),
        ], check=True)
        audio_duration = probe_duration(normalized_audio)
        if abs(audio_duration - timeline.duration) > max(0.05, 1 / fps):
            raise ValueError(
                f"assembly PCM is {audio_duration:.3f}s for a {timeline.duration:.3f}s teaser"
            )
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(normalized_audio),
            "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(output),
        ], check=True)
    sidecar = f", PCM {assembly_audio}" if assembly_audio else ""
    print(
        f"{output}: {timeline.duration:.2f} s, {len(timeline.segments)} moments, "
        f"{fps_expression} fps{sidecar}"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--ass-only", action="store_true", help="write OUT with an .ass suffix without rendering")
    parser.add_argument("--force", action="store_true", help="overwrite an existing output")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("layout", "fullframe") != "fullframe":
        parser.error("this renderer supports only layout=fullframe")
    try:
        render(config, config_path, args.force, args.ass_only)
    except (FileNotFoundError, FileExistsError, ValueError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
