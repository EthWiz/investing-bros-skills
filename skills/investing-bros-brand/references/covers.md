# Covers: main episodes, segments and the show

Main episodes and two-host segments share one photo-cutout design. The show cover and
illustrated formats are at the end. Shorts covers have [their own file](shorts-covers.md).

## Outputs
| Output | `--kind` / layout | Composition and copy | File and folder | Size |
| --- | --- | --- | --- | --- |
| Main episode wide | `episode-wide` | Approved episode headline; small supplied `פרק N` tab below the title, clear of the centerpiece | `thumbnail-פרק-N.jpg`, episode root | 1920×1080 target |
| Main episode square | `episode-square` | Recompose for 1:1: headline and tab above, both portraits lower, one subordinate topic image if it fits | `cover-פרק-N.png`, episode root | 3000×3000 target, 1400 minimum |
| Segment | `segment-wide` | Topic + short question; no `פרק N` tab | `סגמנט-NN-<סוג>-<נושא>-thumb.jpg`, `segments/` | 1280×720 |

Main episodes need both formats, from the same photos and copy, each composed directly
for its ratio: never squeeze, crop out a brother or pad with a blurred background.
Segments need no square. File names follow `investing-bros-show` → Naming;
`scripts/check_cover.py --kind <kind>` checks name, format, ratio, size and the register.
Zones in `assets/templates/layouts.json` are planning guides (normalized
[x, y, width, height] from the top left), not crop masks.

## Standing option rule (2026-10-22)
Until Amitai says the design is dialed in, make every main-episode cover set, segment
thumbnail and individual Short cover as **three clearly labeled options: A, B and C**,
using Codex through the backend recipe in [prompts](prompts.md). Amitai picks one; do
not promote an option to the final delivery filename before his selection. For a main
episode, each option includes a directly composed square cover and matching wide
thumbnail. Put the option label in its filename, folder or review presentation, never
inside the artwork. Codex being unavailable is a blocker, not permission to switch
generators.

## Selected references
Inspect both before every new cover (Drive `references/covers`, IDs in the
[asset index](asset-index.md)). They define the family; the coin and facade are
topic examples, not mandatory props.

| Reference | What it establishes |
| --- | --- |
| `segment-gold-coin-selected.png` | Natural-colour portraits, central torn-paper headline, one elegant photographic gold coin |
| `segment-sp500-facade-selected.png` | Same family with a stock-exchange facade centerpiece |

## Fixed design and allowed variation
- Navy textured paper, cream and mustard torn-paper strips, heavy navy Hebrew lettering,
  a restrained mustard disc and the compact show mark bottom-right, clear of the chin
  and the platform's duration badge. No host-name strip.
- Amitai left, Nadav right unless the user asks for a swap. Large photographic
  head-and-shoulder cutouts with comparable face scale. Paper may overlap shoulders,
  never faces.
- Topic on the cream upper strip, short question on the mustard lower strip, approved
  wording only. Examples: `זהב` / `למה הבנקים קונים?`, `מדד S&P 500` / `עדיין כדאי?`.
- One high-quality photographic topic image below the headline, between the shoulders.
  Headline and faces dominate; the prop never crowds them.
- Vary the real portraits, expression, crop and topic image between covers. Keep palette,
  headline hierarchy, face scale and logo placement stable. Do not reuse the same two
  cutouts by default.

## Portraits and identity (same-episode source rule, 2026-10-22)
1. For an episode or segment cover, collect a separate original frame of each brother
   from that same episode's recording. Any point in the episode is valid; a segment
   thumbnail does not have to use a frame from the segment itself. Never use a portrait
   or photo from another episode for a new cover. Map identity by looking, never by file
   name or seat. `host-amitai-ep08.png` and `host-nadav-ep08.png` (Drive
   `references/hosts`) are identity anchors only, not reusable production portraits.
   Resolve any doubt first.
