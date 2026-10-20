---
name: investing-bros-title-description
description: >-
  Write the packaging for an Investing Bros / אחים להשקעות episode: five
  concise Hebrew title options that lead with a real question (no clickbait,
  no em or en dashes), the description (intro, disclaimer, time-first chapters
  that work on YouTube and Spotify), checked by a script and saved as .txt
  files in the episode's Drive folder, and thumbnail headline options handed to `investing-bros-brand` for artwork. Use when Amitai asks for "titles", "a title", "description",
  "כותרת", "כותרות", "תיאור", "cover art", "a thumbnail", "תמונה ממוזערת",
  "קאבר לפרק" or a prompt for an AI image tool, for episode N.
---
# Investing Bros titles, description and thumbnail

Load `investing-bros-show` first. Episode number, Drive tree, file names, Hebrew spellings, the disclaimer and the fact-check rule live there.

For every thumbnail or cover request, load `investing-bros-brand` for visual decisions, prompts and artwork. This skill supplies the words and episode context only.

## When to use
- After the audio edit, once the transcript and `extras/edit.json` exist.
- On its own, when Amitai wants new or better titles, a description or a thumbnail for an episode that's already edited.

Read [references/layout.md](references/layout.md) (layout, past titles, good and bad examples) before writing.

## Inputs
- Episode number N **as Amitai states it**.
- The transcript (`extras/transcript/segments.json` or `transcript.txt`) and `extras/edit.json` (`start` in raw seconds).
- The episode's `brief/` docs, for the deep-dive topic and the sources behind any number.
- Existing `כותרות-פרק-N.txt` / `תיאור-פרק-N.txt`, if Amitai wants them redone (keep what he already marked).

For a back-catalogue episode with no raw transcript or `edit.json`, transcribe the
published RedCircle/Drive audio and treat it as the edited timeline (`start = 0`).

## Steps

### 1. Find the episode's story
Read the transcript. Note the deep-dive topic and the question the brothers actually argue about, the 3–5 news items that took real time, each brother's investment idea, and any line that would make a listener stop scrolling. The **deep dive is the title's subject**; news items go in the description.

### 2. Write five titles
Layout: `פרק N - <נושא>: <שאלה>?` (episode 4 is the model: `פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?`).
- **Lead with a question.** At least three of the five are questions, at the end, after the topic.
- **Concise.** 50 characters or less after `פרק N - `; 60 is the hard limit.
- **Engaging, not clickbait.** A question the episode really discusses and delivers on. No secrets, no "you won't believe", no promised returns, no hype words, no `!`, no emoji.
- **No buy or sell call.** "לקנות או לחכות?" only if the episode frames it as a debate.
- **No em dash `—` or en dash `–`.** Use `:` or `,`. The only dash is the plain hyphen after the episode number.
- Five different angles: the debate, the stakes, the "what is it", the investor angle, the contrarian view.
- English company names stay in English (`NVIDIA`); Hebrew brand spellings from `investing-bros-show`. A number goes in a title only if it was said **and** checked against a source.

**Shorts titles** (requested by `investing-bros-shorts`): Hebrew only — the short hook, optionally one emoji. No English words, no `#shorts` or other hashtags, no pipe `|`, no `פרק N - ` prefix.

### 3. Write the description
Three blocks, blank line between them:
1. **Intro.** One paragraph, about 450 characters or less, starting with a Hebrew word. Open with a question when one fits, then the deep dive, the main news and the investment ideas, only as discussed.
2. **Disclaimer**, exactly: `אין כאן המלצת השקעה. רק שיחה.`
3. **Chapters**, time first and zero-padded, from `00:00`, on the edited timeline (`edited = raw − start`). 8–14 chapters, at least 30 seconds apart, labels under 40 characters. **Every label starts with a Hebrew word** (`01:05 מרוץ המודלים: OpenAI מול אנתרופיק`), or the line flips left-to-right on YouTube and Spotify.

When a finished YouTube video has a teaser and intro before that edited audio,
re-time the copy with `scripts/find_offset_and_shift.py VIDEO AUDIO DESCRIPTION OUT`.
It finds the body by audio correlation, adds `00:00 טעימה מהפרק`, and shifts every
chapter. A score below 0.5 means the edits differ; stop and transcribe the video.
`--offset S` uses a separately verified offset.

### 4. Check
Save as `כותרות-פרק-N.txt` and `תיאור-פרק-N.txt` (UTF-8, plain text) and run:
```bash
python3 scripts/check_copy.py --titles כותרות-פרק-N.txt --description תיאור-פרק-N.txt --episode N --spotify
```
Fix every `error:` and rerun until it prints `0 error(s)`. Fix each `warn:` or mention it in the hand-back. Then fact-check every number and claim in both files; anything you can't source comes out.

### 5. Save to Drive and ask Amitai to pick
Upload both files to the episode root (Drive connector, conversion to Google Docs **off**, `text/plain`). If they already exist, replace them; never make a second copy. Send Amitai the five titles in chat, numbered as in the file, with your recommendation and one line on why. He picks; you write his pick after `בחירה סופית:`, rerun the check and upload again. Don't pick for him.

### 6. Cover and thumbnail headline (every episode)
Prepare the artwork brief and 2–3 headline options following [references/thumbnail.md](references/thumbnail.md), preserving any supplied approved copy. Hand visual production to `investing-bros-brand`; load it to continue when the request includes finished artwork.

## Done when
- Episode root has `כותרות-פרק-N.txt` (with Amitai's pick after `בחירה סופית:`) and `תיאור-פרק-N.txt`.
- `check_copy.py --spotify` prints `0 error(s)` on both, and every claim is fact-checked.
- Cover/thumbnail: the headline brief is with Amitai or handed to `investing-bros-brand`; if artwork was also requested, brand owns its delivery.

## Hand back
- Links to both files
- The five titles, with your recommended one
- `check_copy.py` result and any warnings you kept, with the reason
- Any claim or number you removed because it couldn't be verified
- Artwork brief and headline options, plus any brand-skill deliverable if requested

## Never
- Use an em dash `—` or en dash `–` anywhere public. Only the plain hyphen `-`.
- Start a chapter label or the intro with English or a number.
- Write a title the episode doesn't deliver on, or one that sounds like a buy/sell recommendation.
- Put a number or claim in the copy that wasn't said in the episode or isn't fact-checked.
- Add direction marks to the `.txt` files (they're added only for RedCircle, at upload).
- Save the copy as a Google Doc, or choose the final title yourself.
- Skip `check_copy.py`, or edit it locally to make a draft pass. A wrong rule is a PR (show conventions → Working rules).
