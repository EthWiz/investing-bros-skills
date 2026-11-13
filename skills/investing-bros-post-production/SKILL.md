---
name: investing-bros-post-production
description: >-
  Edit a finished Investing Bros / אחים להשקעות recording into the
  upload-ready audio: combine the parts, level the hosts, transcribe, draft
  the cut list, trim from that full draft, and start the episode's Producer
  (investing-bros-producer) for everything after. The episode owner's cut OK
  is round 1 and gates renders, not the trim. Use when
  Amitai says the recording is in, "edit episode N", "ההקלטה מוכנה", "עריכה",
  or sends חלק 1 / חלק 2.
---
# Investing Bros post-production (audio edit)

Load `investing-bros-show` first: naming, Drive tree, roles and the episode flow live there.

This skill makes the audio edit: the main track's first stages in `investing-bros-producer`
(riverside, intake, master, cut list, trim from the draft). The cut approval is round 1 and gates
renders, not the trim. The edited audio, the transcript and `edit.json`
are the handoff to everything else. Starting post-production also starts the episode's
**Producer** (`investing-bros-producer`), which runs the standing bundle (main flow, two
segments, three Shorts; `investing-bros-show` → The show), the review rounds and the retro.
After each step below, record it: `python3 <investing-bros-producer>/scripts/pipeline.py advance
"$EP" main <stage>`.

The full deliverable list ("full treatment") is [references/CHECKLIST.md](references/CHECKLIST.md);
its gate is `pipeline.py gate`. `scripts/postprod_checklist.py` stays as a compatibility wrapper
with the same CLI for older installs.

## When to use
The episode owner says the episode was recorded, the parts are already in, or Amitai asks to redo the edit.

## Inputs
- Episode number N **as Amitai states it**.
- Per-speaker high-quality video and audio in `$EP/riverside/` (every part, when the session was split), and Riverside's native side-by-side export as the default 16:9 master (too soft once cropped to 9:16, so Shorts still use each host's own track). The pull and the side-by-side rule live in `investing-bros-producer` → `references/riverside-pull.md`.
- Working dir `$EP` (show conventions → Roles and accounts).
- Tools: `ffmpeg`, Python 3 with numpy, `faster-whisper`. If Hugging Face is blocked, `sherpa-onnx` + `soundfile` (step 4).
- Long jobs: under a per-command time limit (show conventions → references/environment.md), use the chunked/resumable options below.

## Steps

### 1. Pull the Riverside tracks (`main.riverside`)
When the episode owner says the episode was recorded, the Producer arms one temporary polling routine and pulls every speaker's high-quality video and audio in the browser. How the routine starts, waits, and deletes itself: `investing-bros-producer` → `references/riverside-pull.md`.

```bash
R=<investing-bros-producer>/scripts/riverside_tracks.py
python3 $R begin "$EP" --project "פרק N" --by "<Owner HH:MM: their words>"
python3 $R due "$EP"       # check, wait, or give_up. One look per wake. Do not loop.
python3 $R checked "$EP"   # after a look that is not ready yet
python3 $R commit "$EP" --listing "$EP/extras/riverside-listing.json"
python3 $R verify "$EP"
python3 <investing-bros-producer>/scripts/pipeline.py advance "$EP" main riverside
```

Files go to `$EP/riverside/`. A speaker can have several files when the session was split. Do not upload them to Drive. When the script prints `disarm: true`, delete or disable the routine. About 6 hours with the tracks still processing: alert the owner once and disable the routine.

If that sign-in cannot be completed, the owner may waive `main.riverside`. Only then, ask the WhatsApp owner to download the latest parts from group `אחים להשקעות` into `$EP/parts/` (prefer `m4a`), named so they sort (`part1.m4a`, `part2.m4a`). Host tracks then go in `$EP` as `track-amitai.mp4` / `track-nadav.mp4`, and raw footage may be filed in Drive.

### 2. Combine into the raw master
The 16:9 video master is **Riverside's native side-by-side export**, not a video built from
the separate tracks. After the pull (step 1), record that export and keep the audio
combination for the m4a:

```bash
python3 <investing-bros-producer>/scripts/sbs_master.py commit-export "$EP" --file "$EP"/riverside/side-by-side.mp4
# audio parts (split session or a waived pull in $EP/parts/):
scripts/combine_parts.sh "$EP/extras/investing-bros-episode-raw-untrimmed.m4a" "$EP"/parts/part*
```

