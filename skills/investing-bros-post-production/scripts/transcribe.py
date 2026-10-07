#!/usr/bin/env python3
"""Transcribe the raw episode master in Hebrew.

Usage:
    python3 transcribe.py RAW_AUDIO OUT_DIR [--model ivrit-ai/whisper-large-v3-turbo-ct2]

Writes to OUT_DIR:
    audio-16k-mono.wav   input converted for whisper
    segments.json        [{"start": s, "end": s, "text": "..."}, ...]  (raw timeline)
    transcript.txt       one segment per line, "[M:SS] text"
    transcript.srt       subtitles

Needs ffmpeg and `pip install faster-whisper`.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"


def fmt_srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_clock(t: float) -> str:
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def to_srt(segments) -> str:
    blocks = []
    for i, seg in enumerate(segments, 1):
        blocks.append(f"{i}\n{fmt_srt_time(seg['start'])} --> {fmt_srt_time(seg['end'])}\n{seg['text']}\n")
    return "\n".join(blocks)


def to_txt(segments) -> str:
    return "".join(f"[{fmt_clock(s['start'])}] {s['text']}\n" for s in segments)


def write_outputs(segments, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "transcript.txt").write_text(to_txt(segments), encoding="utf-8")
    (out_dir / "transcript.srt").write_text(to_srt(segments), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("out_dir")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("error: faster-whisper is not installed (pip install faster-whisper)", file=sys.stderr)
        return 1

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "audio-16k-mono.wav"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                    "-i", args.audio, "-ac", "1", "-ar", "16000", str(wav)], check=True)

    model = WhisperModel(args.model, device="auto", compute_type="auto")
    seg_iter, info = model.transcribe(str(wav), language="he", vad_filter=True)
    segments = []
    for seg in seg_iter:
        segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        print(f"\r{fmt_clock(seg.end)} / {fmt_clock(info.duration)}", end="", file=sys.stderr)
    print(file=sys.stderr)

    write_outputs(segments, out)
    print(f"{len(segments)} segments -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
