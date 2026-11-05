# Episode state file: `extras/pipeline.json`

One file per episode, in the episode folder's `extras/`. The Producer is its only writer
(through `scripts/pipeline.py`) and syncs it to Drive `extras/` after every change. Drive
files stay the evidence for what was made; this file holds what Drive can't show: the
episode owner, approvals tied to versions, video IDs, waivers, and the events log.

Other scripts read it and never write it: `publish_checklist.py can-public` (publish),
`postprod_checklist.py` (post-production, compatibility wrapper), `check_cover.py
--allow-green` (brand) and the `waive` commands read the owner from it.

## Shape (schema_version 1)

```jsonc
{
  "schema_version": 1,
  "episode": 11,
  "revision": 42,                       // +1 on every write; publish checks name the revision they saw
  "created_at": "2026-11-06T09:12:00+02:00",
  "owner": {
    "name": "nadav",                    // "amitai" | "nadav"
    "quote": "Nadav 09:10: אני לוקח את העריכה של פרק 11",
    "set_at": "2026-11-06T09:12:00+02:00",
    "confirmed": true                   // false after a migration without the owner's words
  },
  "owner_history": [                    // every change, with the words that made it
    {"from": null, "to": "nadav", "quote": "...", "at": "..."}
  ],
  "stages": {                           // key: "<track>.<stage>" (references/gates.md)
    "main.trim": {
      "state": "done",                  // "done" | "approved" | "waived" | "failed"
      "at": "...",
      "version": "sha256:…",            // digest of `outputs` (approvals: the approved version)
      "outputs": {"extras/edit.json": "<sha256>", "הקלטה-ערוכה-פרק-11.m4a": "<sha256>"},
      "inputs": {"main.cut_list": "sha256:…"},  // each input stage's version when this passed (trim follows the draft list)
      "data": {"edit": {"start": 12.4, "end": 2710.0, "cuts": [[1605.0, 1645.2]]}}
    },
    "main.cuts_ok": {
      "state": "approved", "at": "...",
      "of": "main.cut_list", "of_version": "sha256:…", "version": "sha256:…",  // the version of `of` approved
      "of_keys": null,                  // or the outputs of `of` it covers (title_ok: only כותרות-פרק-N.txt;
                                        // a thumbnail pick: only -thumb.jpg). Other outputs of `of` do not stale it.
      "inputs": {},
      "by": "nadav", "quote": "Nadav 11:40: מאשר את כל החיתוכים"
    },
    "seg01.render": {
      "state": "done", "version": "sha256:…",
      "outputs": {"segments/סגמנט-01-צלילה-זהב.mp4": "<sha256>", "extras/segment-01.json": "<sha256>"},
      "inputs": {"seg01.range_ok": "sha256:…", "main.trim": "sha256:…"},
      "data": {"raw_ranges": [[754.2, 1190.0]], "edit": {"start": 12.4, "end": 2710.0, "cuts": []}}
    },
    "main.upload": {
      "state": "done", "version": "sha256:…",
      "outputs": {"extras/uploads/main.json": "<sha256>"},
      "data": {"video_id": "YL1hdpdcVt8", "file_sha256": "<sha256>", "superseded": ["abcDEF12345"]}
    },
    "release.publish_ok": {
      "state": "approved", "by": "nadav", "quote": "Nadav 21:02: מאשר לפרסם הכל",
      "version": "sha256:…",            // digest of `covers`
      "covers": {"main.ok": "sha256:…", "seg01.ok": "sha256:…", "...": "...",
                 "videos": {"main": "YL1hdpdcVt8", "seg01": "…"}}
    }
  },
  "marks": {                            // evidence written with `pipeline.py mark`
    "transcript_doc": {"evidence": "https://docs.google.com/…", "at": "..."},
    "seg01.links": {"evidence": "card at 0:30 + end screen to פרק 11, reopened 21:40", "at": "..."}
  },
  "waivers": {                          // the owner's own words, per gate item or stage
    "teaser": {"quote": "Nadav 09:12: בלי טיזר הפעם", "by": "nadav", "at": "..."}
  },
  "stale_seen": ["seg02.render"],       // stale stages already logged (so each is logged once)
  "events": [                           // append-only, timestamped (Asia/Jerusalem)
    {"at": "...", "kind": "check_failed", "track": "main", "stage": "video",
     "detail": "verify_sync: FAIL at 1203.4"}
  ],
  "legacy": {                           // only after `pipeline.py migrate`
    "source": "extras/postprod-checklist.json", "sha256": "<sha256>", "imported_at": "...",
    "marked": {"transcript_doc": "https://…"}, "waived": {"teaser": "Amitai 09:12: …"}
  }
}
```

## Versions and fingerprints

