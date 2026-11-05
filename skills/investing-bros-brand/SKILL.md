---
name: investing-bros-brand
description: >-
  Create and review Financial Journal artwork for Investing Bros / אחים להשקעות.
  Use for podcast branding, cover art, episode and segment thumbnails, Shorts covers
  ("קאבר לשורט", "תמונת שער לשורט"), discussion cards, lower thirds, intro art direction,
  brand guides, templates, קאבר, תמונת פרק, מיתוג and שפה עיצובית. Indexes selected
  reference images (kept in Drive), exact Hebrew copy, format specifications, reusable
  image-generation prompts, Heebo title typesetting and cover checks.
---
# Investing Bros brand

## When to use
Any podcast visual artifact or design-system change, at any episode stage: show cover,
episode cover and thumbnail, segment thumbnail, Shorts cover, discussion card, lower
third, explainer graphic and intro artwork. Load this skill even when another skill
creates or uploads the file.

## Inputs
The format, topic, approved headline and episode number; reuse known session values and
ask only for what blocks accurate work. Photo-cutout covers also need a separate usable
frame of each brother from that same episode's recording. Any point in the episode is
valid, including outside a segment being covered; never use a portrait from another
episode. Never invent episode numbers, quotes, claims, portraits or company logos.

## Authority and scope
`investing-bros-show` owns names, episode numbering, Drive paths, approvals and
publishing. This skill alone owns the visual identity, layouts, selected references,
prompts and visual review; title-description supplies copy, and video and Shorts consume
the design without restating it. Existing renderer code describes what is deployed; it
does not override this skill. GitHub is canonical; refresh installed copies after merges.

| Read | For |
| --- | --- |
| [brand rules](references/brand-rules.md) | Identity every format shares: copy, palette, Heebo, paper |
| [covers](references/covers.md) | Main-episode cover and thumbnail, segment thumbnail, show cover, illustrated alternatives |
| [Shorts covers](references/shorts-covers.md) | Vertical Shorts cover and its Heebo title step |
| [video graphics](references/video-graphics.md) | Teaser, Shorts hook, discussion card, lower third, motion |
| [prompts](references/prompts.md) | Image-generation prompts and the Codex backend |
| [face picks](references/face-picks.md) | Each episode's host stills: ~10 per speaker, the operator picks and rejects (with reasons), recorded as eval labels |
| [quality checks](references/quality-checks.md) | What to inspect by eye |
| [asset index](references/asset-index.md) | Every reference image with its Drive ID |
| [ownership](references/ownership.md) | Handoffs, versioning, artifact register |
| [history](references/history.md) | Why the rules are what they are |

## Steps
1. Read the brand rules and the one format file for the request, and load its entry in
   `assets/templates/layouts.json` (planning zones, not crop masks or layered files).
2. Download the references you need from Drive by their IDs in the asset index (they are
   not bundled here), run `scripts/check_reference_index.py --dir <work> <names…>`, and
   inspect each. A missing reference stops the run: report it, don't substitute. For an
   edit, use the exact image the user selected, never a nearby variant.
