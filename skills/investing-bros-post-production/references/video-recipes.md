# Video assembly recipes

Shell recipes from the video-editing agent for the full episode video. Run them from this skill's `scripts/` directory.

Shorts are not rendered here. The batch playbook is `SHORTS_GUIDE` in `investing-bros-shorts` (`shorts.sh` and `scripts/reel/`).

**Not in this repo:** the Heebo font, the YuNet `yunet.onnx` model, and the logo end-card video. Those belong to the shorts pipeline (`HEEBO_FONT`, `YUNET`, `ENDCARD`). **These scripts were syntax-checked only. They have not been run end to end.**

## One command per stage

| Stage | Command |
|---|---|
| Cold open + intro (hard cut) | `INTRO=intro.mp4 ./cold_open.sh SRC.mp4 "00:12:01.2-00:12:06,00:31:10-00:31:14.5" cold_intro.mp4 [music.wav]` |
| Episode cut + join | `./cut_episode.sh SRC.mp4 edl.txt episode.mp4 cold_intro.mp4` |
| Share / export | `./export.sh episode.mp4 out_dir/` |
| Conform the intro (only if the spec differs) | `INTRO=intro.mp4 ./conform_intro.sh SRC.mp4 intro_1080p.mp4` |

- **cold_open.sh** — segments are `start-end` (seconds or `HH:MM:SS`), comma-separated. Re-encodes only the opener, to the intro's spec, then `join.sh` concatenates opener + intro with `-c copy` (intro bytes untouched). `--no-join` writes the opener only. `LIKE=ref.mp4` matches another spec. `MUSIC_START` seeks into the bed.
- **cut_episode.sh** — EDL lines are `HH:MM:SS.mmm -> HH:MM:SS.mmm` (episode 7 `KEEPS` format) or `start end`. `#` comments are skipped. All keeps on keyframes means a stream copy; otherwise one fast single-pass encode (x264 veryfast CRF 18, input-seeked ranges). Then concat-demuxer `-c copy` with the cold open. The body is encoded to the source's own res/fps, so `COLD_OPEN` must match it (`cold_open.sh` with `LIKE` pointing at the source).
- **join.sh** `OUT a.mp4 b.mp4 ...` — refuses a mismatched codec, resolution, fps or audio (prints `MISMATCH`).
- **export.sh** — a share file under `SHARE_MB` (default 100): copied when it is already small, otherwise 2-pass bitrate-targeted x264 + AAC 128k. Files over `PART_MB` (default 50) are also split into `.partNN` plus `NAME_SHA256SUMS`. Rejoin: `cat NAME.mp4.part* > NAME.mp4 && sha256sum -c NAME_SHA256SUMS`. The same script is in `investing-bros-shorts`.

`assemble_episode.sh` is still how you join teasers that `investing-bros-teaser` already rendered. These recipes cut the opener and the body from the master instead.

## Music

`cold_open.sh` applies the cold-open music bed in `investing-bros-teaser` (Cold-open music bed). It does not define a second mix.

- Speech: `highpass=f=80`, then `afftdn=nr=10:nf=-30`. `ARNNDN_MODEL` only when that file is already on the machine. `SKIP_DENOISE=1` if the voice turns watery. Segment edges fade 10–20 ms.
- Bed: WAV/FLAC, or at least 256 kbps. Rejected when the band above 8 kHz is within 10 dB of the whole file (hiss). Listen once — any watermark or voice tag is a reject.
- Duck: `sidechaincompress=threshold=0.03:ratio=4:attack=15:release=400`. The bed sits about −18 to −24 dB under the dialogue. Fade in ~0.8 s, fade out ~1 s.
- Master: two-pass `loudnorm` −14 LUFS, true peak −1 dBTP, LRA 11. Shorts use the social-clip true peak −1.5 dBTP (`investing-bros-shorts`), not this target.
- Amitai's intro is not re-mixed. The join is a hard cut (`-c copy`).

## Paths

Nothing defaults to a machine path.

| Variable | Used by | Meaning |
|---|---|---|
| `INTRO` | `cold_open.sh`, `conform_intro.sh` | Amitai's intro mp4. Required for the join (and for the opener's spec unless `LIKE` is set). |
| `LIKE` | `cold_open.sh` | Spec reference when it should not be the intro. |
| `MUSIC_START` | `cold_open.sh` | Seconds to skip into the bed. Default 0. |
| `ARNNDN_MODEL` | `cold_open.sh` | Optional rnnoise model. No path is assumed. |
| `SKIP_DENOISE` | `cold_open.sh` | Set to skip speech denoise. |
| `SHARE_MB`, `PART_MB` | `export.sh` | Share cap (100) and split size (50), in MB. |

`lib.sh` in this skill is the same file as in `investing-bros-shorts`.

## House accent

Gold is `#F5B71F` (`investing-bros-show`). These recipes do not pick a colour. The shorts pipeline uses that accent for the active caption word, the title underline and motion-graphic gold.

## Limits

- The intro is often 1280×720/24 and the Riverside source is 1920×1080/24. A `-c copy` concat needs one spec. Either produce the episode at the intro's spec, or make a scale-only conformed intro once with `conform_intro.sh` and pass that file as `INTRO`.
- Keyframe probing of a one-hour source is slow. That cost was not re-measured here.
- The shorts wrapper that originally sat next to these recipes hardcoded a reel directory and an end-card path on one machine. Use `shorts.sh` in `investing-bros-shorts` instead. It reads `ENDCARD`, `HEEBO_FONT`, `YUNET` and `MODELS_DIR`, and it ships with `scripts/reel/`.
