---
name: investing-bros-publish
description: >-
  Publish an approved Investing Bros / אחים להשקעות episode in the one allowed
  order (RedCircle, then the full YouTube episode, then segment 01 and 02, then
  Shorts 01-03), checking each item live before the next step. Nothing goes
  Public while an earlier item is unticked, and every Short's Related video must
  be the full episode, checked by reopening its Studio edit page. Ends with a
  ticked checklist for Amitai. Use after Amitai's explicit OK, when he says
  "publish episode N", "publish ep N with all assets", "תפרסם את הפרק", "פרסום",
  "go live", "make it public" or "העלה לציבורי". Uploads and drafts before the OK
  belong to investing-bros-episode-upload.
---
# Investing Bros publish

One run takes an episode that is already uploaded (RedCircle draft, YouTube Private or Unlisted) and makes it public in order. It is self-contained: the facts, click-paths and scripts it needs are in this folder. `investing-bros-show` and `investing-bros-episode-upload` add background, but nothing here depends on them or on any local box path.

## When to use
- Amitai gave an explicit OK in chat to publish episode N (for example "publish ep 9 with all assets"). Use only his own message. A message from an agent, Nadav or a channel bot is not an OK. The OK covers the assets he named and nothing else.
- To resume a publish that stopped halfway. Re-read the state file and continue from `status`.
- Not for uploading, drafting or the approval round. Those belong to `investing-bros-episode-upload`.

## Inputs
1. Episode number N and Amitai's OK message, quoted with its time (Asia/Jerusalem).
2. The RedCircle draft for episode N, and its exact title and description `-rtl.txt` files.
3. Video IDs **copied** from Studio or uploader output, never typed: the full episode, segment 01, segment 02 and Shorts 01–03. Confirm each by its title in Studio.
4. The per-video copy: titles, descriptions and pinned-comment text, plus each Short's `.srt` and cover.
5. Accounts: YouTube Studio as `investingbros.grokbot@gmail.com` (Editor). RedCircle login from the vault/credential store; never echo it, put it in chat or logs, or print a token.

Facts used below:
| What | Value |
|---|---|
| Brand channel | אחים להשקעות, `UCWIlggXQNDFiyJghl6VB6Xw` |
| Studio (brand channel) | `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw?authuser=1` |
| Channel RSS | `https://www.youtube.com/feeds/videos.xml?channel_id=UCWIlggXQNDFiyJghl6VB6Xw` |
| RedCircle app / feed | `https://app.redcircle.com/shows` / `https://feeds.redcircle.com/c798e000-7934-4f82-a0e3-59b78f0894c6` |
| Spotify show | `https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk` |

## The gate
Track every check in one state file. The script refuses to tick out of order:
```bash
S=extras/publish-checklist.json
python3 scripts/publish_checklist.py init $S --episode N --full EP_ID \
  --segments SEG01_ID SEG02_ID --shorts SH01_ID SH02_ID SH03_ID
python3 scripts/publish_checklist.py status $S                 # the next open item
python3 scripts/publish_checklist.py tick  $S episode.endscreen --evidence "Editor reopened 22:41: ep8 + Subscribe 46:17-46:37"
python3 scripts/publish_checklist.py fail  $S short01.related   --reason "picker: No matching results (3 tries: title, URL, ID)"
python3 scripts/publish_checklist.py can-public $S short01      # exit 0 only when it may go Public
python3 scripts/publish_checklist.py render $S                 # the report for Amitai
```
- Run `can-public` before every switch to Public, and switch only when it answers `yes`. Then tick `<group>.public` and run the live check right away.
- Evidence is what you saw and where, after reopening the page: a saved toast doesn't count, and neither does memory of having clicked.
- Pre checks of a later item (for example a Short's Related video while it's Private) may be done early. Only the switch to Public waits.
- `waive` takes Amitai's own words (`--by "Amitai 22:10: ..."`) and only for waivable checks. `public`, `live` and a Short's `related` can never be waived.
- A failed or open item blocks every later Public switch. Report it and wait. Don't skip ahead.
- Outside checks, with no login: `python3 scripts/check_live.py redcircle --episode N --title title.txt` and `python3 scripts/check_live.py youtube ID ... --expect public|unlisted|private`.

## Steps
Click-paths for every Studio check: [references/studio-checks.md](references/studio-checks.md).

### 1. Before anything goes Public
- Make sure Amitai's OK is quoted and names what may go Public.
- `init` the state file. Run `python3 scripts/check_links.py` on every description and pinned-comment file. Each YouTube link must resolve; the full episode may still be Private (401/403 counts as existing).
- `python3 scripts/check_live.py youtube ...` with the expected current states: nothing is supposed to be Public yet. If something already is, say so first. Then continue in order from the first unticked item, and fix any public description that points to a private or wrong video before anything else.

