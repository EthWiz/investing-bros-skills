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

## While a file uploads
- Upload the compressed copy (`compress_for_youtube.sh`, about 1 GB), not the master.
- Do not reload the Studio tab, open another page in it or close the dialog until the
  upload reaches 100% and processing starts. If the browser shows **Leave site?**,
  press **Cancel**.
- Copy the new video link from Studio's upload dialog (or the Content row's ⋮ → Get
  shareable link); never type it.

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
- For a Short, use its approved cover title unchanged as both the YouTube title and
  the first line of the description. Do not append emoji, hashtags or an episode label
  to the title. Never add a disclosure, holdings statement, number or claim that was
  not stated in the episode.

## Checks and elements
- Wait for YouTube's copyright check. Report a claim; do not dispute it.
- The full episode always gets the end screen below over its canonical outro.
- Thumbnail, title and description go in before saving.
- While HD processes the row shows **Pending**/processing and the watch page may be
  SD only; that's normal, wait before reporting quality.
- Make Public only after Amitai's explicit OK.
- **Shorts → Related video (hard rule):** set it to the full episode, Save, then reopen
  the edit page and confirm the field shows the episode. A link in the description does
  NOT count. The picker has answered "No matching results" (episode 9): retry with the
  title, then the URL, then after reloading Studio. The Private upload may continue, but
  if the field still can't be set the Short stays Private and you report the failure.
  Never publish a Short with only a description link (`investing-bros-publish`).
  **Known failure mode:** the `investingbros.grokbot` account (Studio Manager) sees an EMPTY Related video picker ("No matching results" for the episode URL, ID and title alike). When that happens, keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Send them the direct edit link for each Short, `https://studio.youtube.com/video/<SHORT_ID>/edit`, and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`). After they say it's done, reopen each edit page yourself and check that the field shows the episode before ticking it.
- Save as **Private**, then confirm the Studio row says Private and HD processing
  finishes.
- Open the private watch page as the Editor and check title, description direction,
  increasing chapter times, the `00:00` teaser chapter and the progress-bar chapters.

## Full episode: previous episodes end screen
Content → the full episode → **Editor** → **End screen**. Add one or two **Video**
elements for previous episodes (best related episode first; one is enough when no
second episode is a good match) plus **Subscribe**. Make every element span the final
20 seconds, exactly over the canonical outro, and arrange them clear of any burned-in
`פרקים קודמים` callout. Save, then verify the entire window and every target in the
Editor preview while the upload is Private; end screens do not appear on a Private
watch page. Verify again on the watch page after publication. The video build holds
the outro's last frame when its source clip is shorter than 20 seconds.

## Segment videos: cards, end screen, pinned comment
On the אחים להשקעות channel (Switch account first), Content → the segment video → **Editor** (left menu).
- **Card:** Editor → **Cards** (ⓘ) → **Video** → pick the full episode (search its title, or *Choose a specific video* → paste the URL) → set **Custom message** `לפרק המלא` and **Teaser text** `צפו בפרק המלא` → drag the card on the timeline to ~0:30 (or to the natural "in the episode" mention). **Save**.
  **Limit:** one card per target video. A second card to the same video fails with "Multiple cards cannot reference the same video"; the end screen covers the second link.
- **End screen:** Editor → **End screen** → **+ Element** → **Video** → *Choose specific video* → the full episode; **+ Element** → **Subscribe**. On the timeline, make both run over the last 20 s (end screens can be 5–20 s and need a video ≥25 s). Arrange so they don't cover faces. **Save**.
- **Pinned comment** (after Public only): open the watch page as the channel (avatar = אחים להשקעות), comment `לפרק המלא: <full-episode URL>` → ⋮ on the comment → **Pin** → confirm. Or Studio → Comments → the video → ⋮ → Pin.
- Check: watch page shows the ⓘ teaser at the card time and the end screen in the last 20 s.
