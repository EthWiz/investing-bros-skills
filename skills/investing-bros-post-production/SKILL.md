---
name: investing-bros-post-production
description: >-
  Turn a finished Investing Bros / אחים להשקעות recording into an upload-ready
  episode: fetch the parts, combine, transcribe (Hebrew), trim intro/outro,
  write the Hebrew description and title Docs, file everything in the episode's
  Drive folder and ping the group for review. Use when Amitai says the
  recording is in, "edit episode N", "ההקלטה מוכנה", or sends חלק 1 / חלק 2.
---
# Investing Bros post-production

Load `investing-bros-show` first — naming, Drive tree, roles and WhatsApp rules live there.

This skill covers the core edit only. Promo material is separate:
- Shorts → `investing-bros-shorts`
- Teaser → `investing-bros-teaser`
- Episode artwork → `investing-bros-cover-art` (placeholder — not defined yet)
- RedCircle upload (incl. Hebrew RTL fix) → `investing-bros-episode-upload`

## Inputs
- Episode number N **as Amitai states it**.
- The recording parts (`חלק 1`, `חלק 2`, … from group `אחים להשקעות`).
- Working dir `/workspace/investing-bros/episode-N/` (or `episode-latest/` until N is confirmed); the steps below call it `$EP`.
- Tools: `ffmpeg`, Python 3, `faster-whisper` (`pip install faster-whisper`).

## Steps (order matters)

### 1. Fetch the parts
Ask the WhatsApp owner to download the latest parts from group `אחים להשקעות` **only** into `$EP/parts/` (prefer `m4a`). Name them so they sort in order (`part1.m4a`, `part2.m4a`).

### 2. Combine into the raw master
```bash
scripts/combine_parts.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP"/parts/part*
```
Extracts audio from video parts and joins them in the order given. Never overwrite the raw master. If the parts are video and promo clips may be wanted, also run with `--video "$EP/investing-bros-episode-raw-untrimmed.mp4"` (see the script's usage).

### 3. Transcribe the raw master
```bash
python3 scripts/transcribe.py "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP/transcript"
```
Uses `ivrit-ai/whisper-large-v3-turbo-ct2` on 16 kHz mono audio. Writes `segments.json`, `transcript.txt`, `transcript.srt` (raw timeline).

### 4. Trim intro and outro
```bash
python3 scripts/find_bounds.py "$EP/transcript/segments.json"   # suggests start/end
scripts/trim.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" START END "$EP/investing-bros-episode-edited.m4a"
```
- Start: the first real open (ברוכים הבאים / אחים להשקעות / פרק).
- End: right after the real outro.
- `find_bounds.py` only suggests — read the transcript around both points. If either cut is ambiguous, ask Amitai.
- `trim.sh` also writes `edit.json` next to the output (`start`/`end` in raw seconds). Promo clips and chapters use it to map raw → edited time (`edited = raw − start`).
- 192k mp3 is fine instead of m4a if needed (`.mp3` output name).

### 5. Drive episode folder
Find the existing `פרק N` folder (prefix match; prep normally created it) and **reuse it**. Only create `פרק N — נושא` if none exists. Create `extras/` inside it if missing. Leave `brief/` alone.

### 6. Hebrew Google Docs (exactly two, in the episode root)
Write `תיאור הפרק` and `אפשרויות כותרת` following [references/episode-docs.md](references/episode-docs.md). Chapters use the **edited** timeline. Keep the Docs plain — no invisible direction marks (those are added only at upload time). Local `.txt` drafts are fine while working; they end up in `extras/` or get deleted.

### 7. File everything in Drive
| Where | What |
|---|---|
| Episode root | Edited audio renamed `הקלטה-ערוכה-פרק-N.m4a`, Doc `תיאור הפרק`, Doc `אפשרויות כותרת` |
| `extras/` | Raw untrimmed audio (and video), part files, wavs, `segments.json`, transcript `.txt`/`.srt`, `edit.json`, `.txt` copies of Docs, drafts and temp files |

Large audio: upload through the browser as the Drive upload account (show conventions → accounts) when the connector can't carry the file. Nothing else at the episode root.

### 8. Ready-for-review ping
Once the root is right: get a shareable link to the **episode folder** and ask the WhatsApp owner to send one message to `אחים להשקעות` — ready for review + link, ending with the show tag. Don't delete earlier messages.

## Hand back
Report to Amitai:
- Episode folder link and Doc links
- Confirmation the root holds only edited audio + 2 Docs, with everything else in `extras/`
- Edited duration and the start/end cut points
- WhatsApp ping status
- Blockers

Next: promo skills if wanted; `investing-bros-episode-upload` once Amitai approves.

## Never
- Auto-number the episode or create a duplicate `פרק N` folder.
- Make ambiguous cuts without asking.
- Leave the description or titles only as `.txt`, or clutter the episode root.
- Drive WhatsApp Web, or delete WhatsApp messages without explicit OK.
- Make Mac-local editing the primary path.
