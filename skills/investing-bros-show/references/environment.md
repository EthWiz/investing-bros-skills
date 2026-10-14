# Environment: what works where

Read this before working around anything. Every line here cost an agent time to find out (episode 7 shorts, 2026-10-14). If something here is wrong or new, fix it in a PR.

## Getting raw video and other big files
- **Drive connector:** downloads Docs and files up to **100 MB** on the newer connector (episode 7). A raw episode (1–2 GB) still cannot come through it. The shorts run also hit an older **10 MB** cap — if a download between 10 and 100 MB is rejected, use the Mac or `drive.sh` (Drive API) path instead of retrying the connector. Browser upload (Claude in Chrome) is a separate **10 MB** per call; that limit is unchanged (show conventions → accounts).
- **Riverside** login from an agent box hits a captcha. Workaround: the host downloads the files on his Mac and uploads them to Drive. Nadav drags full episodes to Drive himself.
- **Local-exec transfer** (CopyToBox/CopyFromBox) and a Drive upload of a big file are capped at **100 MB**. Split anything larger into 50 MB parts (`split -b 50M`), rejoin with `cat`, and check the sha256 of the original against the rejoined file.
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

## Fonts
- The skills need static Heebo weights (`brand.py fonts`). If `github.com/google/fonts` isn't reachable: `npm pack @fontsource-variable/heebo`, then instance the Hebrew and Latin `*-wght-normal.woff2` subsets at 600/800/900 with fontTools and merge each pair (`fontTools.merge`), naming the families `Heebo SemiBold` / `Heebo ExtraBold` / `Heebo Black`.

## HyperFrames in the cloud workspace
- Use the preinstalled headless shell: `export PRODUCER_HEADLESS_SHELL_PATH=$(ls -d /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell | head -1)`. `doctor` complains about Docker; it isn't needed.
- A 48 s render takes about 3 minutes on 2 cores; run it in the background and poll its log.
- The input video needs a keyframe every second (`-g 24 -keyint_min 24`), or seeks freeze frames.

## Delivering files
- Chat attachments are capped at **30 MB**: send a re-encoded review copy (`-crf 21`) and keep the master.
- Telegram bot uploads are capped at **50 MB**.
