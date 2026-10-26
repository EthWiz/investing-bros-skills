# Financial Journal identity

The rules every format shares. Each format's own file ([covers](covers.md),
[Shorts covers](shorts-covers.md), [video graphics](video-graphics.md)) adds its layout.

## Positioning
Two brothers discussing investments and the technology behind them. Communicate
curiosity, careful reasoning and long-term thinking. Feel professional and personable,
like an independent financial journal. Avoid urgency, trading cues and wealth promises.
Elegant but engaging: one clear focal point and breathing room. Not loud or busy, and
not so minimal it looks empty. When unsure, stay close to the last approved artwork.

## Exact copy
- Show: `אחים להשקעות`
- Wordmark: `אחים` on cream above `להשקעות` on mustard. On artwork it sits bottom-right
  as the compact show mark, high contrast against the background.
- Host credit: `עם אמיתי ונדב רסקין`, only on the square show cover. Episode covers,
  segment thumbnails and Shorts covers carry no host-name strip.
- Individual hosts: `אמיתי רסקין`, `נדב רסקין`. `investing-bros-show` is authoritative
  for spelling and credit order.
- Number label: `פרק {N}`. Never auto-increment or infer N for a new episode.
- Natural RTL Hebrew; check punctuation (`?` on the left) and mixed numbers visually.
  Latin names stay Latin (`S&P 500`, `SpaceX` styled like its wordmark).

## Palette
Production targets, not claims of exact sampled pixels:

| Role | Hex | Use |
| --- | --- | --- |
| Navy ink | #09243B | Background, all headline ink, engraved shadows |
| Warm cream | #F5EBD5 | Paper strips, illustration highlights |
| Mustard | #D8A52E | Second title strip, backing disc, selective details |

Permit natural tonal variation from paper grain and engraving. Keep the three-colour
family consistent. No topic-specific neon palette. Gold is printed mustard, not glossy
luxury metal. Use cream for comfortable contrast, not clinical white.

Screen exception: the motion stack keeps its screen-tested accent gold `#F5B71F`.
The approved kinetic Shorts captions use it as the active box for keywords and numbers
(ordinary active words use a navy box), and the full-frame teaser uses gold current
words plus white type with a `#13203E` navy title outline over live video. Those constants live in `brand.py` in
`investing-bros-video` and `investing-bros-shorts`; do not redefine them in a renderer.

## Typography
**Heebo is the show's typeface** (decided 2026-10-22): Heebo Black for headlines and
title strips and the approved kinetic Shorts captions, Heebo ExtraBold for other
video captions, Heebo SemiBold for small copy. Every
deterministic renderer uses static Heebo weights (`brand.py fonts` in
`investing-bros-shorts` makes them from Google's variable Heebo). No other font, no
antique calligraphy, serif display titles, bevels, thick outlines or glow on text.
Generated artwork contains generated lettering, not Heebo; when exact Hebrew matters,
generate the art text-free and typeset the words with Heebo. Font files are not bundled.

## Paper and illustration
Slightly irregular torn paper edges, restrained real paper shadows and subtle navy grain.
Headline strips stay nearly horizontal, up to about 3° of tilt (Shorts strips ±1–2°).
Photo-cutout covers use natural-colour portraits and one photographic centerpiece
([covers](covers.md)). Illustrated formats use cream-and-navy engraving or halftone with
selective mustard: one primary subject, at most one supporting concept, navy breathing
room. A rough mustard disc behind the subject is a recurring motif, not mandatory. Do not
scatter decorative charts, logos, globes or landmarks. Newsprint is illegible texture;
no fabricated legible headlines or numeric data.

## Never
- Glossy cinematic finance, neon blue, 3D or metallic headlines, busy market charts.
- A blanket ban on digital details: tokenization deliberately uses warm gold wireframes
  on detached fragments ([covers](covers.md) → illustrated alternatives).
