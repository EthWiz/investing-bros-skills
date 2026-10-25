---
name: investing-bros-episode-upload
description: >-
  Take a finished Investing Bros / אחים להשקעות episode out: review ping,
  RedCircle draft (edited audio, final Hebrew title and description with the
  RTL + "?" fix, episode number), a Private full episode when made, exactly two
  Unlisted segment evaluations, then exactly three shorts uploaded after the
  episode is live, plus optional mid-form. With Amitai's OK, publish and check how it
  renders on Spotify, RedCircle and YouTube, and share it on WhatsApp. Use
  when Amitai says "upload episode N", "put it on RedCircle", "העלאה",
  "YouTube", "יוטיוב", "publish", "Spotify", "share the episode" or "תפיץ את
  הפרק". Going live needs his explicit OK.
---
# Investing Bros upload, publish and share

Load `investing-bros-show` first: accounts, naming, the Drive tree and the WhatsApp destinations live there.

Use approved artwork supplied through `investing-bros-brand` for every cover and thumbnail. If artwork needs creation or revision, continue with that skill; do not redesign assets or maintain separate design rules in the upload workflow.

## When to use
When the episode folder is complete (audio, title and description files, exactly two segment packages and exactly three short packages, plus any full episode video or requested mid-form), for the review ping and uploads; again after Amitai's OK, to publish, check and share. Also use this for a private back-catalogue re-upload.

## Inputs
1. Episode number N, confirmed with Amitai.
2. From the episode root: `הקלטה-ערוכה-פרק-N.m4a` (never anything from `extras/`), `כותרות-פרק-N.txt` (title = the text after `בחירה סופית:`; if the file holds a single title, that one) and `תיאור-פרק-N.txt`. Episodes 1–7: the Docs `אפשרויות כותרת` / `תיאור הפרק`.
3. Exactly two complete packages in `segments/`, exactly three complete packages in `Shorts/`, plus `video/` when made and `mid-form/` when requested.
4. RedCircle login from show conventions → Roles and accounts. Never echo the password or put it in chat or logs.

### Back-catalogue re-upload
An already-published episode may have only its published audio and a finished video,
with no raw recording, transcript or `edit.json`. Download the RedCircle enclosure
or final Drive audio, transcribe it with `investing-bros-post-production`, and treat
that audio as the edited timeline (`start = 0`). Use the chapter offset tool in
`investing-bros-title-description` to locate that body after the video's teaser and
intro. Upload the replacement as Private and compare it with the current public
episode; replacing or deleting the public upload still requires Amitai's explicit OK.

## Steps

### 1. Review ping
List the episode folder and compare it with the show's Drive tree: the root holds only the audio and the two `.txt` files; `segments/` has exactly two complete packages (01 deep dive and 02 next-best qualifying topic); `Shorts/` has exactly three complete four-file packages. Then get a shareable link to the **episode folder** and ask the WhatsApp owner to send one message to `אחים להשקעות`: ready for review + link, ending with the show tag. Wait for Amitai's OK to upload. If Amitai directly asked in chat for this upload, that request is the upload OK and no duplicate review ping is needed; it is not permission to publish.

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

### 3. YouTube uploads (Private episode, Unlisted segments, Shorts after live)
**Preferred: the YouTube Data API** when `~/.config/youtube-uploader/` has `client_secret.json` and `token.json` on the Grok Bot box: `scripts/yt_upload.py` (resumable, frees the browser, Private-only, ~6 uploads/day, reauth every ~7 days while the app is in Testing). See [references/youtube-api.md](references/youtube-api.md). Otherwise, or if it fails, use Studio in the browser as below. Either way, publishing still needs Amitai's OK.

Follow [the Studio checklist](references/youtube-studio.md). In particular, switch
from the Editor account's personal **Grok Bot** channel to the **אחים להשקעות**
brand channel before selecting files. Upload the full episode as **Private** and
the two segment evaluations as **Unlisted**; choose **No, it's not made for kids**.
The API uploader creates Private uploads, so switch both segment videos to Unlisted
in Studio before card/end-screen review. Do not upload the three Shorts until the
full episode is live.
- **Video episode** (`video/`): title from `כותרות-פרק-N.txt`, description from `video/תיאור-פרק-N-youtube.txt`, pasted **plain** (no RTL marks). It must include the `האזינו בספוטיפיי:` line (show link until step 5 swaps in the episode link).
  Add one or two previous-episode video elements (best related first) plus Subscribe
  across the final 20 seconds, exactly over the canonical outro; verify them on the
  Studio Editor preview while Private, then on the watch page after publication.
