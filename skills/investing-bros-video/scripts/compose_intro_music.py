#!/usr/bin/env python3
"""Render the show's original 8 s intro music from a General MIDI SoundFont.

The score is written for the intro timeline in `build_intro.py` (120 BPM, one
beat = 0.5 s): a soft piano pulse and strings under the hosts (0-3 s), a riser
and timpani roll into the wordmark, hits on 3.0 s (`אחים`) and 3.5 s
(`להשקעות`), a short piano tag under the credit lines, then a ring-out.
Paper swishes mark the strip and each host entering.

Usage:
    python3 compose_intro_music.py GeneralUser-GS.sf2 intro-music.wav

SoundFont: GeneralUser GS (https://schristiancollins.com/generaluser.php),
licensed for private or commercial music without restriction. The output is
48 kHz stereo PCM, mastered to -16 LUFS and true peak <= -1.5 dBTP (the episode
level; `assemble_episode.sh` re-normalizes the intro anyway).

Needs: tinysoundfont, numpy, pedalboard (pip), ffmpeg.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

SR = 48000
LENGTH = 8.0          # seconds; the intro is exactly 8 s
BEAT = 0.5            # 120 BPM
LOGO_1 = 3.0          # אחים lands
LOGO_2 = 3.5          # להשקעות lands

# GM programs (0-based)
PIANO, GLOCK, CELLO, CONTRABASS, STRINGS, TIMPANI = 0, 9, 42, 43, 48, 47

# MIDI note helpers
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6,
        "Gb": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def n(name: str) -> int:
    """'A4' -> 69."""
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTE[pitch]


def chord(names: str) -> list[int]:
    return [n(x) for x in names.split()]


# --- score: (start s, duration s, midi keys, velocity) per stem -------------

def score() -> dict[str, dict]:
    stems: dict[str, dict] = {}

    # Strings: Dm -> Bb (swell) -> F, C/E, F (ring out).
    strings = [
        (0.0, 2.0, chord("D3 A3 D4 F4"), 70),
        (2.0, 1.0, chord("Bb2 F3 Bb3 D4"), 85),
        (LOGO_1, 0.5, chord("F3 C4 F4 A4"), 105),
        (LOGO_2, 0.5, chord("E3 C4 G4 C5"), 100),
        (4.0, 3.7, chord("F3 C4 F4 A4 G4"), 92),
    ]
    # Expression (CC11) ramps: quiet start, swell into the logo, fade out.
    expr = [(0.0, 84), (1.0, 90), (2.0, 98), (2.5, 110), (2.9, 124),
            (3.0, 127), (5.0, 118), (6.0, 95), (7.0, 60), (7.6, 30)]
    stems["strings"] = dict(program=STRINGS, events=strings, expr=expr,
                            gain=0.55, reverb=0.35)

    bass = [
        (0.0, 2.0, [n("D2")], 75), (2.0, 1.0, [n("Bb1")], 85),
        (LOGO_1, 0.5, [n("F1")], 110), (LOGO_2, 0.5, [n("C2")], 105),
        (4.0, 3.6, [n("F1")], 95),
    ]
    stems["bass"] = dict(program=CONTRABASS, events=bass, expr=expr,
                         gain=0.5, reverb=0.2)

    # Piano: staccato eighth-note pulse under the hosts, then hits and a tag.
    piano = []
    pulse_dm = ["D4", "A4", "F4", "A4"]
    pulse_bb = ["D4", "Bb4", "F4", "Bb4"]
    for i in range(6):                       # 0.0 - 3.0 s, eighths
        for j in range(2):
            t = i * BEAT + j * BEAT / 2
            pat = pulse_dm if t < 2.0 else pulse_bb
            key = n(pat[(i * 2 + j) % 4])
            vel = int(42 + 30 * t / 3.0)
            piano.append((t, 0.2, [key], vel))
    # Melody over the pulse (sparse, rising).
    piano += [
        (0.5, 0.45, [n("A5")], 62), (1.0, 0.45, [n("D6")], 66),
        (1.5, 0.45, [n("C6")], 64), (2.0, 0.95, [n("Bb5")], 70),
    ]
    # Hits and the tag.
    piano += [
        (LOGO_1, 0.5, chord("F2 F3 A3 C4 F4 A4 C5 F5"), 112),
        (LOGO_2, 0.5, chord("C2 E3 G3 C4 E4 G4 C5 E5"), 106),
        (4.0, 0.45, chord("F2 F3 C4 A4 F5"), 95),
        (4.5, 0.25, [n("G5")], 80),
        (4.75, 3.0, chord("A3 C4 F4 A5"), 84),
    ]
    stems["piano"] = dict(program=PIANO, events=piano, gain=0.7, reverb=0.3)

    # Timpani: roll into the logo, then three hits.
    timp = []
    t = 2.25
    while t < LOGO_1 - 0.01:
        timp.append((t, 0.1, [n("F2")], int(35 + 70 * (t - 2.25) / 0.75)))
        t += 0.0625
    timp += [(LOGO_1, 1.0, [n("F2")], 118), (LOGO_2, 1.0, [n("C2")], 108),
             (4.0, 2.0, [n("F2")], 92)]
    stems["timpani"] = dict(program=TIMPANI, events=timp, gain=0.32, reverb=0.25)

    glock = [(4.0, 1.0, [n("F6")], 52), (4.5, 1.0, [n("C7")], 46),
             (4.75, 2.0, [n("A6")], 50)]
    stems["glock"] = dict(program=GLOCK, events=glock, gain=0.25, reverb=0.45)
    return stems


# --- rendering ---------------------------------------------------------------

def render_stem(sf2: str, program: int, events, expr=None) -> np.ndarray:
    import tinysoundfont

    synth = tinysoundfont.Synth(samplerate=SR)
    sfid = synth.sfload(sf2)
    synth.program_select(0, sfid, 0, program)
    timeline = []                             # (time, order, action, args)
    for start, dur, keys, vel in events:
        for k in keys:
            timeline.append((start, 1, "on", (k, vel)))
            timeline.append((start + dur, 0, "off", (k,)))
    for t, val in expr or []:
        timeline.append((t, 0, "cc", (11, val)))
    timeline.sort(key=lambda e: (e[0], e[1]))

    total = int(LENGTH * SR)
    out = np.zeros((total, 2), np.float32)
    pos = 0
    for t, _, action, args in timeline + [(LENGTH, 9, "end", ())]:
        target = min(total, int(round(t * SR)))
        if target > pos:
            buf = np.frombuffer(synth.generate(target - pos), np.float32)
            out[pos:target] = buf.reshape(-1, 2)
            pos = target
        if action == "on":
            synth.noteon(0, *args)
        elif action == "off":
            synth.noteoff(0, *args)
        elif action == "cc":
            synth.control_change(0, *args)
    return out


def sfx_paper(t0: float, length: float = 0.35, seed: int = 0) -> np.ndarray:
    """A soft paper swish: band-passed noise with a quick swell and decay."""
    rng = np.random.default_rng(seed)
    total = int(LENGTH * SR)
    out = np.zeros((total, 2), np.float32)
    k = int(length * SR)
    noise = rng.standard_normal(k).astype(np.float32)
    # crude band-pass via FFT (1.2 - 6 kHz)
    spec = np.fft.rfft(noise)
    f = np.fft.rfftfreq(k, 1 / SR)
    spec *= ((f > 1200) & (f < 6000)) * (1 / (1 + ((f - 3000) / 2500) ** 2))
    band = np.fft.irfft(spec, k).astype(np.float32)
    x = np.linspace(0, 1, k)
    env = (x ** 0.6) * np.exp(-6 * x) * 3.2
    band = band / (np.abs(band).max() + 1e-9) * env
    i0 = int(t0 * SR)
    i1 = min(total, i0 + k)
    out[i0:i1, 0] = band[: i1 - i0] * 0.9
    out[i0:i1, 1] = band[: i1 - i0]
    return out


def sfx_boom(t0: float) -> np.ndarray:
    """Sub boom under the logo hit: sine with a pitch drop."""
    total = int(LENGTH * SR)
    out = np.zeros((total, 2), np.float32)
    k = int(1.4 * SR)
    t = np.arange(k) / SR
    freq = 42 + 48 * np.exp(-t * 18)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sig = np.sin(phase) * np.exp(-t * 3.2) * np.minimum(1, t * 400)
    i0 = int(t0 * SR)
    i1 = min(total, i0 + k)
    out[i0:i1, :] = sig[: i1 - i0, None]
    return out.astype(np.float32)


def sfx_riser(t0: float, t1: float, seed: int = 1) -> np.ndarray:
    """Airy noise swell that rises in brightness into the logo."""
    rng = np.random.default_rng(seed)
    total = int(LENGTH * SR)
    out = np.zeros((total, 2), np.float32)
    k = int((t1 - t0) * SR)
    noise = rng.standard_normal((k, 2)).astype(np.float32)
    # moving lowpass that opens up: mix of smoothed and raw noise
    from scipy.signal import lfilter  # type: ignore
    x = np.linspace(0, 1, k)
    # one-pole high-pass keeps it airy (no rumble); brightness rises over time
    air = lfilter([1, -1], [1, -0.97], noise, axis=0)
    soft = lfilter([0.15], [1, -0.85], air, axis=0)
    sig = soft * (1 - x[:, None]) + air * 0.6 * x[:, None] ** 2
    sig *= (x ** 2.2)[:, None]
    sig /= np.abs(sig).max() + 1e-9
    i0 = int(t0 * SR)
    out[i0:i0 + k] = sig * 0.5
    return out


def mix(sf2: str) -> np.ndarray:
    from pedalboard import Pedalboard, Reverb, HighpassFilter, LowShelfFilter

    total = int(LENGTH * SR)
    bus = np.zeros((total, 2), np.float32)
    for name, st in score().items():
        dry = render_stem(sf2, st["program"], st["events"], st.get("expr"))
        board = Pedalboard([Reverb(room_size=0.72, damping=0.45,
                                   wet_level=st["reverb"], dry_level=1.0,
                                   width=1.0)])
        wet = board(dry.T.copy(), SR).T
        bus += wet[:total] * st["gain"]
    sfx = (sfx_paper(0.0, 0.5, 1) * 0.10 + sfx_paper(0.48, 0.35, 2) * 0.07
           + sfx_paper(0.98, 0.35, 3) * 0.07
           + sfx_paper(LOGO_1 - 0.02, 0.22, 4) * 0.10
           + sfx_paper(LOGO_2 - 0.02, 0.22, 5) * 0.08
           + sfx_boom(LOGO_1) * 0.45 + sfx_riser(1.6, LOGO_1) * 0.10)
    bus += sfx
    bus = Pedalboard([HighpassFilter(28), LowShelfFilter(120, 1.5)])(bus.T.copy(), SR).T
    # gentle fade in / out
    t = np.arange(total) / SR
    bus *= np.clip(t / 0.03, 0, 1)[:, None]
    bus *= np.clip((LENGTH - t) / 0.6, 0, 1)[:, None]
    return bus


def write_wav(path: str, x: np.ndarray) -> None:
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("soundfont")
    ap.add_argument("output", help="output .wav (48 kHz stereo)")
    ap.add_argument("--lufs", type=float, default=-16.0)
    a = ap.parse_args(argv)
    bus = mix(a.soundfont)
    bus /= np.abs(bus).max() + 1e-9
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "raw.wav")
        write_wav(raw, bus * 0.8)
        # Two-pass-equivalent for a short clip: loudnorm in linear mode is
        # unreliable under 3 s of gating, so measure then apply a static gain
        # and a true-peak limiter.
        meas = subprocess.run(
            ["ffmpeg", "-nostats", "-i", raw, "-af", "ebur128=peak=true",
             "-f", "null", "-"], capture_output=True, text=True).stderr
        lufs = float(meas.rsplit("I:", 1)[1].split("LUFS")[0])
        gain = a.lufs - lufs
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
             f"volume={gain}dB,alimiter=limit=0.79:attack=1:release=40:level=false",
             "-ar", str(SR), "-c:a", "pcm_s16le", a.output], check=True)
    print(f"wrote {a.output} ({LENGTH:.1f} s); gain {gain:+.1f} dB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
