# Per-episode face picks

One file per episode, `epNN.json`, written by the brand skill's
`record_face_picks.py` (see `investing-bros-brand` → face picks): the stills shown to
the operator, each with host, raw recording time `t_sec`, `label` (good = picked,
bad = rejected, unknown = shown but not marked) and, for every reject, the operator's
reason. The images are not committed.

`ep09.json` holds the same episode-9 stills as the face-pick eval's `labels.json`
(PR #75). Once both are on `main`, the eval should read these files too, so a new
episode's labels need no hand edit of `labels.json`.
