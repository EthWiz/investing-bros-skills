# YouTube Shorts Guide: "אחים להשקעות"

This is a portable playbook that any AI agent (or person) can follow to turn a long Hebrew investing-podcast episode into
**5 high-quality vertical Shorts** with as few tokens and renders as possible. It works with any agent and depends only
on a shell, ffmpeg and Python.

> **Golden rules:** read the transcript instead of watching the video. Cut only the clips you need. Run one command per
> Short. Test on 5–10 s before rendering. Do one QA pass. **Nothing is published without Amitai's approval.**

> **Not included in this repo:** the Heebo font, the YuNet `yunet.onnx` model, and the logo end-card video. Pass them as
> `HEEBO_FONT`, `YUNET` and `ENDCARD`. The scripts were syntax-checked only; they have not been run end to end.
> House accent is gold `#F5B71F`. A cold-open music bed is the recipe in `investing-bros-teaser`, not section 4.

---

## 0. Requirements

| Need | Notes |
|---|---|
| ffmpeg ≥ 6, bash | `ffmpeg`, `ffprobe`, `split`, `sha256sum` |
| Python 3 + `numpy`, `opencv-python` (≥4.8, for `FaceDetectorYN`) | |
| **Pillow built with raqm** | Check it with `python3 -c 'from PIL import features; print(features.check("raqm"))'`. It **must** print `True`. |
| `faster-whisper`, `huggingface_hub` | Word timestamps from `ivrit-ai/whisper-large-v3-turbo-ct2` (Hebrew-tuned, CPU is fine) |
| `fonts/Heebo-Variable.ttf` | Google Fonts Heebo, variable weight. Black = wght 900. **Not in the repo.** Override with `HEEBO_FONT=` |
| `models/yunet.onnx` | OpenCV Zoo `face_detection_yunet_2023mar.onnx`, only for two-shot sources. **Not in the repo.** Override with `YUNET=` |
| Logo end-card mp4 | 2–4 s brand card. **Not in the repo.** Pass it as `ENDCARD=` |

This file lives in `investing-bros-shorts` → `references/SHORTS_GUIDE.md`. Scripts live in that skill's `scripts/` (run commands from there). Nothing is machine-specific:
```
references/SHORTS_GUIDE.md
scripts/  shorts.sh lib.sh make_title.py patch_reel.py facetrack_split.py export.sh shorts.example.cfg
          reel/  run.sh plan.py render.py captions.py mg.py audio.py asr_clip.py
fonts/ models/            # you provide these (not in the repo)
```
Hand-editing one short's shots, name tags and reaction cuts still goes through `build_fullbleed.py` in this skill. This playbook is the batch path.

---

## 1. Inputs: the transcript first, never the whole video

1. Get the episode **.srt** (from Riverside/YouTube auto-captions/whisper). Convert it to plain text with timestamps if that
   helps. A 1-hour episode is about 10–15k tokens of text, while watching it as frames costs orders of magnitude more.
2. Pick moments **only from the srt** (section 2). Open video frames only to check framing (a few stills,
   e.g. `ffmpeg -ss 1023 -i src.mp4 -frames:v 1 f.png`).
3. The source is large (1–2 GB, about 1 h). **Never transcode it whole.** `shorts.sh` input-seeks (`-ss … -t …` before `-i`)
   and encodes only the 30–90 s it needs. If you must move clips between machines, cut them with stream copy first:
   `ffmpeg -ss 1020 -t 60 -i src.mp4 -c copy clip.mp4` (this snaps to keyframes, so leave about 2 s of slack on both sides).
4. Note the source layout: a **single framing**, or a **two-shot / split-screen** (two speakers side by side). That decides the crop
   (section 3c).

---

## 2. Pick 5 moments (+1 backup)

Criteria for every candidate:
- **Hook in the first 2 seconds.** The opening words must create curiosity on their own: a surprising number, a bold claim,
  or a question. Never open on "אז…", "כן, ו…" or a reply to something we didn't hear.
