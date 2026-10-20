---
name: investing-bros-short-covers
description: >-
  Make the vertical (1080×1920) cover image for an Investing Bros / אחים להשקעות
  Short in the approved "cut newspaper" style: torn-paper title strips, navy
  textured background, gold engraved illustration over a mustard sun. Use when
  asked for a Short cover, "קאבר לשורט", "תמונת שער לשורט" or a Shorts thumbnail.
---
# Investing Bros Short covers (vertical)

Load `investing-bros-brand` first (palette, logo, ownership). This skill owns only the vertical Short cover layout; long-form thumbnails stay in the brand skill.
Reference (Amitai's approved example): [assets/amitai-short-cover-example.png](assets/amitai-short-cover-example.png).

## Layout (1080×1920, top to bottom)
- **Background:** dark navy (~#111B30) with subtle paper/print texture.
- **Title — cut-newspaper torn strips** (upper third, inside the centre 1080×1080 safe square):
  - Line 1 on a **cream** (#F6EEDE) strip, line 2 on a **mustard** (#F5B71F) strip; the strips **overlap slightly** and are **slightly tilted** in opposite directions (≈ ±1–2°).
  - **Very heavy Rubik Black (wght 900)**, navy text, filling the strip (tight padding, big type).
  - **Rough torn edges with a white fringe** (paper fibre), soft drop shadow.
  - White **"פרק X" pill** sitting on the bottom edge of the mustard strip, navy text.
- **Illustration:** gold/engraved (etching, line-hatched) illustration relevant to the Short's topic (e.g. robotaxi, robot, data-center satellite) over a large **mustard sun** with rays, centre/lower half.
- **Credit strip:** cream torn strip "עם אמתי ונדב רסקין" (lower area, slight tilt).
- **Logo:** torn-paper podcast logo **bottom-left**.
- Title = the Short's hook (faithful paraphrase, ≤ 2 lines, ≤ ~14 chars a line). No numbers that aren't in the clip.

## Process
1. **AI-generate the art text-free.** Prompt for: vertical 9:16, navy textured background, gold engraved-style illustration of <topic> over a mustard sun, empty space at the top third for a title and at the bottom for a credit strip, **no text, no letters, no logos**. Hebrew from image models is unreliable — never keep generated text.
2. **Overlay the exact Hebrew text with scripts** (`scripts/make_torn_title.py`, PIL + raqm, RTL):
   ```python
   from make_torn_title import title_block, torn_strip, shadow, CREAM
   tb = title_block("דאטה סנטרים", "בחלל?", "פרק 3", width=1010)   # cream+mustard strips + white pill
   ns = torn_strip("עם אמתי ונדב רסקין", CREAM, 64, -0.8, pad=(30, 24), seed=11)
   ```
   Then composite the logo bottom-left. `python3 scripts/make_torn_title.py ART.jpg OUT.jpg` reproduces the ep3 cover (it also paints over old text regions — adjust the boxes for new art).
   `RUBIK` points at the box font path; change it if Rubik lives elsewhere (Rubik variable font from google/fonts).
3. **Check:** view at ~200 px wide — title readable, Hebrew RTL with "?" on the left, pill not clipped, nothing important outside the centre square, logo and credit present. Save JPEG q≈92 next to the Short as `<short>-cover.jpg`.

## Done when
- `<short>-cover.jpg` (1080×1920 JPEG) sits next to each Short in the episode's `shorts/` folder, with the exact Hebrew hook title, `פרק X` pill, credit strip and logo, checked at ~200 px wide.
