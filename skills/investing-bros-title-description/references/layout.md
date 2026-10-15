# Title and description layout

Both Docs live in the episode root, in Hebrew, as plain text (no direction marks; `investing-bros-episode-upload` adds those to the copy pasted into RedCircle). `scripts/check_copy.py` enforces everything marked **(checked)**.

## `אפשרויות כותרת`

```
1. פרק N – <נושא>: <שאלה>?
2. פרק N – <נושא>: <שאלה>?
3. פרק N – <שאלה>?
4. פרק N – <נושא> מול <נושא>: <שאלה>?
5. פרק N – <נושא>: <הצהרה קצרה>

בחירה סופית:
```

- Exactly five options, numbered `1.`–`5.` **(checked)**
- Every option starts `פרק N – ` with an **en dash** `–` (U+2013) and a space on each side **(checked)**. The Drive folder name uses an em dash; the title never does.
- After the prefix: 50 characters or less is the aim, 60 is the hard limit **(checked)**.
- At least three of the five are questions **(checked)**, one question per title, at the end **(checked)**.
- No em dash `—` anywhere **(checked)**. Where you'd reach for one, use `:` or `,`, or split the sentence.
- No `!`, no emoji, no hype words **(checked)**.
- `בחירה סופית:` stays empty for Amitai **(checked: nothing after it but his pick)**. If he cuts the Doc down to one title, that title is the pick.

## `תיאור הפרק`

Three blocks separated by blank lines:

```
<שאלה פותחת?> <משפט או שניים: נושא הצלילה, החדשות המרכזיות, רעיונות ההשקעה.>

אין כאן המלצת השקעה. רק שיחה.

0:00 פתיחה
1:05 חדשות השבוע: <נושא>
11:30 <נושא הצלילה>: <שאלה>?
31:10 רעיון השקעה – אמיתי
36:00 רעיון השקעה – נדב
```

1. **Intro**: one cohesive paragraph, about 450 characters or less **(warned)**. Open with a question when one fits **(warned, not required)**. Name only what was actually discussed.
2. **Disclaimer**: exactly `אין כאן המלצת השקעה. רק שיחה.` on its own line **(checked)**.
3. **Chapters**: time first, `M:SS` or `H:MM:SS` past an hour, start at `0:00`, times go up **(checked)**. On the **edited** audio timeline: `edited = raw − start`, with `start` from `extras/edit.json`. 8–14 chapters for a ~45 min episode. Short labels (60 characters or less, **warned**); a chapter may be a question. An en dash inside a chapter label (`רעיון השקעה – אמיתי`) is fine; an em dash is not **(checked)**.

The video episode has a cold open + intro (~28 s) in front. Its YouTube description offsets every chapter by that length; the Doc stays on the edited-audio timeline.

## Past episodes (for tone and length)

| Ep | Title as written | Note |
|---|---|---|
| 2 | `ניו פריימס: איך זן חדש של חברות טכנולוגיה משנה את חוקי המשחק` | Right shape (topic: hook), but 58 characters and no `פרק 2 – ` prefix in the Doc |
| 4 | `פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?` | **The model.** 34 characters, topic then a real question the episode debates |
| 6 | `פרק 6 - מהפכת הטוקניזציה` | Hyphen instead of en dash, no question. Off-layout; don't copy |
| 7 | `פרק 7- זהב` (working title, from the Drive folder) | One word, no hook. Rewritten 2026-10-15 to five options led by the episode's own question: `פרק 7 – זהב: למה להחזיק מתכת שלא מייצרת כלום?` |

Episode 5's (`אנרגיה גרעינית`) final title wasn't in Drive when this skill was written. Add it here when Amitai shares it. When an episode has no `אפשרויות כותרת` Doc, the Drive folder name is the working title; say so in the hand-back.

Past slips the checker now catches:
- Episode 2's `.txt` draft opened `אחים להשקעות פרק 2 — שני אחים מדברים...` (em dash).
- Episode 4's description Doc had no disclaimer line.
- Episode 2 spelled `ספייסקס` in the draft; the brand spelling is `ספייסאקס` (`investing-bros-show` → Hebrew).

## Good and bad titles

| | Title | Why |
|---|---|---|
| ✓ | `פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?` | Names the topic, asks the question the deep dive argues |
| ✓ | `פרק 7 – זהב: למה הבנקים המרכזיים קונים?` | Concrete, answerable from the episode (only if they discussed it) |
| ✗ | `פרק 7 – הסוד שהבנקים לא מספרים לכם על זהב` | Clickbait: promises a secret the episode doesn't reveal |
| ✗ | `פרק 7 – זהב — האם זה הזמן לקנות?` | Em dash, and reads as a buy call |
| ✗ | `פרק 7 – כל מה שצריך לדעת על זהב, ביטקוין, בנקים מרכזיים ואינפלציה` | Too long, no hook |
| ✗ | `פרק 7 – זהב!!! 🚀` | Hype, emoji |
