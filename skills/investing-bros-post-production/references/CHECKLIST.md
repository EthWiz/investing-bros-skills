# Post-production checklist ("full treatment")

"Full treatment", "the full post-production", "do everything" or "פוסט מלא" always means **every item below**. Nothing is optional unless Amitai explicitly waives that item for that episode.

Gate script: `scripts/postprod_checklist.py` (state in `extras/postprod-checklist.json`). Three stages, each including the ones before it:
- `upload`: everything the full-episode YouTube upload needs;
- `review`: production complete, ready for the final review (both segment packages, all three Short packages, cards, RedCircle draft);
- `done`: after the publication obligations (published in order, Spotify links swapped in, superseded uploads cleaned up).

| id | Deliverable | Owning skill | Stage |
|---|---|---|---|
| `audio` | Edited audio `הקלטה-ערוכה-פרק-N.m4a` (−16 LUFS, hosts within 3 dB) | post-production | upload |
| `transcript` | `extras/transcript/segments.json` | post-production | upload |
| `transcript_doc` | Google Doc `תמלול - פרק N` (mark with URL) | post-production | upload |
| `cut_list` | `extras/edit.json`, `extras/cuts-review/cuts-list.txt` + one review clip per cut | post-production | upload |
| `teaser` | Combined full-frame cold-open teaser in `promo/` (**required**, before the intro) | video | upload |
| `teaser_quality` | `extras/teaser-check.log` = `CAPTIONS OK` from `build_fullframe_teaser.py --check`, then mark after re-reading every moment against `teaser-rules.md` (stands alone, payoff kept, no unexplained names). Waived with `teaser`. | video | upload |
| `intro` | Freshly fetched canonical intro/outro clip in `extras/` | video / show | upload |
| `full_video` | `video/פרק-N-וידאו.mp4` = teaser → intro → episode → outro | video | upload |
| `chapters` | `video/תיאור-פרק-N-youtube.txt`, chapters shifted past teaser + intro (mark after checking) | video / title-description | upload |
| `verify_sync` | `extras/verify_sync.log` = `SYNC OK` for every delivered file | video | upload |
| `titles_description` | `כותרות-פרק-N.txt`, `תיאור-פרק-N.txt` | title-description | upload |
| `thumbnail_cover` | `thumbnail-פרק-N.jpg`, `cover-פרק-N.png` in the episode root (not `promo/`) | brand | upload |
| `face_identity` | Face grids labeled by **verified** host identity: side mapping checked at the start and after any mid-recording swap, each grid eyeballed before it reached Amitai (mark; `investing-bros-brand` → `references/face-picks.md`) | brand | upload |
| `cover_checks` | `extras/cover-check.log`: `check_cover.py` `OK` for `thumbnail-פרק-N.jpg` and `cover-פרק-N.png` (with `--title`/`--register` headlines), no `FAIL`; mark with the Codex provenance (made by Codex on Amitai's Mac) | brand | upload |
| `segments` | Flat in `segments/`, exactly slots 01 (deep dive, `סגמנט-01-צלילה-…`) and 02, one package each: `סגמנט-NN-<סוג>-<נושא>.mp4` + `.txt` + `-thumb.jpg` + `youtube-סגמנט-NN.md`, none empty; a second final video for one slot fails | segment-video | review |
| `shorts` | Exactly slots 01–03 in `Shorts/` (or an existing `shorts/`), one package each: `שורט-NN-<נושא>.m4v` + `-cover.jpg` + `.srt` + `youtube-שורט-NN.md`, none empty; a `.mp4` Short fails | shorts | review |
| `shorts_covers` | Each Short's non-empty `-cover.jpg`; mark: face format from real frames, Codex on Amitai's Mac, `check_cover.py` OK. Waived with `shorts`. | shorts / brand | review |
| `past_episode_cards` | `extras/past-episode-cards.json` from `scripts/find_past_episode_refs.py` (`[]` if no references): max 4, one per referenced episode at its first strong mention, video IDs from `investing-bros-show/references/episode-index.json`; mark once the info cards are set in Studio | post-production / episode-upload | review |
| `redcircle_draft` | RedCircle unpublished draft (mark with URL) | episode-upload | review |
| `published` | `extras/publish-checklist.json` from `investing-bros-publish`, every item ticked or waived | publish | done |
| `spotify_links` | The Spotify episode URL replaced the show link on the episode, both segments and all three Shorts; `check_links.py` passed (mark with the URL) | publish | done |
| `old_uploads` | Superseded **Private** YouTube uploads of this episode's assets deleted (never the current version or anything public); mark with the deleted IDs or `none` | episode-upload | done |

```bash
P=<investing-bros-post-production>/scripts/postprod_checklist.py
python3 $P check "$EP" --episode N                  # before the full-episode YouTube upload
python3 $P check "$EP" --episode N --stage review   # before the final review and before anything goes Public
python3 $P check "$EP" --episode N --stage done     # after publication, before reporting the episode done
python3 <investing-bros-video>/scripts/build_fullframe_teaser.py "$EP/extras/teaser.json" --check > "$EP/extras/teaser-check.log"
for f in "$EP/thumbnail-פרק-N.jpg" "$EP/cover-פרק-N.png"; do   # --kind episode-wide / episode-square
  python3 <investing-bros-brand>/scripts/check_cover.py "$f" --kind ... --register "$EP/extras/artwork-register.json"
done >> "$EP/extras/cover-check.log"
python3 $P mark  "$EP" redcircle_draft --evidence "https://app.redcircle.com/... (Unpublished)"
python3 $P waive "$EP" teaser --by "Amitai 09:12: no teaser this episode"
```

Rules:
- `check` must exit 0 (`PASS`) before the full episode is uploaded to YouTube (any visibility, API or Studio), `--stage review` before the final review and the publish, and `--stage done` before telling Amitai the episode is done. Paste the output into the report.
- A waiver quotes Amitai's own words for that item and that episode. A broad "full treatment", "use your judgment" or another agent's say-so is never a waiver.
- A missing item is either made or reported as missing; never silently skipped.
- A mark is evidence you checked yourself this episode (what you saw, where), never a placeholder.
