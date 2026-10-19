#!/usr/bin/env python3
"""Find an episode-body offset in video and shift a description's chapters.

The match compares the published/edited audio with the beginning of the video,
whose cold open and intro make its chapters later. Audio decoding preserves PTS
gaps so the measured offset stays on the picture clock.

Usage:
  find_offset_and_shift.py VIDEO AUDIO DESCRIPTION OUT [--offset SECONDS] [--force]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

PTS_FILTER = "aresample=async=1:min_hard_comp=0.01:first_pts=0"
CHAPTER_RE = re.compile(r"^(?:(\d+):)?(\d{2}):(\d{2}) (.+)$")


def decode_pcm(path: Path, start: float, duration: float, sample_rate: int = 8000) -> np.ndarray:
    command = [
        "ffmpeg", "-v", "error", "-ss", str(start), "-t", str(duration), "-i", str(path),
        "-vn", "-af", PTS_FILTER, "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-",
    ]
    raw = subprocess.run(command, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32)


def energy_envelope(samples: np.ndarray, sample_rate: int = 8000, hop: int = 80) -> np.ndarray:
    count = len(samples) // hop
    if count == 0:
        raise ValueError("not enough decoded audio to build an envelope")
    energy = np.sqrt((samples[:count * hop].reshape(count, hop) ** 2).mean(axis=1) + 1e-6)
    logged = np.log(energy)
    return (logged - logged.mean()) / (logged.std() + 1e-9)


def normalized_correlation(candidate: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Pearson-like correlation for every candidate window."""
    if len(candidate) < len(reference):
        raise ValueError("candidate is shorter than the reference")
    count = len(reference)
    reference = reference - reference.mean()
    dot = np.correlate(candidate, reference, "valid")
    ones = np.ones(count, dtype=np.float32)
    window_sum = np.convolve(candidate, ones, "valid")
    window_squares = np.convolve(candidate * candidate, ones, "valid")
    window_variance = np.maximum(window_squares - (window_sum * window_sum / count), 0)
    denominator = np.sqrt(window_variance * np.sum(reference * reference))
    return np.divide(dot, denominator, out=np.zeros_like(dot), where=denominator > 1e-9)


def find_offset(video: Path, audio: Path) -> tuple[float, float]:
    audio_probe_start = 30.0
    reference = energy_envelope(decode_pcm(audio, audio_probe_start, 60))
    candidate = energy_envelope(decode_pcm(video, 0, 240))
    correlation = normalized_correlation(candidate, reference)
    index = int(np.argmax(correlation))
    score = float(correlation[index])
    return index * 0.01 - audio_probe_start, score


def format_timestamp(seconds: float) -> str:
    value = int(round(seconds))
    if value < 0:
        raise ValueError(f"shifted chapter is before zero: {seconds:.2f}s")
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


def shift_description(text: str, offset: float) -> str:
    lines = text.splitlines()
    shifted = []
    inserted_opening = False
    chapter_count = 0
    for line in lines:
        match = CHAPTER_RE.match(line)
        if not match:
            shifted.append(line)
            continue
        if not inserted_opening:
            shifted.append("00:00 טעימה מהפרק")
            inserted_opening = True
        source_time = int(match[1] or 0) * 3600 + int(match[2]) * 60 + int(match[3])
        shifted.append(f"{format_timestamp(source_time + offset)} {match[4]}")
        chapter_count += 1
    if chapter_count == 0:
        raise ValueError("description contains no time-first chapter lines")
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(shifted) + suffix


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return float(result)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("audio", type=Path)
    parser.add_argument("description", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--offset", type=float, help="use a verified offset instead of matching")
    parser.add_argument("--min-score", type=float, default=0.5)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    for path in (args.video, args.audio, args.description):
        if not path.is_file():
            parser.error(f"not found: {path}")
    if args.out.exists() and not args.force:
        parser.error(f"{args.out} exists; use --force to replace it")

    if args.offset is None:
        offset, score = find_offset(args.video, args.audio)
        if score < args.min_score:
            print(
                f"error: weak audio match ({score:.2f} < {args.min_score:.2f}); "
                "the video may use a different edit. Re-time it from its own transcript.",
                file=sys.stderr,
            )
            return 1
    else:
        offset, score = args.offset, None

    output = shift_description(args.description.read_text(encoding="utf-8"), offset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8")
    video_duration = probe_duration(args.video)
    audio_duration = probe_duration(args.audio)
    score_text = "manual" if score is None else f"{score:.2f}"
    print(
        f"offset {offset:.2f}s, match {score_text}, "
        f"video-audio length delta {video_duration - audio_duration:.2f}s -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
