---
name: investing-bros-post-production
description: >-
  Turn a finished Investing Bros / אחים להשקעות recording into an upload-ready
  episode: fetch the parts, combine, level the two hosts, transcribe (Hebrew),
  trim intro/outro, write the Hebrew description and title Docs, optionally
  assemble the full video episode (teasers + intro + episode), file everything
  in the episode's Drive folder and ping the group for review. Use when Amitai
  says the recording is in, "edit episode N", "ההקלטה מוכנה", "פרק מלא",
  "full episode video", or sends חלק 1 / חלק 2.
---
# Investing Bros post-production

Load `investing-bros-show` first — naming, Drive tree, roles and WhatsApp rules live there.

This skill covers the core edit only. Promo material is separate:
- Shorts → `investing-bros-shorts`
- Teaser → `investing-bros-teaser`
- YouTube thumbnail / episode artwork → `investing-bros-cover-art`
- RedCircle upload (incl. Hebrew RTL fix) → `investing-bros-episode-upload`

## Inputs
- Episode number N **as Amitai states it**.
- The recording parts (`חלק 1`, `חלק 2`, … from group `אחים להשקעות`).
- Working dir `/workspace/investing-bros/episode-N/` (or `episode-latest/` until N is confirmed); the steps below call it `$EP`.
- Tools: `ffmpeg`, Python 3 with numpy, `faster-whisper` (`pip install faster-whisper`). If Hugging Face is blocked, `sherpa-onnx` + `soundfile` (models come from GitHub releases; see step 4).
- Long jobs: if your shell has a per-command time limit (some agent sandboxes kill commands after ~3 min and don't keep background jobs), use the resumable / chunked options below instead of one long ffmpeg run.

- **For shorts in the house style:** also download each host's own video track from Riverside (Individual tracks, highest resolution recorded — 4K if available) and file them in `extras/` as `track-amitai.mp4` / `track-nadav.mp4`. The side-by-side export only has ~600 px of width per face once cropped to 9:16, so full-screen shorts look soft; `build_fullbleed.py` takes the tracks through `sources` + `crop`.

## Steps (order matters)

### 1. Fetch the parts
Ask the WhatsApp owner to download the latest parts from group `אחים להשקעות` **only** into `$EP/parts/` (prefer `m4a`). Name them so they sort in order (`part1.m4a`, `part2.m4a`).

### 2. Combine into the raw master
```bash
scripts/combine_parts.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP"/parts/part*
```
Extracts audio from video parts and joins them in the order given. Never overwrite the raw master. If the parts are video and promo clips may be wanted, also run with `--video "$EP/investing-bros-episode-raw-untrimmed.mp4"` (see the script's usage).

### 3. Level the two hosts
Riverside records each host on his own mic and level; the mix is often uneven (episode 6: Amitai ~16 dB below Nadav — inaudible on a phone). Check, then level:
```bash
python3 scripts/speaker_balance.py "$EP/investing-bros-episode-raw-untrimmed.m4a" --spread   # >10 dB spread = imbalanced
scripts/level_audio.sh "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP/episode-leveled.wav"
```
`level_audio.sh` keeps the raw timeline (no trim, no delay), lifts the quiet host, and lands the episode at −16 LUFS / −1.5 dBTP. Confirm with `speaker_balance.py` on 2–3 solo stretches per host (`--a START:END --b START:END`, from the transcript) — they should be within 3 dB. The leveled WAV is what gets trimmed (step 5), and what teasers and the video episode use.

### 4. Transcribe the raw master
```bash
python3 scripts/transcribe.py "$EP/investing-bros-episode-raw-untrimmed.m4a" "$EP/transcript"
# Hugging Face unreachable: add --engine sherpa
```
Uses `ivrit-ai/whisper-large-v3-turbo-ct2` on a leveled 16 kHz mono copy (without leveling, whisper's VAD drops a quiet host's sentences). Writes `segments.json`, `transcript.txt`, `transcript.srt` (raw timeline). The `sherpa` engine (Whisper turbo int8 from the sherpa-onnx GitHub releases) is noticeably weaker on Hebrew: names, numbers and English terms need a careful proofread.

### 5. Trim intro and outro
```bash
python3 scripts/find_bounds.py "$EP/transcript/segments.json"   # suggests start/end
scripts/trim.sh "$EP/episode-leveled.wav" START END "$EP/investing-bros-episode-edited.m4a"
```
- Start: the first real open (ברוכים הבאים / אחים להשקעות / פרק).
- End: right after the real outro.
- Before any cut, send Nadav a cut list — false starts, silences, pre/post-roll chatter — and wait for his OK. A later change needs his OK again before a rebuild or upload. Going public still needs Amitai's OK (`investing-bros-show`).
- `find_bounds.py` only suggests — read the transcript around both points. If either cut is ambiguous, ask Amitai.
- `trim.sh` also writes `edit.json` next to the output (`start`/`end` in raw seconds). Promo clips and chapters use it to map raw → edited time (`edited = raw − start`).
- 192k mp3 is fine instead of m4a if needed (`.mp3` output name).

### 6. Drive episode folder
Find the existing `פרק N` folder (prefix match; prep normally created it) and **reuse it**. Only create `פרק N — נושא` if none exists. Create `extras/` inside it if missing. Leave `brief/` alone.

### 7. Hebrew Google Docs (exactly two, in the episode root)
Write `תיאור הפרק` and `אפשרויות כותרת` following [references/episode-docs.md](references/episode-docs.md). Chapters use the **edited** timeline. Keep the Docs plain — no invisible direction marks (those are added only at upload time). Local `.txt` drafts are fine while working; they end up in `extras/` or get deleted.

### 8. Video episode (when the recording has video and Amitai wants it)
Video assets are made only by ליאורה (`investing-bros-show` → Roles). Order: cold open (~22 s) → Amitai's intro, used as-is → the episode. The cold open has a strong hook and ends on a full sentence, then a hard cut into the intro. Music is allowed when it sits under the speech (−14 LUFS; `investing-bros-teaser`). Per-host teasers, when there are two, are that cold open.
1. Make the teasers with `investing-bros-teaser` (per-host cold open, audio from `episode-leveled.wav`).
2. Assemble:
   ```bash
   scripts/assemble_episode.sh "$EP/פרק-N-וידאו.mp4" \
     --body "$EP/investing-bros-episode-raw-untrimmed.mp4" --body-audio "$EP/episode-leveled.wav" \
     --start START --end END \
     --before "טיזר 1 - נדב.mp4" --before "טיזר 2 - אמיתי.mp4" --intro "אחים להשקעות-Intro.mp4"
   ```
   Every segment is encoded with the same x264 settings and joined without re-encoding; the body goes in ~8-minute chunks. Under a command time limit add `--max-seconds 150` and re-run the same command until it stops printing `resume` — finished chunks are kept. (Episode 6 on a 4-core laptop VM: ~100 s per 460 s chunk.) When the only change is a trim at the head of an already-encoded master, re-encode that opening and concat the rest with `-c copy` (minutes, not a half-hour re-encode). That `-c copy` is the same encode — don't use it to join pieces that were encoded separately.
3. Check: video and audio durations match (the script prints both); spot-check a frame and the sound at each join (teaser → teaser → intro → episode) and somewhere late in the episode for sync.

### 8b. Shorts (when this run includes them)
If Amitai asked for shorts with this edit (or the run's brief lists them), make them now with `investing-bros-shorts` — it renders each short, makes its sized cover and uploads both (plus captions) to the episode's `promo/` folder. Include the `promo/` link in the review ping.

### 9. File everything in Drive
| Where | What |
|---|---|
| Episode root | Edited audio renamed `הקלטה-ערוכה-פרק-N.m4a`, Doc `תיאור הפרק`, Doc `אפשרויות כותרת` |
| `video/` | The full video episode, if made (step 8) |
| `promo/` | Shorts (`.mp4` + `-cover.jpg` + `.srt` each) and teasers, if made (step 8b) |
| `extras/` | Raw untrimmed audio (and video), leveled WAV, part files, `segments.json`, transcript `.txt`/`.srt`, `edit.json`, `.txt` copies of Docs, drafts and temp files |

Large audio: upload through the browser as the Drive upload account (show conventions → accounts) when the connector can't carry the file. Nothing else at the episode root.

### 10. Ready-for-review ping
Once the root is right: get a shareable link to the **episode folder** and ask the WhatsApp owner to send one message to `אחים להשקעות` — ready for review + link, ending with the show tag. Don't delete earlier messages.

## Hand back
Report to Amitai:
- Episode folder link and Doc links
- Confirmation the root holds only edited audio + 2 Docs, with everything else in `extras/`
- Edited duration and the start/end cut points
- Loudness: integrated LUFS and the host balance (dB difference) before → after leveling
- Video episode link and length, if made
- Shorts: the `promo/` link, and per short its length and cover headline, if made
- WhatsApp ping status
- Blockers

Next: promo skills if wanted; `investing-bros-episode-upload` once Amitai approves.

## Never
- Auto-number the episode or create a duplicate `פרק N` folder.
- Make ambiguous cuts without asking.
- Leave the description or titles only as `.txt`, or clutter the episode root.
- Drive WhatsApp Web, or delete WhatsApp messages without explicit OK.
- Make Mac-local editing the primary path.
- Ship an episode (or clip) where one host is more than ~3 dB quieter than the other.
- Join video segments encoded with different x264 settings using `-c copy` — re-encode them with the same settings (`assemble_episode.sh` does).
- Write your own code where this skill has a script, or work around a missing step without saying so — follow the working rules in `investing-bros-show`.
