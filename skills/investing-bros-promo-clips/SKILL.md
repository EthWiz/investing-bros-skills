---
name: investing-bros-promo-clips
description: >-
  Make promo video from an edited Investing Bros / אחים להשקעות episode:
  vertical shorts (Reels / YouTube Shorts / TikTok) and a 30–60 s teaser, with
  burned-in Hebrew captions, from the recording video or as audiograms over the
  cover art. Use when Amitai asks for "shorts", "clips", "a teaser",
  "trailer", "רילס", "טיזר" for episode N.
---
# Investing Bros promo clips

Load `investing-bros-show` first. Formats and editorial rules per output:
- Shorts → [references/shorts.md](references/shorts.md)
- Teaser → [references/teaser.md](references/teaser.md)

## When to use
After post-production for episode N is done (edited audio and transcript exist). Promo is optional — only when Amitai asks.

## Inputs (all from post-production)
| Input | Where |
|---|---|
| Transcript `segments.json` (raw timeline) | `extras/` or local `$EP/transcript/` |
| Raw master: `investing-bros-episode-raw-untrimmed.mp4` (video) or `.m4a` (audio-only) | `extras/` or `$EP/` |
| `edit.json` (raw → edited offset) | `extras/` or `$EP/` |
| Show cover art (audiograms only) | Ask Amitai where it lives if `investing-bros-show` doesn't say |

**Times:** cut from the **raw** files with **raw** times from `segments.json` — no conversion needed. Only when you tell Amitai where a moment is in the published episode, convert: `edited = raw − start` (`start` from `edit.json`).

Tools: `ffmpeg` built with libass (`ffmpeg -filters | grep subtitles`), Python 3, a Hebrew font (Heebo or Rubik recommended; the scripts auto-detect any installed font with Hebrew; override with `clip_captions.py --font-family NAME` and, if the font isn't installed, `make_clip.sh --fonts-dir DIR`).

## Steps

### 1. Pick moments — and get them approved
Read the transcript and propose candidates to Amitai **before cutting**: for each, raw start–end, edited time, the hook line, and one line on why it works. Rules in the format reference. Wait for his picks; don't cut a dozen clips speculatively.

### 2. Captions
For each approved moment:
```bash
python3 scripts/clip_captions.py segments.json START END clip1.ass --format vertical
```
Writes Hebrew captions for just that range, shifted to start at 0, wrapped and sized for the format. **Proofread the `.ass` text against the audio** — whisper mishears names and numbers; fix the text lines in the file. Keep brand spellings (ספייסאקס).

### 3. Render
```bash
# from the recording video
scripts/make_clip.sh --source raw.mp4 --start START --end END --format vertical --captions clip1.ass clip1.mp4
# audio-only recording → audiogram over the cover
scripts/make_clip.sh --source raw.m4a --cover cover.png --start START --end END --format vertical --captions clip1.ass clip1.mp4
# teaser: render each moment (same --format) then join
scripts/make_teaser.sh teaser.mp4 clip1.mp4 clip2.mp4 clip3.mp4
```
Check one frame of each clip (`ffmpeg -ss 2 -i clip1.mp4 -frames:v 1 check.png`) — captions readable, right-to-left, not covering faces.

### 4. File and hand back
- Upload finished clips to the episode's `promo/` folder (create it if missing). Working files (`.ass`, frames) go in `extras/` or get deleted.
- Report to Amitai: Drive link to `promo/`, one line per clip (edited time, length, hook line). If he wants the brothers to see them, hand the `promo/` link to the WhatsApp owner for `אחים להשקעות` with the show tag.

## Never
- Post clips to any platform — the agent prepares files, Amitai (or whoever he names) posts.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Add music or stock footage unless Amitai supplies it.
- Use `extras/` raw audio as the published episode — clips only.