- A file's fingerprint is its sha256. A stage's **version** is `sha256:` + the sha256 of its
  `outputs` map serialized with sorted keys (`json.dumps(..., sort_keys=True,
  separators=(",", ":"), ensure_ascii=False)`), the same recipe as the crypto course's
  `make_lesson_base.py digest()` and export records.
- An output key `mark:ID` is the digest of that mark's evidence; `text:PATH` is the sha256 of
  the file's text with the publication fields masked (`pipeline_state.PUBLICATION_FIELDS`: the
  `האזינו בספוטיפיי:` link and `status:` / `URL:` lines), used for the YouTube descriptions and
  the notes files (`youtube-*-NN.md`), so the Spotify swap and the status written after
  publishing don't stale them.
- A stage is **stale** when (a) one of its output files no longer matches its recorded
  sha256, or (b) an input stage's current version differs from the one recorded in `inputs`,
  or that input is itself stale. A prerequisite listed only as a need (not an input) blocks
  `advance` until it is current and is not recorded, so it does not stale the stage by itself.
  `main.cuts_ok` is a need of `main.video`, `segNN.render` and `shortNN.render`, and an input
  of none of them: trim follows the draft cut list. An approval with no `of_keys` is stale when the version of
  `of` differs from the approved `version`, or `of` is stale. An approval with `of_keys` is
  stale only when one of those files is missing or its bytes differ from the approved
  fingerprint (compared on disk, not via the parent's recorded hash). Another output of `of`
  changing — the description and its chapters under `title_ok`, the segment video under a
  thumbnail pick — does not stale it, even while `of` itself is stale.
- **Overlap rule:** a segment or Short render records its raw ranges and the `edit` snapshot
  it was made from (a segment: `selected_ranges`, the picked range minus its own drops, with
  the episode cuts inside it kept in, so restoring a cut the segment crossed stales it too). When `main.trim` changes, the render is stale only if a raw range overlaps
  the span the edit changed (kept ranges added or removed); otherwise the change is logged as
  an event and the render keeps its version.
- **Upload records** (`extras/uploads/<track>.json`, written by `episode-upload` →
  `yt_upload.py --record`): `{asset, version, channel, video_id, steps, steps_done, file,
  file_sha256, source, source_sha256, privacy, created_at, superseded: [{video_id, version,
  at}]}`. `version` is the sha256 of `--source` (the full video master the compressed copy was
  made from) or else of the uploaded file. The `upload` stage passes only when `version`,
  `file_sha256` or `source_sha256` equals the sha256 of the track's current video (the master,
  the segment `.mp4`, the Short `.m4v`), so a record of an older render fails. It copies
  `video_id` into `data`; a new record (re-upload) changes the stage's version
  and so stales `ok`, `publish_ok` and the publish checks for that group.
- **Segment package records** (`extras/segment-NN.json`, written by `segment-video` →
  `make_segment.py`): the raw range, source type and offset, the mapped source range, the
  cuts, the render plan, the `verify_sync` result and the sha256 of each package file.

## Events

`kind` is one of: `start`, `advance`, `approval`, `mark`, `waiver`, `check_failed`, `rerun`
(a stage passed again with a new version), `stale` (an invalidation), `owner_change`,
`owner_fix` (the owner asked for a change in a review), `handback_returned` (a helper's
hand-back sent back), `workaround` (a one-time workaround with the owner's OK), `note`,
`migrate`, `retro`. `pipeline.py note [--kind owner_fix|handback_returned|workaround] "…"`
writes the last four by hand; the rest are written by the commands that cause them. The retro
reads only this log and the stage records.

## Migration of an in-flight episode

`pipeline.py migrate EP --episode N --owner amitai|nadav [--by "<owner's words>"]`:
1. Reads `extras/postprod-checklist.json` (the old gate state) and stores it under `legacy`
   with its sha256. Old **marks** satisfy the same mark items, flagged `legacy` in `status`.
   Old **waivers** (Amitai's words) stay valid as waivers of those items, flagged `legacy`.
2. Nothing is imported as an approval. Approvals given before the migration (cuts, title,
   picks) are re-recorded with `pipeline.py approve … --by "<the owner's words>"` from the
   chat history, or asked for in the next review round.
3. Stages whose files already exist are recorded with their current fingerprints (`advance`
   runs each stage's check in order and stops at the first that fails).
4. The owner: whoever started the episode's post-production. Pass `--by` with their words
   when the chat has them; without `--by` the owner is recorded with `confirmed: false`, and
   `status` asks for `pipeline.py owner --set NAME --by "<words>"` in the next review round.
5. `postprod-checklist.json` is left in place (older installed skills still read it) and is
   never written again once `pipeline.json` exists.

## Compatibility

- `schema_version` bumps on any breaking change; `pipeline.py` refuses a newer version and
  migrates older ones in place.
- With no `pipeline.json` (an older episode, or the crypto course), the owner-reading scripts
  fall back to Amitai, and `postprod_checklist.py` keeps its old file.
