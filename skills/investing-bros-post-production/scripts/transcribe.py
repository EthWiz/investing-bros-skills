#!/usr/bin/env python3
"""Transcribe the raw episode master in Hebrew.

Usage:
    python3 transcribe.py RAW_AUDIO OUT_DIR [--model ivrit-ai/whisper-large-v3-turbo-ct2]
                          [--no-level] [--engine faster-whisper|sherpa]

Writes to OUT_DIR:
    audio-16k-mono.wav   input converted for whisper
    segments.json        [{"start": s, "end": s, "text": "..."}, ...]  (raw timeline)
    transcript.txt       one segment per line, "[M:SS] text"
    transcript.srt       subtitles

The 16 kHz copy is leveled first (dynaudnorm) unless --no-level: when one
host is much quieter (episode 6: 16 dB), whisper's VAD skips whole stretches
of him and the transcript silently loses them. Leveling only affects this
analysis copy, not the episode audio.

Engines:
  faster-whisper (default)  needs `pip install faster-whisper` and the model
                            from Hugging Face.
  sherpa                    fallback when Hugging Face is unreachable (some
                            sandboxes block it): `pip install sherpa-onnx
                            soundfile`; Whisper large-v3-turbo (int8 ONNX) and
                            the Silero VAD come from the k2-fsa/sherpa-onnx
                            GitHub releases. Weaker on Hebrew than ivrit-ai —
                            proofread names, numbers and English terms.

Needs ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"
# float32 on purpose: the "auto" compute type picks int8 on CPU, which garbles Hebrew
# (seen on episodes 5-8, Oct 2026). Slower, but the transcript is usable.
COMPUTE_TYPE = "float32"
LEVEL_FILTER = "highpass=f=70,dynaudnorm=f=200:g=11:p=0.9:m=40:s=0"
PTS_FILTER = "aresample=async=1:min_hard_comp=0.01:first_pts=0"
SHERPA_RELEASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
SHERPA_DIR = Path(os.environ.get("SHERPA_MODELS", Path.home() / ".cache" / "sherpa-onnx"))


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


def sherpa_models() -> dict:
    """Download (once) Whisper turbo int8 + Silero VAD from the sherpa-onnx releases."""
    import tarfile
    SHERPA_DIR.mkdir(parents=True, exist_ok=True)
    m = SHERPA_DIR / "sherpa-onnx-whisper-turbo"
    if not (m / "turbo-encoder.int8.onnx").exists():
        tar = SHERPA_DIR / "turbo.tar.bz2"
        print("downloading whisper turbo (~560 MB) from GitHub releases...", file=sys.stderr)
        urllib.request.urlretrieve(SHERPA_RELEASE + "sherpa-onnx-whisper-turbo.tar.bz2", tar)
        with tarfile.open(tar) as t:
            t.extractall(SHERPA_DIR)
        tar.unlink()
    vad = SHERPA_DIR / "silero_vad.onnx"
    if not vad.exists():
        urllib.request.urlretrieve(SHERPA_RELEASE + "silero_vad.onnx", vad)
    return {"encoder": str(m / "turbo-encoder.int8.onnx"), "decoder": str(m / "turbo-decoder.int8.onnx"),
            "tokens": str(m / "turbo-tokens.txt"), "vad": str(vad)}


def merge_speech(spans, max_gap=0.6, max_len=12.0):
    """Join VAD speech spans into chunks whisper can take (< 30 s), keeping pauses as boundaries."""
    out = []
    for a, b in spans:
        if out and a - out[-1][1] < max_gap and b - out[-1][0] < max_len:
            out[-1][1] = b
        else:
            out.append([a, b])
    return out


def transcribe_sherpa(wav: Path, threads: int):
    import sherpa_onnx
    import soundfile as sf
    paths = sherpa_models()
    audio, sr = sf.read(str(wav), dtype="float32")
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = paths["vad"]
    cfg.silero_vad.min_silence_duration = 0.3
    cfg.silero_vad.min_speech_duration = 0.2
    cfg.silero_vad.max_speech_duration = 14
    cfg.silero_vad.threshold = 0.45
    cfg.sample_rate = sr
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=120)
    spans = []

    def drain():
        while not vad.empty():
            s = vad.front
            spans.append((s.start / sr, (s.start + len(s.samples)) / sr))
            vad.pop()
    for i in range(0, len(audio), 512):
        vad.accept_waveform(audio[i:i + 512])
        drain()
    vad.flush()
    drain()
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=paths["encoder"], decoder=paths["decoder"], tokens=paths["tokens"],
        language="he", task="transcribe", num_threads=threads, tail_paddings=800)
    segments, chunks = [], merge_speech(spans)
    for k, (a, b) in enumerate(chunks):
        st = rec.create_stream()
        st.accept_waveform(sr, audio[max(0, int((a - 0.1) * sr)):int((b + 0.15) * sr)])
        rec.decode_stream(st)
        text = st.result.text.strip()
        if text:
            segments.append({"start": round(a, 2), "end": round(b, 2), "text": text})
        print(f"\r{k + 1}/{len(chunks)}", end="", file=sys.stderr)
    print(file=sys.stderr)
    return segments


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("out_dir")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--no-level", action="store_true", help="don't level the analysis copy")
    ap.add_argument("--engine", choices=("faster-whisper", "sherpa"), default="faster-whisper")
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--compute-type", default=COMPUTE_TYPE,
                    help="faster-whisper compute type (default float32; int8/auto garble Hebrew)")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "audio-16k-mono.wav"
    analysis_filter = PTS_FILTER if args.no_level else f"{PTS_FILTER},{LEVEL_FILTER}"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                    "-i", args.audio, "-vn", "-af", analysis_filter,
                    "-ac", "1", "-ar", "16000", str(wav)], check=True)

    if args.engine == "sherpa":
        segments = transcribe_sherpa(wav, args.threads)
        write_outputs(segments, out)
        print(f"{len(segments)} segments -> {out}")
        return 0

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("error: faster-whisper is not installed (pip install faster-whisper); "
              "or use --engine sherpa", file=sys.stderr)
        return 1

    model = WhisperModel(args.model, device="auto", compute_type=args.compute_type, cpu_threads=args.threads)
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
