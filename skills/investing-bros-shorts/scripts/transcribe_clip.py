#!/usr/bin/env python3
"""Word-level timings for the picked clip windows only (never the whole episode).

Usage:
    python3 transcribe_clip.py AUDIO.wav --offset 2065 --from 41 --to 90 --model ~/.cache/whisper/small.pt -o words.json

AUDIO: mono 16 kHz WAV of a window of the episode; --offset: its start on the source
timeline; --from/--to: the part to transcribe, in seconds of the WAV. Writes
[{"w","s","e"}] with source-timeline times. Uses openai-whisper (a local .pt model);
falls back to faster-whisper if openai-whisper isn't installed. Text from whisper is
only for timing: captions come from the proofread transcript (align_words.py).
Install notes for Amitai's Mac: investing-bros-show -> references/environment.md.
"""
import argparse
import json
import os


def transcribe(wav, offset, a, b, model):
    try:
        import torch  # noqa: F401
        import whisper
        m = whisper.load_model(os.path.expanduser(model), device="cpu")
        audio = whisper.load_audio(wav)[int(a * 16000):int(b * 16000)]
        r = m.transcribe(audio, language="he", word_timestamps=True, fp16=False, condition_on_previous_text=False)
        return [{"w": w["word"].strip(), "s": round(w["start"] + a + offset, 2), "e": round(w["end"] + a + offset, 2)}
                for s in r["segments"] for w in s["words"]]
    except ImportError:
        from faster_whisper import WhisperModel
        m = WhisperModel(model, device="cpu", compute_type="int8")
        segs, _ = m.transcribe(wav, language="he", word_timestamps=True, clip_timestamps=[a, b])
        return [{"w": w.word.strip(), "s": round(w.start + offset, 2), "e": round(w.end + offset, 2)} for s in segs for w in s.words]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio"); ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--from", dest="a", type=float, required=True); ap.add_argument("--to", dest="b", type=float, required=True)
    ap.add_argument("--model", default="~/.cache/whisper/small.pt"); ap.add_argument("-o", "--out", default="words.json")
    x = ap.parse_args()
    words = transcribe(x.audio, x.offset, x.a, x.b, x.model)
    json.dump(words, open(x.out, "w"), ensure_ascii=False)
    print(f"{x.out}: {len(words)} words")


if __name__ == "__main__":
    main()
