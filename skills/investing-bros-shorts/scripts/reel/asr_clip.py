import json, time
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download
p = snapshot_download("ivrit-ai/whisper-large-v3-turbo-ct2", cache_dir=__import__("os").environ.get("MODELS_DIR", "models"))
t = time.time()
m = WhisperModel(p, device="cpu", compute_type="float32", cpu_threads=8)
segs, info = m.transcribe(__import__("numpy").frombuffer(__import__("wave").open("src16k.wav").readframes(10**9),__import__("numpy").int16).astype("float32")/32768.0, language="he", beam_size=5, word_timestamps=True,
                          condition_on_previous_text=False)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                "words": [{"start": w.start, "end": w.end, "word": w.word.strip(), "p": w.probability} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
json.dump(out, open("asr_ivrit_turbo.json", "w"), ensure_ascii=False, indent=1)
print("DONE", time.time() - t)