3. Fill the matching prompt with the exact copy, number, format and subject, and attach
   only the relevant references. **Hard rule (Amitai, episode 10): every episode, segment
   and Shorts cover is made by Codex on Amitai's Mac** through prompts → Codex backend,
   with this skill's references and the episode's real host frames as `-i` inputs. There
   is no fallback: no Pillow compositing on the box, no other image generator, no
   template pasted together in code. If Codex or the Mac is unavailable, stop and report
   a blocker (to the Producer when one runs the episode). Until Amitai says the design is
   dialed in, each of those covers is three clearly labeled options A/B/C. Independent Codex renders (A/B/C, wide vs square, each Short's cover) run as **parallel concurrent sessions** on the Mac, each in its own subfolder; sequential only when one depends on another (prompts → Codex backend). Other artwork
   may use the built-in image tool with the same prompt; say which generator ran in the
   hand-back. No code-drawn illustrations and no ad hoc Pillow renderers: the only
   typesetting script is `scripts/make_cover_title.py` (Heebo Black).
4. Photo-cutout covers: distinct original frames for each brother from the same episode
   being covered, a fresh portrait pair, the approved two-line headline, one photographic
   centerpiece and only the allowed touch-ups. Frames may come from anywhere in the
   episode, not necessarily the segment; shortlist them with `scripts/face_score.py` and
   pick by the portrait rules in covers. **Label every face grid by verified identity**
   (face picks → Verify who is who): confirm which host sits on which side at the start
   and after any mid-recording swap, name files by host, and look at each grid yourself
   before it goes to Amitai. Real frames are passed to Codex as photographic cutouts;
   what is forbidden is inventing, reshaping or synthesizing a face. Shorts covers use the
   **face format** (a real frame of the speaking host; `references/shorts-covers.md`):
   **the one-pass Codex cover with the real face frame via `-i` is the default** (Amitai's
   pick, episode 10; prompt on stdin, ~941×1672 upscaled to 1080×1920 with ffmpeg, named
   `שורט-NN-<נושא>-cover.jpg`); only if its Hebrew is not exact, text-free Codex art
   plus the shared `cover_title` with `make_cover_title.py --config short.json`; that
   field also drives the opening banner and YouTube metadata.
5. Review all three labeled options against the quality checks; fix an isolated error
   with one targeted edit and re-inspect. Keep each option in an A/B/C-labeled folder
   under its final-form filename so `check_cover.py` can check all three before review.
   Never put the option label inside the artwork or claim typography, resolution, layers
   or source provenance from the prompt alone.
6. Show the three labeled options to the episode owner (`investing-bros-show` → Episode owner;
   Amitai for non-episode artwork), through the Producer when one runs the episode, batched
   with the other reviews; the owner picks. Promote only that selection to the final filename.
7. Record the selected artifact in the episode's `extras/artwork-register.json` (actual
   path, size, sources, `episode_tab`), then run
   `scripts/check_cover.py FILE --kind <kind> --episode N --register extras/artwork-register.json --title "<line>" ...`
   (Shorts: `--config short.json`; add `--font` with the Heebo file when you have it),
   appending its output to `extras/cover-check.log`. Record the headline lines as the
   register row's `headline` too. It checks the headline for characters that render as
   tofu or never belong (U+061F Arabic question mark, brackets, box characters, missing
   glyphs) and the palette (brand mustard present, no green disc). It must pass before
   anything is shown to the owner or filed; still look at the text yourself, letter by letter.
8. File the final artwork in Drive (find the episode folder by its `פרק N` prefix): main
   episodes get both `cover-פרק-N.png` and `thumbnail-פרק-N.jpg` in the episode root,
   next to `תמלול - פרק N`; segment thumbnails go in `segments/`, Shorts covers in
   `Shorts/`. Images can go through the Drive connector; confirm each shows as
   `image/png` or `image/jpeg`. Replace an existing file of the same name rather than
   adding a duplicate, and preserve other files. Nothing is published or sent to anyone
   without the owner's explicit OK.

## Done when
- The requested artwork sits in its Drive folder under the `investing-bros-show` name:
  `cover-פרק-N.png` and `thumbnail-פרק-N.jpg` in the episode root,
  `סגמנט-NN-<סוג>-<נושא>-thumb.jpg` in `segments/`, `שורט-NN-<נושא>-cover.jpg` in
  `Shorts/`; no copies in `promo/`.
- `check_cover.py` passes for each file and `extras/artwork-register.json` records actual
  paths, sizes, version, status and sources.
- Until Amitai says the design is dialed in, each requested cover was presented as three
  labeled Codex options and the final filename is only the owner's selected option.
- For a prompt-only request, the filled prompt is delivered; no image is implied.
- A brand change updates this skill and passes review. A new or replaced reference is in
  Drive `Brand Resources/references/` with its row in the asset index, and
  `check_reference_index.py` passes.

## Hand back
Show the artwork and say briefly what changed, which generator was used, and any
unresolved text, size (`check_cover.py` warnings) or format limits. For a prompt-only
request return the filled prompt. Label a new format as a proposed adaptation until reviewed.

## Never
- Glossy cinematic finance, neon blue, 3D or metallic headlines, busy market charts.
- A font other than Heebo for typeset text.
- Infer font files, editable layers or isolated logos from a flattened PNG.
- Override the host spelling or credit order in `investing-bros-show`.
- Treat decorative newsprint as real data, claims or quotations.
- Commit reference images or generated variations to the repo.
- Invent, reshape, "improve" or synthesize a real host's face, or use a host frame the
  operator didn't pick for that episode (face picks). Passing the picked real frames to
  Codex as `-i` inputs and keeping them as photographic cutouts is required, not forbidden.
- Label a face grid by seat or file order without checking who is who (episode 10: the
  Amitai and Nadav grids were swapped).
- Make an episode, segment or Shorts cover anywhere but Codex on Amitai's Mac, or
  composite one with Pillow on the box as a fallback.
- Show or file a cover whose `check_cover.py` run failed, or a headline with tofu, brackets
  or Arabic punctuation (episode 10).