`combine_parts.sh --video` joins parts end to end; it is not the side-by-side master. If
Riverside's export failed ("Couldn't download your edit", the Exports tab never loads,
Export disabled), record the failure and get the episode owner's approval **before**
building from tracks (each time; it does not run automatically):

```bash
python3 <investing-bros-producer>/scripts/sbs_master.py export-failed "$EP" --reason "<what failed>"
python3 <investing-bros-producer>/scripts/pipeline.py approve "$EP" main sbs_fallback_ok --by "<Owner HH:MM: their words>"
python3 <investing-bros-producer>/scripts/sbs_master.py build-from-tracks "$EP" --left <amitai-track> --right <nadav-track>
```

The approval (`by`, `at`, the owner's words) is stored on `main.sbs_fallback_ok`. Details:
`investing-bros-producer` → `references/riverside-pull.md`. Never overwrite the raw master.
When `main.riverside` passed, keep it on the box; do not upload it to Drive.

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
  say so if the edit later shifts it). Add the speaker (`נדב:` / `אמיתי:`) when known.
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
- **Silences under 2 s are kept by default — never cut them** (Amitai, episode 10: the five 1–3 s silence trims were all put back). Only a silence of 2 s or longer may be trimmed, and even then leave a natural beat on each side so the join doesn't sound clipped.
- Listen for what else should go: long silences (2 s+), false starts, a restarted sentence, a technical drop-out, chatter about the recording. Use the gap list as the starting point.
- Write `extras/cuts-review/cuts-list.txt` with one line per cut, tagged `[routine]` (a long silence, a false start, a technical drop) or `[content]` (a section the owner should be asked about). Then trim immediately (step 6) from the **full** list. Do not wait for `cuts_ok`.
- Round 1 (`investing-bros-producer`) shows the whole list and asks each `[content]` line as its own question (raw times + the words around the cut). Routine lines stay visible; they are not a separate approval. `cuts_ok` gates `main.video`, `segNN.render` and `shortNN.render`. A restore in that round re-trims and re-copies only: nothing has been rendered yet.
- **A section cut from the middle** (an off-topic call, a part the hosts asked the editor to remove; episode 8: the courier call, raw 1605.0–1645.2 s):
  1. Find it in the transcript and put exact raw start/end times, with the words on both sides, on the list as `[content]` (e.g. "remove the 40 s"). It is in the draft trim; round 1 asks it as a question. A restore re-trims and re-copies only.
  2. Cut on a pause, not mid-word; listen to the join.
  3. Make the cut in audio **and** video with the same times. `trim.sh --cut A-B` (repeatable) removes it from the audio and records it in `edit.json`; `investing-bros-video` → `assemble_episode.sh --edit edit.json` removes the same range from the video. Don't splice by hand.
  4. Chapters: when the copy is written after `trim.sh --cut`, map raw times with `edit_map.py` (the cut is already accounted for). Only when a description already exists on the old timeline, move its later chapters with `investing-bros-title-description` → `shift_after_cut.py --cut A-B` (times on that description's timeline).
  5. Check A/V drift at the end of the assembled video (`assemble_episode.sh` prints the sync check) and spot-check lips right after the join. Then measure it: `investing-bros-video` → `verify_sync.py` must report `SYNC OK` (0 ms audio offset, 0-frame picture shift before, between and after every cut and near the end) before the video goes to anyone.
  6. A cut made **after** the video is assembled (a re-cut sample or master) goes through `investing-bros-video` → `render_cuts.py`: one pass, video and audio from the same input with the same frame-snapped boundaries. Never cut the audio on its own and mux it back.
- Every cut inside the episode is a raw `A-B` range that starts and ends in a pause. Don't cut a caveat, and keep cuts few: a thinking pause can belong in the conversation. A pause shorter than 2 s is never a cut on its own.

### 6. Trim and check
Trim right after the cut list, using every line on it (routine and content) as the draft. `cuts_ok` comes later, in round 1, and does not block this step.
```bash
scripts/trim.sh "$EP/episode-leveled.wav" START END "$EP/investing-bros-episode-edited.m4a" \
  --cut 1203.4-1209.9 --cut 1830-1836.2      # every cut on the draft list, routine and content
ffmpeg -i "$EP/investing-bros-episode-edited.m4a" -af ebur128=peak=true -f null - 2>&1 | tail -12
```
`trim.sh` writes `edit.json` (`start`, `end` and `cuts`, in raw seconds); each join gets a 10 ms fade. Chapters, shorts and the video map raw → edited time with it: `python3 scripts/edit_map.py edit.json --raw 754.2` (with no cuts that is `raw − start`). Listen to the first and last 20 seconds and to every cut. Loudness: about −16 LUFS, true peak ≤ −1.5 dBTP.

### 7. File in Drive
Find the `פרק N` folder (prefix match; prep normally created it). Only create `פרק N — נושא` if none exists.

| Where | What |
|---|---|
| Episode root | Edited audio, renamed `הקלטה-ערוכה-פרק-N.m4a` |
| `extras/` | When `main.riverside` was waived: raw untrimmed audio (and video), parts, host tracks. Always: leveled WAV, `transcript/` (`segments.json`, `.txt`, `.srt`), `edit.json`, the cut list. A passed Riverside pull keeps raw footage in the working folder, not here. |

Large files: if a final video must reach Amitai's Mac, use the verified
10–20 MB chunked `CopyFromBox` handoff to `~/Downloads` (show conventions →
references/environment.md → Delivering files); large Drive web uploads from the
box can stall.

### 8. Past-episode references (cards)
Find every reference to a past episode (by number or by topic) for the YouTube info cards:
```bash
python3 scripts/find_past_episode_refs.py "$EP/extras/transcript/segments.json" --episode N \
  --index <investing-bros-show>/references/episode-index.json --offset <raw→video shift> \
  --out "$EP/extras/past-episode-cards.json"
```
The transcript is in raw-master time: convert to the delivered video (teaser + intro shift,
minus any cuts before that point; `edit_map.py`), then check each time by ear. Max 4 cards,
one per referenced episode at its first strong mention, clearest / most repeated first. Read
every quote and delete false hits; write `[]` when nothing references a past episode. A topic
reference to an episode missing from `episode-index.json`: look it up (Drive tree, channel),
verify the ID, and add it to the index by PR. After each episode goes up, add it to the index
(ID + topics). `episode-upload` sets the cards in Studio.

## Done when
The audio edit is done; the episode is done only when `investing-bros-producer` says so.
- Episode root has `הקלטה-ערוכה-פרק-N.m4a`, at −16 LUFS with the hosts within 3 dB.
- `main.riverside` passed, or the owner waived it. When it passed, `extras/pipeline.json` lists every speaker's files and those files are in the working folder `riverside/`, not on Drive.
- `extras/` has `transcript/segments.json`, `edit.json`, `cuts-review/` (the cut list + one clip
  per cut) and the raw master on the box (plus host tracks if shorts will use them).
- The episode folder has the Google Doc `תמלול - פרק N` (automatic transcript, timestamped).
- `pipeline.py advance "$EP" main trim` passed on the draft cut list. `extras/cuts-review/cuts-list.txt`
  tags every cut `[routine]` or `[content]`. `cuts_ok` is in round 1 (with the title, the segment
  ranges and the Short picks); it gates renders, not this trim.
- Once the full video exists, `extras/past-episode-cards.json` (step 8).

## Hand back
- Whether `main.riverside` passed (tracks stayed off Drive) or was waived
- Drive folder link
- Link to the `תמלול - פרק N` Doc
- Edited length, the start/end cut points and every cut inside the episode (raw time + the words around it)
- Loudness (integrated LUFS) and the host balance before → after leveling
- `pipeline.py next "$EP"` output: the next step on every track.

## Never
- Treat a step as optional because its wording sounds conditional.
- Auto-number the episode or create a second `פרק N` folder.
- Cut a silence under 2 s, drop a `[content]` cut from the review, or hide the `[routine]` lines.
- Render the full video, a segment or a Short before `cuts_ok`. A content cut is trimmed in the draft and asked in round 1; a restore re-trims and re-copies only.
- Ship an episode where one host is more than ~3 dB quieter than the other.
- Put anything in the episode root except the files named in the show's Drive tree.
- Upload raw Riverside footage to Drive when `main.riverside` passed, poll that pull in a loop, or delete a Riverside studio, project or recording.
- Build the side-by-side video master from tracks except as `investing-bros-producer` allows (native Riverside export first; `main.sbs_fallback_ok` after it fails).
- Put the Riverside login anywhere except secure fill.
- Drive WhatsApp Web yourself, or make Mac-local editing the primary path.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).

Transcription runs faster-whisper with `compute_type=float32` (the default in `transcribe.py`); never use int8/auto, which garble Hebrew.