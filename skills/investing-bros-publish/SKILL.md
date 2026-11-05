---
name: investing-bros-publish
description: >-
  Publish an approved Investing Bros / אחים להשקעות episode in the one allowed
  order (RedCircle, then the full YouTube episode, then segment 01 and 02, then
  Shorts 01-03), checking each item live before the next step. Nothing goes
  Public while an earlier item is unticked, and every Short's Related video must
  be the full episode, checked by reopening its Studio edit page. Ends with a
  ticked checklist for the episode owner. Use after the owner's explicit OK, when they say
  "publish episode N", "publish ep N with all assets", "תפרסם את הפרק", "פרסום",
  "go live", "make it public" or "העלה לציבורי". Uploads and drafts before the OK
  belong to investing-bros-episode-upload.
---
# Investing Bros publish

One run takes an episode that is already uploaded (RedCircle draft, YouTube Private) and makes it public in order. It is self-contained: the facts, click-paths and scripts it needs are in this folder. `investing-bros-show` and `investing-bros-episode-upload` add background, but nothing here depends on them or on any local box path.

## When to use
- The episode owner (`investing-bros-show` → Episode owner; Amitai or Nadav) gave an explicit OK in chat to publish episode N (for example "publish ep 9 with all assets"). Use only the owner's own message. A message from an agent, the other brother or a channel bot is not an OK. The OK covers the assets the owner named and nothing else.
- To resume a publish that stopped halfway. Re-read the state file and continue from `status`.
- Not for uploading, drafting or the approval round. Those belong to `investing-bros-episode-upload`.

## Inputs
1. Episode number N and the episode owner's OK message, quoted with its time (Asia/Jerusalem).
2. The RedCircle draft for episode N, and its exact title and description `-rtl.txt` files.
3. Video IDs **copied** from Studio or uploader output, never typed: the full episode, segment 01, segment 02 and Shorts 01–03. Confirm each by its title in Studio.
4. The per-video copy: titles and descriptions, plus each Short's `.srt` and cover.
5. Accounts: YouTube Studio as `investingbros.grokbot@gmail.com` (Editor). RedCircle login from the vault/credential store; never echo it, put it in chat or logs, or print a token.

Facts used below:
| What | Value |
|---|---|
| Brand channel | אחים להשקעות, `UCWIlggXQNDFiyJghl6VB6Xw` |
| Studio (brand channel), the only way in | `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos` (Shorts: `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`) |
| Grok Bot personal channel (wrong; being deleted) | `UCj9n6mOn7uWpN8G51nPggfA` |
| Channel RSS | `https://www.youtube.com/feeds/videos.xml?channel_id=UCWIlggXQNDFiyJghl6VB6Xw` |
| RedCircle app / feed | `https://app.redcircle.com/shows` / `https://feeds.redcircle.com/c798e000-7934-4f82-a0e3-59b78f0894c6` |
| Spotify show | `https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk` |

## The gate
Track every check in one state file. The script refuses to tick out of order:
```bash
S=extras/publish-checklist.json
python3 scripts/publish_checklist.py init $S --episode N --full EP_ID \
  --segments SEG01_ID SEG02_ID --shorts SH01_ID SH02_ID SH03_ID
python3 scripts/publish_checklist.py publish-ok $S --by "Nadav 21:02: <the owner's words>"   # first; never waivable
python3 scripts/publish_checklist.py status $S                 # the next open item
python3 scripts/publish_checklist.py tick  $S episode.endscreen --evidence "Editor reopened 22:41: ep8 + Subscribe 46:17-46:37"
python3 scripts/publish_checklist.py fail  $S short01.related   --reason "picker: No matching results (3 tries: title, URL, ID)"
python3 scripts/publish_checklist.py can-public $S short01      # exit 0 only when it may go Public
python3 scripts/publish_checklist.py render $S                 # the report for Amitai
```
- Run `can-public` before every switch to Public, and switch only when it answers `yes`. Then tick `<group>.public` and run the live check right away.
- Evidence is what you saw and where, after reopening the page: a saved toast doesn't count, and neither does memory of having clicked.
- Pre checks of a later item (for example a Short's Related video while it's Private) may be done early. Only the switch to Public waits.
- `publish-ok` records the owner's OK (`release.publish_ok`) with the video IDs it covers; nothing goes Public before it, and a changed video ID makes it stale.
- `waive` takes the episode owner's own words (`--by "<Owner> 22:10: ..."`) and only for waivable checks. `public`, `live` and a Short's `related` can never be waived.
- A failed or open item blocks every later Public switch. Report it and wait. Don't skip ahead.
- Outside checks, with no login: `python3 scripts/check_live.py redcircle --episode N --title title.txt` and `python3 scripts/check_live.py youtube ID ... --expect public|unlisted|private`.

