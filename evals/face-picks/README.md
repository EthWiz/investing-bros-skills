# Face-pick eval

Does `skills/investing-bros-brand/scripts/face_score.py` rank host stills the way Amitai
picks thumbnail portraits? The scorer must score **every good still above every bad
still**: 100% pairwise accuracy, for both hosts.

## Labels (episode 9, 2026-10-29)
27 stills from the episode-9 recording, 9 per grid (Amitai `A1`–`A9` and `B1`–`B9`,
Nadav `N1`–`N9`). `labels.json` has each still's host, raw recording time `t_sec`,
label and reason.

| label | stills | why |
|---|---|---|
| good | B1, B9, B2, A4 (Amitai); N1, N2, N4 (Nadav) | picked for thumbnails |
| bad | A1 | "my eyes look weird": a wide stare, with the irises turned sideways |
| bad | A3 | "eyes completely looking down and almost completely shut": head dropped, brows lowered |
| bad | A8 | "a weird face": a stretched, lopsided mouth with the head turned and a hand on the chin |
| bad | B7 | "eyes looking into the abyss and my mouth is in a weird shape": a blank stare, no smile |
| unknown | the rest | shown but not labelled; listed in the report, but not scored |

`labels.json` `baselines` holds each host's medians over the whole episode (one frame
every 4 s). That is the same baseline `face_score.py` computes when it scans an episode,
so the eval scores the stills as a real run would.

## Run it
```
python3 evals/face-picks/run_eval.py            # current scorer (v2)
python3 evals/face-picks/run_eval.py --scorer v1  # the old formula, for comparison
```
This needs only the Python standard library. It reads `features.json` and prints each
still's score and its biggest penalties, pairwise accuracy (overall and same host), the
margin (worst good − best bad) and any misranked pair. It exits 1 below 100%. CI runs
the same check in `tools/test_face_pick_eval.py`.

| scorer | pairwise | same host | margin |
|---|---|---|---|
| v1 (smile − blink − look-down − jaw + sharpness − yaw) | 39% | 56% | −2.06 |
| v2 (`face_score.py`) | 100% | 100% | +0.52 |

v1 scored `eyeLookDown` as bad. The camera sits above the screen, so the good stills
score high on it too. v2 measures where the irises sit in each eye, eye opening and head
pitch against the host's own baseline, brow lowering, and mouth shape. Robustness check:
each v2 term alone can be scaled ×0.7 or ×1.3, or dropped, and the eval still passes 100%.

## The images are not in the repo
This repo is public, episode 9 isn't published, and the brand skill forbids committing
reference images. Only the times and derived features are committed. To rebuild the
stills and features (this needs `ffmpeg`, `mediapipe`, `opencv-python` and the
MediaPipe `face_landmarker.task` model):
```
python3 evals/face-picks/extract_frames.py riverside-combined.mp4 /tmp/face-picks
python3 evals/face-picks/build_features.py --images /tmp/face-picks --model face_landmarker.task
python3 evals/face-picks/run_eval.py --images /tmp/face-picks --model face_landmarker.task
```
The recording is in the episode's Drive folder. Each still is that host's half of the
side-by-side frame at `t_sec` (Amitai left, Nadav right).

## Adding labels from a later episode
Add the stills Amitai picks (good) and rejects (bad, with his words as `reason`) to
`labels.json`. Give each one a new id, its host and its raw `t_sec`. Then rebuild
`features.json` with `build_features.py` and run the eval. If a new reject slips
through, fix it with a general face feature, such as gaze, eye opening, mouth shape or
head pose, not a rule for one still. Then check the top picks on the full episode
(`face_score.py FRAMES_DIR --side left|right --pick 9`) and look at them yourself.
