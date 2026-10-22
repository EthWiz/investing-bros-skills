# YouTube Studio checklist

The preferred upload path is the YouTube Data API ([youtube-api.md](youtube-api.md)); this checklist is the fallback for uploads and is always used for the steps the API leaves to Studio (visibility change after Amitai's OK, Related video, captions, chapters check).

Use the browser profile for the Editor account named in `investing-bros-show`.

## Before selecting a file
1. The upload account `investingbros.grokbot@gmail.com` is a **manager** of the
   channel, not its owner. `studio.youtube.com/?authuser=1` opens its own empty
   **Grok Bot** channel by default.
2. Avatar (top right) → **Switch account** → **אחים להשקעות**. Verify the URL shows
   `/channel/UCWIlggXQNDFiyJghl6VB6Xw` and the channel name before any upload or
   edit. Re-check after every reload or new tab.
3. **Feature eligibility** (Settings → Channel → Feature eligibility): all three tiers
   must be **Enabled**. Intermediate features (owner phone verification, done by
   Nadav/Amitai, not the manager) unlock videos over 15 minutes, custom thumbnails
   and clickable links in descriptions. If a tier isn't enabled, report it; a
   manager can't verify.

## Details
- Paste the approved title and the YouTube description as plain text, with no
  RedCircle RTL marks.
- Audience: **No, it's not made for kids**.
- Visibility: **Private** until Amitai explicitly approves publication.
- Video language: Hebrew.
- Thumbnail: use only the approved final `promo/thumbnail-פרק-N.jpg` (16:9, from the square cover). If the custom-thumbnail
  control is unavailable, report the channel-verification blocker.
- Altered-content answer: answer truthfully for the video. A generated thumbnail
  alone does not make a real-recording episode altered video content.
- Leave episode-specific tags, category, playlist, cards and recording location
  unchanged unless Amitai supplied them or the channel already has an established
  default. Do not invent metadata.

## Checks and elements
- Wait for YouTube's copyright check. Report a claim; do not dispute it.
- Add an end screen only when a suitable published episode, playlist or subscribe
  target exists.
- Thumbnail, title and description go in before saving.
- While HD processes the row shows **Pending**/processing and the watch page may be
  SD only; that's normal, wait before reporting quality.
- Make Public only after Amitai's explicit OK.
- **Shorts → Related video:** the picker currently answers "No matching results" for
  every search. Retry later; don't block the upload on it, and report it.
- Save as **Private**, then confirm the Studio row says Private and HD processing
  finishes.
- Open the private watch page as the Editor and check title, description direction,
  increasing chapter times, the `00:00` teaser chapter and the progress-bar chapters.

## Segment videos: cards, end screen, pinned comment
On the אחים להשקעות channel (Switch account first), Content → the segment video → **Editor** (left menu).
- **Cards:** Editor → **Cards** (ⓘ) → **Video** → pick the full episode (search its title, or *Choose a specific video* → paste the URL) → set **Custom message** `לפרק המלא` and **Teaser text** `צפו בפרק המלא` → drag the card on the timeline to ~0:30. Repeat for a second card at ~2/3 of the runtime (or at a natural "in the episode" mention). **Save**.
- **End screen:** Editor → **End screen** → **+ Element** → **Video** → *Choose specific video* → the full episode; **+ Element** → **Subscribe**. On the timeline, make both run over the last 20 s (end screens can be 5–20 s and need a video ≥25 s). Arrange so they don't cover faces. **Save**.
- **Pinned comment** (after Public only): open the watch page as the channel (avatar = אחים להשקעות), comment `לפרק המלא: <full-episode URL>` → ⋮ on the comment → **Pin** → confirm. Or Studio → Comments → the video → ⋮ → Pin.
- Check: watch page shows the ⓘ teaser at ~0:30 and the end screen in the last 20 s.
