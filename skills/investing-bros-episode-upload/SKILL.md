---
name: investing-bros-episode-upload
description: >-
  Take a finished Investing Bros / אחים להשקעות episode out: review ping,
  RedCircle draft (edited audio, final Hebrew title and description with the
  RTL + "?" fix, episode number), YouTube uploads (video episode, shorts,
  mid-form) as private, then, with Amitai's OK, publish and check how it
  renders on Spotify, RedCircle and YouTube, and share it on WhatsApp. Use
  when Amitai says "upload episode N", "put it on RedCircle", "העלאה",
  "YouTube", "יוטיוב", "publish", "Spotify", "share the episode" or "תפיץ את
  הפרק". Going live needs his explicit OK.
---
# Investing Bros upload, publish and share

Load `investing-bros-show` first: accounts, naming, the Drive tree and the WhatsApp destinations live there.

Use approved artwork supplied through `investing-bros-brand` for every cover and thumbnail. If artwork needs creation or revision, continue with that skill; do not redesign assets or maintain separate design rules in the upload workflow.

## When to use
When the episode folder is complete (audio, title and description files, plus whichever of video, shorts and mid-form were made), for the review ping and the uploads; again after Amitai's OK, to publish, check and share.

## Inputs
1. Episode number N, confirmed with Amitai.
2. From the episode root: `הקלטה-ערוכה-פרק-N.m4a` (never anything from `extras/`), `כותרות-פרק-N.txt` (title = the text after `בחירה סופית:`; if the file holds a single title, that one) and `תיאור-פרק-N.txt`. Episodes 1–7: the Docs `אפשרויות כותרת` / `תיאור הפרק`.
3. `video/`, `shorts/`, `mid-form/` contents, when made.
4. RedCircle login from show conventions → Roles and accounts. Never echo the password or put it in chat or logs.

## Steps

### 1. Review ping
List the episode folder and compare it with the show's Drive tree: the root holds only the audio and the two `.txt` files; every short has its four files. Then get a shareable link to the **episode folder** and ask the WhatsApp owner to send one message to `אחים להשקעות`: ready for review + link, ending with the show tag. Wait for Amitai's OK to upload.

### 2. RedCircle draft
Make the RTL-safe copy with the script, never by hand:
```bash
python3 scripts/rtl_fix.py --title  title.txt       > title-rtl.txt     # title.txt = the final title, one line
python3 scripts/rtl_fix.py --description תיאור-פרק-N.txt > description-rtl.txt
```
Why and what the marks do: [references/redcircle-rtl.md](references/redcircle-rtl.md). Put both `-rtl.txt` files in `extras/`.
1. Open `https://app.redcircle.com/shows`, sign in, open **אחים להשקעות**.
2. **Add / New Episode** (a URL like `/shows/{showId}/ep/create`).
3. **Title** and **Description**: paste the `-rtl.txt` contents via clipboard (select-all, paste). Typing strips the marks. Keep the blank lines.
4. **Upload File**: the edited audio. On a network error, retry once. If `.m4a` is rejected, a byte-identical copy renamed `.mp3` uploads fine.
5. **More Options** → **Episode Number** = N, when the field exists.
6. **Save as Draft** / leave **Unpublished**. Leave RedCircle's default ad insertion points unless Amitai asks.
7. Screenshot the title and description: `?` at the end of the Hebrew sentence, timestamps at the start of chapter lines. A draft edited back and forth that still looks broken: make a **fresh draft** and leave the old one for Amitai.

### 3. YouTube uploads (private)
YouTube Studio in the box browser (already signed in). Upload as **Private**; "No, it's not made for kids".
- **Video episode** (`video/`): title from `כותרות-פרק-N.txt`, description from `video/תיאור-פרק-N-youtube.txt`, pasted **plain** (no RTL marks).
- **Shorts** (`shorts/`): title, description, Related video, pinned comment and `.srt` from each `youtube-שורט-NN.md`. The full-episode link goes in once the episode has a URL.
- **Mid-form** (`mid-form/`): title and description from its `.txt`, with the full-episode link.
- Thumbnail from `promo/`, if Amitai approved one.

### 4. Publish (only after Amitai's OK in chat)
Publish the RedCircle draft, and switch the YouTube uploads he named to Public (or schedule them as he says). Nothing goes live on its own. After the YouTube uploads go public, a daily morning analytics report runs for one week.

### 5. Check how it renders
- **YouTube**: open the public watch page. Every description line right-aligned with its timestamp on the right, times in order, chapters on the progress bar. A wrong line almost always starts with English; reword it to start with Hebrew.
- **RedCircle**: the public episode page shows the title with `?` at the end.
- **Spotify** (a few hours after publishing; RedCircle feeds it): open [the show](https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk). Without a browser, read the newest episode's title through `https://open.spotify.com/embed/show/4fREAemgQDMWIUK58N5Jjk`. Check:
  - the episode is there, with the exact title (no en dash, `?` at the end of the sentence)
  - the description lines read right-to-left and nothing visible is scrambled
  - chapters show in the Spotify app (episode page → chapters)

  Wrong on Spotify but right on RedCircle: tell Amitai what you saw (screenshot) and open a GitHub issue on the repo; don't change show settings or re-publish to fix it.

Video stays on YouTube. Uploading video to Spotify cuts that episode off from RedCircle (no automatic updates, no RedCircle stats or ads), so do it only if Amitai decides to.

### 6. WhatsApp (when Amitai asks)
Follow [references/share-whatsapp.md](references/share-whatsapp.md): exact group, text ending with the show tag, public link, sent by the WhatsApp owner, confirmation reported.

## Done when
- Before the OK: RedCircle draft saved and screenshot-checked; YouTube uploads private with titles and descriptions; review ping sent.
- After the OK: live on RedCircle and YouTube, and the Spotify, RedCircle and YouTube checks passed (or the problem is with Amitai and in an issue).
- WhatsApp sends confirmed, when asked.

## Hand back
- RedCircle draft URL (or public URL), title used, episode number
- YouTube links, with each video's visibility
- The render checks: Spotify, RedCircle, YouTube, with anything that looked wrong
- Upload retries or blockers
- WhatsApp send status, when asked

Update this skill when the RedCircle or YouTube Studio click-path changes.

## Never
- Publish, set anything Public, submit to directories or post on WhatsApp/Telegram without Amitai's explicit OK in chat.
- Echo or paste the password.
- Upload raw or `extras/` audio.
- Paste Hebrew into RedCircle without the RTL + `?` marks, or put those marks in the YouTube copy.
- Upload video to Spotify, or change RedCircle show settings, without Amitai's decision.
- Drive WhatsApp Web yourself.
- Write your own code where this skill has a script, or work around a missing step without saying so (show conventions → Working rules).
