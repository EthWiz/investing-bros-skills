# YouTube Studio checklist

The preferred upload path is the YouTube Data API ([youtube-api.md](youtube-api.md)); this checklist is the fallback for uploads and is always used for the steps the API leaves to Studio (visibility change after Amitai's OK, Related video, captions, chapters check).

Use the browser profile for the Editor account named in `investing-bros-show`.

## Before selecting a file
1. **Active channel first (non-waivable; before any Studio action: upload, edit, comment, Related video).** `investingbros.grokbot@gmail.com` also owns a personal channel, **Grok Bot** (`UCj9n6mOn7uWpN8G51nPggfA`), and it is the default. Studio acts as whichever channel is active. The Related video picker lists only the active channel's videos (that is why it came up empty in episode 9), and comments post as the active channel (that is why episode 9's comments came from Grok Bot). Opening `studio.youtube.com/video/<id>/edit` directly still loads as Grok Bot, even with `authuser=1`, so never work from direct edit links. Open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos` (Shorts: `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`), confirm in the avatar menu that **אחים להשקעות** is the active channel, and click into each video from that list. Check the active channel again on every edit page before changing anything. The Grok Bot channel is being deleted; keep this check anyway.
2. If the avatar menu shows Grok Bot: Avatar (top right) → **Switch account** → **אחים להשקעות**, then reopen the list URL. Re-check after every reload, new tab or edit page.
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

## After saving
A toast that says "not able to save your video" is not proof the save failed. Leave the page, reopen the video from the Content list (with אחים להשקעות active) and check whether the change is actually there (`investing-bros-publish` → references/studio-checks.md). If it is, you're done; if it isn't, save again. A "Saved" toast is not verification either.

## Details
- Paste the approved title and the YouTube description as plain text, with no
  RedCircle RTL marks.
- Audience: **No, it's not made for kids**.
- Visibility: **Private** until Amitai explicitly approves publication.
- Video language: Hebrew.
- Thumbnail: use only the approved final `thumbnail-פרק-N.jpg` from the episode root (16:9, from the square cover). If the custom-thumbnail
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
  **Empty Related video picker.** "No matching results" for the episode URL, ID and title is usually a Studio quirk, not a permissions problem. First confirm אחים להשקעות is the active channel (if Studio is acting as Grok Bot, go back to `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`, confirm the avatar menu, and click into the Short from that list). If אחים להשקעות is already active and the picker is still empty: reload Studio — leave the page and reopen the Short from that same list. The picker often stays empty until a reload, and it sometimes only works once the full episode is Public; searching own videos for distinctive title text (for example "פרק 11") can hit when the URL or ID does not. Only if the picker is still empty with אחים להשקעות active after a reload, and the episode is already Public: keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Name the Short (title + ID) and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`), with the path Studio → אחים להשקעות → Content → Shorts → the Short. Then reopen it yourself (from the list, with אחים להשקעות active) and check the field before ticking.
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

## Segment videos: cards, end screen
On the אחים להשקעות channel (open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos` and confirm the active channel in the avatar menu first; never a direct edit link), Content → the segment video → **Editor** (left menu).
- **Card:** Editor → **Cards** (ⓘ) → **Video** → pick the full episode (search its title, or *Choose a specific video* → paste the URL) → set **Custom message** `לפרק המלא` and **Teaser text** `צפו בפרק המלא` → drag the card on the timeline to ~0:30 (or to the natural "in the episode" mention). **Save**.
  **Limit:** one card per target video. A second card to the same video fails with "Multiple cards cannot reference the same video"; the end screen covers the second link.
- **End screen:** Editor → **End screen** → **+ Element** → **Video** → *Choose specific video* → the full episode; **+ Element** → **Subscribe**. On the timeline, make both run over the last 20 s (end screens can be 5–20 s and need a video ≥25 s). Arrange so they don't cover faces, including foreheads. **Save**, reopen and play the preview; if it does not render, reload once or twice, then report if the preview still doesn't render — do not leave elements in the default template position (`investing-bros-publish` → references/studio-checks.md).
- **No pinned comment** (Amitai, 2026-11-01): the description, card and end screen carry the full-episode link.
- Check: watch page shows the ⓘ teaser at the card time and the end screen in the last 20 s.
