# Studio and RedCircle checks, one per checklist item

Always work on the brand channel: open
`https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw?authuser=1` and check that the header reads
**אחים להשקעות** and that the URL still has that channel id. Studio sometimes opens on the personal
**Grok Bot** channel and drops `authuser`. If it does, use Switch account and go back to the URL.
"Verified" means you saved, left the page, reopened it and saw the value. A "Saved" toast is not
verification.

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
  preview over the window.

## Segments
- **card**: Editor → Cards → Video → paste the full-episode URL into *Search videos from other
  channels* (searching your own videos by URL returns nothing) → custom message and teaser
  `לפרק המלא` → drag to ~0:30 → Save. Only one card per target video is allowed. Reopen to check.
- **endscreen**: Editor → End screen → Video (*Choose specific video* → the full episode) +
  Subscribe over the last 20 s, clear of faces. Reopen to check.

## Shorts
- **related** (hard rule): Content → Shorts tab → the Short → Details → **Related video** → search
  the full episode's title (or paste its URL) → pick it → Save. Close the edit page, open it again,
  and check that the Related video box shows the full episode's title and thumbnail. Evidence for the tick:
  "reopened <time>: Related video = <episode title> (<id>)".
  - A link in the description, title or pinned comment is not the Related video and never counts.
  - **Known failure mode (episode 9):** the `investingbros.grokbot` account (Studio Manager) sees an EMPTY Related video picker ("No matching results" for the episode URL, ID and title alike). When that happens, keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Send them the direct edit link for each Short, `https://studio.youtube.com/video/<SHORT_ID>/edit`, and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`). After they say it's done, reopen each edit page yourself and check that the field shows the episode before ticking it.
    Fill the checklist in with `fail shortNN.related --reason "Manager picker empty; asked <who> <time>"`, then
    tick it after your own reopen check.
  - Any other "No matching results": try the title, then the URL, then reload Studio after a few minutes
    (the episode must already be Public). Still failing: `fail shortNN.related --reason ...`, leave the
    Short Private and report it. No waiver.
- **srt**: Subtitles → Add language → Hebrew → Upload file → With timing. Reopen Subtitles and check that
  the Hebrew row shows as published. A "failed" toast is a failure even if the lines show in the editor.
- **cover**: desktop Studio may not offer a cover for a Short. Then the cover is set in the YouTube phone
  app by Amitai or Nadav, or Amitai waives it in his own words.

## Pinned comments
On the watch page, the comment box avatar must be אחים להשקעות. A comment from Grok Bot
(`@GrokBot-c2b`) can't be pinned and has to be redone by the brand owner. Post, then ⋮ → Pin → confirm,
then reload the page and check it shows as "Pinned by אחים להשקעות".