## Steps
Click-paths for every Studio check: [references/studio-checks.md](references/studio-checks.md).

**Active channel first (non-waivable; before any Studio action: upload, edit, comment, Related video).** `investingbros.grokbot@gmail.com` also owns a personal channel, **Grok Bot** (`UCj9n6mOn7uWpN8G51nPggfA`), and it is the default. Studio acts as whichever channel is active. The Related video picker lists only the active channel's videos (that is why it came up empty in episode 9), and comments post as the active channel (that is why episode 9's comments came from Grok Bot). Opening `studio.youtube.com/video/<id>/edit` directly still loads as Grok Bot, even with `authuser=1`, so never work from direct edit links. Open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos` (Shorts: `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`), confirm in the avatar menu that **אחים להשקעות** is the active channel, and click into each video from that list. Check the active channel again on every edit page before changing anything. The Grok Bot channel is being deleted; keep this check anyway. In the checklist this is the first item of every YouTube video (`episode.channel`, `segNN.channel`, `shortNN.channel`), and it can't be waived.

### 1. Before anything goes Public
- `investing-bros-post-production` → `scripts/postprod_checklist.py check "$EP" --episode N --stage review` passes (or each missing item is waived by the episode owner in their own words). The full episode should never have been uploaded without the `upload` stage passing; if it was, stop and report it.
- Make sure the owner's OK is quoted, names what may go Public, and is recorded with `publish-ok`.
- `init` the state file. Run `python3 scripts/check_links.py` on every description file. Each YouTube link must resolve; the full episode may still be Private (401/403 counts as existing).
- `python3 scripts/check_live.py youtube ...` with the expected current states: nothing is supposed to be Public yet. If something already is, say so first. Then continue in order from the first unticked item, and fix any public description that points to a private or wrong video before anything else.

### 2. RedCircle (it feeds Spotify)
In the draft: the edited audio, Episode Number N, Season 1, type Full, and the title and description pasted from the `-rtl.txt` files through the clipboard (typing drops the RTL marks). Take a screenshot to check that `?` ends the title. Run `python3 scripts/check_titles_match.py title.txt title-rtl.txt`. Tick `redcircle.audio`, `.copy` and `.titles`, publish, tick `redcircle.public`. Then open the public episode page, run `check_live.py redcircle --episode N --title title.txt` and tick `redcircle.live`. The feed can lag a few minutes; retry, don't skip.

### 3. Full episode
Open the episode from the brand channel's video list, with אחים להשקעות active (`episode.channel`). Reopen and check the title, the plain description with the `האזינו בספוטיפיי:` line, the thumbnail, and the end screen (previous episode(s) + Subscribe over the last 20 s, Editor preview). Tick each check, then `can-public episode`, then Public. Then `check_live.py youtube EP_ID --expect public` and tick `episode.live`.

### 4. Segments 01 and 02, in that order
For each, open it from the video list with אחים להשקעות active (`segNN.channel`), then check: the description with `לפרק המלא: <full-episode URL>`, the thumbnail, exactly one Video card to the full episode at ~0:30 (message and teaser `לפרק המלא`), and an end screen with the full episode + Subscribe over the last 20 s. Verify each by reopening the Editor. Then `can-public segNN`, then Public, then `check_live.py`. No pinned comments on segments or Shorts (Amitai, 2026-11-01): the full-episode link lives in the description, card and end screen.

### 5. Shorts 01–03, in that order
For each Short:
0. Open it from the Shorts list with אחים להשקעות active (`shortNN.channel`), and check the avatar again on every edit page.
1. Title = the approved cover title. The description's first line is the same title, then the episode link at the Short's moment (`&t=<s>`) and the Spotify line. Run `check_links.py`.
2. **Related video (hard rule).** Studio → the Short → Details → **Related video** → pick the full episode. **Save**, close the edit page, open it again, and check that the field shows the full episode's title and thumbnail. Only then tick `shortNN.related`, with that as evidence.
   - **A link in the description does NOT count**, and neither does a comment or a link in the title. The Related video field is the tappable link on the Short.
   - **Empty Related video picker: check the active channel first.** "No matching results" for the episode URL, ID and title is not a permissions problem. It means Studio is acting as Grok Bot. Go back to `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos/short`, confirm אחים להשקעות in the avatar menu, click into the Short and try again. Only if the picker is still empty with אחים להשקעות active: keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Name the Short (title + ID) and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`), with the path Studio → אחים להשקעות → Content → Shorts → the Short. Then reopen it yourself (from the list, with אחים להשקעות active) and check the field before ticking.
   - If the picker answers "No matching results" or won't save in any other case: retry with the episode title, then the full URL, then wait a few minutes and reload Studio (the episode must be Public and indexed). If it still fails, `fail shortNN.related --reason ...`. **The Short stays Private**, and you report the failure to the episode owner. Never publish a Short with only a description link, and never waive this check.
