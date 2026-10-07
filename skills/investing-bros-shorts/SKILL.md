---
name: investing-bros-shorts
description: >-
  Make vertical shorts (Reels / YouTube Shorts / TikTok) from an Investing
  Bros / אחים להשקעות episode, with burned-in Hebrew captions. Use when Amitai
  asks for "shorts", "clips", "reels", "רילס" or "קליפים" for episode N.
---
# Investing Bros shorts

Load `investing-bros-show` first.

## When to use
After post-production for episode N, when Amitai asks for shorts.

## Inputs
From the episode's `extras/` folder:
- `segments.json` — the transcript
- the raw master — `.mp4` if the recording has video, otherwise `.m4a`

For audio-only recordings, also the show cover (location in `investing-bros-show`).

Times are on the raw timeline, the same one as `segments.json`. To tell Amitai where a moment is in the published episode, subtract `start` from `edit.json`.

## Steps
1. **Pick moments with Amitai.** Propose 4–6: start–end, the opening line, why it works. Wait for his picks (usually 3–5). A good short:
   - hooks in the first 3 seconds (a claim, a number, a question — not "אז…")
   - makes sense without the episode
   - is one idea, 20–60 seconds, and ends cleanly
   Skip crosstalk and anything that sounds like a buy/sell call out of context. Flag on-air mistakes instead of clipping them.
2. **Captions** for each pick:
   ```bash
   python3 scripts/clip_captions.py segments.json START END short-01.ass
   ```
   Proofread the text against the audio — whisper gets names and numbers wrong. If the short names a stock with a view, add a last caption line `אין כאן המלצת השקעה`.
3. **Render** (1080×1920):
   ```bash
   scripts/make_clip.sh --source raw.mp4 --start START --end END --captions short-01.ass short-01-<slug>.mp4
   # audio-only: --source raw.m4a --cover show-cover.png
   ```
4. **Check a frame** (`ffmpeg -ss 2 -i short-01-<slug>.mp4 -frames:v 1 check.png`): captions readable and right-to-left, not covering faces.

## Hand back
Upload the shorts to the episode's `promo/` folder. Send Amitai the folder link and one line per short: where it is in the episode, its length, and its opening line.

## Never
- Post anywhere — Amitai posts.
- Put words on screen the hosts didn't say, or captions you haven't proofread.
- Add music or stock footage unless Amitai supplies it.
