---
name: investing-bros-segment-video
description: >-
  Cut a standalone segment of an Investing Bros / אחים להשקעות episode into
  its own search-first YouTube video: one topic, one question. Types: deep
  dive (required every episode), investment idea, interview, explainer, etc.
  Covers segment selection, full-frame cut, search-first title, description
  linking the full episode + Spotify line, thumbnail, on-screen nudge + card, Unlisted
  evaluation upload to the אחים להשקעות channel, Public after Amitai's OK, and linking back from the
  full episode. Use when Amitai asks for a "segment video", "deep dive video",
  "צלילה לעומק", "סרטון נפרד", or when publishing episode N.
---
# Investing Bros segment videos

A **segment video** is one stretch of an episode published as its own YouTube video, built so people find it in search. A 40 min episode doesn't rank for "<company> + question"; a focused segment does.

**Length: ~7 min, 10 min max.** A segment answers **one self-contained sub-question** of the topic, not the whole deep dive (a 36 min deep dive cut whole defeats the purpose). It opens with a clear hook (the question, said on camera) in the first 15–20 s and ends on a payoff (the answer / takeaway). A long deep dive can yield several segment videos, one per sub-question.

## Types
| Type | Length | When |
|---|---|---|
| **Deep dive** | ~7 min, max 10 | **Every episode, required (at least one).** The single most searchable sub-question of the deep dive (e.g. "why are central banks buying gold?"); more sub-questions → more segment videos. |
| Investment idea | ~5–7 min | When a host's idea stands alone (Amitai picks). |
| Interview | ~7 min, max 10 | One question/answer thread from a guest. |
| Explainer | ~7 min, max 10 | A concept explained cleanly (e.g. tokenization). |
| Other | — | Anything Amitai names. |

Short 5–10 min highlights that are not one of these stay mid-form (`investing-bros-shorts`).

Load `investing-bros-show` (naming, Drive tree, approvals) and `investing-bros-brand` (look) first.

## Inputs
The edited episode video (`video/פרק-N-וידאו.mp4`) or its source, the transcript and `edit.json` from `investing-bros-post-production`, the chapters in `תיאור-פרק-N.txt`, the `brief/` docs.