- **Exactly three Shorts** (`Shorts/`): only after the full episode is live, upload with the title, description, Related video, pinned comment and `.srt` from each `youtube-שורט-NN.md`.
- **Exactly two segment videos** (`segments/`; segment 01 is the required deep dive): follow `investing-bros-segment-video`.
- **Mid-form** (`mid-form/`): title and description from its `.txt`, with the full-episode link.
- Thumbnail: the episode's 16:9 `promo/thumbnail-פרק-N.jpg` (made from the square cover by `investing-bros-brand`). If it isn't approved yet, upload without one and say so.

### 4. Publish (only after Amitai's OK in chat)
Order ([references/publish-order.md](references/publish-order.md)): RedCircle publish (it feeds Spotify) → rerun `check_titles_match.py` on the live YouTube and RedCircle titles → Spotify ingests it (a few hours) → the YouTube description's `האזינו בספוטיפיי:` line (after the disclaimer, before the chapters; `check_copy.py --youtube`) gets the Spotify episode link, replacing the show link, on the episode and its shorts. Publishing always includes RedCircle. If Amitai is fine waiting, suggest publishing RedCircle first so the episode link exists before YouTube goes Public. Then the segment videos go Public, then shorts. Segment videos link back through their own description, card, end screen and pinned comment; do not add segment links to the full episode's description. Switch the YouTube uploads he named to Public (or schedule them as he says). Nothing goes live on its own. After the YouTube uploads go public, a daily morning analytics report runs for one week.

### 5. Check how it renders
- **YouTube**: open the public watch page. Every description line right-aligned with its timestamp on the right, times in order, chapters on the progress bar. A wrong line almost always starts with English; reword it to start with Hebrew.
- **RedCircle**: the public episode page shows the title with `?` at the end.
- **Spotify** (a few hours after publishing; RedCircle feeds it): open [the show](https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk). Without a browser, read the newest episode's title through `https://open.spotify.com/embed/show/4fREAemgQDMWIUK58N5Jjk`. Check:
  - the episode is there, with the exact title (no en dash, `?` at the end of the sentence)
  - the description lines read right-to-left and nothing visible is scrambled
  - chapters show in the Spotify app (episode page → chapters)
  - **then link it on YouTube**: copy the Spotify episode URL (`https://open.spotify.com/episode/<id>`, without `?si=`), edit the public episode's YouTube description to replace the show link on the `האזינו בספוטיפיי:` line with it, and do the same on that episode's shorts. Update `video/תיאור-פרק-N-youtube.txt` and each `youtube-שורט-NN.md` to match. Editing a Public video's description is part of the approved publish, not a new public action.

  Wrong on Spotify but right on RedCircle: tell Amitai what you saw (screenshot) and open a GitHub issue on the repo; don't change show settings or re-publish to fix it.

Video stays on YouTube. Uploading video to Spotify cuts that episode off from RedCircle (no automatic updates, no RedCircle stats or ads), so do it only if Amitai decides to.

### 6. WhatsApp (when Amitai asks)
Follow [references/share-whatsapp.md](references/share-whatsapp.md): exact group, text ending with the show tag, public link, sent by the WhatsApp owner, confirmation reported.

## Done when
- Before the OK: RedCircle draft saved with the YouTube title (`check_titles_match.py` passes) and screenshot-checked; the full episode when made is uploaded with its previous-episode + Subscribe end screen over the canonical outro, both segment videos are uploaded for review, all three Shorts have completed Telegram approval and Drive filing, and the review ping was sent.
- After the OK: live on RedCircle **and** YouTube with identical titles; both segment videos are Public after the full episode; all three Shorts were uploaded only after the episode went live; the episode is listed on Spotify; and the Spotify, RedCircle and YouTube checks passed (or the problem is with Amitai and in an issue). The YouTube episode and all three Shorts link the Spotify **episode** URL, not the show.
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
- Publish, set anything Public, submit to directories or post on WhatsApp/Telegram without Amitai's explicit OK in chat.
- Echo or paste the password.
- Upload raw or `extras/` audio.
- Paste Hebrew into RedCircle without the RTL + `?` marks, or put those marks in the YouTube copy.
- Upload video to Spotify, or change RedCircle show settings, without Amitai's decision.
- Drive WhatsApp Web yourself.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).

Publish order: `references/publish-order.md` (RedCircle, Spotify, YouTube Spotify line, then Shorts).