### 2. RedCircle (it feeds Spotify)
In the draft: the edited audio, Episode Number N, Season 1, type Full, and the title and description pasted from the `-rtl.txt` files through the clipboard (typing drops the RTL marks). Take a screenshot to check that `?` ends the title. Run `python3 scripts/check_titles_match.py title.txt title-rtl.txt`. Tick `redcircle.audio`, `.copy` and `.titles`, publish, tick `redcircle.public`. Then open the public episode page, run `check_live.py redcircle --episode N --title title.txt` and tick `redcircle.live`. The feed can lag a few minutes; retry, don't skip.

### 3. Full episode
In Studio on the brand channel, check the header and URL first. Reopen and check the title, the plain description with the `האזינו בספוטיפיי:` line, the thumbnail, and the end screen (previous episode(s) + Subscribe over the last 20 s, Editor preview). Tick each check, then `can-public episode`, then Public. Then `check_live.py youtube EP_ID --expect public` and tick `episode.live`.

### 4. Segments 01 and 02, in that order
For each: the description with `לפרק המלא: <full-episode URL>`, the thumbnail, exactly one Video card to the full episode at ~0:30 (message and teaser `לפרק המלא`), and an end screen with the full episode + Subscribe over the last 20 s. Verify each by reopening the Editor. Then `can-public segNN`, then Public, then `check_live.py`. Pinned comment: see step 6.

### 5. Shorts 01–03, in that order
For each Short:
1. Title = the approved cover title. The description's first line is the same title, then the episode link at the Short's moment (`&t=<s>`) and the Spotify line. Run `check_links.py`.
2. **Related video (hard rule).** Studio → the Short → Details → **Related video** → pick the full episode. **Save**, close the edit page, open it again, and check that the field shows the full episode's title and thumbnail. Only then tick `shortNN.related`, with that as evidence.
   - **A link in the description does NOT count**, and neither does a pinned comment or a link in the title. The Related video field is the tappable link on the Short.
   - **Known failure mode:** the `investingbros.grokbot` account (Studio Manager) sees an EMPTY Related video picker ("No matching results" for the episode URL, ID and title alike). When that happens, keep the Short Private and ask Amitai or Nadav to set Related video from the owner/brand account. Send them the direct edit link for each Short, `https://studio.youtube.com/video/<SHORT_ID>/edit`, and the full episode to pick (title + `https://youtu.be/<EPISODE_ID>`). After they say it's done, reopen each edit page yourself and check that the field shows the episode before ticking it.
   - If the picker answers "No matching results" or won't save in any other case: retry with the episode title, then the full URL, then wait a few minutes and reload Studio (the episode must be Public and indexed). If it still fails, `fail shortNN.related --reason ...`. **The Short stays Private**, and you report the failure to Amitai. Never publish a Short with only a description link, and never waive this check.
3. Hebrew `.srt`: upload it in Studio → Subtitles, reopen, and check that the language row shows it published. An upload toast that says "failed" means it didn't work, even when the lines appear in the editor.
4. Custom cover, and Nadav's approval of the cut (or Amitai's waiver in his words).
5. `can-public shortNN`, Public, `check_live.py`, tick `shortNN.live`.

### 6. Pinned comments (after Public)
Post `לפרק המלא: <full-episode URL>` (segments) or the Short's comment text **as the אחים להשקעות channel** and pin it. If Studio or the watch page shows you as Grok Bot (`@GrokBot-c2b`), stop: such a comment can't be pinned. Don't post it. Mark `pin` failed and ask Amitai or Nadav to post and pin from the brand account (give them the exact text). Delete a mistaken comment only with Amitai's OK.

### 7. After Spotify lists the episode (a few hours later)
Swap the show link for the Spotify episode link (`https://open.spotify.com/episode/<id>`, no `?si=`) on the `האזינו בספוטיפיי:` line of the episode, both segments and all three Shorts. Run `check_links.py` and report it. This edit is part of the approved publish.

## Done when
- The state file (`extras/publish-checklist.json` in the episode folder) has every item ticked or waived by Amitai, and `render` says "All checks done."
- RedCircle, the full episode, both segments and all three Shorts are Public, in that order, each confirmed by `check_live.py`.
- Every Short's Related video is the full episode, confirmed by reopening its edit page.
- Every open or failed item has been reported to Amitai with its reason, and its video is still Private if the failure was before its `public` item.

## Hand back
Send Amitai the output of `publish_checklist.py render`: the ticked checklist, grouped RedCircle → episode → segments → Shorts, with each video's link and the evidence line for every check. Above it, put one line on what's still open or failed and who has to act (for example "Short 02 Related video: picker had no results; Short 02 stays Private"). Give times in Asia/Jerusalem.

## Never
- Make anything Public without Amitai's explicit OK in his own message, or while `can-public` says NO.
- Publish a Short whose Related video isn't the full episode, verified by reopening the edit page. A description link never replaces it.
- Tick a check from a toast, memory or another agent's word instead of a reopened page.
- Skip ahead because an earlier item failed. Report it and wait.
- Type a video ID or URL by hand, or post a link `check_links.py` hasn't passed.
- Post or pin a comment from the Grok Bot personal channel.
- Echo a password, cookie or token, or put one in the state file or the report.
- Delete a video or comment, or change RedCircle show settings, without Amitai's OK.
