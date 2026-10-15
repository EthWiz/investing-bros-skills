---
name: investing-bros-title-description
description: >-
  Write the Hebrew title options and episode description for an Investing
  Bros / אחים להשקעות episode, in the show's layout: five concise, engaging
  titles that lead with a real question (no clickbait, no em or en dashes), and the
  description Doc (intro paragraph, disclaimer, time-first chapters), checked
  by a script before they go in Drive. Use when Amitai asks for "titles",
  "a title", "description", "כותרת", "כותרות", "אפשרויות כותרת", "תיאור הפרק"
  or "תיאור" for episode N, and at step 7 of investing-bros-post-production.
---
# Investing Bros titles and description

Load `investing-bros-show` first. Episode number, Drive tree, Hebrew spellings, the disclaimer and the fact-check rule live there.

## When to use
- As step 7 of `investing-bros-post-production`, once the edited timeline (`extras/edit.json`) and the transcript exist.
- On its own, when Amitai asks for new or better titles or a description for an episode that's already edited.

The full layout, past examples and good/bad titles are in [references/layout.md](references/layout.md). Read it before writing.

## Inputs
- Episode number N **as Amitai states it**.
- The transcript (`extras/transcript/segments.json` or `transcript.txt`) and `extras/edit.json` (`start` in raw seconds).
- The episode's `brief/` docs, for the deep-dive topic and the sources behind any number.
- Existing Docs `אפשרויות כותרת` / `תיאור הפרק`, if Amitai wants them redone (keep what he already marked).

## Steps

### 1. Find the episode's story
Read the transcript. Note: the deep-dive topic and the question the brothers actually argue about, the 3–5 news items that took real time, each brother's investment idea, and any line that would make a listener stop scrolling. The **deep dive is the title's subject**; news items go in the description, not the title.

### 2. Write five titles
Layout: `פרק N - <נושא>: <שאלה>?` (episode 4 is the model: `פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?`).
- **Lead with a question.** At least three of the five are questions; the question goes at the end, after the topic. Question-first (`פרק N - <שאלה>?`) is fine for one or two options.
- **Concise.** 50 characters or less after `פרק N - `; 60 is the hard limit.
- **Engaging, not clickbait.** The question must be one the episode really discusses, and a listener should feel the episode delivered on it. No secrets, no "you won't believe", no promised returns, no hype words, no `!`, no emoji.
- **No buy or sell call.** "לקנות או לחכות?" only if the episode frames it as a debate, never as advice.
- **No em dash `—` and no en dash `–`.** Both read as AI-written. Use `:` or `,`. The only dash is the plain hyphen `-` after the episode number.
- Give five different angles, e.g. the debate, the stakes, the "what is it", the investor angle, the contrarian view.
- English company and product names stay in English (`NVIDIA`, `CoreWeave`); Hebrew brand spellings from `investing-bros-show`.
- A number goes in a title only if it was said in the episode **and** you've checked it against a source.

### 3. Write the description
Three blocks, blank line between them (exact layout in references):
1. **Intro.** One paragraph, about 450 characters or less. Open with a question when one fits naturally, then the deep dive, the main news items and the investment ideas, only as discussed.
2. **Disclaimer**, exactly: `אין כאן המלצת השקעה. רק שיחה.`
3. **Chapters**, time first, from `0:00`, on the edited timeline (`edited = raw − start`). 8–14 chapters, short labels, names spelled as in the brand list.

No em dash or en dash anywhere: intro, chapters or titles. Plain hyphen only.

### 4. Check
Save each as a plain `.txt` and run:
```bash
python3 scripts/check_copy.py --titles titles.txt --description description.txt --episode N
```
Fix every `error:` and rerun until it prints `0 error(s)`. Read each `warn:` and either fix it or mention it in the hand-back. Then fact-check every number and claim in both texts (`investing-bros-show` → Hebrew); anything you can't source comes out.

### 5. Write the Docs
Write the checked text into the two Google Docs in the episode root, `אפשרויות כותרת` and `תיאור הפרק` (Drive rules in `investing-bros-show`). Plain text: no direction marks, no bold. If the Docs already exist, update them in place; don't create a second copy. The `.txt` files go in `extras/`.

### 6. Ask Amitai to pick
Send him the five titles in chat, numbered as in the Doc, with your recommendation and one line on why. He fills `בחירה סופית:` (or tells you, and you fill it). Don't pick for him.

## Hand back
- Links to both Docs
- The five titles, with your recommended one
- `check_copy.py` result (0 errors) and any warnings you kept, with the reason
- Any claim or number you removed because it couldn't be verified
- Next: `investing-bros-episode-upload` uses the text after `בחירה סופית:` and the full description

## Never
- Use an em dash `—` or en dash `–` in a title, description or chapter. Only the plain hyphen `-`.
- Write a title the episode doesn't deliver on, or one that sounds like a buy/sell recommendation.
- Put a number or claim in the copy that wasn't said in the episode or isn't fact-checked.
- Add direction marks to the Docs (they're added only at upload).
- Choose the final title yourself, or upload or publish anything (`investing-bros-episode-upload`, and only with Amitai's OK).
- Skip `check_copy.py`, or edit it locally to make a draft pass. If a rule is wrong, propose the change as a PR (working rules in `investing-bros-show`).
