---
name: investing-bros-episode-upload
description: >-
  Take a finished Investing Bros / אחים להשקעות episode out up to the OK:
  review ping, RedCircle draft with the RTL + "?" fix, Private YouTube uploads
  (episode, two segments, three Shorts) with upload records, the Telegram
  approval round, then the Spotify/RedCircle/YouTube checks and the WhatsApp
  share. Use for "upload episode N", "put it on RedCircle", "העלאה", "יוטיוב",
  "Spotify", "תפיץ את הפרק".
---
# Investing Bros upload, publish and share

Load `investing-bros-show` first: accounts, naming, the Drive tree and the WhatsApp destinations live there.

Use approved artwork supplied through `investing-bros-brand` for every cover and thumbnail. If artwork needs creation or revision, continue with that skill; do not redesign assets or maintain separate design rules in the upload workflow.

## When to use
When the episode folder is complete (audio, title and description files, exactly two segment packages and exactly three short packages, plus any full episode video or requested mid-form), for the review ping and uploads; again after the episode owner's OK, to publish, check and share. Also use this for a private back-catalogue re-upload.

## Inputs
1. Episode number N, confirmed with Amitai.
2. From the episode root: `הקלטה-ערוכה-פרק-N.m4a` (never anything from `extras/`), `כותרות-פרק-N.txt` (title = the text after `בחירה סופית:`; if the file holds a single title, that one) and `תיאור-פרק-N.txt`. Episodes 1–7: the Docs `אפשרויות כותרת` / `תיאור הפרק`.
3. Exactly two complete packages in `segments/`, exactly three complete packages in
   `Shorts/` (each Drive video is `.m4v` / `video/x-m4v`, never `.mp4` /
   `application/mp4`), plus `video/` when made and `mid-form/` when requested.
4. RedCircle login from show conventions → Roles and accounts. Never echo the password or put it in chat or logs.

### Back-catalogue re-upload
An already-published episode may have only its published audio and a finished video,
with no raw recording, transcript or `edit.json`. Download the RedCircle enclosure
or final Drive audio, transcribe it with `investing-bros-post-production`, and treat
that audio as the edited timeline (`start = 0`). Use the chapter offset tool in
`investing-bros-title-description` to locate that body after the video's teaser and
intro. Upload the replacement as Private and compare it with the current public
episode; replacing or deleting the public upload still requires the episode owner's explicit OK (Amitai for an episode with no state file). A superseded
Private copy of the same asset is deleted without asking (below).
A replacement is a full-episode re-upload: follow its rule in step 3.

## Steps

### 1. Review ping
List the episode folder and compare it with the show's Drive tree: the root holds only the audio and the two `.txt` files; `segments/` has exactly two complete packages (01 deep dive and 02 next-best qualifying topic); `Shorts/` has exactly three complete four-file packages. Then get a shareable link to the **episode folder** and post one message to Telegram group `tg-achim` with `<investing-bros-shorts>/scripts/send_telegram.py text`: ready for review + link, ending with `sent by Grokbot`. Review pings and drafts go to Telegram only, never WhatsApp (show conventions → Telegram). Wait for the episode owner's OK to upload. If the owner directly asked in chat for this upload, that request is the upload OK and no duplicate review ping is needed; it is not permission to publish.

### 2. RedCircle draft
Make the RTL-safe copy with the script, never by hand:
```bash
python3 scripts/rtl_fix.py --title  title.txt       > title-rtl.txt     # title.txt = the final title, one line
python3 scripts/rtl_fix.py --description תיאור-פרק-N.txt > description-rtl.txt
```
**Same title everywhere:** `title.txt` is the exact YouTube title; RedCircle gets that text plus only the marks `rtl_fix.py` adds. Check before saving and again before publishing:
```bash
python3 scripts/check_titles_match.py title.txt title-rtl.txt   # or paste the title from each site
```
Why and what the marks do: [references/redcircle-rtl.md](references/redcircle-rtl.md). Put both `-rtl.txt` files in `extras/`.
1. Open `https://app.redcircle.com/shows`, sign in, open **אחים להשקעות**.
2. **Add / New Episode** (a URL like `/shows/{showId}/ep/create`).
3. **Title** and **Description**: paste the `-rtl.txt` contents via clipboard (select-all, paste). Typing strips the marks. Keep the blank lines.
4. **Upload File**: the edited audio. On a network error, retry once. If `.m4a` is rejected, a byte-identical copy renamed `.mp3` uploads fine.
5. **More Options** → **Episode Number** = N, when the field exists.
6. **Save as Draft** / leave **Unpublished**. Leave RedCircle's default ad insertion points unless Amitai asks.
7. Screenshot the title and description: `?` at the end of the Hebrew sentence, timestamps at the start of chapter lines. A draft edited back and forth that still looks broken: make a **fresh draft** and leave the old one for Amitai.

