---
name: Investing Bros episode upload
description: >-
  Use this when uploading an approved Investing Bros / אחים להשקעות episode to
  RedCircle (edited audio + Hebrew Docs); draft by default, publish only with
  explicit OK.
---
# Investing Bros episode upload

Use when Amitai is ready to put an Investing Bros / אחים להשקעות episode on the podcast host after post-production review (or he explicitly says to upload).

**Host:** [RedCircle](https://app.redcircle.com) — this show’s host. Do **not** use RSS.com unless Amitai says the host changed.

**Credentials**
- Email: `ami.ruskin@gmail.com`
- Password: env secret `REDCIRCLE_PASSWORD` (never echo / paste into chat or logs)
- If the env secret is missing in the browser process, use in-chat password form on the live page — never ask him to paste the password in chat.

## Before you start
1. Confirm episode number and that the **edited** audio is the approved cut (Drive episode folder **root**, not `extras/` / not raw).
2. Read final copy from the episode Google Docs:
   - `תיאור הפרק` — description + disclaimer + chapters
   - `אפשרויות כותרת` — use text under `בחירה סופית:` if present; if the Doc was reduced to a single title, use that title
3. Chapters stay **time-first** like פרק 1: `1:05 נושא` (do not flip to `נושא — זמן` unless Amitai asks).
4. Hebrew brand spellings from memory (e.g. ספייסאקס).
5. Keep a local copy of edited audio handy for the file picker (from Drive download or `/workspace/investing-bros/...`).

## RedCircle click-path (verified)
1. Open `https://app.redcircle.com/shows` and sign in.
2. Open the show **אחים להשקעות** (Investing Bros).
3. **Add / New Episode** → lands on a create URL shaped like `/shows/{showId}/ep/create`.
4. Fill **Title** (final Hebrew title from the Titles Doc).
5. Fill **Description** by pasting the Description Doc text (preserve blank lines / paragraphs).
6. **Upload File** — select the edited m4a/mp3. If the first upload fails with a network error, retry once with the same file.
7. **More Options** → set **Episode Number** when the field exists.
8. **Save as Draft** / leave **Unpublished**.  
   **Do not** hit public Publish / submit to directories / make live unless Amitai explicitly said go live.
9. **Insertion points** (ads pre/mid/post): RedCircle may auto-add defaults after processing. Leave defaults unless Amitai asks to move them — they are placeholders for dynamic ads, not part of the recording. Do not block the draft on fine-tuning them.

## After upload
1. Report: unpublished draft confirmation, app episode URL, title used, episode number, any upload retry/blocker.
2. Ping Amitai Personal / Investing Bros chat with the draft link.
3. WhatsApp host-live notice only if Amitai asked — default post-prod ping is Drive review only.
4. Tighten this skill only when the UI path changes.

## Safety
- Never echo the password.
- Never publish live without explicit OK.
- Not for Genesis / Hyperliquid work.
- Do not upload raw/`extras` audio.
