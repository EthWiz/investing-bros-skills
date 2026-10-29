# Face picks: every episode

Thumbnails and photo-cutout covers use only real frames of each brother that the
operator (Amitai) picked from that episode's recording. Each episode's picks and
rejects also become eval labels, so the face scorer keeps learning his taste.

## The loop
1. **Shortlist about 10 stills per speaker.** Sample the whole recording every few
   seconds and score each host on his own side with `scripts/face_score.py`
   (`FRAMES_DIR --side left|right --pick 10 --json HOST-scores.json`; Amitai left,
   Nadav right in the Riverside side-by-side; frame naming, model and refinement as in
   [covers](covers.md)). It is a best-effort shortlist: look at each still yourself.
   Until `face_score.py` is on `main` (PR #75), pick the times by eye.
2. **Show labelled grids.** One grid per host:
   ```bash
   python3 scripts/make_face_grid.py riverside-combined.mp4 OUT --host amitai --side left \
     --prefix A --score-json amitai-scores.json --pick 10
   python3 scripts/make_face_grid.py riverside-combined.mp4 OUT --host nadav --side right \
     --prefix N --score-json nadav-scores.json --pick 10
   ```
   Each tile carries its id and recording time (`A3  33:15.4`). Show Amitai the grids,
   not loose files. Files are named per round, `grid-<host>-<prefix>.jpg` and
   `manifest-<host>-<prefix>.json`: a second round for the same host takes a new prefix
   (episode 9: `A`, then `B` for Amitai), and the script refuses to overwrite a round.
3. **The operator picks and rejects.** Ask which stills he wants and which he doesn't
   want, and **why** for each reject, in his words. Don't fill in reasons for him; an
   unmarked still stays `unknown`.
4. **Record them as eval labels** in the repo, one file per episode:
   ```bash
   python3 scripts/record_face_picks.py --episode N \
     --manifest OUT/manifest-amitai-A.json OUT/manifest-nadav-N.json \
     --good A4,N1,N2 --bad "A3=eyes looking down, almost shut" \
     --out evals/face-picks/episodes/epNN.json
   ```
   Pass every round you showed (or just `OUT`, which takes all its manifests). Each
   still keeps its host, raw `t_sec`, label and reason; the file records the
   recording and the date. Open a PR with it (Amitai merges). The stills themselves stay
   out of the repo (public repo; reference images live in Drive).
5. **Run the eval** in the repo's `evals/face-picks/` (see its README) with the new
   labels added. If a new reject now scores above a pick, fix the scorer with a
   general face feature, not a rule for one still.
6. **Use only the picked frames** for that episode's thumbnails and covers. A cover that
   needs a frame no one picked goes back to step 2.

## TODO after PR #75 merges
- The face-pick eval (`evals/face-picks/run_eval.py`, `extract_frames.py`, its
  `labels.json`) reads only episode 9's hand-made labels. Make it also read every
  `evals/face-picks/episodes/epNN.json` (same item fields: host, `t_sec`, label,
  reason), so a new episode's picks join the eval without hand-editing `labels.json`.
  Until then, add the new episode to `labels.json` by hand when you run step 5.
- Then point step 1 at `face_score.py` on `main` and drop the "pick by eye" fallback.

## Rules
- Real frames only. Never generate, regenerate or "improve" a real host's face with an
  image model; only the touch-ups allowed in [covers](covers.md).
- Picks are per episode: never reuse a portrait from another episode.
- A reject without the operator's reason is not recorded as a reject.
