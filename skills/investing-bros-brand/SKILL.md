---
name: investing-bros-brand
description: >-
  Create and review Financial Journal artwork for Investing Bros / אחים להשקעות.
  Use for podcast branding, cover art, episode thumbnails, Shorts covers, discussion
  cards, lower thirds, intro art direction, brand guides, templates, קאבר, תמונת פרק,
  מיתוג and שפה עיצובית. Includes selected reference images, exact Hebrew copy,
  format specifications, reusable image-generation prompts and quality checks.
---
# Investing Bros brand

## When to use
Use for any podcast visual artifact or design-system update, across episode stages.

## Inputs
Collect the requested format, topic, supplied headline and episode number. Reuse known
session values. Ask only for missing information that prevents accurate production.
Do not invent episode numbers, quotes, claims, host portraits or company logos.

## Authority and scope
Load `investing-bros-show` for exact show/host names, episode numbering, Drive paths,
approvals and publishing conventions. This skill is the sole owner of the visual
identity, design templates, selected artwork and artwork creation/review workflow.
Title-description supplies approved copy; video and Shorts consume this design system.
Do not maintain competing visual rules in those skills. GitHub is the canonical source;
installed copies must be refreshed after changes merge.

This includes every show cover, square episode cover, YouTube thumbnail, Shorts cover,
discussion card, lower third, explainer graphic and intro artwork. Load this skill even
when another workflow creates or uploads the file. Existing renderer code describes
the deployed implementation; it cannot override this skill's design guidance. Reusing
legacy styling is an explicit compatibility choice, not the default for new artwork.

## Steps
1. Read [brand rules](references/brand-rules.md) and [asset index](references/asset-index.md).
2. Inspect the relevant bundled PNG with an image-view tool. Use the exact attached
   image when the user selects an edit target; never replace it with a nearby variant.
3. Read [layouts](references/layouts.md) and load the matching entry in
   `assets/templates/layouts.json`. These are compositional specifications, not layered
   Canva/Figma files or a renderer. Square covers have visual references; other formats
   are proposed adaptations, not approved final templates.
4. Read [prompt templates](references/prompts.md). Fill the topic, exact Hebrew copy,
   number, format and subject. Use the built-in image-generation tool for raster
   creation/edits. Do not substitute code-drawn illustrations. Read the available
   imagegen skill for tool invocation. Supply only relevant image references.
5. Preserve the reference layout for localized edits. For a new topic change the
   central illustration and headline while maintaining the brand structure.
6. Review with [quality checks](references/quality-checks.md). Correct text or visual
   errors with a targeted edit, then re-inspect. Never assert exact typography,
   resolution or layered editability merely from the generation prompt.
7. Deliver requested files/previews using the active environment's persistence rules.
   Do not publish or send to other people without explicit authorization.

## Done when
- Requested episode artwork is reviewed and saved to the owning episode folder under
  the paths in `investing-bros-show` (for example `promo/` or `shorts/`).
- The artifact register records actual output paths, version, status and source refs.
- For prompt-only requests, the filled prompt is delivered; no image is implied.
- Brand changes update this skill and pass review before becoming canonical.

## Hand back
Show the finished artwork and briefly state what changed. Mention material unresolved
text, size or format limitations. For a prompt-only request return the filled prompt.
For a brand extension identify it as a proposed adaptation until reviewed.

Read [ownership and asset lifecycle](references/ownership.md) for handoffs, versioning
and the distinction between selected references and approved published deliverables.

## Never
- Revert to glossy cinematic finance, neon blue, 3D metallic headlines or busy market charts.
- Infer actual font files, editable layers or isolated logos from a flattened PNG.
- Spell Amitai as אמיתי or reverse the established host credit order.
- Treat decorative newsprint as real data, claims or quotations.
- Make a blanket ban on digital details: tokenization deliberately uses subtle warm
  gold wireframes and pixels on the detached fragments, as documented in the rules.
