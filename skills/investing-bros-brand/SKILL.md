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
photo or frame of each brother. Never invent episode numbers, quotes, claims, portraits
or company logos.

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
   only the relevant references. Generate with the built-in image tool; Grokbot runs it
   through Codex on Amitai's Mac when connected (prompts → Codex backend) and otherwise
   uses its own image tool with the same prompt; say which in the hand-back (Shorts
   covers for the standing batch need Codex: report a blocker instead). No
   code-drawn illustrations and no ad hoc Pillow renderers: the only typesetting script
   is `scripts/make_cover_title.py` (Heebo Black).
4. Photo-cutout covers: distinct original sources for each brother, a fresh portrait
   pair, the approved two-line headline, one photographic centerpiece, only the allowed
   touch-ups; verify both identities. Shorts covers: text-free art, then the title with
   `make_cover_title.py`.
5. Review against the quality checks; fix an isolated error with one targeted edit and
   re-inspect. Never claim typography, resolution or layers from the prompt alone.
6. Record the artifact in the episode's `extras/artwork-register.json` (actual path, size,
   sources, `episode_tab`), then run
   `scripts/check_cover.py FILE --kind <kind> --episode N --register extras/artwork-register.json`.
   It must pass before filing.
7. File the final artwork in Drive (find the episode folder by its `פרק N` prefix): main
   episodes get both `cover-פרק-N.png` and `thumbnail-פרק-N.jpg` in the episode root,
   next to `תמלול - פרק N`; segment thumbnails go in `segments/`, Shorts covers in
   `Shorts/`. Images can go through the Drive connector; confirm each shows as
   `image/png` or `image/jpeg`. Replace an existing file of the same name rather than
   adding a duplicate, and preserve other files.
8. Show Amitai; he picks. Nothing is published or sent to anyone without his explicit OK.

## Done when
- The requested artwork sits in its Drive folder under the `investing-bros-show` name:
  `cover-פרק-N.png` and `thumbnail-פרק-N.jpg` in the episode root,
  `סגמנט-NN-<סוג>-<נושא>-thumb.jpg` in `segments/`, `שורט-NN-<נושא>-cover.jpg` in
  `Shorts/`; no copies in `promo/`.
- `check_cover.py` passes for each file and `extras/artwork-register.json` records actual
  paths, sizes, version, status and sources.
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
