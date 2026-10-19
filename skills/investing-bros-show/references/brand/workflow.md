# Financial Journal artwork workflow

## Inputs
Use the requested format, supplied headline, topic and episode number. Reuse session
values. Do not infer a new episode number from examples. Read the shared Hebrew names
and publication rules in investing-bros-show before creating artwork.

## Steps
1. Read [brand rules](brand-rules.md) and [asset index](asset-index.md).
2. Inspect the relevant bundled PNG. For an edit, use the exact user-selected image.
3. Read [layouts](layouts.md) and the matching entry in `assets/brand/templates/layouts.json`.
4. Fill [prompt templates](prompts.md) with exact Hebrew copy. Use the available image-generation
   tool and its skill for raster creation/edits. Do not generate art with custom drawing code.
5. Preserve layout for localized edits. Change the topic illustration and headline for new episodes.
6. Review [quality checks](quality-checks.md), correct isolated errors and re-inspect.
7. Hand back requested artwork or prompts. Save finished episode artwork in `promo/` through
   supported upload tools. Respect the environment limits and publication approvals.

## Limits
The PNGs are flattened visual references. There are no editable Canva/Figma templates,
font binaries, clean logo layers, soundtracks or animation renderers in this bundle.
Check actual output dimensions. Proposed formats need visual review before becoming
canonical references. Do not publish or replace deployed assets without explicit OK.
