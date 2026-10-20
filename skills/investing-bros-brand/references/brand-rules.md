# Financial Journal identity

## Positioning
Two brothers discussing investments and the technology behind them. Communicate
curiosity, careful reasoning and long-term thinking. Feel professional and personable,
like an independent financial journal. Avoid urgency, trading cues and wealth promises.

## Exact copy
- Show: `אחים להשקעות`
- Main wordmark: `אחים` on cream above `להשקעות` on mustard.
- Host credit: `עם אמיתי ונדב רסקין` (show cover, Shorts covers; not on episode covers since episode 3)
- Individual hosts: `אמיתי רסקין`, `נדב רסקין`
- Amitai is four Hebrew letters: א מ ת י. The extra yod in אמיתי is wrong here.
- Number label: `פרק {N}`. Never auto-increment or infer N for a new episode.
- Established examples: 7 `למה דווקא זהב?`; 6 `וול סטריט עוברת לבלוקצ׳יין`;
  4 `מלחמת העננים`.
- Use natural RTL Hebrew. Check punctuation and mixed numbers visually.

## Palette
Use these as production targets, not claims of exact sampled pixels:

| Role | Hex | Use |
| --- | --- | --- |
| Navy ink | #09243B | Background, all headline ink, engraved shadows |
| Warm cream | #F5EBD5 | Paper strips, illustration highlights, footer |
| Mustard | #D8A52E | Second title strip, backing shape, selective details |

Permit natural tonal variation from paper grain and engraving. Keep the three-color
family consistent. No new topic-specific neon palette. Gold is printed mustard,
not glossy luxury metal. Use cream for comfortable contrast, not clinical white.

The approved deterministic motion stack (teasers and Shorts captions) retains its
screen-tested accent gold `#F5B71F`. The approved full-frame teaser also uses white
type and a `#13203E` navy title outline for legibility over live video. These values
are constants in both installed copies of `brand.py`; do not redefine them in an
individual renderer.

**Shorts hook vs captions (approved 2026-10-19).** On a Short the hook headline and the
captions must never share a treatment. The hook is print: torn-paper strips (line 1
cream `#F5EBD5`, line 2 mustard `#D8A52E`), navy `#09243B` Heebo Black type, a restrained
paper shadow, up to ~1.2° tilt. Captions stay the screen-tested motion style: white type
with the current word in `#F5B71F`. Hooks are as short as possible: one idea, ideally six
words or fewer, two lines (`למה לסייברקאב` / `אין הגה?`, not `למה לסייברקאב אין הגה ורק
שני מקומות?`). The Short's cover uses the same two-strip headline.

## Typography
Use heavy contemporary Hebrew sans-serif for titles, with compact but open counters.
Do not use antique calligraphic lettering, serif display titles, bevels, thick outlines
or glow on text. Reference PNGs contain generated lettering, not an identified font.
For deterministic typesetting, Heebo Black for headlines and Heebo SemiBold for small
copy are recommended candidates consistent with the older production stack. They are
NOT claimed to exactly match generated artwork. Inspect before adoption. Fonts and
licenses are not bundled. Never synthesize a thin variable font as a substitute for
an unavailable heavy static weight without checking the result.

## Paper and illustration
Use slightly irregular torn paper edges, restrained real paper shadows and subtle navy
grain. Keep the headline strips nearly horizontal, up to about 3 degrees of tilt.
Use cream-and-navy engraved or halftone cutout illustrations with selective mustard.
Use one primary subject and at most one supporting concept. Leave navy breathing room.
A rough mustard disc behind the subject is a recurring motif, not mandatory for all
future subjects. Do not scatter decorative charts, logos, globes or landmarks around it.
Newsprint can be illegible texture; no fabricated legible headlines or numeric data.

## Main cover
Use two inward-facing midcentury chairs, one table, two coffees and one newspaper.
This conveys the brothers without inventing portraits. Keep the show name dominant.
Use the corrected main-cover.png, not the earlier extra-yod version.

## Episode illustrations
Since episode 3 the subject stands on its own, big, with no newspaper base (see layouts → Square episode cover). The entries below describe past covers.
- Gold: engraved ingot on newspaper; a small balance scale supplies a supporting
  concept of value. Keep the scale subordinate to the ingot.
- Tokenization: intact cream engraved certificate transitioning on its right into
  detached digital tiles. Near tiles retain paper texture; outer tiles use navy
  surfaces, fine mustard wireframe/pixel patterns and recognizable certificate
  fragments. Allow restrained warm edge light, a few square pixels and short
  right-angle connections. This is a localized, meaningful exception to the general
  no-glow rule. Avoid a neon network over the entire cover. Paper shards alone fail
  to show digital ownership; preserve the user's digital-version correction.
- Cloud Wars: engraved server cabinets below one halftone cloud, a few physical
  mustard cables and one small newspaper base. No combat, lightning, VS or logos.

## Motion and sound direction
If requested, use paper slides, gentle settling and restrained cuts. Keep type readable
on the final hold. Suggest subtle paper sounds and a warm understated instrumental
sting. This package contains no licensed music, soundtrack, animation or video template.
Do not claim those assets exist; source/create them through appropriate authorized tools.

Episode cold opens use the approved full-frame teaser layout in
[layouts](layouts.md), not the older half-frame speaker plus side panel.
