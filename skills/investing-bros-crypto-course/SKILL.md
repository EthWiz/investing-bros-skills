---
name: investing-bros-crypto-course
description: >-
  Make the free seven-lesson Hebrew crypto course (קורס קריפטו) for the
  אחים להשקעות YouTube channel: the lesson plan, a slide deck per lesson
  in the show's brand with speaker notes, the recording script, and filing
  each lesson in its Drive folder. Carries Amitai's fixed stance (Bitcoin as
  the base, a small Ethereum position, great caution with every other token)
  and the disclaimer rules. Use when Amitai says "crypto course", "קורס
  קריפטו", "lesson N", "שיעור N", "slides for lesson N", "מצגת לשיעור",
  "תסריט לשיעור" or asks about the course plan.
---
# Investing Bros crypto course

Load `investing-bros-show` first (naming, Drive tree, approvals) and `investing-bros-brand` for every visual decision. The lesson plan and each lesson's status are in [references/course-plan.md](references/course-plan.md).

## When to use
Any work on the crypto course: planning a lesson, its slides, its script, filing it in Drive, or changing the course plan. The course is not an episode: it has no `פרק N` folder, RedCircle draft or episode number.

## Inputs
- Lesson number N **as Amitai states it**, and its topic from the course plan. A topic change is Amitai's call; update the plan when he makes it.
- For revisions: the lesson's existing deck link (course plan) or Drive folder.

## Course rules (decided 2026-10-26)
- Free, on the אחים להשקעות channel as one playlist, seven lessons, Hebrew, for Israeli beginners. Risk is covered inside each lesson, not as a lesson of its own. Each lesson stands on its own, since most viewers arrive from search.
- **The stance, the same in every lesson that touches it:** Bitcoin is the base; of all the altcoins, only Ethereum gets a small position; great caution with every other token, and in most cases don't touch it. Present it as Amitai's personal approach.
- **Disclaimer:** lesson 1 opens with a disclaimer slide (educational content, not investment advice; Amitai isn't a licensed investment adviser; invest only what you can afford to lose). Any slide stating the stance carries the line `זו הגישה האישית שלי ולא ייעוץ השקעות מותאם אישית`. Never say "buy now", a target price, or a percentage of anyone's portfolio.
- Facts follow the show's hard rules: every number, date and claim has a source URL in the speaker notes or the script, and Israel-specific facts (tax, exchanges, banks, funds) are checked again before recording because they change.

## Steps
1. **Plan.** Read the lesson's row in the course plan. Write the outline (one sentence per part, 12–16 slides) and confirm it with Amitai before building.
2. **Research.** Collect sources for every fact. If something can't be verified, leave it out or mark it in the speaker notes as unchecked.
3. **Deck.** Build it as a Claude Slides artifact: brand palette and Heebo from `investing-bros-brand`, Hebrew right-to-left as in [references/slides-rtl.md](references/slides-rtl.md), speaker notes in Hebrew on every slide as talking points. Title the deck `קורס קריפטו - שיעור N: <נושא>` (plain hyphen). Add the deck link to the course plan.
4. **Review.** Send Amitai the deck link and apply his changes. The link is private until he shares it from the deck's Share menu.
5. **Drive.** Export the deck as a PDF (the deck page's export, which needs a claude.ai sign-in; if the browser isn't signed in, ask Amitai to sign in or to export it himself) and upload it to the lesson's folder as `מצגת-שיעור-N.pdf`, replacing any older file of that name. Confirm it shows as `application/pdf`.
6. **Script.** When Amitai asks, write the recording script from the deck: hook, the deck's parts in order, recap, the pointer to the next lesson. Save it as plain text, conversion to Google Docs off, as `תסריט-שיעור-N.txt` in the lesson's folder.
7. **Video and upload** are not defined for the course yet. Ask Amitai which episode skills to reuse before cutting, titling or uploading a lesson; nothing goes public without his OK.

## Done when
- The lesson's folder `קורס קריפטו/שיעור N — נושא/` holds `מצגת-שיעור-N.pdf` (and `תסריט-שיעור-N.txt` when a script was asked for).
- The course plan lists the lesson's deck link and current status.

## Hand back
The deck link, the Drive folder link, the sources used, any fact left unchecked, and anything about the right-to-left layout not yet checked in the rendered deck.

## Never
- Recommend a specific amount, percentage, entry price or timing.
- Present any token other than Bitcoin and Ethereum as something to buy.
- Put English words inside a Hebrew sentence on a slide (see the RTL reference).
- Create a second `קורס קריפטו` folder or a second folder for the same lesson; find them by the `שיעור N` prefix.
