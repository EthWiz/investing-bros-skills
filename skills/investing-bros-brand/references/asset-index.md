# Selected visual references

The reference images live in Google Drive, not in this skill:
[אחים להשקעות / Brand Resources / references](https://drive.google.com/drive/folders/1P0MFXIt9vrLiPP5jMHElmnpDEUAAetAh),
in `covers/`, `hosts/`, `teasers/` and `shorts-thumbnails/`. GitHub keeps only this index
and the rules. To add or replace a reference, put the file in that Drive folder and
update its row here; never commit reference images to the repo.

**Fetching.** Download each reference you need by its Drive file ID (Drive connector →
`download_file_content`, or `get_file_metadata` to check it), never by searching for the
file name: names repeat and drift. Save it under its file name in the working folder,
then inspect it. Run `scripts/check_reference_index.py --dir <working folder> <names…>`
to confirm what you downloaded is complete. If an ID returns not-found, or the file in Drive
no longer matches the row, stop and tell Amitai which reference is missing. Do not
substitute a nearby file.

Files are flattened raster references, not editable layered templates. Preserve
originals in Drive and create new versions for edits. The four legacy square cover
references are 1254×1254 pixels. Export sizes in `layouts.json` are targets, not the
dimensions of these references. The teaser stills are 1920×1080 JPEG references.

The two images kept in this skill are, first, `assets/logo-solid.png` (solid torn-paper wordmark
for live video, 1228×740 RGBA, approved production asset; navy letters remain opaque).
The video and Shorts scripts copy it from here, so it is a production input, not a
reference. The other is `assets/lesson-background-navy-studio.jpg` (1920×1080, navy `#09243B`
with a soft lighter glow behind the head and a vignette, chosen by Amitai on 2026-10-28 from six
options): the background behind Amitai in crypto-course lessons, copied into each lesson's
`assets/` and keyed in by `make_lesson_base.py` (`investing-bros-crypto-course`).

| File | Drive folder | Drive file ID | Role | Status |
| --- | --- | --- | --- | --- |
| segment-gold-coin-selected.png | references/covers | 1pG8AMCtKwGhs7K9iot3BGaBvzBdHNOxf | Selected gold coin design; 1672×941 PNG | User-selected 2026-10-22; shared episode/segment style reference |
| segment-sp500-facade-selected.png | references/covers | 1JlyVH4VLjcUBVL70TeQHjlIVM72nhrEa | Selected combined S&P 500 facade design; 1672×941 PNG | User-selected 2026-10-22; shared episode/segment style reference |
| episode-08-photo-cutouts.png | references/covers | 1wZb4trmkyyDue74NYL2kPdL4nBiEmRAv | Early main-episode photo-cutout exploration; 1672×941 PNG | Historical; superseded for this family by the selected coin/facade pair |
| main-cover.png | references/covers | 1Cs12YBSBHtPPmw6EFp4pHgLZu10cYBVW | Show masthead, chairs, paper, corrected host credit | Selected working reference |
| episode-07-gold.png | references/covers | 1UcwOlm-KTB0KJr54mgJKZv6rPdxwIfC9 | Square episode hierarchy, texture, hero/footer treatment | Selected working reference |
| episode-06-tokenization-digital.png | references/covers | 1ihJquvPBgq5_31TeGVgcyZ1ickY65t0x | Physical certificate transitioning to digital tiles | Latest user-selected edit source, canonical tokenization example |
| episode-04-cloud-wars.png | references/covers | 1uPE8XZBGa-KCWcOwuQ5usw8EIBrGE6m7 | Technology episode in the same engraving language | Selected working reference |
| host-amitai-ep08.png | references/hosts | 1MJ18ONc72KRxeN4ySA6KOsXcEEdL_OFa | Original episode-8 teaser frame, 00:04.200; 1920×1080 | Amitai identity anchor; video overlays retained, not a reusable default cutout |
| host-nadav-ep08.png | references/hosts | 1ytw352Xt8nL6DftJcxS2JQDFB85bV3FJ | Original episode-8 teaser frame, 00:21.500; 1920×1080 | Nadav identity anchor; video overlays retained, not a reusable default cutout |
| teaser-v5-amitai.jpg | references/teasers | 1nVeAGqK21cxdX6HmtB5Ehw1HCFL3abUz | Full-frame teaser on a bright wall | Approved v5 production reference |
| teaser-v5-nadav.jpg | references/teasers | 1zPNyr_f9EzxVJMQSFAEY1ZNYwlIY5nNy | Full-frame teaser with second host | Approved v5 production reference |
| shorts-title-strips-ep1.png | references/covers | 1bom32E_JkCnMYqZUpwYmPU_47oiFZzIy | Approved Shorts cover title: cream/mustard torn strips, `פרק N` pill; 1280×505 crop | Selected; Shorts cover title reference |

For photo-cutout episodes and segments, inspect both selected references and follow
[covers](covers.md). They are exact copies of the selected generated masters, not raw
portrait sources or production-size exports (1672×941 is not an exact 16:9 export).
Use the illustrated references only for explicitly requested illustrated formats, and the
user's exact selected image for localized edits. Never infer identity from a file name.
Designed portrait covers in
[references / shorts-thumbnails](https://drive.google.com/drive/folders/1Z2O0iYmq7XaZKSDQY6-LSnaux6INs7Ub)
are not verified camera originals. Where each reference came from: [history](history.md).

## Good and bad applications
- Good: two distinct hosts frame two readable strips and one refined topic photo, matching the selected pair.
  Bad: substitute engraved portraits or framed-photo panels without a request.
- Good: an explicitly illustrated format uses one engraved topic object.
  Bad: many unrelated stock-exchange buildings and chart lines surrounding the subject.
- Good: localized digital grids on tokenized certificate fragments.
  Bad: identical paper scraps with no digital cue, or cyan holograms covering the image.
- Good: a topic illustration changes while masthead, hierarchy and logo placement persist.
  Bad: applying the same gold-bar illustration to every investment topic.
- Good: modern bold Hebrew and generous spacing.
  Bad: tiny decorative subtitle, antique type or host spelling that conflicts with `investing-bros-show`.
