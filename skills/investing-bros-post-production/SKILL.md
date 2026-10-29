---
name: investing-bros-post-production
description: >-
  Start the full post-production pipeline for a finished Investing Bros /
  אחים להשקעות recording: edit the upload-ready audio, then track the main
  episode flow plus exactly two complete segment videos and exactly three
  complete shorts through their owning skills. Use when Amitai says the
  recording is in, "edit episode N", "ההקלטה מוכנה", "עריכה", or sends
  חלק 1 / חלק 2.
---
# Investing Bros post-production (audio edit)

Load `investing-bros-show` first: naming, Drive tree, roles and the episode flow live there.

Starting post-production opens one standing deliverable bundle:
1. the main episode flow;
2. **exactly two segment videos**: segment 01 is the required deep-dive segment, and segment 02 is the next-best self-contained sub-question from the deep dive or another strong topic;
3. **exactly three shorts**.

This skill performs the audio edit and starts and tracks that complete bundle. The edited audio is the handoff to the downstream skills, not completion of post-production. Everything after the audio edit reads the transcript and `edit.json` it leaves:
- titles, description, artwork copy brief → `investing-bros-title-description`
- show/episode cover art, thumbnails and graphic assets → `investing-bros-brand`
- cold opens, canonical intro + matching outro, video episode, teaser → `investing-bros-video`
- exactly two segment videos, each through selection, nudge, title, thumbnail, card/end screen/pinned comment, Drive, Unlisted review and Amitai's OK → `investing-bros-segment-video`
- exactly three shorts, each through picks, render, Codex cover, Telegram approval, Drive, post-episode upload and links → `investing-bros-shorts`
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

**Required: put a readable transcript in Drive.** Right after transcribing, create a Google Doc
named `תמלול - פרק N` in the episode's `אחים להשקעות > פרק N` folder (find it by prefix match).
- Hebrew, UTF-8. First lines: `אחים להשקעות — פרק N`, the length, and
  `תמלול אוטומטי — ייתכנו שגיאות בשמות, במספרים ובמונחים באנגלית.`
- One line or paragraph per segment, each starting with its `[m:ss]` timestamp (raw timeline;
  say so if the edit later shifts it). Add the speaker (`נדב:` / `עמיתי:`) when known.
- Create it through the Google Drive connector as a text Google Doc (fine for text; only MP4s
  must go through the browser). Don't overwrite or move other Drive files; if the Doc already
  exists, update it rather than adding a duplicate.