- **Standalone.** It must make sense with zero context. No "כמו שאמרתי קודם" and no unresolved "הוא" or "זה".
- **About 30–90 s** (45–60 s is the sweet spot).
- **Ends on a complete sentence** that resolves the idea. Never cut mid-thought or on a rising intonation.
- **Variety** across the 5: different topics and different speakers.
- **One backup** pick, in case a candidate fails QA or gets rejected (in Ep7 the Ukraine clip was rejected and backup #5 replaced it).

Write `shorts_candidates.md` in this format (real Ep7 example, srt times, ASR typos fixed in quotes):

```markdown
1. 17:03–17:55 (52s) — "כל הזהב בעולם בבריכה אולימפית אחת"
   Open: "כי הטבע מגביל אותו, אין הרבה זהב בטבע. כל הזהב בעולם... ממלא בריכה אולימפית אחת."
   Close: "...אז ההיצע של הנפט יגדל בגדול פי עשר, כי אין מחסור בנפט בעולם."
2. 23:58–24:55 (57s) — "1971: היום שבו הדולר התנתק מהזהב"
   Open: "בשנת 1971, ניקסון, נשיא ארה״ב, בצורה מפורסמת מקפיא את היכולת לפדות דולרים בזהב"
   Close: "...תדאג שהדולר שלך יהיה שווה עוד כסף בעתיד. בגדול." (option: end 24:59)
4. 35:04–35:54 (50s) — "אסטרואיד שיכול להפיל את מחיר הזהב בחצי"
   Open: "דוגמה ראשונה, אומר גווין בייקר..." (caption: "לדבריו", claim unverified)
5. 32:34–33:28 (54s) — "למה סין קונה המון זהב" (replaces rejected Ukraine clip)
   Close: "...שהיא לא תדפיס את הדרך שלה החוצה." (ASR: ריידליו=ריי דאליו)
```
The Olympic-pool line in that example is an episode-7 title that is **false**: all the gold ever mined is about four pools, not one (`investing-bros-show` → Hebrew). Keep it only as a shape example. Do not put an unverified figure in a title.

Each entry has a time range, a duration, a working title, the exact **Open** and **Close** lines, and notes (ASR fixes,
alternative end points, unverified claims). Present the list to the human before rendering if you can. It's cheap to change at this stage.

---

## 3. Pipeline: one command per Short

```bash
# from this skill's scripts/ directory
cp shorts.example.cfg ep.cfg    # edit: SOURCE | START | END | TITLE (\n = newline) | OUT.mp4 [| facetrack]
ENDCARD=/path/to/endcard.mp4 LIMIT_FRAMES=200 KEEP_WORK=1 ./shorts.sh ep.cfg out/   # ~7 s test first
ENDCARD=/path/to/endcard.mp4 ./shorts.sh ep.cfg out/                                # full render
```
Config line example:
```
src/episode.mp4 | 00:17:03.0 | 00:17:55.0 | כל הזהב בעולם\nבבריכה אולימפית אחת | short1_gold_pool.mp4 | facetrack
```
Optional files next to the config: `short1_gold_pool.fix.json` (ASR word fixes, e.g. `{"עצה": "היצע", "שקבוע": "שקבור"}`)
and `short1_gold_pool.mgs.json` (motion-graphic cues, see 3f).

What happens per line (stage, then file):

**a. Cut + ASR** (`shorts.sh`, `reel/asr_clip.py`): input-seek the clip, then use ivrit-ai whisper word timestamps on a 16 kHz mono copy
(about 30 s CPU per Short).

**b. Silence cuts** (`reel/plan.py`): an energy VAD (−42 dBFS, 10 ms hops) finds gaps > 0.25 s and trims them, leaving 0.08 s of padding
and a 15 ms audio crossfade at each cut. Word edges are snapped to the detected speech. Breaths with no ASR word can be dropped
(`use_words=True`).

**c. 9:16 crop** (`shorts.sh` / `facetrack_split.py`):
- Single framing: centre crop `crop=ih*9/16:ih`, scaled to 1080×1920 @25 fps.
- **Two-shot: add `| facetrack`.** YuNet finds a face in each half, mouth-motion energy picks the active speaker
  (hysteresis, min hold 1.6 s), and x is median+gaussian smoothed and clamped inside that speaker's half. If you have speaker
  turns (Riverside), pass `--turns turns.json --offset <clip start>` for exact switches. A centre crop on a two-shot
  **splits both faces in half**. Never ship that.

**d. Zoom rhythm** (`reel/render.py`, `zoom_for`): segments alternate between **100% and 112%** at every silence cut, plus a slow
+4.5% push-in on segments > 2.5 s. This hides jump cuts and keeps the energy up without "zoom spam".

**e. Captions** (`reel/captions.py`): Hebrew **word-by-word**, chunks of ≤3 words (break on punctuation, gaps > 0.3 s and
connector words). Font **Heebo Black (900)**, white with a thick black stroke and a soft shadow. The **active word is gold `#F5B71F`** (the house accent).
Centre line y≈1490 (below the chin). There's a slight pop-in (75→100% scale, 0.16 s).
- Rendered with **PIL + raqm** (`direction="rtl", language="he"`). Each word is placed right-to-left manually.
- **Never use libass/ASS/`subtitles=`.** libass breaks RTL ordering (words reversed, and punctuation/numbers like "1971" or "2%"
  jump to the wrong side). `make_title.py` asserts raqm is present.

**f. Title box + explainers** (`make_title.py`, `reel/mg.py`):
- The title is a **navy rounded box** (`#0C1B3A`, α≈235) with white Heebo Black text and a **yellow/gold bar** under it. It sits at the top
  (y 150–380) for the whole Short and is pasted after the zoom, so it never scales. Keep it to ≤2 lines (about 30 characters).
- **Motion-graphic explainers** go only where an idea is abstract (a number, a mechanism, a comparison). Cue them with
  `OUT.mgs.json`: `[["pool", "בריכה", -1.0, 3.6]]` = card kind, anchor word, offset (s), duration (s). Add a card by writing
  a function in `mg.py` and registering it in `KINDS` (the existing Tesla cards are templates: navy gradient panel, cyan
  outline, gold accents, ease-in/out). The background is blurred and dimmed while the card shows. **Calm:** 1–2 cards per Short, ≥3 s each,
  simple icons + one number or label, no spinning or flashing.

**g. Logo end card**: `ENDCARD` is appended untouched (silent) after the content.

**h. Audio** (`reel/audio.py`, `reel/run.sh`): segment crossfades, a very soft synthesized pop per caption chunk (−33 dB)
and a whoosh under each MG card (−21 dB). Then **two-pass `loudnorm` I=−14 LUFS, TP=−1.5 dBTP, LRA 11, linear**
(the social-clip target; a cold-open music mix uses −1 dBTP and is not this script).
`shorts.sh` prints the measured I/Peak at the end. Check that it reads about −14.

Output: 1080×1920, 30 fps, H.264 CRF 16 + AAC 256k, `+faststart`.

---

## 4. Style rules

- **Professional and calm.** This is an educational investing show, not get-rich-quick content.
- **No** money-rain, cash/coin explosions, rocket/lambo emojis, flashing or neon colors, shake effects, or rapid zoom spam.
- Palette: navy (`#0C1B3A`, `#001E4E`), white, and the house accent gold `#F5B71F`. Font: Heebo only. The episode-1 Tesla cards in `reel/mg.py` still use a cyan outline; new cards stay navy / gold / white.
- **Music under a Short is optional.** A cold-open music bed is a different mix: follow `investing-bros-teaser` → Cold-open music bed (`cold_open.sh` in `investing-bros-post-production` applies it). Do not use the fades in this paragraph for a cold open. For a Short, use a bed only if the track is clean (WAV/FLAC or ≥256 kbps, no hiss), **licensed**, and has **no watermark or voice tag**.
  Listen to the whole bed, because any watermark means you reject it. Sit it about 20 dB under speech (18–24) and duck it further with
  `sidechaincompress` keyed by speech, with about a 1 s fade-in and a 1.5 s fade-out. If there's any doubt, use no music. A clean dry voice beats a bad bed.
- Speech cleanup on a Short, if needed: `highpass=80`, then `arnndn` (if a model is available) or `afftdn=nf=-25`. A cold open uses `afftdn=nr=10:nf=-30` (see `investing-bros-teaser`).
- Claims attributed to others get "לדבריו" in the caption or title. Don't present unverified numbers as fact.

---

## 5. QA: one pass, targeted fixes

Review the full Short **once**, using cheap probes:
```bash
f=out/short1.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $f          # duration 30-90s (+card), size
ffmpeg -v error -i $f -vf "fps=1/3,scale=270:-1,tile=6x4" -frames:v 1 strip.png  # one contact sheet = whole Short
ffmpeg -v error -i $f -frames:v 1 first.png; ffmpeg -v error -sseof -0.1 -i $f -frames:v 1 last.png
ffmpeg -hide_banner -i $f -af ebur128=peak=true -f null - 2>&1 | tail -12     # I ≈ -14, peak ≤ -1.5
cat $WORK/captions_chunks.json   # read caption WORDING as text (KEEP_WORK=1), cheaper than frames
```
Checklist:
- [ ] **Caption wording**: names, numbers and finance terms (ASR errors like ריידליו→ריי דאליו, עצה→היצע). Fix them in `fix.json`.
- [ ] **First frame / first 2 s**: a face is visible, the title is readable, and the hook word is on screen.
- [ ] **Last frame**: the sentence is complete before the end card, and there's no clipped word.
- [ ] The crop keeps the active speaker's face. No split faces and no empty half-frame.
- [ ] Captions don't overlap the chin or the title. RTL order is correct (check a frame that has a number).
- [ ] Loudness is −14 LUFS ±1, TP ≤ −1.5. No clipping and no audible music watermark.

Fix only what failed (edit the `fix.json`, nudge START/END, or add `--turns`), re-run **that one Short**, and re-check only the
failed items. Don't redesign after QA.

---

## 6. Metadata

Write `titles_descriptions.md`, one block per Short:

- **Title** ≤ 70 chars, Hebrew hook + an **English part** (helps search/discovery), e.g.
  `כל הזהב בעולם בבריכה אחת? | Why Gold Is Scarce #Shorts`
- **Description** (all required):
  1. A one-line hook / summary.
  2. **A comment-bait question**: `ואתם – הייתם מחזיקים זהב או ביטקוין? כתבו בתגובות 👇`
  3. **Subscribe CTA**: `הירשמו לערוץ לעוד פרקים של אחים להשקעות 🔔`
  4. **Link to the full episode**: `לפרק המלא: <YouTube URL of the full episode>`
  5. **Hashtags** (3–6): `#אחים_להשקעות #השקעות #זהב #כלכלה #Shorts`
  6. **Disclaimer**: `אין כאן המלצת השקעה. רק שיחה.`

---

## 7. Export and transfer

```bash
./export.sh out/short1.mp4 share/
```
- A share copy **< 100 MB**. If it's already small, it's just copied (no re-encode). Otherwise it goes through a 2-pass bitrate-targeted x264 + AAC 128k.
  A 60 s Short is normally 30–80 MB, so it's copied as is.
- Files > 50 MB (`PART_MB`) are also split into `NAME.mp4.partNN` + `NAME_SHA256SUMS`. To rejoin and verify:
  `cat NAME.mp4.part* > NAME.mp4 && sha256sum -c NAME_SHA256SUMS`
- Use this for any channel with copy or attachment limits (chat uploads, agent file-copy tools, email). Always verify the sha256 after transfer.

---

## 8. Token-efficiency rules

1. **Reuse the scripts.** Don't rewrite a pipeline per episode. Change the config, `fix.json` and `mgs.json` only.
2. **Text over pixels.** Use the srt for picking, `captions_chunks.json` for wording, and one tiled contact sheet instead of many frames.
3. **Test on 5–10 s** (`LIMIT_FRAMES=150..300`) before every first full render, or after any code change.
4. **Never re-render the full episode or the full source.** Cut the clip and work on it.
5. **No iteration loops.** One test, one full render, one QA pass, targeted fixes. If something fails twice, stop and report.
6. **Stream copy wherever possible.** Use `-c copy` for joins, trims at keyframes and splits. Re-encode only when the pixels change.
7. Keep logs short (`-v error`, `| tail`). Don't dump ffmpeg progress or JSON blobs into context.
8. Batch all 5 Shorts in one config, but test the first line before running the rest.

---

## 9. Pitfalls we hit (and the fixes)

| Pitfall | Symptom | Fix |
|---|---|---|
| **libass RTL ordering** | Hebrew words reversed and numbers/punctuation on the wrong side | Render captions with PIL + raqm (`captions.py`). Never `subtitles=`/ASS |
| **Centre crop on a two-shot** | Both speakers cut in half, or an empty middle | `\| facetrack` (`facetrack_split.py`) and `--turns` if available |
| **Quiet or noisy music bed** | Music inaudible or hissy, or it masks speech after loudnorm | On a Short: gate it (bitrate, noise floor, watermark), keep it about −20 dB under with sidechain ducking, or drop the music. A cold open follows `investing-bros-teaser` → Cold-open music bed |
| **Watermarked "free" music** | A voice tag mid-Short | Listen to the whole track and reject it. Use only licensed tracks |
| **Re-encoding when a join was enough** | A slow, lossy, huge job | Join same-spec files with the concat demuxer `-c copy`. Check codec/res/fps/audio first |
| **Copy-size limits** | Transfer fails or truncates a > 50–100 MB file | `export.sh`: < 100 MB share file + split parts + sha256 |
| ASR mistakes on names/terms | Wrong caption words | `OUT.fix.json` per Short. Read the chunks as text in QA |
| Cut mid-sentence | Abrupt ending | Choose END from the srt **Close** line, add about 0.3 s, and check the last frame |
| Variable font at default weight | Thin captions | `set_variation_by_axes([900])` (already in the scripts) |

---

## 10. Approval: the human decides

- **Never upload, publish, schedule or post** anything (YouTube, social, shared drives) without Amitai's explicit approval (`investing-bros-show`).
- Deliver: the rendered Shorts, the `share/` copies, `shorts_candidates.md`, `titles_descriptions.md`, and a short QA note
  per Short (duration, LUFS, what was fixed, anything uncertain such as unverified claims).
- Wait for an OK on each Short. Apply the requested changes as targeted fixes (section 5) and resubmit.
