---
name: investing-bros-segment-video
description: >-
  Cut exactly two standalone, search-first YouTube segments from each
  Investing Bros / אחים להשקעות episode: 01 a deep-dive sub-question, 02 the
  next-best one or another strong topic. Selection, make_segment.py (cut,
  nudge, loudness, sync), title, description, thumbnail, card, end screen and
  the Private upload. Use for "segment video", "deep dive video", "צלילה
  לעומק", "סרטון נפרד".
---
# Investing Bros segment videos

A **segment video** is one stretch of an episode published as its own YouTube video, built so people find it in search. A 40 min episode doesn't rank for "<company> + question"; a focused segment does.

**Standing count: exactly two per episode.** `סגמנט-01` is always the strongest searchable, self-contained sub-question from the deep dive. `סגמנט-02` is the next-best self-contained sub-question from that deep dive; when no second deep-dive stretch is strong enough on its own, use the strongest other self-contained episode topic (investment idea, interview, explainer or another topic). Do not use the whole deep dive merely to fill the count.

**Length: ~7 min each, 10 min max.** Each segment answers **one self-contained sub-question** of the topic, not the whole deep dive (a 36 min deep dive cut whole defeats the purpose). It opens with a clear hook (the question, said on camera) in the first 15–20 s and ends on a payoff (the answer / takeaway).

## Types
| Type | Length | When |
|---|---|---|
| **Deep dive** | ~7 min, max 10 | **Segment 01 every episode.** Use the single most searchable sub-question of the deep dive (e.g. "why are central banks buying gold?"). Prefer the next-best qualifying deep-dive sub-question for segment 02. |
| Investment idea | ~5–7 min | Eligible for segment 02 when it is stronger and more self-contained than the remaining deep-dive sub-questions. |
| Interview | ~7 min, max 10 | Eligible for segment 02: one question/answer thread from a guest. |
| Explainer | ~7 min, max 10 | Eligible for segment 02: a concept explained cleanly (e.g. tokenization). |
| Other | — | Eligible for segment 02 when it is the strongest self-contained remaining topic. |

Short 5–10 min highlights that are not one of these stay mid-form (`investing-bros-shorts`).

Load `investing-bros-show` (naming, Drive tree, approvals) and `investing-bros-brand` (look) first.

**Helper rule** (`investing-bros-show` → Ownership and contact): report to the episode's Producer, never to the hosts directly; wherever this skill says "tell the owner", "offer the owner" or "show the owner", put it in your hand-back and the Producer batches it into one review for the episode owner. You contact the owner yourself only when no Producer runs the episode. Superseded Private uploads of a segment are deleted once the replacement is verified (list the IDs).

## When to use
After the audio edit (the transcript and `edit.json` exist), for both standing segments of every episode; again to fix or re-upload one, and when publishing the episode (step 12).

## Inputs
The full video episode (`video/פרק-N-וידאו.mp4`, with its teaser + intro length from the assembly log) or the raw master video, the transcript and `edit.json` from `investing-bros-post-production`, the chapters in `תיאור-פרק-N.txt`, the `brief/` docs.

## Steps (same for every type)
1. **Pick both segments as one batch.** Read the transcript of the whole deep dive and list its sub-questions. Assign the strongest qualifying one to segment 01. Assign the next-best qualifying deep-dive sub-question to segment 02; only if none is strong and self-contained enough, compare the other episode topics and choose the strongest qualifying one. Each pick must be appealing, searchable and self-contained, fit ~7 min (max 10), start with the hook (the question) and end on the payoff. Contiguous preferred; at most 1–2 internal cuts (a tangent, a detour), each on a sentence boundary in a pause (`find_cuts.py` in `investing-bros-shorts`, `trim.sh --cut`). Drop any part being re-recorded. Tell the owner both in/out ranges and lengths, plus one alternative for segment 02 (times + one line).
   Run steps 2–12 independently for both selected segments; neither one is a partial or optional deliverable.
