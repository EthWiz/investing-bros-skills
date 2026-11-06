# Gate map

Every gate an episode passes, from the recording to the retro. `scripts/pipeline.py`
implements this map; `extras/pipeline.json` ([state-schema.md](state-schema.md)) records
which gates passed, for which version of which files.

## Words used here

- **Track**: one deliverable followed end to end. `main` (audio, copy, art, full video),
  `seg01`, `seg02`, `short01`, `short02`, `short03`, and `release` (RedCircle, the approval
  round, publishing, the Spotify follow-up, cleanup, the retro).
- **Stage**: one step of a track, in order. A stage passes when its evidence is there; it
  records the sha256 of its output files (its **version**) and the versions of the stages it
  was made from (its **inputs**).
- **Evidence**: `file` (the pipeline checks the file exists and is not empty), `log` (a
  script's saved output must say OK), `mark` (what someone saw and where, written with
  `pipeline.py mark`), `record` (a JSON record a script wrote: an upload record, a segment
  package record), `approval` (the approver's own words, tied to a version).
- **Editorial approval**: the episode owner OKs **one version** of one asset (a cut list, a
  title, a cover pick, an uploaded video). It goes stale when that asset changes.
- **Publish permission** (`release.publish_ok`): the owner's OK to make the release Public.
  It is tied to the set of approved versions and video IDs at that moment; a change to any of
  them makes it stale. It can never be waived.
- **Post-live obligations**: what still has to happen after everything is Public: the Spotify
  link swap, cleaning up superseded Private uploads, and the retro.
- **Approver**: the **episode owner** (`investing-bros-show` → Roles and accounts) for every
  episode asset; Amitai for anything outside episodes (the crypto course, show-wide metadata,
  new destinations). "—" means no approval, only evidence.
- **Invalidation**: when an input's version changes, every stage that recorded the old
  version is **stale** and has to pass again; an approval of a stale version is stale too.
  Stale stages show in `pipeline.py next` and are logged as events.
- **What publishing fills in is not a change**: the Spotify line of a YouTube description (the
  show link becomes the episode link, `investing-bros-publish` step 7) and the `- status:` /
  `- URL:` lines of the notes files (`youtube-סגמנט-NN.md`, `youtube-שורט-NN.md`) are masked in
  their fingerprints. Neither stales an approval or the publish OK; any other change to those
  files (title, description) still does.

The postprod gate items (`investing-bros-post-production` → `references/CHECKLIST.md`) keep
their ids; the table says which stage each belongs to.

## main

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `intake` | post-production (steps 1–2) | the recording parts | file: `extras/investing-bros-episode-raw-untrimmed.m4a` (or `.mp4`) | — | a new raw master (everything below) |
| `master` | post-production (steps 3–4, 8 transcript Doc) | `intake` | file: `extras/transcript/segments.json` (item `transcript`); mark: `transcript_doc` (Doc URL) | — | `intake` |
| `cut_list` | post-production (step 5) | `master` | file: `extras/cuts-review/cuts-list.txt`, every cut tagged `[routine]` or `[content]` | — | `master` |
| `trim` | post-production (step 6) | `cut_list` | file: edited audio in the root (item `audio`), `extras/edit.json` + one review clip per cut (item `cut_list`). Runs on the full draft list, before `cuts_ok` | — | `cut_list`; a new `edit.json` stales `copy`, `video`, `upload`, `release.redcircle_draft` and every segment/Short whose raw ranges overlap the changed span |
| `copy` | title-description | `trim` | file: `כותרות-פרק-N.txt`, `תיאור-פרק-N.txt` (item `titles_description`) | — | `trim` (chapters are mapped through `edit.json`) |
| `cuts_ok` | post-production (step 5) | `cut_list` | approval of the cut-list version (raw times + words around each cut). Each `[content]` cut is asked as a question; the whole list, routine cuts included, stays visible. Gates the renders, not the trim, and is an input of `publish_ok` | owner | a changed cut list |
| `title_ok` | title-description | `copy` | approval: the owner's `בחירה סופית:` title, tied to `כותרות-פרק-N.txt` only (`of_keys`, the same way a segment thumbnail pick is tied to `-thumb.jpg`) | owner | a changed titles file. A description or chapter edit does not |
| `art` | brand (steps 3–8) | `title_ok` | file: `cover-פרק-N.png`, `thumbnail-פרק-N.jpg` in the root (item `thumbnail_cover`); log: `extras/cover-check.log` OK for both + mark: Codex provenance (item `cover_checks`); mark: `face_identity`. Option A is what gets uploaded | — | `title_ok` (the headline) |
| `video` | video | `trim`, `copy`, `cuts_ok` | file: teaser in `promo/` (item `teaser`); log `extras/teaser-check.log` CAPTIONS OK + mark (item `teaser_quality`); intro in `extras/` (item `intro`); `video/פרק-N-וידאו.mp4` (item `full_video`); log `extras/verify_sync.log` SYNC OK (item `verify_sync`); `video/תיאור-פרק-N-youtube.txt` with chapters + mark (item `chapters`) | — (the owner sees it in the approval round) | `trim`, `copy` (`cuts_ok` blocks the render until it is current; a later re-approval does not by itself stale a video whose picture did not change) |
| `upload` | episode-upload (step 3) | `video`, `title_ok`; the postprod `upload` stage passes | record: `extras/uploads/main.json` from `yt_upload.py --source <master> --thumbnail <option A> --record` (Private, show channel, video ID, version = the current master's sha256: a record of an older render fails). The thumbnail's sha256 is `extras/uploads/main-thumb.json`, not a field of the upload record. File + mark: `extras/past-episode-cards.json`, cards set (item `past_episode_cards`); mark: `main.endscreen` | — | `video`, `title_ok`; a re-upload (new video ID). A thumbnail swap does not |
| `art_ok` | brand (step 6) | `art` | approval, in round 2: the owner's A/B/C pick, tied to the cover and thumbnail files (`of_hashes`). Promote the picked file onto the canonical name before approving. One quote may cover this and the other art picks | owner | a changed cover or thumbnail. That stales `publish_ok`; it does not stale `upload` or `ok` |
| `ok` | episode-upload (3b approval round) | `upload` | approval of the uploaded version (file sha256 + video ID) | owner | `upload` |

## seg01, seg02

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `select` | segment-video (step 1) | `main.trim` | mark: `segNN.select` (raw in/out, internal cuts, length, the alternative) | — | — |
| `range_ok` | segment-video (step 1) | `select` | approval of the range | owner | a changed selection |
| `render` | segment-video (`make_segment.py`) | `range_ok`, `main.cuts_ok` | record: `extras/segment-NN.json` (raw range, source, mapping, `SYNC OK`, output sha256) | — | `range_ok`; a `main.trim` change that overlaps the picked range minus the segment's own drops (`selected_ranges`: a new cut there, or restoring one the segment crossed). `cuts_ok` blocks the render until it is current |
| `package` | segment-video (steps 5–9) | `render` | file: the slot's four files in `segments/`, none empty (item `segments`, this slot); mark: `segNN.nudge` (0:31 frame checked). `-thumb.jpg` must exist (option A) and is not part of the fingerprint | — | `render`. Replacing the thumbnail does not |
| `upload` | segment-video (steps 10–11) | `package`, `main.upload` | record: `extras/uploads/segNN.json` (Private, version = the current `.mp4`'s sha256, thumbnail = option A); mark: `segNN.links`. Thumbnail sha: `extras/uploads/segNN-thumb.json` | — | `package`, `main.upload` (the full-episode link); a re-upload. A thumbnail swap does not |
| `thumb_ok` | segment-video (step 7) / brand | `package` | approval, in round 2: the owner's A/B/C pick, tied to the live `-thumb.jpg` (`of_keys`, `of_hashes`). Promote the pick first | owner | a changed thumbnail. That stales `publish_ok`, not `package`, `upload` or `ok` |
| `ok` | episode-upload (3b) | `upload` | approval of the uploaded version | owner | `upload` |

## short01, short02, short03

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `pick` | shorts (step 1) | `main.trim` | mark: `shortNN.pick` (raw ranges, cover title) | — | — |
| `pick_ok` | shorts (step 1) | `pick` | approval: the owner's three picks (one quote may approve all three) | owner | a changed pick |
| `render` | shorts (steps 2–6) / remotion | `pick_ok`, `main.cuts_ok` | log: `extras/check-short-NN.log` (saved `check_short.py` output: a LUFS line, no `warning:`) | — | `pick_ok`; a `main.trim` change that overlaps the Short's raw ranges. `cuts_ok` blocks the render until it is current |
| `cover` | brand (Shorts covers) | `pick_ok`, `main.title_ok` | file: `Shorts/שורט-NN-<נושא>-cover.jpg` (option A); log: `extras/cover-check.log` has `OK` for it. Render only after round 1: the episode title and this Short's cover title. No best-guess title. A/B/C differ in art only | — | `pick_ok` (the cover title). `main.title_ok` blocks the render until it is current |
| `package` | shorts (step 7) | `render`, `cover` | file: the slot's four files in `Shorts/`, none empty (item `shorts`, this slot). `-cover.jpg` must exist and is not part of the fingerprint | — | `render`. Replacing the cover does not (`cover` blocks a re-run until it is current; it is not an input) |
| `upload` | shorts / episode-upload (step 3) | `package`, `main.upload` | record: `extras/uploads/shortNN.json` (Private, option A cover, version = the current `.m4v`'s sha256), `.srt` published. Cover sha: `extras/uploads/shortNN-thumb.json`. Related video is not required here: the full episode is still Private, so it is set and checked before the Short goes Public (`investing-bros-publish`, item `related`, never waived) | — | `package`, `main.upload`; a re-upload. A cover swap does not |
| `cover_ok` | brand | `cover` | approval, in round 2: the owner's A/B/C pick, tied to the cover file (`of_hashes`). Promote the pick first. A cover-title change is a re-render and a re-upload, not a pick | owner | a changed cover. That stales `publish_ok`, not `package`, `upload` or `ok` |
| `ok` | episode-upload (3b) | `upload` | approval of the uploaded version (this is the cut approval) | owner | `upload` |

## release

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `redcircle_draft` | episode-upload (step 2) | `main.trim`, `main.title_ok` | mark: `redcircle_draft` (draft URL, screenshot checked, `check_titles_match.py` passed) | — | `main.trim` (new audio), `main.title_ok`, `main.copy` |
| `review_gate` | post-production | every track's `upload`, `redcircle_draft` | the postprod `review` stage passes | — | any of its inputs |
| `approval_round` | episode-upload (3b) | `review_gate` | mark: `release.approval_round` (the one Telegram message: file, time, every link passed `check_links.py --message`) | — (a pipeline message) | any `upload` (re-send one full message) |
| `publish_ok` | publish | every track's `ok`, `main.cuts_ok`, `main.art_ok`, `segNN.thumb_ok`, `shortNN.cover_ok`, `approval_round` | approval: the owner's own words naming what may go Public, tied to every `ok`, the current cut approval, every art pick and video ID; **never waivable**. Record the oks and the art picks first (the same quote may be passed to each `approve`), then this | owner | `cuts_ok`, any `ok`, any art pick, any re-upload. The thumbnail swap itself does not, because it is not written into the upload record |
| `publish` | publish | `publish_ok` | file: `extras/publish-checklist.json` (item `published`). A thumb or cover counts when its thumbnail record matches; a failed one stays open. `can-public` re-checks `publish_ok` and the video IDs every time | — | `publish_ok` |
| `spotify_links` | publish (step 7) | `publish` | mark (item `spotify_links`): the Spotify episode URL on the episode, both segments and all three Shorts, `check_links.py` passed | — | `publish` |
| `old_uploads` | episode-upload / publish | `publish` | mark (item `old_uploads`): superseded Private IDs deleted, naming every ID in the upload records' `superseded`, or `none` when there are none | — | any upload record changing (a new superseded upload) |
| `retro` | producer (`pipeline.py retro`) | `spotify_links`, `old_uploads` | file: `extras/retro-פרק-N.md`; mark: `release.retro` (the learnings PR/issue links, the one message to the owner) | — | — (never blocks publishing) |

The postprod `done` stage passes once `publish`, `spotify_links` and `old_uploads` pass.

## Waivers

- The owner may waive a gate item or a non-approval stage for this episode, in their own
  words (`pipeline.py waive ITEM --by "<owner> HH:MM: ..."`). A waived parent clears its
  child items (`teaser` → `teaser_quality`; `shorts` → `shorts_covers`).
- Approvals are never waived: an approval is the owner's OK or nothing. `release.publish_ok`,
  and the publish checklist's `channel`, `public`, `live`, `thumb`, `cover` and every Short's
  `related`, can never be waived. With `extras/pipeline.json`, `thumb` and `cover` are not hand
  ticks: `can-public` accepts them only when `extras/uploads/<asset>-thumb.json` matches the
  approved pick. A `failed` thumb or cover blocks Public even when that record matches. An
  approval that has no file hash does not pass: re-approve it, or `pipeline.py backfill-art`
  with the owner's words (that records the hashes and does not change the approval's version).
- A waiver from someone who isn't the episode owner is refused (outside episodes: Amitai).

## Who waits on whom (`pipeline.py next`)

- `waits: producer`: the Producer runs the command.
- `waits: helper`: a helper agent runs it and hands back to the Producer (brand on Amitai's
  Mac, segment helper); the Producer checks what comes back.
- `waits: owner`: an approval. The Producer batches every pending approval into one review
  round (`investing-bros-show` → Ownership and contact) and never pings per item.
- `next` lists every approval on a track that can be asked now, not only the first. Round 1
  (before any render) holds the cut list, the title, the segment ranges and the Short picks.
  Trim and copy have already run on the draft cut list, so a restore in that round re-trims
  and re-copies only. Silences under 2 s are never cut.

## Review rounds

Round 1, one message, before any render: the cut list (each `[content]` cut as its own question,
every `[routine]` line still on the list), the title, the two segment ranges, the three Short
picks. `cuts_ok` gates `main.video`, `segNN.render` and `shortNN.render`. It does not gate `trim`,
`copy`, `segNN.select` or `shortNN.pick`.

Round 2 is the Telegram approval round (`investing-bros-episode-upload` step 3b): the six Private
links, an A/B/C pick per asset, and the publish go. Uploads go up with option A. Promote the
picked file onto the canonical name, `approve` the art pick (and each asset's `ok`) from that
reply, then `yt_upload.py --set-thumbnail` when the pick is not the file already on the video,
then `approve release publish_ok`. One quote may be passed to each of those `approve` calls.
A later change of mind stales that art approval and `publish_ok`. The swap does not stale the
upload. A/B/C differ in art only. A Short cover-title change is burned into the opening banner,
so it is a re-render and a re-upload.

## Follow-up

An A/B/C contact-sheet script (one sheet per asset, options beside the Private link) is not part
of this map. Until it exists, the approval-round message names each option's file next to the link.

## Open questions (for Amitai)

1. **Dropping a standing deliverable.** Can the owner waive a whole track (for example Short
   03) for one episode? Today the bundle is fixed, `publish_checklist.py` requires all seven
   groups, and `pipeline.py` has no track waiver.
2. **Cuts of the other brother's speech.** With one episode owner approving cuts, should the
   other brother keep a veto on cuts inside his own speech? The map gives the owner every
   approval and sends the other brother a summary after each round.
3. **Shorts cut approval.** The old rule had Nadav approve each Short cut "before a rebuild or
   an upload"; the map takes that approval in the approval round, on the Private upload. Is a
   separate approval before the Private upload still wanted?
4. **Summary to the other brother.** One Telegram summary per review round (as built) or one
   per sign-off?
5. **Mid-form.** Optional mid-form highlights are not a track. Should a requested mid-form
   join the release (publish order, approval round)?
6. **Spotify link swap scope.** `investing-bros-publish` swaps the link on the episode, both
   segments and all three Shorts; `investing-bros-episode-upload` mentions the episode and the
   Shorts. The map follows publish (all six).
7. **Episode art headline.** Does a new final title always invalidate the cover and
   thumbnail, or only when the headline text changes? The map invalidates on any title change.