### 5. Build the cut list
```bash
python3 scripts/find_bounds.py "$EP/transcript/segments.json"             # suggested start and end (outro only near the end; lone ביי needs a pause)
python3 scripts/find_gaps.py "$EP/episode-leveled.wav" --segments "$EP/transcript/segments.json" \
  --start START --end END                                                  # long silences, with context
```
- **Start:** the first real open (ברוכים הבאים / אחים להשקעות / פרק). **End:** right after the real outro. Both scripts only suggest; read the transcript around each point.
- Listen for what else should go: long silences, false starts, a restarted sentence, a technical drop-out, chatter about the recording. Use the gap list as the starting point.
- Send Nadav the list (raw times + the words around each) and wait for his OK. Ambiguous cut → ask Amitai.
- **A section cut from the middle** (an off-topic call, a part the hosts asked the editor to remove; episode 8: the courier call, raw 1605.0–1645.2 s):
  1. Find it in the transcript and propose exact raw start/end times with the words on both sides. Confirm the exact cut with Amitai/Nadav (e.g. "remove the 40 s") before cutting.
  2. Cut on a pause, not mid-word; listen to the join.
  3. Make the cut in audio **and** video with the same times. `trim.sh --cut A-B` (repeatable) removes it from the audio and records it in `edit.json`; `investing-bros-video` → `assemble_episode.sh --edit edit.json` removes the same range from the video. Don't splice by hand.
  4. Chapters: when the copy is written after `trim.sh --cut`, map raw times with `edit_map.py` (the cut is already accounted for). Only when a description already exists on the old timeline, move its later chapters with `investing-bros-title-description` → `shift_after_cut.py --cut A-B` (times on that description's timeline).
  5. Check A/V drift at the end of the assembled video (`assemble_episode.sh` prints the sync check) and spot-check lips right after the join. Then measure it: `investing-bros-video` → `verify_sync.py` must report `SYNC OK` (0 ms audio offset, 0-frame picture shift before, between and after every cut and near the end) before the video goes to anyone.
  6. A cut made **after** the video is assembled (a re-cut sample or master) goes through `investing-bros-video` → `render_cuts.py`: one pass, video and audio from the same input with the same frame-snapped boundaries. Never cut the audio on its own and mux it back.
- Every cut inside the episode is a raw `A-B` range that starts and ends in a pause. Don't cut a caveat, and keep cuts few: a thinking pause can belong in the conversation.

### 6. Trim and check
```bash
scripts/trim.sh "$EP/episode-leveled.wav" START END "$EP/investing-bros-episode-edited.m4a" \
  --cut 1203.4-1209.9 --cut 1830-1836.2      # the approved cuts inside the episode, if any
ffmpeg -i "$EP/investing-bros-episode-edited.m4a" -af ebur128=peak=true -f null - 2>&1 | tail -12
```
`trim.sh` writes `edit.json` (`start`, `end` and `cuts`, in raw seconds); each join gets a 10 ms fade. Chapters, shorts and the video map raw → edited time with it: `python3 scripts/edit_map.py edit.json --raw 754.2` (with no cuts that is `raw − start`). Listen to the first and last 20 seconds and to every cut. Loudness: about −16 LUFS, true peak ≤ −1.5 dBTP.

### 7. File in Drive
Find the `פרק N` folder (prefix match; prep normally created it). Only create `פרק N — נושא` if none exists.

| Where | What |
|---|---|
| Episode root | Edited audio, renamed `הקלטה-ערוכה-פרק-N.m4a` |
| `extras/` | Raw untrimmed audio (and video), leveled WAV, parts, host tracks, `transcript/` (`segments.json`, `.txt`, `.srt`), `edit.json`, the cut list |

Large files: if a final video must reach Amitai's Mac, use the verified
10–20 MB chunked `CopyFromBox` handoff to `~/Downloads` (show conventions →
references/environment.md → Delivering files); large Drive web uploads from the
box can stall.

## Done when
Post-production is not complete at the audio handoff. Every item below must be complete:

**Audio edit**
- Episode root has `הקלטה-ערוכה-פרק-N.m4a`, at −16 LUFS with the hosts within 3 dB.
- `extras/` has `transcript/segments.json`, `edit.json` and the raw master (plus host tracks if shorts will use them).
- The episode folder has the Google Doc `תמלול - פרק N` (automatic transcript, timestamped).
- Once the episode art is final, the folder also has `cover-פרק-N.png` and
  `thumbnail-פרק-N.jpg` (made and filed by `investing-bros-brand`, steps 7–8).
- Nadav OK'd the cut list.

**Standing downstream deliverables**
- The normal main episode flow has completed through its owning title/description,
  brand, video and upload skills as applicable. Its full video uses the freshly
  fetched canonical Drive-ID clip from `investing-bros-show` as both intro and
  outro; the outro provides the final 20 seconds for the YouTube end screen.
- `segments/` has **exactly two** complete segment packages: `סגמנט-01` is the deep-dive segment and `סגמנט-02` is the selected second topic. Both completed the full `investing-bros-segment-video` flow, including Drive files, nudge, title, thumbnail, card, end screen, Unlisted review, Amitai's OK and the pinned comment after publication.
- `Shorts/` has **exactly three** complete short packages. All three completed the full `investing-bros-shorts` flow, including approved picks, render and QA, Codex cover, Telegram approval, Drive files, upload only after the full episode was live, and links back to the episode.
- If an approval or publication step is still waiting, report the bundle as waiting, not done.

## Hand back
- Drive folder link
- Link to the `תמלול - פרק N` Doc
- Edited length, the start/end cut points and every cut inside the episode (raw time + the words around it)
- Loudness (integrated LUFS) and the host balance before → after leveling
- Next: start titles/artwork/video, both segment videos and all three shorts in parallel from the transcript and `edit.json`; publish in the order owned by `investing-bros-episode-upload`.
- Pipeline status: main episode flow (including canonical intro/outro and the
  full-episode end screen), segment 01, segment 02 and shorts 01–03, with the next
  incomplete approval or action for each.

## Never
- Auto-number the episode or create a second `פרק N` folder.
- Make a cut Nadav hasn't OK'd, or an ambiguous cut without asking.
- Ship an episode where one host is more than ~3 dB quieter than the other.
- Put anything in the episode root except the files named in the show's Drive tree.
- Drive WhatsApp Web yourself, or make Mac-local editing the primary path.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).

Transcription runs faster-whisper with `compute_type=float32` (the default in `transcribe.py`); never use int8/auto, which garble Hebrew.
