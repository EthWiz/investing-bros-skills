# Riverside track pull (`main.riverside`)

The Producer pulls each speaker's high-quality video and audio from the Riverside **web
dashboard in the browser**. `scripts/riverside_tracks.py` records the pull. It does not
sign in, download, sleep, or loop.

## What starts it

The episode owner says in chat that the episode was recorded. That message is the trigger.
Do not open Riverside before it, and do not ask them whether the recording happened.

```bash
python3 scripts/riverside_tracks.py begin "$EP" --project "פרק N" \
  --by "<Owner HH:MM: their words>" [--every 15]
```

`begin` stores the words and the clock. It does not reset them if it is run again.

## The temporary polling routine

Arm **one** temporary polling routine for this episode:

- Gap about **15 minutes**. **10–20 minutes** is the allowed range (`--every`, default 15).
  Anything faster or slower is refused.
- Run the first check in the same turn as the owner's message (`due` prints `check` before
  any look has been recorded).
- Each later wake is one check. `due` prints `wait` when the gap has not elapsed: stop,
  and leave the routine armed. Do not look again in that turn.
- After a look that is not ready yet: `checked`. That records the look and prints the next
  time. Leave the routine armed and end the turn.
- The routine is temporary. When a run prints `disarm: true` (the tracks are in, or the
  6 hours are up), **delete or disable the routine in that same turn**. Do not schedule
  another check. Disabling the routine does not delete anything on Riverside.

Do not busy-loop, sleep in a loop, or call `due` again in the same turn.

About **6 hours** after `begin`, `due` prints `give_up` and `disarm: true`. Alert the
episode owner once (this is the one alert outside a review round, `investing-bros-show`
→ Ownership and contact), disable the routine, and stop. A later download can still be
`commit`ted if the files show up; do not keep the routine alive to wait for them.

## Browser

1. Open `https://riverside.fm`. It redirects to `https://riverside.com`.
2. Sign in with the **Grok Bot vault** login, filled only with **secure fill**. Never
   print it, paste it, log it, or store it in the repo or the episode folder.
3. Open this episode's project in the studio dashboard.
4. Read every speaker and every part the project shows. A split session is several files
   for one speaker (episode 10: Amitai had two). A part still processing means the pull
   is not ready: do not download a stand-in and do not drop that part from the list.
5. When every speaker's **high-quality** video and **high-quality** audio are ready for
   every part, download all of them into `$EP/riverside/`. High quality means that
   speaker's own dashboard high-quality track, not a 720p proxy. These tracks stay
   the source for Shorts and one-host crops.
6. Also download Riverside's **native side-by-side export** (1080p, 1920×1080, 24 fps)
   into `$EP/riverside/` (for example `riverside/side-by-side.mp4`). That file is the
   default 16:9 episode master. Download it in the browser from the dashboard or the
   project's Export / side-by-side control. Riverside has no Drive or email export, and
   a shared `exported-clip` link is not this file. Then record it:

   ```bash
   python3 scripts/sbs_master.py commit-export "$EP" --file riverside/side-by-side.mp4
   ```

   If that export fails — "Couldn't download your edit" (at 4k or 1080p), the Exports
   tab never loads, or Export is disabled — record the failure and **stop**. Do not
   build a side-by-side from the per-speaker tracks automatically:

   ```bash
   python3 scripts/sbs_master.py export-failed "$EP" --reason "<what failed>"
   python3 scripts/pipeline.py approve "$EP" main sbs_fallback_ok --by "<Owner HH:MM: their words>"
   python3 scripts/sbs_master.py build-from-tracks "$EP" --left riverside/<amitai>.mp4 --right riverside/<nadav>.mp4
   ```

   The fallback needs the episode owner's explicit approval **each time** (who and when
   are stored on `main.sbs_fallback_ok` in `extras/pipeline.json`). A new Riverside pull
   stales that approval. Seats: Amitai left, Nadav right, unless the first frame shows
   otherwise (`investing-bros-show`).

Never delete a studio, a project, or a recording. The script has no delete command.

## Record and check

Listing (one object; `quality` is `high` and `status` is `ready` only when that file is
the high-quality export and it has finished processing):

```json
{
  "participants": ["Amitai", "Nadav"],
  "tracks": [
    {"speaker": "Amitai", "part": 1, "kind": "video", "quality": "high", "status": "ready",
     "path": "riverside/amitai-1-video.mp4", "bytes": 10, "duration_s": 3600.0},
    {"speaker": "Amitai", "part": 1, "kind": "audio", "quality": "high", "status": "ready",
     "path": "riverside/amitai-1-audio.wav", "bytes": 10, "duration_s": 3600.0}
  ]
}
```

Paths stay under `riverside/` inside the episode folder. `bytes` is the file size.
`duration_s` is the file's duration.

```bash
python3 scripts/riverside_tracks.py commit "$EP" --listing "$EP/extras/riverside-listing.json"
python3 scripts/riverside_tracks.py verify "$EP"
python3 scripts/pipeline.py advance "$EP" main riverside
```

`commit` checks each file's size and its duration (ffprobe, within 1 second) and only
then marks the pull ready. `advance` copies the speaker, part, path, bytes and duration
into `extras/pipeline.json`. Then disable the routine.

## Drive

When `main.riverside` passes, do **not** upload the raw footage to Drive. That is the
`riverside/` files and the untrimmed raw master. `extras/pipeline.json` and
`extras/riverside-pull.json` are the record, not the footage, and still sync.

If sign-in cannot be completed, the owner may waive `main.riverside`. The host-download
path in `investing-bros-show` → references/environment.md applies, and raw footage may
then be filed in Drive `extras/`.

## Commands

| Command | What it does |
|---|---|
| `begin --project --by [--every]` | Record the owner's message. Once per episode; a second run does not move the clock. |
| `due` | `check`, `wait`, `ready`, or `give_up`. Does not look at Riverside. |
| `checked` | Record one look that was not ready yet. Refuses when `due` would say `wait`. |
| `commit --listing` | Store the downloaded files after the size and duration checks. Prints `disarm: true`. |
| `verify` | The same checks `advance` runs. |
