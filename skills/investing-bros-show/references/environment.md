# Environment: what works where

Read this before working around anything. Every line here cost an agent time to find out (episode 7 shorts, 2026-10-14). If something here is wrong or new, fix it in a PR.

## Getting raw video and other big files
- **Drive connector:** downloads Docs and files up to **100 MB** on the newer connector (episode 7). A raw episode (1–2 GB) still cannot come through it. The shorts run also hit an older **10 MB** cap — if a download between 10 and 100 MB is rejected, use the Mac or `drive.sh` (Drive API) path instead of retrying the connector. Browser upload (Claude in Chrome) is a separate **10 MB** per call; that limit is unchanged (show conventions → accounts).
- **Box browser download:** for a Drive file over 100 MB, have Amitai share the
  episode folder with the YouTube Editor account from show conventions, then open
  Drive in that account's existing browser profile and choose Download (and
  **Download anyway** on the large-file scan warning). Do not sign in as Amitai.
  A `show:` rclone remote is not guaranteed to exist; test `drive.sh` once and use
  the browser path when it reports that the remote is missing.
### Getting the full source video (step by step)
1. **Not Telegram.** The Telegram Bot API downloads files only up to **20 MB**, so a full episode
   posted in the group can't be fetched from there. Ask for it in Drive or as a Riverside link.
2. **Drive (preferred for big files):** `drive.sh` needs `rclone`, which isn't installed on the box,
   and the connector can't fetch a 1–2 GB file. Use the box browser signed in as the YouTube upload
   account `investingbros.grokbot@gmail.com` (`?authuser=1`): open the file → Download →
   **Download anyway** on the virus-scan warning. Other bot accounts (e.g. `ami.grokbot`) may hit
   Google re-verification; don't fight it, switch to the upload account.
3. **Riverside:** the episode pull is the web dashboard in the browser (`investing-bros-producer`
   → `main.riverside`). It starts when the owner says the episode was recorded, then a temporary
   polling routine checks about every 15 minutes (10–20 is allowed) and deletes or disables
   itself after the download or after about 6 hours. Sign in at riverside.fm (it redirects to
   riverside.com) with the Grok Bot vault login, secure fill only. Never print it. High-quality
   per-speaker video and audio, every part of a split session, stay in the episode working
   folder. Do not upload that raw footage to Drive.
   A shared `riverside.com/shared/exported-clip/...` link is not this pull: one **Download**
   button, no quality picker, and its "1080p" was 720p on episode 8. The recording share link
   (`/dashboard/studios/…/recordings/<id>?share-token=…`) is the fallback when `main.riverside`
   is waived. If a captcha blocks secure fill, waive the stage and use that fallback; do not
   skip the dashboard before trying it. The Claude app's built-in browser pane doesn't save
   downloads (episode 8): the Producer's browser does. A waived pull can still be the host
   clicking Download → Aligned video in their own Chrome, into `~/Downloads`.
4. **Always check what you got** and keep the highest-quality copy:
   `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -show_entries format=duration -of compact FILE`.
   If Riverside gives 720p, use Nadav's own Drive master (episode 8: `פרק 8 לא ערוך.mp4`, 1920×1080, 24 fps).
   Say in the hand-back when only 720p exists (it gets upscaled).
5. Downloads land in `/home/box/Downloads`; move them into the episode working folder (`$EP`)
   and note which source and resolution you used.