2. **Verify** the cut file: transcribe its first and last ~20 s and check the hook and payoff are intact and no word is clipped at a join.
3. **Cut, nudge, loudness, sync, files: `scripts/make_segment.py`.** Ranges are **raw transcript seconds** (the `segments.json` timeline), whatever the source; the script maps them with `edit_map.py`, refuses a range that crosses one of the episode's internal cuts unless `--allow-cut`, cuts picture and sound in one pass (`render_cuts.py`), checks `verify_sync.py` = `SYNC OK`, burns the nudge (step 9) and sets the episode loudness (−16 LUFS, true peak ≤ −1.5 dBTP) in one encode, checks sync again, and writes the package in `segments/` plus its record `extras/segment-NN.json`:
   ```bash
   python3 scripts/make_segment.py "$EP" --slot 01 --type צלילה --topic זהב --range 1203.4-1650.0 [--drop A-B] \
     --source "$EP/video/פרק-N-וידאו.mp4" --source-type assembled --offset <teaser+intro s> \
     --title-file title.txt --description-file desc.txt --thumb <selected -thumb.jpg>     # --dry-run first
   ```
   (`--source-type raw` with the raw master video needs no offset.) Full frame 16:9, same brand look as the episode (`investing-bros-brand`); never zoomed or reframed. No cold open or episode intro/outro; the canonical clip is only for the full episode.
4. **Chapters** only when it has 3+ sub-topics: rebase to 00:00 (`shift_after_cut.py`), time first, Hebrew first word, ≥30 s apart.
5. **Title (search-first).** Keyword up front (company/topic/guest), then the one sub-question the video answers. Hebrew, no clickbait, no en/em dash, no `פרק N -`; may differ from the episode title. E.g. `זהב: מה באמת מגבה את הכסף שלך?`. An English name (`Tesla`) may appear, but the line starts with Hebrew. RTL copy via `rtl_fix.py --title` (`investing-bros-episode-upload`); YouTube gets plain text. Offer the owner 2–3 options.
6. **Description.** Hook (≤450 chars, starts with Hebrew, has the search keywords), `לפרק המלא: <full-episode YouTube URL>`, disclaimer, the `האזינו בספוטיפיי:` line (after the disclaimer, before chapters, same rules as the episode), chapters. `check_copy.py --youtube`.
7. **Thumbnail.** 16:9 1280×720 from `investing-bros-brand`, headline = the topic
   keyword (2–4 words). Supply each host's frame from this same episode recording; the
   frames may come from anywhere in the episode and do not have to come from this
   segment. Never use portraits from another episode. Until Amitai says the design is
   dialed in, the three options come from `investing-bros-brand`. Put option A on the
   Private upload; round 2 picks (`investing-bros-episode-upload` step 3). Promote the
   chosen file onto `-thumb.jpg`, then `yt_upload.py --set-thumbnail`.
