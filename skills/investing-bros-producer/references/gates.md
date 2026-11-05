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
| `cut_list` | post-production (step 5) | `master` | file: `extras/cuts-review/cuts-list.txt` | — | `master` |
| `cuts_ok` | post-production (step 5) | `cut_list` | approval of the cut-list version (raw times + words around each cut) | owner | a changed cut list |
| `trim` | post-production (step 6) | `cuts_ok` | file: edited audio in the root (item `audio`), `extras/edit.json` + one review clip per cut (item `cut_list`) | — | `cuts_ok`; a new `edit.json` stales `copy`, `video`, `upload`, `release.redcircle_draft` and every segment/Short whose raw ranges overlap the changed span |
| `copy` | title-description | `trim` | file: `כותרות-פרק-N.txt`, `תיאור-פרק-N.txt` (item `titles_description`) | — | `trim` (chapters are mapped through `edit.json`) |
| `title_ok` | title-description | `copy` | approval: the owner's `בחירה סופית:` title, tied to `כותרות-פרק-N.txt` only (`of_keys`, the same way a segment thumbnail pick is tied to `-thumb.jpg`) | owner | a changed titles file. A description or chapter edit does not |
| `art` | brand (steps 3–8) | `title_ok` | file: `cover-פרק-N.png`, `thumbnail-פרק-N.jpg` in the root (item `thumbnail_cover`); log: `extras/cover-check.log` OK for both + mark: Codex provenance (item `cover_checks`); mark: `face_identity` | — | `title_ok` (the headline) |
| `art_ok` | brand (step 6) | `art` | approval: the owner's A/B/C pick, tied to the cover and thumbnail files | owner | a changed cover or thumbnail |
| `video` | video | `trim`, `copy` | file: teaser in `promo/` (item `teaser`); log `extras/teaser-check.log` CAPTIONS OK + mark (item `teaser_quality`); intro in `extras/` (item `intro`); `video/פרק-N-וידאו.mp4` (item `full_video`); log `extras/verify_sync.log` SYNC OK (item `verify_sync`); `video/תיאור-פרק-N-youtube.txt` with chapters + mark (item `chapters`) | — (the owner sees it in the approval round) | `trim`, `copy` |
| `upload` | episode-upload (step 3) | `video`, `art_ok`, `title_ok`; the postprod `upload` stage passes | record: `extras/uploads/main.json` from `yt_upload.py --source <master> --record` (Private, show channel, video ID, version = the current master's sha256: a record of an older render fails); file + mark: `extras/past-episode-cards.json`, cards set (item `past_episode_cards`); mark: `main.endscreen` (previous episode(s) + Subscribe over the outro, Editor preview) | — | `video`, `art_ok`, `title_ok`; a re-upload (new video ID) |
| `ok` | episode-upload (3b approval round) | `upload` | approval of the uploaded version (file sha256 + video ID) | owner | `upload` |

## seg01, seg02

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `select` | segment-video (step 1) | `main.trim` | mark: `segNN.select` (raw in/out, internal cuts, length, the alternative) | — | — |
| `range_ok` | segment-video (step 1) | `select` | approval of the range | owner | a changed selection |
| `render` | segment-video (`make_segment.py`) | `range_ok` | record: `extras/segment-NN.json` (raw range, source, mapping, `SYNC OK`, output sha256) | — | `range_ok`; a `main.trim` change that overlaps the picked range minus the segment's own drops (`selected_ranges`: a new cut there, or restoring one the segment crossed) |
| `package` | segment-video (steps 5–9) | `render` | file: the slot's four files in `segments/`, none empty (item `segments`, this slot); mark: `segNN.nudge` (0:31 frame checked) | — | `render` |
| `thumb_ok` | segment-video (step 7) / brand | `package` | approval: the owner's A/B/C pick, tied to `-thumb.jpg` | owner | a changed thumbnail |
| `upload` | segment-video (steps 10–11) | `thumb_ok` | record: `extras/uploads/segNN.json` (Private, version = the current `.mp4`'s sha256); mark: `segNN.links` (one card at 0:30 + end screen to the full episode, verified) | — | `package`, `thumb_ok`, `main.upload` (the full-episode link); a re-upload |
| `ok` | episode-upload (3b) | `upload` | approval of the uploaded version | owner | `upload` |

## short01, short02, short03

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `pick` | shorts (step 1) | `main.trim` | mark: `shortNN.pick` (raw ranges, cover title) | — | — |
| `pick_ok` | shorts (step 1) | `pick` | approval: the owner's three picks (one quote may approve all three) | owner | a changed pick |
| `render` | shorts (steps 2–6) / remotion | `pick_ok` | log: `extras/check-short-NN.log` (saved `check_short.py` output: a LUFS line, no `warning:`) | — | `pick_ok`; a `main.trim` change that overlaps the Short's raw ranges |
| `cover` | brand (Shorts covers) | `pick_ok` | file: `Shorts/שורט-NN-<נושא>-cover.jpg`; log: `extras/cover-check.log` has `OK` for it (the provenance mark, item `shorts_covers`, is checked by `release.review_gate`) | — | `pick_ok` (the cover title) |
| `cover_ok` | brand | `cover` | approval: the owner's A/B/C pick, tied to the cover file | owner | a changed cover |
| `package` | shorts (step 7) | `render`, `cover_ok` | file: the slot's four files in `Shorts/`, none empty (item `shorts`, this slot) | — | `render`, `cover_ok` |
| `upload` | shorts / episode-upload (step 3) | `package`, `main.upload` | record: `extras/uploads/shortNN.json` (Private, version = the current `.m4v`'s sha256), `.srt` published. Related video is not required here: the full episode is still Private, so it is set and checked before the Short goes Public (`investing-bros-publish`, item `related`, never waived) | — | `package`, `main.upload`; a re-upload |
| `ok` | episode-upload (3b) | `upload` | approval of the uploaded version (this is the cut approval) | owner | `upload` |

## release

| Stage | Owning skill | Prerequisite | Evidence | Approver | Invalidated by |
|---|---|---|---|---|---|
| `redcircle_draft` | episode-upload (step 2) | `main.trim`, `main.title_ok` | mark: `redcircle_draft` (draft URL, screenshot checked, `check_titles_match.py` passed) | — | `main.trim` (new audio), `main.title_ok`, `main.copy` |
| `review_gate` | post-production | every track's `upload`, `redcircle_draft` | the postprod `review` stage passes | — | any of its inputs |
| `approval_round` | episode-upload (3b) | `review_gate` | mark: `release.approval_round` (the one Telegram message: file, time, every link passed `check_links.py --message`) | — (a pipeline message) | any `upload` (re-send one full message) |
| `publish_ok` | publish | every track's `ok`, `approval_round` | approval: the owner's own words naming what may go Public, tied to every `ok` version and video ID; **never waivable** | owner | any `ok`, any re-upload |
| `publish` | publish | `publish_ok` | file: `extras/publish-checklist.json`, every item ticked or waived (item `published`); `publish_checklist.py can-public` re-checks `publish_ok` and the video IDs against this file every time | — | `publish_ok` |
| `spotify_links` | publish (step 7) | `publish` | mark (item `spotify_links`): the Spotify episode URL on the episode, both segments and all three Shorts, `check_links.py` passed | — | `publish` |
| `old_uploads` | episode-upload / publish | `publish` | mark (item `old_uploads`): superseded Private IDs deleted, naming every ID in the upload records' `superseded`, or `none` when there are none | — | any upload record changing (a new superseded upload) |
| `retro` | producer (`pipeline.py retro`) | `spotify_links`, `old_uploads` | file: `extras/retro-פרק-N.md`; mark: `release.retro` (the learnings PR/issue links, the one message to the owner) | — | — (never blocks publishing) |

The postprod `done` stage passes once `publish`, `spotify_links` and `old_uploads` pass.

## Waivers

- The owner may waive a gate item or a non-approval stage for this episode, in their own
  words (`pipeline.py waive ITEM --by "<owner> HH:MM: ..."`). A waived parent clears its
  child items (`teaser` → `teaser_quality`; `shorts` → `shorts_covers`).
- Approvals are never waived: an approval is the owner's OK or nothing. `release.publish_ok`,
  and the publish checklist's `channel`, `public`, `live` and every Short's `related`, can
  never be waived.
- A waiver from someone who isn't the episode owner is refused (outside episodes: Amitai).

## Who waits on whom (`pipeline.py next`)

- `waits: producer`: the Producer runs the command.
- `waits: helper`: a helper agent runs it and hands back to the Producer (brand on Amitai's
  Mac, segment helper); the Producer checks what comes back.
- `waits: owner`: an approval. The Producer batches every pending approval into one review
  round (`investing-bros-show` → Ownership and contact) and never pings per item.

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
