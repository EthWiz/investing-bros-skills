---
name: investing-bros-show
description: >-
  Shared facts and house rules for the Investing Bros / אחים להשקעות podcast:
  hosts, episode format, naming, the Drive folder tree, Hebrew spellings, who
  owns WhatsApp, accounts, approved WhatsApp and Telegram destinations, working
  rules and environment limits. Load this alongside any other investing-bros-*
  skill, or whenever a task touches the show.
---
# Investing Bros show conventions

Single source of truth for shared show facts and operating rules. If another skill disagrees on those facts or rules, this file wins. Visual identity and artwork specifications belong to `investing-bros-brand`.

## The show
- **Name:** Investing Bros, Hebrew **אחים להשקעות**.
- **Hosts:** Amitai Raskin and Nadav Raskin. Amitai is the person you take instructions and approvals from.
- **Episode format:** ~10 min news, ~20 min deep dive, ~5 min each for one investment idea per host.
- **News taste:** All-In-style tech (model releases, launches, big raises/IPOs, hacks, infra, fintech/platform moves) over macro/rates/oil/price action, unless Amitai asks for macro.
- **Podcast host:** [RedCircle](https://app.redcircle.com). Not RSS.com unless Amitai says the host changed. RedCircle feeds Spotify automatically: [the show on Spotify](https://open.spotify.com/show/4fREAemgQDMWIUK58N5Jjk). Video goes to YouTube only; uploading video to Spotify would cut that episode off from RedCircle (see `investing-bros-episode-upload`).
- **Spotify, as of 2026-10-18:** the show's author line reads `אמתי ונדב רסקין`, matching the corrected spelling. Episode 7's title has an en dash; changing that public metadata waits for Amitai's OK.

## Hard rules (every skill)
1. **Never invent** numbers, quotes, events or promo copy. Factual claims need a source URL.
2. **Episode number = the number Amitai states.** Never auto-increment from old folders, Drive names or workspace paths.
3. **Nothing goes public without Amitai's explicit OK** — RedCircle stays a draft; WhatsApp and Telegram messages go only to the approved destinations below, and only when Amitai asks in chat for that post.
4. **Never commit, echo or paste secrets.** Refer to them by env-var name.
5. **Don't delete** WhatsApp messages, old drafts or the `brief/` archive without explicit OK.
6. **Ask, don't guess** on ambiguous cuts, titles or numbers.

## Working rules (every skill)
1. **Use the scripts.** Run the skill's scripts from `scripts/`. Don't write your own render, caption, animation, download or upload code. If a script lacks a feature or has a bug, stop, tell Amitai what's missing, and propose the change as a PR to this repo. A one-time workaround is allowed only with Amitai's OK, and it must be listed in the hand-back.
2. **The hand-back lists what ran:** the scripts run, any generated command patched by hand and why, and the PR that will fix it.
3. **End every run by asking what it taught.** A mistake that could happen again becomes a script check with a test if a script can catch it, otherwise one line in the skill that owns the step, or a fact in this skill. Send it as a small PR the same day. Something you couldn't verify or fix becomes a GitHub issue on the repo. Nothing learned means no PR. Details in the repo's `AGENTS.md` → Improving the skills.
4. **Know the environment before working around it.** Limits of the Drive connector, Amitai's Mac, the network and the tools are in [references/environment.md](references/environment.md).

## Naming
| Thing | Pattern | Example |
|---|---|---|
| Drive episode folder | `פרק N — נושא` (em dash `—`) | `פרק 4 — ניו קלאודס` |
| Episode title (RedCircle, YouTube) | `פרק N - <title>` (plain hyphen `-`, a space each side) | `פרק 4 - ניו קלאודס: מי ינצח במלחמת העננים?` |
| Edited audio | `הקלטה-ערוכה-פרק-N.m4a` | `הקלטה-ערוכה-פרק-4.m4a` |
| Title options (episode root) | `כותרות-פרק-N.txt` | `כותרות-פרק-8.txt` |
| Description (episode root) | `תיאור-פרק-N.txt` | `תיאור-פרק-8.txt` |
| Short (in `shorts/`) | `שורט-NN-<נושא>.mp4` | `שורט-01-סוויפט.mp4` |
| Short cover (in `shorts/`) | `שורט-NN-<נושא>-cover.jpg` (1080×1920) | `שורט-01-סוויפט-cover.jpg` |
| Short captions (in `shorts/`) | `שורט-NN-<נושא>.srt` | `שורט-01-סוויפט.srt` |
| Short YouTube notes (in `shorts/`) | `youtube-שורט-NN.md` | `youtube-שורט-01.md` |
| Mid-form (in `mid-form/`) | `מיד-פורם-NN-<נושא>.mp4` + `.txt` (title, description) | `מיד-פורם-01-זהב.mp4` |
| Video episode (in `video/`) | `פרק-N-וידאו.mp4` + `תיאור-פרק-N-youtube.txt` | `פרק-8-וידאו.mp4` |

**Finding an existing episode folder:** match on the `פרק N` prefix (followed by a space or dash), not the full name — the dash and topic may differ from what you would type. If one matches, reuse it. Never create a second folder for the same N.

## Hebrew
- Write natural, high-quality Hebrew — not literal machine tone.
- Brand spellings: **ספייסאקס** (not ספייסקס). Add new ones here when Amitai corrects a spelling.
- Chapters are **time first, zero-padded**: `01:05 נושא` (`MM:SS`; `HH:MM:SS` past an hour). Spotify only turns timestamps into chapters in that form, 30 s apart; YouTube accepts it too.
- Disclaimer line: `אין כאן המלצת השקעה. רק שיחה.`
- **No em dash `—` and no en dash `–` in anything public**: titles, descriptions, chapters, captions, posts (decided 2026-10-15: both read as AI-written). The only dash is a plain hyphen `-`, e.g. `פרק N - `. The em dash stays only in private Drive folder names. Titles: concise, question-led, no clickbait; see `investing-bros-title-description`.
- Host names on screen: **נדב רסקין**, **אמתי רסקין**. Latest user correction (2026-10-19): spell **אמתי** everywhere. Exact artwork credit: **עם אמתי ונדב רסקין**.
- **Fact-check every claim before it goes into a title or description** (episode 7: "all gold ever mined fits in one Olympic pool" is wrong — it is ~4 pools).
- Hebrew pasted into RedCircle needs the RTL + `?` marks — see `investing-bros-episode-upload`.
- **Every public Hebrew line starts with a Hebrew word**, including chapter labels after the timestamp (`01:05 מרוץ המודלים: OpenAI מול אנתרופיק`). A line that starts with English or a number flips left-to-right and scrambles its timestamp and numbers (episode 5 on YouTube). Checked by `check_copy.py` in `investing-bros-title-description`.

## Drive tree
Show root `אחים להשקעות` already exists. Never create a second root.

Shared resource folder: [Brand Resources](https://drive.google.com/drive/folders/1IRRwUpB3n1SD3-Ltvj3bEiMQS-UfFxyO), formerly `Media Resources` (same folder ID, verified 2026-10-19). Reuse this folder and preserve existing files. Legacy asset paths below record historical filenames; inspect the folder and its archives before resolving an asset, rather than assuming the old path still exists.

```
אחים להשקעות/                      show root (exists)
  פרק N — נושא/                    one per episode — created by prep, reused by everyone after
    הקלטה-ערוכה-פרק-N.m4a   edited, upload-ready audio                     ← post-production
    כותרות-פרק-N.txt        five titles + "בחירה סופית:" (plain UTF-8 text) ← title-description
    תיאור-פרק-N.txt         description + disclaimer + chapters (plain text) ← title-description
    brief/       pre-recording docs (prep archive; keep)                     ← episode-preparation
    extras/      raw audio/video, parts, host tracks, transcripts, edit.json, RTL copies, temp files
    video/       full video episode + its YouTube description, when there is one ← video
    shorts/      every short: .mp4 + -cover.jpg + .srt + youtube-שורט-NN.md      ← shorts
    mid-form/    5–10 min highlights: .mp4 + .txt each, when made                  ← shorts
    promo/       promo teaser, cold opens, thumbnail                              ← video, brand
```

The episode root holds **only** the three files above plus these subfolders. Anything else goes in `extras/` (`תוספות` is accepted if a folder already uses that name). A subfolder is created only when it gets a file.

The title and description are plain `.txt` files (decided 2026-10-18), not Google Docs: what's in the file is exactly what gets pasted into RedCircle and YouTube. Create them with conversion to Google Docs **off**. Episodes 1–7 used Docs named `אפשרויות כותרת` / `תיאור הפרק`; leave those as they are.

**Status = the folder.** Each skill's *Done when* lists the files it leaves in this tree. To see where an episode stands, list the folder; don't keep a separate tracker.

## Brand (video and graphics)
- **Design owner:** load `investing-bros-brand` for all artwork and visual decisions. It owns the Financial Journal rules, palette, typography, templates, selected references and quality checks. Do not copy or redefine those rules here.
- **Existing deployment:** `אחים להשקעות/Media Resources/אחים-להשקעות-cover-1400.jpg` and legacy `brand.py` remain in use until a reviewed renderer/asset migration. New brand documentation alone does not update Drive, channel artwork or existing videos.
- **Production fonts:** static Heebo weights remain available through the existing `brand.py fonts` workflow. See the brand skill for how they relate to the generated reference lettering.
- **Intro clip:** `אחים להשקעות/Media Resources/אינטרו - אחים להשקעות.mp4` — 6 s, stereo music; ends with `עם אמתי ונדב רסקין`. Square and 16:9 versions sit beside it (`investing-bros-intro-square_1.mp4`, `investing-bros-intro-16x9_1.mp4`). Since episode 7, Amitai's Grok Imagine intro (6 s) replaces the old intro — use it as-is, immediately after the cold open. Video order: cold open (~22 s) + intro, then the episode. Never use watermarked music (AudioJungle previews and the like). Keep the tone serious — no "get rich quick" vibe. Keep the correct **אמתי** spelling when adapting artwork or credits.
- **Tone:** professional and calm. No "get rich quick", no money rain, no loud colours.
- **Loudness:** episode −16 LUFS, social clips −14 LUFS, true peak ≤ −1.5 dBTP. A cold-open music mix uses true peak −1 dBTP (`investing-bros-video` → Cold-open music bed). The two hosts within ~3 dB of each other.
- **YouTube thumbnails:** use the Financial Journal brand and the proposed widescreen composition; `investing-bros-title-description` supplies the approved headline and `investing-bros-brand` creates/reviews the artwork. Recompose square art rather than stretching it.
- **Recording layout:** Episodes are recorded in **Riverside**. Riverside side-by-side export, 1920×1080, 24 fps, often **mono** AAC audio: Amitai in the left half, Nadav in the right half (confirmed on episode 7). Check the first frame each episode — seats can change.
- **Host levels in the raw recording:** on episode 7 Amitai measured about 6.5 dB quieter than Nadav; give his pieces about +6 dB so both land within ~2 dB.

## Roles and accounts
| Role / account | Who / what | Notes |
|---|---|---|
| Approver | Amitai | Episode number, cuts, final title, publish, new destinations |
| Video producer | ליאורה | Shorts, cold opens, the intro, mid-form and the video episode. Nadav approves each video change before a rebuild or upload; anything public still needs Amitai's OK |
| WhatsApp owner | **Amitai Personal** (agent that owns WhatsApp Web) | No other agent opens WhatsApp Web or scans a QR. Agents without access to Amitai Personal: give Amitai the exact group, text and links and ask him (or whoever owns that account) to send. |
| RedCircle login | `ami.ruskin@gmail.com` | Password in env `REDCIRCLE_PASSWORD`. If missing, use the live page's own password form — never ask Amitai to paste it in chat. |
| Drive large-file uploads | browser, signed in as `ami.grokbot@gmail.com` | Use when a connector can't carry the file. Newer connector downloads are 100 MB ([references/environment.md](references/environment.md)); base64 uploads above a few MB are still impractical. Connectors are fine for Docs, folders and moves. Claude in Chrome's file upload takes at most 10 MB per call: for bigger video, upload a 2-pass sub-10 MB review copy and tell Amitai, or ask him to drag the full file in. |
| Show cover art | `Media Resources/אחים-להשקעות-cover-1400.jpg` (see Brand) | Used for audiograms, logo cutting and WhatsApp artwork |
| Local working dir | `/workspace/investing-bros/episode-N/` | Or `episode-latest/` until N is confirmed. Agents on another machine: any scratch dir, same sub-layout. |

## WhatsApp
**Every** message sent to a show group ends with the line `sent by Grokbot` (a fixed show tag, whichever agent prepared it).

Hand-off to the WhatsApp owner always includes: exact group name, exact message text (with the tag), link(s), and one line of context. Then wait for a yes/no confirmation and report it.

Approved destinations — don't add new ones without Amitai's OK:
| Id | Group | Use |
|---|---|---|
| `achim` | `אחים להשקעות` | Prep docs, review-ready pings, draft links; live ping only when Amitai asks (review drafts/cold opens/intros go to Telegram instead) |
| `raskin-empire` | `רסקין אימפריה` (also seen as `רסקין אמפריה`) | Family promo of the published episode |

Prefer a **Doc or folder link** over pasting long text — long messages split badly in WhatsApp. Set Docs to anyone-with-link Viewer when the brothers need access.

## Telegram
| Id | Group | Chat ID | Sent by | Use |
|---|---|---|---|---|
| `tg-achim` | `אחים להשקעות` | `-5592316645` | bot `@amitai_ai_bot` | Internal review of shorts and drafts |

- **Secrets:** the bot token lives only in an env file, read as `TELEGRAM_BOT_TOKEN` (with `TELEGRAM_CHAT_ID`). Never in chat, project instructions, project docs or this repo.
- **Each post needs Amitai's OK in chat**, like WhatsApp. Don't add destinations without his OK.
- **Limits:** another program reads this bot's updates, so agents can't see replies or find chat IDs via `getUpdates` — ask Amitai to relay replies. The bot is a plain member: it can delete only its own posts. Bot uploads are capped at 50 MB (a 48 s HyperFrames master is about 40 MB).
- Cold opens, intros and drafts for review are shared **only** in Telegram group `אחים להשקעות` — not WhatsApp. Post drafts with the title only.
- Bot API `sendVideo`: always pass `width` and `height` (otherwise the video displays distorted). `send_telegram.py` in `investing-bros-shorts` already does. Over 50 MB: compress first (e.g. 720p ~700 kbps).
- To see group messages/media a bot needs privacy mode off (@BotFather → /setprivacy → Disable).

## Episode flow
| # | Stage | Skill | Who approves |
|---|---|---|---|
| 0 | Before recording | `investing-bros-episode-preparation` | — |
| 1 | Audio edit | `investing-bros-post-production` | Nadav (cuts) |
| 2 | Titles, description, artwork brief | `investing-bros-title-description` | Amitai (title) |
| 3 | Cold opens + intro + video episode, promo teaser | `investing-bros-video` | Nadav |
| 4 | Shorts, mid-form highlights | `investing-bros-shorts` | Nadav |
| 5 | Review ping, uploads, publish, Spotify check, WhatsApp | `investing-bros-episode-upload` | Amitai (publish) |

`investing-bros-brand` serves stages 2–4 as the shared design and artwork capability.

Stages 2–4 only need the edit (transcript + `edit.json`), so they can run in parallel, by different agents. Every run ends with a learnings PR (Working rules).

## Never
- Put a token, password or cookie in chat, project instructions, project docs or this repo — refer to it by env-var name.
- Sign in to Amitai's Google account from a browser: Advanced Protection blocks automated sign-in (see [references/environment.md](references/environment.md)).
- Write your own code where a skill's script exists, or work around a missing feature without saying so (Working rules).