8. **Files** in `segments/`: `סגמנט-NN-<סוג>-<נושא>.mp4`, `.txt` (title, description), `-thumb.jpg`, `youtube-סגמנט-NN.md` (type, status, URL). The required deep dive is `סגמנט-01-צלילה-<נושא>`; the second deliverable is `סגמנט-02-<סוג>-<נושא>`. To deliver final segment videos from the box to Amitai, use the verified 10–20 MB chunked `CopyFromBox` handoff to `~/Downloads` (show conventions → references/environment.md → Delivering files); Amitai can drag each verified reassembled file to Drive.
9. **Full-episode nudge (burned in).** Design C, from the 1080p segment source: cream `#FBEEDF` torn strip `לפרק המלא` above a mustard `#FCAF02` torn strip `לחצו כאן`, text `#011526`, Heebo Black ~60px at 1080p, soft drop shadow, plus a large mustard up-arrow with navy outline that bounces gently (~12px @ 1.5 Hz). **Right side** (~50px from the right edge), **below YouTube's card teaser** (top-right on Amitai's player): the arrow, bounce included, stays below y≈200 so the card never covers it. Visible 30.0–35.0 s in sync with the card, 0.3 s fade, slides in from the right. Keep spacing compact; check a frame at 0:31 that it doesn't cover a host's eyes (shrink/tuck if it does) and show the owner the frame before uploading. Generate the overlay with `python3 scripts/nudge_overlay.py --font fonts/Heebo-Black.ttf` (reference: `assets/nudge-overlay.png`); `make_segment.py` burns it at 30.0–35.0 s with a 0.3 s fade (`-crf 18`).
10. **Upload** to **אחים להשקעות** (or `yt_upload.py`), not made for kids, with title, description and option A as the thumbnail. Thumbnail timing and the later swap are `investing-bros-episode-upload` step 3. Studio defaults to the personal "Grok Bot" channel, and direct edit links load as Grok Bot: open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos`, confirm אחים להשקעות is active in the avatar menu, and click into the video from that list (check again on every edit page). **Evaluation uploads stay Private** (Amitai, 2026-11-05: Nadav owns the channel, so Private is enough; cards/end screens to the Private episode work). YouTube can't replace a video file, so any visual change of the video = a new upload + re-adding card and end screen. Swapping only the thumbnail is `--set-thumbnail`.
11. **Link back to the full episode** (Studio → Editor; click-path in `investing-bros-episode-upload` → `references/youtube-studio.md` → "Segment videos: cards, end screen"):
   - **Card:** exactly ONE Video card to the full episode at 0:30 (in sync with the nudge). YouTube rejects a second card to the same video. Set BOTH custom message and teaser text to `לפרק המלא`; never leave them blank (a blank teaser shows the full long title, which gets cut off). To pick the target, paste the full-episode URL into **Search videos from other channels** in the card picker (searching your own videos by URL returns nothing); verify title + thumbnail.
   - **Verify** after saving: open the watch page fresh, check around 0:30 that the teaser appears and the card links to the full-episode video ID.
   - **End screen** over the last 20 s: the full episode as a video element + a
     Subscribe element. This segment-specific link-back stays unchanged; the
     previous-episode end screen over the canonical outro belongs only to the full
     episode.
   - **No pinned comment** (Amitai, 2026-11-01): the description, card and end screen carry the link.
   The card and end screen go in while Private (the full episode may be Private too). Report which were done.
12. **Publish** only after the episode owner's explicit OK. Order: after the full episode is Public, before the shorts. The Spotify show-to-episode link swap applies to the segment description too. Do not add the segment URL to the full episode's description.

## Done when
- `segments/` has **exactly two** complete packages: segment 01 is the required deep-dive sub-question and segment 02 is the next-best qualifying deep-dive sub-question or strongest other self-contained topic. Each has `.mp4`, `.txt`, `-thumb.jpg` and `youtube-סגמנט-NN.md`, and `extras/segment-NN.json` records it (`SYNC OK`).
- Each has the description link, card and end screen pointing to the full episode.
- Each has the nudge at 0:30–0:35 and is Private on אחים להשקעות before the OK / Public after.

## Hand back
For segments 01 and 02: type, sub-question, in/out (and any internal cuts), length (≤10 min), segment 02's alternative, title options, Private URL, 0:31 nudge frame, card/end-screen status, Drive status, the `make_segment.py` record (`extras/segment-NN.json`) and anything waiting on the episode owner.

## Never
- Cut a segment by hand or splice its sound separately; use `make_segment.py` (one-pass cut, `SYNC OK`).
- Give `make_segment.py` edited-episode or video times: ranges are raw transcript seconds.
- Cross one of the episode's internal cuts without `--allow-cut` and a reason in the hand-back.
- Leave two final videos for one slot in `segments/`, or a package missing its `.txt`, `-thumb.jpg` or `youtube-סגמנט-NN.md`.
- Upload anything but Private, or make a segment Public before the full episode and without the episode owner's OK.
- Message a host directly while a Producer runs the episode.
- Write your own render, cut or upload code (`investing-bros-show` → Working rules).