- **Riverside sign-in** is the web dashboard with the Grok Bot vault (secure fill only). A captcha that secure fill cannot clear waives `main.riverside`; the host can then download the tracks. Never delete a studio, project or recording there. Do not upload the raw files to Drive when the pull worked.
- For moving a completed large file out of the box, use the chunked handoff under
  [Delivering files](#delivering-files); do not assume a browser upload will be faster.
- **Never sign in to Amitai's Google account from a browser.** The account is in Advanced Protection: sign-in needs his passkey or security key; approving on the phone isn't enough, and a failed attempt locks browser sign-in for 48 hours.
- **Drive for desktop on Amitai's Mac streams files** (`~/Library/CloudStorage/GoogleDrive-…`). That folder shows up empty to the device shell, and listing it can hang the bridge. Don't use it.
- **Until the Drive script exists:** ask Amitai to Option-drag the file from Finder into `~/Downloads` (a connected folder), then process it on the Mac.

## Network (code execution allowlist)
- Reachable after Amitai allowed them: `www.googleapis.com`, `oauth2.googleapis.com`, `accounts.google.com`, `drive.google.com`, `api.telegram.org`, `downloads.rclone.org`, `raw.githubusercontent.com`; plus the package registries (npm, PyPI).
- Still blocked: `drive.usercontent.google.com` and `*.googleusercontent.com` (big Drive downloads redirect there — use the Drive API's `alt=media` on `www.googleapis.com`), Hugging Face, the PyTorch wheel index.
- `github.com` downloads work only for repos attached to the session.
- A running session may keep its old network rules; test new domains in a new session.

## Amitai's Mac (device shell)
- Each command stops after **3 minutes**; background processes are **killed** when the command returns. Split long jobs into steps that each finish in time.
- 4 CPU cores, **4 GB of memory**, a few GB of free disk.
- Moving files to the cloud workspace is slow: one file of up to about 25 MB per call works; several large files in one call time out. **Render on the Mac; move only small files** (word timings, frame strips, finished shorts).
- `ffmpeg` (with libass) and Python 3 with Pillow and numpy are installed on Amitai's Mac. If the Mac you are on has no ffmpeg (Nadav's machine, episode 7), don't install one for a trim — passthrough with `avconvert`.
- Writing a changed file to the Mac under the same name can leave the old version in place; give revised files a new name (`_v2`) and check the content on the Mac.

## Codex CLI (covers)
Facts only; the Mac-first / box-fallback policy lives in `investing-bros-brand`
(prompts → Codex backend, `scripts/codex_runner.py`).
- **Amitai's Mac:** machine `566a74b2-614d-458f-be63-660743243124`. Reach it with
  ListMachines, then Shell with that machineId. Binary:
  `~/.nvm/versions/node/v22.23.1/bin/codex` (npm under nvm). Workdirs under
  `/Users/amitairuskin/Pictures/investing-bros/episode-<N>/`. CopyToBox/CopyFromBox
  need absolute `/Users/amitairuskin/...` paths; `~` is not expanded.
- **Producer box:** `npm i -g @openai/codex` (0.167.2 as of episode 11), binary
  `codex` on PATH (`~/.local/bin/codex`). Workdirs under
  `/workspace/investing-bros/episode-<N>/art/`.
- **Login:** Amitai's ChatGPT plan, never an API key (`env -u OPENAI_API_KEY`).
  Device-code auth is `codex login --device-auth`. If either host needs a login, a
  device code, or re-auth, stop, show Amitai the URL and one-time code, and wait.
  A first device code can fail; use a fresh one. Never copy `~/.codex/auth.json`
  between machines and never print tokens.

## Claude Code on Amitai's Mac (desktop app, crypto course lesson 1, 2026-10-26)
Different from the device shell above: Claude Code in the Claude desktop app runs commands on the Mac itself.
- 10 cores, 16 GB. No 3-minute limit, but run long jobs (Whisper, a full render) as background commands and wait for them to finish.
- Installed: `ffmpeg`, Node 22 + `npx`, Homebrew, a Playwright headless Chrome in `~/Library/Caches/ms-playwright/` (found by `render_short.py` / `render_lesson.py`), and the Homebrew `whisper` command (openai-whisper). `large-v3-turbo` runs fine here: six lesson takes, 3.5 minutes of speech, took about 10 minutes.
- The system `python3` (3.9) has no numpy, fontTools or whisper module, and the repo's tests need a newer Python: make a venv with `/opt/homebrew/bin/python3.14 -m venv …` and `pip install pytest pyyaml fonttools pillow numpy`.
- **Google Drive for desktop is blocked:** `~/Library/CloudStorage/GoogleDrive-…` returns "Operation not permitted" (macOS privacy), even with the sandbox off. Don't copy files into Drive that way.
- **Uploading to Drive from here:** the Drive connector's `create_file` takes the file content inline, so it is fine for text (JSON, SRT, a script) but not for video. Claude in Chrome's `file_upload` takes under 10 MB per call. For video, `drive.sh put` works once the optional rclone remote `show` exists (`brew install rclone`, then `rclone config create show drive scope=drive` and Amitai signs in as the bot in the page it opens; on 2026-10-26 the sign-in didn't complete and was left for later). Without it, stage the files in the Drive layout in a local folder and ask Amitai to drag them in.
- Files sent to Amitai's phone (`SendUserFile`) must be under 30 MB; bigger ones show only in the desktop app. Send a 720p copy (`-b:v 1000k`, about 26 MB for 3:16) to watch on the phone.

## Whisper on the Mac
- Models already on disk: `~/.cache/whisper/` (`base.pt`, `small.pt`, `large-v3-turbo.pt`) and OpenWhispr's `ggml-base.bin`. Ask Amitai to connect the folder.
- `large-v3-turbo` doesn't fit in 4 GB; `small` does (~30 s for 75 s of audio).
- Install recipe (the newer aarch64 torch wheels pull ~2 GB of CUDA libraries and fill the disk):
  ```
  export TMPDIR=/var/tmp
  pip3 install -q --no-deps --target /var/tmp/py "torch==2.5.1" filelock fsspec networkx sympy==1.13.1 mpmath jinja2 MarkupSafe typing_extensions
  pip3 install -q --no-deps --target /var/tmp/py openai-whisper tiktoken regex requests more-itertools tqdm numba llvmlite
  PYTHONPATH=/var/tmp/py python3 …
  ```
- Transcribe only the picked clip windows (with `word_timestamps=True`), never the whole episode — the Drive transcript already covers that.

## Whisper in the cloud workspace (episode 8)
- `pip install --break-system-packages torch==2.5.1 openai-whisper` works (about 5 min, ~3 GB).
  The model download does not: `openaipublic.azureedge.net` and Hugging Face are blocked.
- Bring the model from the Mac instead: Amitai runs
  `cp ~/.cache/whisper/small.pt ~/Downloads/`; stage it in **100 MB pieces** (`split -b 100M`
  in the device shell, one piece per `device_stage_files` call: a 245 MB piece timed out,
  the per-file cap is 400 MB), then `cat` the pieces into `~/.cache/whisper/small.pt` and
  check `sha256sum` = `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794`.
- A 50 s window transcribes in about a minute on 2 cores with `small`.

## Browsers for downloads (episode 8)
- The Claude app's built-in browser pane isn't signed in to Google and doesn't save
  downloads; Claude in Chrome can be offline. A Drive raw master the Drive download can't
  fetch, or a Riverside track the dashboard pull did not get: ask Amitai to download it in
  his Chrome into `~/Downloads`.
- With `~/Downloads` connected, the device shell sees it at `~/mnt/Downloads` (Linux
  sandbox, ffmpeg available): cut the needed window there and stage only that (a 65 s
  1080p window, re-encoded CRF 12, is ~125 MB and stages in one call).

## Telegram from the cloud workspace (episode 8)
- The bot settings (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) are in `telegram.env` in
  Amitai's `~/Downloads`. Stage it with `device_stage_files` just before a post, pass it to
  `send_telegram.py --env`, then delete the staged copy. Never print it.
- When the Mac is asleep or the Claude app is closed the bridge is down and nothing can be
  posted: hand Amitai the file and the exact caption to forward himself.

## Fonts
- The skills need static Heebo weights (`brand.py fonts`). If `github.com/google/fonts` isn't reachable: `npm pack @fontsource-variable/heebo`, then instance the Hebrew and Latin `*-wght-normal.woff2` subsets at 600/800/900 with fontTools and merge each pair (`fontTools.merge`), naming the families `Heebo SemiBold` / `Heebo ExtraBold` / `Heebo Black`.

## HyperFrames in the cloud workspace
- Use the preinstalled headless shell: `export PRODUCER_HEADLESS_SHELL_PATH=$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell | head -1)`. `doctor` complains about Docker; it isn't needed.
- A 48 s render takes about 3 minutes on 2 cores; run it in the background and poll its log.
- The input video needs a keyframe every second (`-g 24 -keyint_min 24`), or seeks freeze frames.

## Delivering files
- Chat attachments are capped at **30 MB**: send a re-encoded review copy (`-crf 21`) and keep the master.
- Telegram bot uploads are capped at **50 MB**.
- **Bot transfer tools (verified 2026-10-22):** `UploadFile` (box → Google
  Drive) and `CopyFromBox` (box → Amitai's Mac) each cap a single file at
  **100 MB**. Uploading a large video through Drive's web UI in the box browser
  stalls on the box's slow connection.
- **Working large-video handoff:** record the original sha256, split into
  10–20 MB pieces (for example, `split -b 15M FILE FILE.part-`), then
  `CopyFromBox` each piece to the Mac's `~/Downloads` one at a time, retrying a
  failed piece. On the Mac, run `cat FILE.part-* > FILE`, then compare
  `shasum -a 256 FILE` with the original checksum. This successfully delivered
  final segment videos; Amitai can drag the verified reassembled file from
  `~/Downloads` to Drive.