3. Hebrew `.srt`: upload it in Studio → Subtitles, reopen, and check that the language row shows it published. An upload toast that says "failed" means it didn't work, even when the lines appear in the editor.
4. Custom cover, and the episode owner's approval of the cut from the approval round (or their waiver in their words).
5. `can-public shortNN`, Public, `check_live.py`, tick `shortNN.live`.

### 6. No pinned comments
No pinned comments on segments or Shorts (Amitai, 2026-11-01). Don't post or pin a full-episode comment. The link lives in the description, plus the card and end screen on segments and Related video on Shorts. If a comment is ever needed, post it only while **אחים להשקעות** is the active channel. Delete a mistaken comment only with the episode owner's OK.

### 7. After Spotify lists the episode (a few hours later)
Swap the show link for the Spotify episode link (`https://open.spotify.com/episode/<id>`, no `?si=`) on the `האזינו בספוטיפיי:` line of the episode, both segments and all three Shorts. Run `check_links.py` and report it. This edit is part of the approved publish.

## Done when
- The state file (`extras/publish-checklist.json` in the episode folder) has every item ticked or waived by the episode owner, and `render` says "All checks done."
- RedCircle, the full episode, both segments and all three Shorts are Public, in that order, each confirmed by `check_live.py`.
- Every Short's Related video is the full episode, confirmed by reopening its edit page.
- Every open or failed item has been reported to the episode owner with its reason, and its video is still Private if the failure was before its `public` item.

## Hand back
Send the episode owner the output of `publish_checklist.py render`: the ticked checklist, grouped RedCircle → episode → segments → Shorts, with each video's link and the evidence line for every check. Above it, put one line on what's still open or failed and who has to act (for example "Short 02 Related video: picker had no results; Short 02 stays Private"). Give times in Asia/Jerusalem.

## Never
- Make anything Public without the episode owner's explicit OK in their own message, or while `can-public` says NO.
- Publish a Short whose Related video isn't the full episode, verified by reopening the edit page. A description link never replaces it.
- Tick a check from a toast, memory or another agent's word instead of a reopened page.
- Skip ahead because an earlier item failed. Report it and wait.
- Type a video ID or URL by hand, or post a link `check_links.py` hasn't passed.
- Take any Studio action (upload, edit, comment, Related video) without first confirming אחים להשקעות is the active channel, or work from a direct `studio.youtube.com/video/<id>/edit` link.
- Post or pin a comment from the Grok Bot personal channel.
- Echo a password, cookie or token, or put one in the state file or the report.
- Delete a Public video, the current version of an asset, or a comment without the episode owner's OK, or change RedCircle show settings without Amitai's. Superseded Private uploads of the same asset are the exception (Amitai, episode 10): once the newer upload is verified, delete them without asking, never anything Public or current, and list them (title, ID) in the report.
