# Title and description layout

Both Docs live in the episode root, in Hebrew, as plain text (no direction marks; `investing-bros-episode-upload` adds those to the copy pasted into RedCircle). `scripts/check_copy.py` enforces everything marked **(checked)**.

## `אפשרויות כותרת`

```
1. פרק N - <נושא>: <שאלה>?
2. פרק N - <נושא>: <שאלה>?
3. פרק N - <שאלה>?
4. פרק N - <נושא> מול <נושא>: <שאלה>?
5. פרק N - <נושא>: <הצהרה קצרה>

בחירה סופית:
```

- Exactly five options, numbered `1.`–`5.` **(checked)**
- Every option starts `פרק N - ` with a **plain hyphen** `-` and a space on each side **(checked)**. The Drive folder name uses an em dash; the title never does.
- After the prefix: 50 characters or less is the aim, 60 is the hard limit **(checked)**.
- At least three of the five are questions **(checked)**, one question per title, at the end **(checked)**.
- No em dash `—` and no en dash `–` anywhere **(checked)**: both read as AI-written (Amitai, 2026-10-15). Where you'd reach for one, use `:` or `,`, or split the sentence.
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
31:10 רעיון השקעה - אמיתי
36:00 רעיון השקעה - נדב
```

1. **Intro**: one cohesive paragraph, about 450 characters or less **(warned)**. Open with a question when one fits **(warned, not required)**. Name only what was actually discussed.
2. **Disclaimer**: exactly `אין כאן המלצת השקעה. רק שיחה.` on its own line **(checked)**.
3. **Chapters**: time first, `M:SS` or `H:MM:SS` past an hour, start at `0:00`, times go up **(checked)**. On the **edited** audio timeline: `edited = raw − start`, with `start` from `extras/edit.json`. 8–14 chapters for a ~45 min episode. Short labels (60 characters or less, **warned**); a chapter may be a question. A plain hyphen inside a chapter label (`רעיון השקעה - אמיתי`) is fine; an em or en dash is not **(checked)**.

### Hebrew next to English and numbers (YouTube, RedCircle, WhatsApp)
Each line is laid out right-to-left or left-to-right by its **first letter**. A line whose first letter is English flips to left-to-right, so in a Hebrew description its timestamp jumps to the other side and its numbers and words come out in the wrong order (episode 5 on YouTube: `00:46 Anthropic: ...`, `09:46 AMD ...`, `31:16 SMR: ...`, `47:45 Oracle: ...`).
- Every chapter label starts with a **Hebrew word**: `1:05 מרוץ המודלים: OpenAI מול אנתרופיק`, not `1:05 OpenAI מול אנתרופיק` **(checked)**. Not a number, a symbol or `- ` either.
- The intro's first line starts with a Hebrew word too **(checked)**.
- English names and numbers are fine **inside** a Hebrew line (`סייבר: Zscaler ו-CrowdStrike`).
- Timestamps only at the start of the line, as `M:SS` or `H:MM:SS` (no `00:` hours prefix under an hour, no `-` after the time).
- YouTube chapter rules: first at `0:00`, at least 3, going up, at least 10 seconds apart **(checked)**, or YouTube shows no chapters.
- YouTube gets the plain Doc text. The RTL marks from `investing-bros-episode-upload` are for RedCircle only.

The video episode has a cold open + intro (~28 s) in front. Its YouTube description offsets every chapter by that length; the Doc stays on the edited-audio timeline.

## Past episodes (for tone and length)

| Ep | Title as written | Note |
|---|---|---|
| 2 | `ניו פריימס: איך זן חדש של חברות טכנולוגיה משנה את חוקי המשחק` | Right shape (topic: hook), but 58 characters and no `פרק 2 - ` prefix in the Doc |
| 4 | `פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?` | **The model.** 34 characters, topic then a real question the episode debates |
| 6 | `פרק 6 - מהפכת הטוקניזציה` | Right dash, but no question and no hook |
| 7 | `פרק 7 - למה כולם קונים זהב?` (YouTube) | Good hook: short, a real question the episode answers. Right dash. "קונים" leans toward a buy call. Suggested fix: `פרק 7 - למה כולם חוזרים לזהב?` |

Episode 5's (`אנרגיה גרעינית`) final title wasn't in Drive when this skill was written. Add it here when Amitai shares it. When an episode has no `אפשרויות כותרת` Doc, check the published YouTube title before treating the Drive folder name as the working title (episode 7's folder said `פרק 7- זהב`; YouTube had the real title). Read a YouTube title without a browser through `https://www.youtube.com/oembed?url=<video URL>&format=json`.

Past slips the checker now catches:
- Episode 2's `.txt` draft opened `אחים להשקעות פרק 2 — שני אחים מדברים...` (em dash).
- Episode 4's description Doc had no disclaimer line.
- Episode 2 spelled `ספייסקס` in the draft; the brand spelling is `ספייסאקס` (`investing-bros-show` → Hebrew).

## Good and bad titles

| | Title | Why |
|---|---|---|
| ✓ | `פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?` | Names the topic, asks the question the deep dive argues |
| ✓ | `פרק 7 - זהב: למה הבנקים המרכזיים קונים?` | Concrete, answerable from the episode (only if they discussed it) |
| ✗ | `פרק 7 - הסוד שהבנקים לא מספרים לכם על זהב` | Clickbait: promises a secret the episode doesn't reveal |
| ✗ | `פרק 7 - זהב — האם זה הזמן לקנות?` | Em dash, and reads as a buy call |
| ✗ | `פרק 7 - כל מה שצריך לדעת על זהב, ביטקוין, בנקים מרכזיים ואינפלציה` | Too long, no hook |
| ✗ | `פרק 7 - זהב!!! 🚀` | Hype, emoji |
