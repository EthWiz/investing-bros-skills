---
name: investing-bros-episode-upload
description: >-
  Upload an approved Investing Bros / אחים להשקעות episode to RedCircle as a
  draft: edited audio, final Hebrew title and description with the RTL + "?"
  fix, episode number. Use when Amitai says "upload episode N", "put it on
  RedCircle", "העלאה". Publishing live needs his explicit OK.
---
# Investing Bros episode upload

Load `investing-bros-show` first — accounts, naming and the Drive tree live there.

## When to use
After post-production review, when Amitai says to upload (or explicitly asks for it). Host is RedCircle.

## Inputs
1. Episode number N — confirm with Amitai.
2. **Edited** audio from the episode folder **root** (the approved cut — never anything from `extras/`, never raw). Keep a local copy for the file picker.
3. Final copy from the episode Docs:
   - Title: text after `בחירה סופית:` in `אפשרויות כותרת`; if the Doc was reduced to a single title, use that.
   - Description: full text of `תיאור הפרק` (intro, disclaimer, chapters — chapters stay time-first).
4. RedCircle login from show conventions → accounts. Never echo the password or put it in chat or logs.

## Steps

### 1. Make the RTL-safe copy
RedCircle's editor is left-to-right; plain Hebrew with `?` or English names renders scrambled. Generate marked copy with the script — never by hand:
```bash
python3 scripts/rtl_fix.py --title  title.txt       > title-rtl.txt
python3 scripts/rtl_fix.py --description description.txt > description-rtl.txt
```
Why and what the marks do: [references/redcircle-rtl.md](references/redcircle-rtl.md). Put both `-rtl.txt` files in the episode's `extras/` afterwards.

### 2. RedCircle click-path (verified)
1. Open `https://app.redcircle.com/shows` and sign in.
2. Open the show **אחים להשקעות** (Investing Bros).
3. **Add / New Episode** → a URL like `/shows/{showId}/ep/create`.
4. **Title**: paste the contents of `title-rtl.txt` via clipboard (select-all, paste). Retyping strips the marks.
5. **Description**: paste `description-rtl.txt` the same way; keep the blank lines between blocks.
6. **Upload File**: the edited m4a/mp3. On a network error, retry once with the same file. If `.m4a` is rejected, a byte-identical copy renamed `.mp3` uploads fine.
7. **More Options** → **Episode Number** = N, when the field exists.
8. **Save as Draft** / leave **Unpublished**.
9. **Insertion points** (pre/mid/post ads): RedCircle may add defaults after processing. Leave them unless Amitai asks — they're dynamic-ad placeholders, not part of the recording. Don't block the draft on them.

### 3. Verify
Screenshot the title and description in the editor. `?` must sit at the end of the Hebrew sentence and timestamps must stay at the start of chapter lines. If an edited-back-and-forth draft still looks broken, create a **fresh draft** with the marked copy instead of patching it, and leave the old draft for Amitai to decide about.

## Hand back
- Unpublished-draft confirmation and the app episode URL
- Title used and episode number
- Any upload retries or blockers

Then send the draft link to Amitai, via the WhatsApp owner if he wants it in the group. Announce the episode as live on WhatsApp only if Amitai asked. Once it's published, sharing is `investing-bros-share-new-episode`.

Update this skill when the RedCircle UI path changes.

## Never
- Publish live, submit to directories or make public without Amitai's explicit OK.
- Echo or paste the password.
- Upload raw or `extras/` audio.
- Paste Hebrew copy without the RTL + `?` marks.
