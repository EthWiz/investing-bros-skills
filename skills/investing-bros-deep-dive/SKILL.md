---
name: investing-bros-deep-dive
description: >-
  Cut the ~20 min deep-dive segment of every Investing Bros / אחים להשקעות
  episode into its own standalone YouTube video with a search-first title,
  its own description (links the full episode + Spotify line), its own
  thumbnail, uploaded Private to the אחים להשקעות channel, Public after
  Amitai's OK, and linked back from the full episode. Required every episode.
  Use when Amitai asks for "deep dive video", "צלילה לעומק", "סרטון נפרד",
  "standalone deep dive" or when publishing episode N.
---
# Investing Bros deep-dive video

The deep dive (one company, one topic, one question, ~20 min) is the show's most searchable content. A 40 min episode doesn't rank for "<company> + question"; a focused video does. **Every episode gets one.** It replaces the optional mid-form highlight when they'd be the same stretch.

Load `investing-bros-show` (naming, Drive tree, approvals) and `investing-bros-brand` (look) first.

## Inputs
The edited episode video (`video/פרק-N-וידאו.mp4`) or its source, the transcript and `edit.json` from `investing-bros-post-production`, the chapters in `תיאור-פרק-N.txt`, the `brief/` deep-dive doc.

## Steps
1. **Pick the segment.** From the chapters/transcript, the deep-dive start to its end (usually ~20 min). Start and end on sentence boundaries (`find_cuts.py` in `investing-bros-shorts`). Skip the news intro and investment ideas. Drop any part being re-recorded. Tell Amitai the in/out times.
2. **Cut.** Full frame 16:9, same brand look as the episode (logo, colors, lower thirds from `investing-bros-brand`); never zoomed or reframed. No cold open or episode intro; a 2–5 s branded title card is fine. Use `trim.sh` from `investing-bros-post-production` with the in/out times; keep the audio loudness of the episode.
3. **Chapters** inside it when it has 3+ sub-topics: rebase the episode chapters to 00:00 (`shift_after_cut.py`), time first, Hebrew first word, ≥30 s apart; first chapter `00:00`.
4. **Title (search-first).** Keyword up front: the company/topic name, then the question the brothers answer. Hebrew, question-led, no clickbait, no en/em dash. May differ from the episode title and does **not** carry `פרק N -`. Examples: `אנרגיה גרעינית: מי יספק את החשמל ל-AI?`, `זהב: מה באמת מגבה את הכסף שלך?`. Add the English name if people search for it (`Tesla`, `SpaceX`) but start the line with a Hebrew word. Make the RTL copy with `rtl_fix.py --title` (in `investing-bros-episode-upload`); YouTube gets the plain text. Amitai picks from 2–3 options.
5. **Description.** Hook paragraph (≤450 chars, starts with Hebrew, includes the search keywords), `לפרק המלא: <full-episode YouTube URL>`, the disclaimer, then the `האזינו בספוטיפיי:` line (after the disclaimer, before the chapters, same rules as the episode), then chapters. Run `check_copy.py --youtube` (in `investing-bros-title-description`).
6. **Thumbnail.** 16:9 1280×720 from `investing-bros-brand`, headline = the topic keyword (2–4 words). Save to the episode Drive folder.
7. **Files** in `deep-dive/`: `צלילה-פרק-N-<נושא>.mp4`, `צלילה-פרק-N-<נושא>.txt` (title, description), `צלילה-פרק-N-<נושא>-thumb.jpg`, and `youtube-צלילה.md` (status, URL).
8. **Upload Private** to the **אחים להשקעות** channel (Studio: Switch account from the personal Grok Bot channel first; or `yt_upload.py`), not made for kids, with title, description, thumbnail. Follow `investing-bros-episode-upload` step 3.
9. **Publish** only after Amitai's explicit OK: switch to Public. Order: after the full episode is Public (its URL goes in this description), before the shorts. Then edit the full episode's YouTube description to add `הצלילה לעומק כסרטון נפרד: <deep-dive URL>` (after the disclaimer, next to the Spotify line), and update `video/תיאור-פרק-N-youtube.txt`. Swapping the Spotify show link for the episode link applies here too.

## Done when
- `deep-dive/` has the `.mp4`, `.txt`, `-thumb.jpg` and `youtube-צלילה.md`.
- The video is Private on אחים להשקעות (before the OK) / Public (after), and the full episode's description links it.

## Hand back
In/out times, length, title options, the Private URL, and anything still waiting on Amitai.