## Steps (same for every type)
1. **Pick the segment.** Read the transcript of the whole topic and list its sub-questions; pick the most appealing, searchable, self-contained one that fits ~7 min (max 10). It must start with the hook (the question) and end on the payoff. Contiguous preferred; at most 1–2 internal cuts (a tangent, a detour), each on a sentence boundary in a pause (`find_cuts.py` in `investing-bros-shorts`, `trim.sh --cut`). Drop any part being re-recorded. Tell Amitai the in/out times, the length, and 1 alternative sub-question (times + one line).
2. **Verify** the cut file: transcribe its first and last ~20 s and check the hook and payoff are intact and no word is clipped at a join.
3. **Cut.** Full frame 16:9, same brand look as the episode (`investing-bros-brand`); never zoomed or reframed. No cold open or episode intro; a 2–5 s branded title card is fine. Use `trim.sh` (`investing-bros-post-production`); keep the episode loudness.
4. **Chapters** only when it has 3+ sub-topics: rebase to 00:00 (`shift_after_cut.py`), time first, Hebrew first word, ≥30 s apart.
5. **Title (search-first).** Keyword up front (company/topic/guest), then the one sub-question the video answers. Hebrew, no clickbait, no en/em dash, no `פרק N -`; may differ from the episode title. E.g. `זהב: מה באמת מגבה את הכסף שלך?`. An English name (`Tesla`) may appear, but the line starts with Hebrew. RTL copy via `rtl_fix.py --title` (`investing-bros-episode-upload`); YouTube gets plain text. Offer Amitai 2–3 options.
6. **Description.** Hook (≤450 chars, starts with Hebrew, has the search keywords), `לפרק המלא: <full-episode YouTube URL>`, disclaimer, the `האזינו בספוטיפיי:` line (after the disclaimer, before chapters, same rules as the episode), chapters. `check_copy.py --youtube`.
7. **Thumbnail.** 16:9 1280×720 from `investing-bros-brand`, headline = the topic keyword (2–4 words). Save in the episode Drive folder.
8. **Files** in `segments/`: `סגמנט-NN-<סוג>-<נושא>.mp4`, `.txt` (title, description), `-thumb.jpg`, `youtube-סגמנט-NN.md` (type, status, URL). The deep dive is `סגמנט-01-צלילה-<נושא>`.
9. **Full-episode nudge (burned in).** Design C, from the 1080p segment source: cream `#FBEEDF` torn strip `לפרק המלא` above a mustard `#FCAF02` torn strip `לחצו כאן`, text `#011526`, Rubik Black ~60px at 1080p, soft drop shadow, plus a large mustard up-arrow with navy outline that bounces gently (~12px @ 1.5 Hz). **Right side** (~50px from the right edge), **below YouTube's card teaser** (top-right on Amitai's player): the arrow, bounce included, stays below y≈200 so the card never covers it. Visible 30.0–35.0 s in sync with the card, 0.3 s fade, slides in from the right. Keep spacing compact; check a frame at 0:31 that it doesn't cover a host's eyes (shrink/tuck if it does) and show Amitai the frame before uploading. If it still covers part of a host's face, show him the frame; he may accept it as is (accepted on ep8, 2026-10-22). Generate the overlay with [scripts/nudge_overlay.py](scripts/nudge_overlay.py) (reference: `assets/nudge-overlay.png`), then burn with ffmpeg overlay `enable='between(t,30,35)'`, `-crf 18`, `-c:a copy`.
10. **Upload** to **אחים להשקעות** (or `yt_upload.py`), not made for kids, with title, description, thumbnail. See `investing-bros-episode-upload` step 3. Studio may open on the personal "Grok Bot" channel and drop `authuser`: always confirm the header shows אחים להשקעות before editing (direct URL `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw?authuser=1`). **Evaluation uploads go up Unlisted** (end screens don't show on Private). YouTube can't replace a video file, so any visual change = a new upload + re-adding card and end screen.
11. **Link back to the full episode** (Studio → Editor; click-path in `investing-bros-episode-upload` [references/youtube-studio.md](../investing-bros-episode-upload/references/youtube-studio.md#segment-videos-cards-end-screen-pinned-comment)):
   - **Card:** exactly ONE Video card to the full episode at 0:30 (in sync with the nudge). YouTube rejects a second card to the same video. Set BOTH custom message and teaser text to `לפרק המלא`; never leave them blank (a blank teaser shows the full long title, which gets cut off). To pick the target, paste the full-episode URL into **Search videos from other channels** in the card picker (searching your own videos by URL returns nothing); verify title + thumbnail.
   - **Verify** after saving: open the watch page fresh, check around 0:30 that the teaser appears and the card links to the full-episode video ID.
   - **End screen** over the last 20 s: the full episode as a video element + a Subscribe element.
   - **Pinned comment** once Public, posted as the channel **אחים להשקעות** (not Grok Bot), then pinned: `לפרק המלא על <short topic> 👈 https://youtu.be/<full-episode ID>`.
   The card and end screen go in while Private (the full episode may be Private too); the pinned comment after Public. Report which were done.
12. **Publish** only after Amitai's explicit OK: flip Unlisted → Public. Order: after the full episode is Public, before the shorts. Then edit the full episode's YouTube description: insert on its own line, after the Spotify line + a blank line and directly before the `00:00` chapter line, `🎬 קטע נבחר: <segment title> https://youtu.be/<segment ID>` (one line per segment). Change nothing else in the description. Update `video/תיאור-פרק-N-youtube.txt` to match. The Spotify show-to-episode link swap applies here too.

## Done when
- `segments/` has the deep dive (and any other segments asked for), each with `.mp4`, `.txt`, `-thumb.jpg`, `youtube-סגמנט-NN.md`.
- Each has the card and end screen (and, once Public, the pinned comment) pointing to the full episode.
- Each has the nudge at 0:30–0:35 and is Unlisted/Private on אחים להשקעות before the OK / Public after, and the full episode's description links it.

## Hand back
Per segment: type, sub-question, in/out (and any internal cuts), length (≤10 min), alternative sub-question, title options, Unlisted URL, 0:31 nudge frame, anything waiting on Amitai.