2. Pick sharp, well-lit frames with a real smile or laugh, teeth showing, eyes open and
   both irises centred on the lens. A slight three-quarter turn is fine. Reject (Amitai's
   episode-9 picks and rejects):
   - eyes shut or downcast, or the head dropped with lowered brows (A3);
   - a wide-eyed blank stare, or irises turned off the lens, even with a smile (A1, B7);
   - mid-word, puckered, stretched, lopsided or hanging-open mouths (A8, B7);
   - blinks, motion blur, or a hand over the face.
   A smile narrows the eyes; that is not a blink. Prefer a sharper source recording over
   synthetic sharpening; don't claim a teaser frame came from the full recording.
   To shortlist, run `scripts/face_score.py FRAMES_DIR --side left|right --pick 9` on
   frames sampled every few seconds from the whole recording (Amitai left, Nadav right in
   the Riverside side-by-side; needs `mediapipe` and `opencv-python`, model via
   `--model` or `$FACE_LANDMARKER_TASK`). It scores each host against their own
   whole-episode baseline. Refine around the top times (±1.5 s), then look at every pick
   yourself; the score is a shortlist, not a decision. Changing the scorer: run the eval in
   the repo's `evals/face-picks/` (see its README); it must keep every good above every bad.
3. Compare with the last approved covers and pick visibly different frames. A tint, shirt
   recolour or slight AI smile on the same portrait is not a different photo.
4. Supply the originals separately from the style reference, label each by role and side,
   and never use a generated cover as the only identity reference.
5. Preserve each brother's facial structure, age, hairline, beard, eye shape and skin
   texture. Check each face against its original, then together: exactly one Amitai and
   one Nadav, not two versions of one brother.
6. Record source, timestamp, identity, side, reuse and touch-ups in the episode's
   artifact register (see [ownership](ownership.md)).

## Light touch-ups
Allowed: exposure and white balance, softer harsh shadows, modest clarity, and relaxing a
speaking expression into a natural small smile. Start from a good frame; don't
manufacture alertness. Not allowed: strong filters, orange skin, plastic smoothing,
enlarged eyes, changed proportions, added teeth or exaggerated emotion. Image generation
can change faces even when told not to: inspect, and disclose AI portrait changes plainly.
Never call an AI-edited portrait an untouched cutout. If untouched portraits are
requested, use a non-generative compositing workflow, or say that capability is missing.

## Centerpiece and alternatives
One clear subject with realistic material detail, soft light and a restrained shadow; the
selected coin and facade set the bar. No low-detail clip art, cartoon rays, glossy toy
objects, floating decorations, fake charts, invented numbers or unrelated props. Natural
metallic detail on a gold object is fine; metallic headlines are not. A thematic
stock-exchange photo is not a claim that an index is an exchange.
The required A/B/C options must vary portraits and centerpiece meaningfully; label all
three and record Amitai's exact selection. For a mixed selection, map each chosen
portrait and centerpiece to its source and side, then combine them without redesigning
faces.

## Delivery checks
Read the real pixel size and disclose it: a generated 1672×941 or 1254×1254 image is not
a 1920×1080 or 3000×3000 master, and upscaling adds no detail. Check at 160–200 px wide.
Review every artifact and every square adaptation; selection does not authorize publishing.

## Show cover
Square, `show-square` layout. Two-strip masthead (`אחים` cream, `להשקעות` mustard) dominates
the top; below, two inward-facing midcentury chairs, one table, two coffees and one
newspaper as engraved cutouts (the brothers without portraits); the host credit strip at
the foot. Follow `main-cover.png`. Keep the name legible at 160 px.

## Illustrated alternatives (on request only)
Older illustrated episode covers are references for explicitly requested illustrated
formats, not the default:
- Gold (`episode-07-gold.png`): engraved ingot on newspaper, a small subordinate balance scale.
- Tokenization (`episode-06-tokenization-digital.png`, canonical): intact cream engraved
  certificate turning, on its right, into detached navy digital tiles with fine mustard
  wireframes, a few square pixels and short right-angle links; near tiles keep paper
  texture. Subtle warm edge light is allowed only here. No cyan neon or global hologram;
  paper shards alone don't show digital ownership.
- Cloud Wars (`episode-04-cloud-wars.png`): engraved server cabinets under one halftone
  cloud, a few mustard cables, a small newspaper base. No combat, lightning, VS or logos.