### 3. YouTube uploads (all Private for the approval round)
**Gate first:** before uploading the full episode (API or Studio, any visibility) run `investing-bros-producer` → `scripts/pipeline.py gate "$EP" --stage upload` (an episode without `extras/pipeline.json`: `investing-bros-post-production` → `scripts/postprod_checklist.py check "$EP" --episode N`). It must print `PASS`; any missing item (for example the cold-open teaser) is made first or explicitly waived by the episode owner for this episode. See `investing-bros-post-production` → `references/CHECKLIST.md`.

**Preferred: the YouTube Data API** when `~/.config/youtube-uploader/` has `client_secret.json` and `token.json` on the Grok Bot box: `scripts/yt_upload.py --asset main|segNN|shortNN --record "$EP/extras/uploads/<asset>.json"` (resumable, frees the browser, Private only, show channel only, ~6 uploads/day, reauth every ~7 days while the app is in Testing). It writes the upload record right after the insert; if a later step fails, `--resume RECORD` finishes it on the same video. See [references/youtube-api.md](references/youtube-api.md).
**Studio fallback** (no credentials, a refused token, quota used up): first read `extras/uploads/<asset>.json`. If it holds a `video_id` for this asset version, the video is already uploaded: finish the remaining steps on that video in Studio and never upload a second copy. Only with no record (or a record of an older version) upload in the browser as below, then write the video ID you copied into the record, with `source_sha256` = the sha256 of the master (full episode) or of the segment/Short file. Either way, publishing still needs the publish OK.

**Upload a compressed copy, not the master.** Make a ~1 GB copy (H.264 CRF 23,
max 3000 kb/s, AAC 160 kb/s, faststart) and check it against the master with
`investing-bros-video` → `verify_sync.py MASTER COPY` (`SYNC OK`) before uploading:
```bash
scripts/compress_for_youtube.sh "$EP/video/פרק-N-וידאו.mp4" "$EP/extras/פרק-N-youtube.mp4"
```
Upload the copy with `--source "$EP/video/פרק-N-וידאו.mp4"`, so the record's version is the master's.
In Studio, never reload the tab or navigate away while a file uploads; if a "Leave
site?" dialog appears, press **Cancel**.

**Links are copied, never typed.** Take each video ID or URL from tool output
(`yt_upload.py`, the Studio share link), never retype it, and before saving any
description, notes file or message run
`python3 scripts/check_links.py FILE`: every YouTube link must resolve
(episode 9 shipped a link with `I` typed for `l`), and a link on a look-alike
domain (`youtube.com.evil.io`, `y0utube.com`) fails. Links to hosts outside the
show's usual list (sponsors) are flagged for you to open, not failed.

Follow [the Studio checklist](references/youtube-studio.md). Its first check can't be waived: before any Studio action (upload, edit, comment, Related video), open `https://studio.youtube.com/channel/UCWIlggXQNDFiyJghl6VB6Xw/videos`, confirm in the avatar menu that **אחים להשקעות** (not the account's personal **Grok Bot** channel, `UCj9n6mOn7uWpN8G51nPggfA`) is active, and click into videos from that list. Direct `studio.youtube.com/video/<id>/edit` links load as Grok Bot even with `authuser=1`. Check the avatar again on every edit page, and post comments only with אחים להשקעות active. Upload the full episode as **Private** and
the two segment evaluations as **Private** too (Amitai, 2026-11-05: all review uploads
stay Private; Nadav owns the channel, so Private is enough, and segment cards/end
screens pointing to the Private episode work); choose **No, it's not made for kids**.
The API uploader's Private default is correct; don't switch anything to Unlisted.
The three Shorts are uploaded **Private** too, for the approval round; they go Public
only after the full episode is live and publishing is OK'd.
- **Video episode** (`video/`): title from `כותרות-פרק-N.txt`, description from `video/תיאור-פרק-N-youtube.txt`, pasted **plain** (no RTL marks). It must include the `האזינו בספוטיפיי:` line (show link until step 5 swaps in the episode link).
  Add one or two previous-episode video elements (best related first) plus Subscribe
  across the final 20 seconds, exactly over the canonical outro; verify them on the
  Studio Editor preview while Private, then on the watch page after publication.
- **Exactly three Shorts** (`Shorts/`): uploaded Private for the approval round;
  Public only after the full episode is live (`investing-bros-publish`). Before
  upload, compare each `youtube-שורט-NN.md` with its approved cover: the YouTube title
  and description's first line must both equal the cover title exactly. Upload the
  `.m4v` video with that metadata, Related video and `.srt` (no pinned comment). **Related video is a hard rule:** set it to the full episode in Studio (Shorts → Details → Related video), then reopen the edit page and confirm the field shows the episode. A link in the description does NOT count. If it can't be set (e.g. "No matching results"), the Short stays Private and the failure is reported; never publish a Short with only a description link. The publish gate is `investing-bros-publish`. Do not add
  a disclosure, holdings statement, number or claim unless the hosts stated it in the
  episode; preserve the meaning of anything they did state.
