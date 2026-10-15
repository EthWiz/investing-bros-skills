import numpy as np, subprocess, json, wave
import plan
SR = 48000
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", plan.SRC, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
tm, cdur = plan.timemap(); XF = plan.XF; nx = int(XF * SR)
out = np.zeros((0, 2), np.float32)
for i, (a, b, o) in enumerate(tm):
    s = x[int(round(a * SR)):int(round(b * SR))].copy()
    if i == 0: out = s; continue
    fi = np.sin(np.linspace(0, np.pi / 2, nx))[:, None]; fo = np.cos(np.linspace(0, np.pi / 2, nx))[:, None]
    ov = out[-nx:] * fo + s[:nx] * fi
    out = np.concatenate([out[:-nx], ov, s[nx:]])
end = x[int(round(plan.CONTENT_END * SR)):]
out = np.concatenate([out, end])
print("content", round(cdur, 3), "audio total", round(len(out) / SR, 3))

# --- synthesized SFX ---
rng = np.random.default_rng(3)
def whoosh(d=0.45):
    n = int(d * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # sweeping band-pass via FFT mask per block (simple): lowpass ramp using cumulative filter
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2 * np.exp(-2.0 * t / d)
    sig = np.zeros(n); y = 0.0
    for i in range(n):
        alpha = 0.02 + 0.25 * (t[i] / d)          # cutoff rises: "air" sweep
        y += alpha * (noise[i] - y); sig[i] = y
    sig = sig - np.convolve(sig, np.ones(32) / 32, mode="same")   # remove rumble
    sig *= env; sig /= np.abs(sig).max() + 1e-9
    return sig
def pop(d=0.07):
    n = int(d * SR); t = np.arange(n) / SR
    f = 900 * np.exp(-t * 30) + 380
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 60) * (1 - np.exp(-t * 2000))
    return s / np.abs(s).max()
def add(sig, at, gain_db):
    i = int(at * SR); g = 10 ** (gain_db / 20)
    j = min(len(out), i + len(sig))
    if i < 0 or i >= len(out): return
    out[i:j] += (sig[:j - i] * g)[:, None]
W_ = whoosh(); P_ = pop()
mgs = json.load(open("mg_schedule.json"))
for kind, s, d in mgs:
    add(W_, s - 0.12, -21)
chunks = json.load(open("captions_chunks.json"))
for c in chunks:
    add(P_, c["s"] - 0.01, -33)
out = out.astype(np.float32)
with wave.open("mix_pre.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
print("peak dBFS", round(20 * np.log10(np.abs(out).max()), 2))
