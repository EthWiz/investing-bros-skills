---
name: investing-bros-post-production
description: >-
  Edit the audio of a finished Investing Bros / אחים להשקעות recording into
  the upload-ready episode: fetch the parts, combine, level the two hosts,
  transcribe (Hebrew), find the start, end and long silences, get the cut list
  approved, trim, check loudness and file the edited audio and working files in
  the episode's Drive folder. Use when Amitai says the recording is in, "edit
  episode N", "ההקלטה מוכנה", "עריכה", or sends חלק 1 / חלק 2. Titles,
  video and shorts come after this, from their own skills.
---
# Investing Bros post-production (audio edit)

Load `investing-bros-show` first: naming, Drive tree, roles and the episode flow live there.

This skill ends at the edited audio. Everything after it reads the transcript and `edit.json` it leaves:
- titles, description, artwork copy brief → `investing-bros-title-description`
- show/episode cover art, thumbnails and graphic assets → `investing-bros-brand`
- cold opens, intro, video episode, teaser → `investing-bros-video`
- shorts, mid-form → `investing-bros-shorts`
- review ping, uploads, publish → `investing-bros-episode-upload`

## When to use
The recording is in (parts posted in group `אחים להשקעות`, or files in Drive), or Amitai asks to redo the edit.

## Inputs
- Episode number N **as Amitai states it**.
- The recording parts (`חלק 1`, `חלק 2`, …). For shorts in the house style, also each host's own Riverside track (Individual tracks, highest resolution): the side-by-side export is too soft once cropped to 9:16.
- Working dir `$EP` (show conventions → Roles and accounts).
- Tools: `ffmpeg`, Python 3 with numpy, `faster-whisper`. If Hugging Face is blocked, `sherpa-onnx` + `soundfile` (step 4).
- Long jobs: under a per-command time limit (show conventions → references/environment.md), use the chunked/resumable options below.

## Steps

### 1. Fetch the parts
Ask the WhatsApp owner to download the latest parts from group `אחים להשקעות` into `$EP/parts/` (prefer `m4a`), named so they sort in order (`part1.m4a`, `part2.m4a`). Host tracks go in `$EP` as `track-amitai.mp4` / `track-nadav.mp4`.

### 2. Combine into the raw master
```bash
scripts/combine_parts.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP"/parts/part*
# video parts, when video or shorts will be made: add --video "$EP/investing-bros-episode-raw-untrimmed.mp4"
```
Never overwrite the raw master.

### 3. Level the two hosts
```bash
python3 scripts/speaker_balance.py "$EP/investing-bros-episode-raw-untrimmed.m4a" --spread   # >10 dB spread = imbalanced
scripts/level_audio.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP/episode-leveled.wav"
```
`level_audio.sh` keeps the raw timeline, lifts the quiet host and lands the episode at −16 LUFS / −1.5 dBTP. Confirm with `speaker_balance.py --a START:END --b START:END` on 2–3 solo stretches per host: within 3 dB.
It preserves packet timestamp gaps and fails if the output duration leaves the source
clock. If an already-mastered back-catalogue source measures −16 ±0.5 LUFS and the
hosts are already within 3 dB, use it as-is instead of processing it twice; report
the measurements.

### 4. Transcribe the raw master
```bash
python3 scripts/transcribe.py "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP/transcript"
# Hugging Face unreachable: add --engine sherpa (weaker on Hebrew: proofread names, numbers, English terms)
# CPU tuning: add --threads N (applies to either engine)
```
Writes `segments.json`, `transcript.txt`, `transcript.srt` on the raw timeline.
Its analysis WAV also preserves packet timestamp gaps. Every later skill uses this transcript.

### 5. Build the cut list
```bash
python3 scripts/find_bounds.py "$EP/transcript/segments.json"             # suggested start and end
python3 scripts/find_gaps.py "$EP/episode-leveled.wav" --segments "$EP/transcript/segments.json" \
  --start START --end END                                                  # long silences, with context
```
- **Start:** the first real open (ברוכים הבאים / אחים להשקעות / פרק). **End:** right after the real outro. Both scripts only suggest; read the transcript around each point.
- Listen for what else should go: long silences, false starts, a restarted sentence, a technical drop-out, chatter about the recording. Use the gap list as the starting point.
- Send Nadav the list (raw times + the words around each) and wait for his OK. Ambiguous cut → ask Amitai.
- `trim.sh` cuts only the start and end today. A cut inside the episode needs script support: say which cuts are waiting for it in the hand-back, don't make them by hand (show conventions → Working rules).

### 6. Trim and check
```bash
scripts/trim.sh "$EP/episode-leveled.wav" START END "$EP/investing-bros-episode-edited.m4a"
ffmpeg -i "$EP/investing-bros-episode-edited.m4a" -af ebur128=peak=true -f null - 2>&1 | tail -12
```
`trim.sh` writes `edit.json` (`start`/`end` in raw seconds). Chapters, shorts and the video map raw → edited time with it (`edited = raw − start`). Listen to the first and last 20 seconds and to every cut. Loudness: about −16 LUFS, true peak ≤ −1.5 dBTP.

### 7. File in Drive
Find the `פרק N` folder (prefix match; prep normally created it). Only create `פרק N — נושא` if none exists.

| Where | What |
|---|---|
| Episode root | Edited audio, renamed `הקלטה-ערוכה-פרק-N.m4a` |
| `extras/` | Raw untrimmed audio (and video), leveled WAV, parts, host tracks, `transcript/` (`segments.json`, `.txt`, `.srt`), `edit.json`, the cut list |

Large files: upload as the Drive upload account in the browser when the connector can't carry them (show conventions → Roles and accounts).

## Done when
- Episode root has `הקלטה-ערוכה-פרק-N.m4a`, at −16 LUFS with the hosts within 3 dB.
- `extras/` has `transcript/segments.json`, `edit.json` and the raw master (plus host tracks if shorts will use them).
- Nadav OK'd the cut list.

## Hand back
- Drive folder link
- Edited length, the start/end cut points, and any cut waiting for script support
- Loudness (integrated LUFS) and the host balance before → after leveling
- Next: titles, video and shorts can start now, in parallel

## Never
- Auto-number the episode or create a second `פרק N` folder.
- Make a cut Nadav hasn't OK'd, or an ambiguous cut without asking.
- Ship an episode where one host is more than ~3 dB quieter than the other.
- Put anything in the episode root except the files named in the show's Drive tree.
- Drive WhatsApp Web yourself, or make Mac-local editing the primary path.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).