- **Exactly two segment videos** (`segments/`; segment 01 is the required deep dive): follow `investing-bros-segment-video`.
- **Mid-form** (`mid-form/`): title and description from its `.txt`, with the full-episode link.
- **Full episode re-uploaded** (a fixed master, a replacement): in the same step,
  update every segment video's description, card and end screen and every Short's
  description and Related video, plus `video/תיאור-פרק-N-youtube.txt`, the segment files and each
  `youtube-שורט-NN.md`, to the new URL, and run `check_links.py` on all of them. Retire
  the old upload: once the new one is verified in Studio, **delete the superseded Private
  upload of the same asset** without asking (Amitai, episode 10: "you can always delete the
  old uploads that are not relevant anymore from YouTube"). Never delete a Public upload or the
  current version; a Public one still needs the episode owner's explicit OK. List the deleted titles and
  IDs in the hand-back and mark `old_uploads` (`investing-bros-producer` → `pipeline.py mark`).
- **Superseded uploads (any asset):** the same rule applies to segments and Shorts. Before
  deleting, confirm in Studio that the video is Private, is the same asset as a newer verified
  upload, and is not linked from any current description, card, end screen or Related video.
- **Past-episode cards (required, full episode):** whenever the hosts reference a past
  episode, by number ("פרק 8", "בפרק שמונה") or by topic ("the nuclear / SpaceX episode"),
  add a YouTube info card (Studio → Editor → Cards → Video) at that moment linking to the
  referenced episode. Amitai, episode 10: "whenever a previous episode is mentioned, then a
  card at the top of the YouTube is shown with a reference to the episode". Rules: **max 4
  cards** per episode; **one card per referenced episode**, at its first strong mention;
  prioritise the clearest and most-repeated references (number references beat topic ones).
  Source: `extras/past-episode-cards.json`, made in post-production by
  `<investing-bros-post-production>/scripts/find_past_episode_refs.py` and resolved through
  `<investing-bros-show>/references/episode-index.json`. Read every quote yourself; drop false
  hits (a topic word that isn't a back-reference). Card teaser text = the episode title.
  Recheck each time against the delivered file (cuts shift times). After a re-upload, set the
  cards on the new video. Mark `past_episode_cards` with the times you set. These are added to
  the Private upload, no extra approval needed.
- Thumbnail: upload option A, the episode's 16:9 `thumbnail-פרק-N.jpg` from the episode root (made from the square cover by `investing-bros-brand`). The same for a segment's `-thumb.jpg` and a Short's `-cover.jpg`. The A/B/C pick is round 2 and gates publish, not this upload. If the pick is not A, promote that file onto the canonical name and run `yt_upload.py --set-thumbnail VIDEO_ID --thumbnail <pick> --asset <track> --record extras/uploads/<track>.json`. That writes `extras/uploads/<track>-thumb.json` (the file's sha256 and the video ID) and does not rewrite the upload record.

### 3b. Approval round: one Telegram message
The episode owner approves the episode's assets together. Once **all** of them are ready — the
full episode (YouTube Private), both segment videos (YouTube Private; Nadav owns the
channel), the three Shorts (uploaded Private with option A) and the RedCircle draft link — write **one**
message for the `אחים להשקעות` Telegram group (show conventions → Telegram). Each asset
gets its copied link and, beside it, the A/B/C options (the file name of each; option A is
the one on the video). End with the line `sent by Grokbot`. A contact sheet that would
draw those options is a follow-up (`investing-bros-producer` → `references/gates.md`); until
then the names are enough. Check it, then post it automatically as part of the
pipeline; no separate preview or OK is needed for this message (Amitai,
2026-11-05, ep10):
```bash
python3 scripts/check_links.py approval.txt --message
python3 <investing-bros-shorts>/scripts/send_telegram.py text approval.txt
```
Never one post per asset; something added later goes in a new single message with the
full list. Once the owner signs the round off, post the one round summary for the other
brother (show conventions → Telegram → Round summary; pre-approved), with the same two commands.

### 4. Publish (only after the episode owner's OK in chat)
Run the publish itself with `investing-bros-publish`: its checklist enforces the order below, a live check before each next step, the Shorts' Related video rule, and the ticked report for Amitai.

Order ([references/publish-order.md](references/publish-order.md)): RedCircle publish (it feeds Spotify) → rerun `check_titles_match.py` on the live YouTube and RedCircle titles → Spotify ingests it (a few hours) → the YouTube description's `האזינו בספוטיפיי:` line (after the disclaimer, before the chapters; `check_copy.py --youtube`) gets the Spotify episode link, replacing the show link, on the episode and its shorts. Publishing always includes RedCircle. If the owner is fine waiting, suggest publishing RedCircle first so the episode link exists before YouTube goes Public. Then the segment videos go Public, then shorts. Segment videos link back through their own description, card and end screen (no pinned comment); do not add segment links to the full episode's description. Switch the YouTube uploads the owner named to Public (or schedule them as they say). Nothing goes live on its own. After the YouTube uploads go public, a daily morning analytics report runs for one week.

### 5. Check how it renders
- **YouTube**: open the public watch page. Every description line right-aligned with its timestamp on the right, times in order, chapters on the progress bar. A wrong line almost always starts with English; reword it to start with Hebrew.
- **RedCircle**: the public episode page shows the title with `?` at the end.
- **Spotify** (a few hours after publishing; RedCircle feeds it): open [the show](https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk). Without a browser, read the newest episode's title through `https://open.spotify.com/embed/show/4fREAemgQDMWIUK58N5Jjk`. Check:
  - the episode is there, with the exact title (no en dash, `?` at the end of the sentence)
  - the description lines read right-to-left and nothing visible is scrambled
  - chapters show in the Spotify app (episode page → chapters)
  - **then link it on YouTube**: copy the Spotify episode URL (`https://open.spotify.com/episode/<id>`, without `?si=`), edit the public episode's YouTube description to replace the show link on the `האזינו בספוטיפיי:` line with it, and do the same on that episode's shorts. Update `video/תיאור-פרק-N-youtube.txt` and each `youtube-שורט-NN.md` to match. Editing a Public video's description is part of the approved publish, not a new public action.

  Wrong on Spotify but right on RedCircle: tell the episode owner what you saw (screenshot) and open a GitHub issue on the repo; don't change show settings or re-publish to fix it.

Video stays on YouTube. Uploading video to Spotify cuts that episode off from RedCircle (no automatic updates, no RedCircle stats or ads), so do it only if Amitai decides to.

### 6. WhatsApp (when Amitai asks)
Follow [references/share-whatsapp.md](references/share-whatsapp.md): exact group, text ending with the show tag, public link, sent by the WhatsApp owner, confirmation reported.

## Done when
- Before the OK: RedCircle draft saved with the YouTube title (`check_titles_match.py` passes) and screenshot-checked; the full episode when made is uploaded with its previous-episode + Subscribe end screen over the canonical outro, both segment videos and all three Shorts are uploaded Private for review, all three Shorts have completed Telegram approval and Drive filing, and the review ping was sent; the full episode went up as the compressed copy with `SYNC OK`; every link in the descriptions passed `check_links.py`; and all assets went for approval in one Telegram message ending `sent by Grokbot`.
- After the OK: live on RedCircle **and** YouTube with identical titles; both segment videos are Public after the full episode; all three Shorts went Public only after the episode went live; the episode is listed on Spotify; and the Spotify, RedCircle and YouTube checks passed (or the problem is with the episode owner and in an issue). The YouTube episode and all three Shorts link the Spotify **episode** URL, not the show.
- WhatsApp sends confirmed, when asked.

## Hand back
- RedCircle draft URL (or public URL), title used, episode number
- YouTube links, with each video's visibility
- The render checks: Spotify, RedCircle, YouTube, with anything that looked wrong
- The Spotify episode URL, and confirmation it replaced the show link in the YouTube descriptions (or that Spotify hasn't listed it yet, and when to retry)
- Upload retries or blockers
- WhatsApp send status, when asked

Update this skill when the RedCircle or YouTube Studio click-path changes.

## Never
- Publish on YouTube without also publishing the RedCircle episode, or with a RedCircle title that differs from the YouTube one.
- Publish or set anything Public without the episode owner's explicit OK in chat; submit to directories or post on WhatsApp/Telegram (other than the pipeline messages) without Amitai's.
- Echo or paste the password.
- Type a video ID or URL by hand, or post a link `check_links.py` hasn't passed.
- Act in Studio (upload, edit, comment, Related video) without confirming אחים להשקעות is the active channel.
- Make a Short Public whose Related video isn't the full episode (verified by reopening its edit page), or treat a description link as the Related video.
- Reload or leave the Studio tab during an upload; delete a Public upload or the current version of anything without the episode owner's OK (superseded Private uploads are deleted automatically).
- Send assets for approval one by one instead of in one message.
- Upload raw or `extras/` audio.
- Paste Hebrew into RedCircle without the RTL + `?` marks, or put those marks in the YouTube copy.
- Upload video to Spotify, or change RedCircle show settings, without Amitai's decision.
- Drive WhatsApp Web yourself.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).

Publish order: `references/publish-order.md` (RedCircle, Spotify, YouTube Spotify line, then Shorts).
