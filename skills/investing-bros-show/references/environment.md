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
3. **Riverside:** a shared `riverside.com/shared/exported-clip/...` link has one **Download** button
   and no quality picker. Riverside's "1080p" cloud download was really 720p on episode 8.
   A **recording** share link (`/dashboard/studios/…/recordings/<id>?share-token=…`) lists each
   host's track with raw / **aligned** video and audio. It opens without a sign-in, but the
   Claude app's built-in browser pane doesn't save downloads (episode 8): ask Amitai to click
   Download → Aligned video for each host in his own Chrome, into `~/Downloads`.
4. **Always check what you got** and keep the highest-quality copy:
   `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate -show_entries format=duration -of compact FILE`.
   If Riverside gives 720p, use Nadav's own Drive master (episode 8: `פרק 8 לא ערוך.mp4`, 1920×1080, 24 fps).
   Say in the hand-back when only 720p exists (it gets upscaled).
5. Downloads land in `/home/box/Downloads`; move them into the episode working folder (`$EP`)
   and note which source and resolution you used.

- **Riverside** login from an agent box hits a captcha. Workaround: the host downloads the files on his Mac and uploads them to Drive. Nadav drags full episodes to Drive himself.
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
  downloads; Claude in Chrome can be offline. A Drive raw master or a Riverside track that
  the connector can't fetch: ask Amitai to download it in his Chrome into `~/Downloads`.
- With `~/Downloads` connected, the device shell sees it at `~/mnt/Downloads` (Linux
  sandbox, ffmpeg available): cut the needed window there and stage only that (a 65 s
  1080p window, re-encoded CRF 12, is ~125 MB and stages in one call).

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
