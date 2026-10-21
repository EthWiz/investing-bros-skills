---
name: investing-bros-segment-video
description: >-
  Cut a standalone segment of an Investing Bros / אחים להשקעות episode into
  its own search-first YouTube video: one topic, one question. Types: deep
  dive (required every episode), investment idea, interview, explainer, etc.
  Covers segment selection, full-frame cut, search-first title, description
  linking the full episode + Spotify line, thumbnail, Private upload to the
  אחים להשקעות channel, Public after Amitai's OK, and linking back from the
  full episode. Use when Amitai asks for a "segment video", "deep dive video",
  "צלילה לעומק", "סרטון נפרד", or when publishing episode N.
---
# Investing Bros segment videos

A **segment video** is one continuous stretch of an episode published as its own YouTube video, built so people find it in search. A 40 min episode doesn't rank for "<company> + question"; a focused segment does.

## Types
| Type | Length | When |
|---|---|---|
| **Deep dive** | ~20 min | **Every episode, required.** One company/topic/question. |
| Investment idea | ~5 min | When a host's idea stands alone (Amitai picks). |
| Interview | varies | When the episode has a guest. |
| Explainer | 5–15 min | A concept explained cleanly (e.g. tokenization). |
| Other | — | Anything Amitai names. |

Short 5–10 min highlights that are not one of these stay mid-form (`investing-bros-shorts`).

Load `investing-bros-show` (naming, Drive tree, approvals) and `investing-bros-brand` (look) first.

## Inputs
The edited episode video (`video/פרק-N-וידאו.mp4`) or its source, the transcript and `edit.json` from `investing-bros-post-production`, the chapters in `תיאור-פרק-N.txt`, the `brief/` docs.

## Steps (same for every type)
1. **Pick the segment.** Its start to its end from the chapters/transcript, on sentence boundaries (`find_cuts.py` in `investing-bros-shorts`). Drop any part being re-recorded. Tell Amitai the in/out times.
2. **Cut.** Full frame 16:9, same brand look as the episode (`investing-bros-brand`); never zoomed or reframed. No cold open or episode intro; a 2–5 s branded title card is fine. Use `trim.sh` (`investing-bros-post-production`); keep the episode loudness.
3. **Chapters** when it has 3+ sub-topics: rebase to 00:00 (`shift_after_cut.py`), time first, Hebrew first word, ≥30 s apart.
4. **Title (search-first).** Keyword up front (company/topic/guest), then the question. Hebrew, no clickbait, no en/em dash, no `פרק N -`; may differ from the episode title. E.g. `זהב: מה באמת מגבה את הכסף שלך?`. An English name (`Tesla`) may appear, but the line starts with Hebrew. RTL copy via `rtl_fix.py --title` (`investing-bros-episode-upload`); YouTube gets plain text. Offer Amitai 2–3 options.
5. **Description.** Hook (≤450 chars, starts with Hebrew, has the search keywords), `לפרק המלא: <full-episode YouTube URL>`, disclaimer, the `האזינו בספוטיפיי:` line (after the disclaimer, before chapters, same rules as the episode), chapters. `check_copy.py --youtube`.
6. **Thumbnail.** 16:9 1280×720 from `investing-bros-brand`, headline = the topic keyword (2–4 words). Save in the episode Drive folder.
7. **Files** in `segments/`: `סגמנט-NN-<סוג>-<נושא>.mp4`, `.txt` (title, description), `-thumb.jpg`, `youtube-סגמנט-NN.md` (type, status, URL). The deep dive is `סגמנט-01-צלילה-<נושא>`.
8. **Upload Private** to **אחים להשקעות** (Studio: Switch account off the personal Grok Bot channel first; or `yt_upload.py`), not made for kids, with title, description, thumbnail. See `investing-bros-episode-upload` step 3.
9. **Publish** only after Amitai's explicit OK. Order: after the full episode is Public, before the shorts. Then add to the full episode's YouTube description (after the disclaimer, by the Spotify line) one line per segment, e.g. `הצלילה לעומק כסרטון נפרד: <URL>`, and update `video/תיאור-פרק-N-youtube.txt`. The Spotify show-to-episode link swap applies here too.

## Done when
- `segments/` has the deep dive (and any other segments asked for), each with `.mp4`, `.txt`, `-thumb.jpg`, `youtube-סגמנט-NN.md`.
- Each is Private on אחים להשקעות before the OK / Public after, and the full episode's description links it.

## Hand back
Per segment: type, in/out, length, title options, Private URL, anything waiting on Amitai.
