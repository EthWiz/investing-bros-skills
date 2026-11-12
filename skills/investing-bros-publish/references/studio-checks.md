# Studio and RedCircle checks, one per checklist item

## channel (first, every video, never waived)
**Active channel first (non-waivable; before any Studio action: upload, edit, comment, Related video).** `investingbros.grokbot@gmail.com` also owns a personal channel, **Grok Bot** (`UCj9n6mOn7uWpN8G51nPggfA`), and it is the default. Studio acts as whichever channel is active. The Related video picker lists only the active channel's videos (that is why it came up empty in episode 9), and comments post as the active channel (that is why episode 9's comments came from Grok Bot). Opening `studio.youtube.com/video/<id>/edit` directly still loads as Grok Bot, even with `authuser=1`, so never work from direct edit links. Open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos` (Shorts: `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`), confirm in the avatar menu that **אחים להשקעות** is the active channel, and click into each video from that list. Check the active channel again on every edit page before changing anything. The Grok Bot channel is being deleted; keep this check anyway.
"Verified" means you saved, left the page, reopened it and saw the value. A "Saved" toast is not
verification. A toast that says "not able to save your video" is not proof it failed either: leave
the page, reopen the video from the Content list (with אחים להשקעות active) and check whether the
change is actually there. If it is, you're done; if it isn't, save again.

## RedCircle
- **audio / copy / titles**: draft → Upload File (on a network error, retry once; if `.m4a` is
  rejected, a byte-identical copy renamed `.mp3` uploads). More Options → Episode Number N, Season 1,
  Full. Paste the title and description from the `-rtl.txt` files through the clipboard
  (select-all, paste). Typing drops the RTL marks. If the description pastes as a code block, use the
  editor's clear-formatting button. Screenshot both fields.
- **live**: the public episode page shows the title ending with `?`, and
  `check_live.py redcircle --episode N --title title.txt` passes.

## Full episode
- **endscreen**: Content → the video → Editor → End screen. Add one or two previous-episode Video
  elements plus Subscribe, spanning exactly the last 20 s. Save, reopen the Editor and play the
  preview over the window. If the preview does not render, reload once or twice, then report if the preview still doesn't render — do not leave
  elements in the default template position. Keep every Video element clear of faces, including
  foreheads.

## Segments
- **card**: Editor → Cards → Video → paste the full-episode URL into *Search videos from other
  channels* (searching your own videos by URL returns nothing) → custom message and teaser
  `לפרק המלא` → drag to ~0:30 → Save. Only one card per target video is allowed. Reopen to check.
- **endscreen**: Editor → End screen → Video (*Choose specific video* → the full episode) +
  Subscribe over the last 20 s, clear of faces (including foreheads). Reopen and play the
  preview; if it does not render, reload once or twice, then report if the preview still doesn't render — do not leave elements in the default
  template position.

## Shorts
- **related** (hard rule): Content → Shorts tab → the Short → Details → **Related video** → search
  the full episode's title (or paste its URL) → pick it → Save. Close the edit page, open it again,
  and check that the Related video box shows the full episode's title and thumbnail. Evidence for the tick:
  "reopened <time>: Related video = <episode title> (<id>)".
  - A link in the description, title or a comment is not the Related video and never counts.
  - **Empty Related video picker.** "No matching results" for the episode URL, ID and title is usually a Studio quirk, not a permissions problem. First confirm אחים להשקעות is the active channel (if Studio is acting as Grok Bot, go back to `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`, confirm the avatar menu, and click into the Short from that list). If אחים להשקעות is already active and the picker is still empty: reload Studio — leave the page and reopen the Short from that same list. The picker often stays empty until a reload, and it sometimes only works once the full episode is Public; searching own videos for distinctive title text (for example "פרק 11") can hit when the URL or ID does not. Only if the picker is still empty with אחים להשקעות active after a reload, and the episode is already Public: keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Name the Short (title + ID) and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`), with the path Studio → אחים להשקעות → Content → Shorts → the Short. Then reopen it yourself (from the list, with אחים להשקעות active) and check the field before ticking.
    Fill the checklist in with `fail shortNN.related --reason "picker empty with אחים להשקעות active; asked <who> <time>"`, then
    tick it after your own reopen check.
  - Still failing after that reload, with the episode Public and אחים להשקעות active: `fail shortNN.related --reason ...`, leave the
    Short Private and report it. No waiver.
- **srt**: Languages → Upload manual → With timing (Hebrew is the Short's own language, so it is greyed out under Add language). Reopen Subtitles and check that
  the Hebrew row shows as published. A "failed" toast is a failure even if the lines show in the editor.
- **cover**: desktop Studio may not offer a cover for a Short, and `thumbnails.set` sometimes refuses
  one. Amitai or Nadav sets it in the YouTube phone app, then
  `publish_checklist.py record-thumb STATE --asset shortNN --thumbnail <cover> --video-id ID --evidence <screenshot> --by "<owner> HH:MM: <their words>"`
  writes `extras/uploads/shortNN-thumb.json` (the file's sha256, the video ID, the quote, the screenshot).
  That is not a waiver and it does not tick the item. `can-public` accepts it only when the sha256 is the
  approved pick. A failed cover stays failed.

## Comments
No pinned comments on segments or Shorts (Amitai, 2026-11-01): there is no comment check. Any comment is posted only while **אחים להשקעות** is the active channel (a comment from Grok Bot, `@GrokBot-c2b`, appears under the wrong channel).
