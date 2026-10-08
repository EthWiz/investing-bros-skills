---
name: investing-bros-show
description: >-
  Shared facts and house rules for the Investing Bros / אחים להשקעות podcast:
  hosts, episode format, naming, the Drive folder tree, Hebrew spellings, who
  owns WhatsApp, accounts and approved WhatsApp groups. Load this alongside any
  other investing-bros-* skill, or whenever a task touches the show.
---
# Investing Bros show conventions

Single source of truth for everything the other `investing-bros-*` skills share. If a rule here and a rule in another skill disagree, this file wins — fix the other skill.

## The show
- **Name:** Investing Bros, Hebrew **אחים להשקעות**.
- **Hosts:** Amitai Raskin and Nadav Raskin. Amitai is the person you take instructions and approvals from.
- **Episode format:** ~10 min news, ~20 min deep dive, ~5 min each for one investment idea per host.
- **News taste:** All-In-style tech (model releases, launches, big raises/IPOs, hacks, infra, fintech/platform moves) over macro/rates/oil/price action, unless Amitai asks for macro.
- **Podcast host:** [RedCircle](https://app.redcircle.com). Not RSS.com unless Amitai says the host changed.

## Hard rules (every skill)
1. **Never invent** numbers, quotes, events or promo copy. Factual claims need a source URL.
2. **Episode number = the number Amitai states.** Never auto-increment from old folders, Drive names or workspace paths.
3. **Nothing goes public without Amitai's explicit OK** — RedCircle stays a draft, WhatsApp goes only to approved groups, promo clips are not posted anywhere by the agent.
4. **Never commit, echo or paste secrets.** Refer to them by env-var name.
5. **Don't delete** WhatsApp messages, old drafts or the `brief/` archive without explicit OK.
6. **Ask, don't guess** on ambiguous cuts, titles or numbers.

## Naming
| Thing | Pattern | Example |
|---|---|---|
| Drive episode folder | `פרק N — נושא` (em dash `—`) | `פרק 4 — ניו קלאודס` |
| Episode title (RedCircle) | `פרק N – <title>` (en dash `–`) | `פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?` |
| Edited audio | `הקלטה-ערוכה-פרק-N.m4a` | `הקלטה-ערוכה-פרק-4.m4a` |

**Finding an existing episode folder:** match on the `פרק N` prefix (followed by a space or dash), not the full name — the dash and topic may differ from what you would type. If one matches, reuse it. Never create a second folder for the same N.

## Hebrew
- Write natural, high-quality Hebrew — not literal machine tone.
- Brand spellings: **ספייסאקס** (not ספייסקס). Add new ones here when Amitai corrects a spelling.
- Chapters are **time first**: `1:05 נושא`.
- Disclaimer line: `אין כאן המלצת השקעה. רק שיחה.`
- Host names on screen: **נדב רסקין**, **אמיתי רסקין**. The intro clip spells **אמתי** — open question for Amitai; use אמיתי until he decides, then record the answer here.
- Hebrew pasted into RedCircle needs the RTL + `?` marks — see `investing-bros-episode-upload`.

## Drive tree
Show root `אחים להשקעות` already exists. Never create a second root.

```
אחים להשקעות/                      show root (exists)
  פרק N — נושא/                    one per episode — created by prep, reused by everyone after
    הקלטה-ערוכה-פרק-N.m4a          edited, upload-ready audio      ← post-production
    תיאור הפרק          (Google Doc) description + disclaimer + chapters ← post-production
    אפשרויות כותרת      (Google Doc) five titles + "בחירה סופית:"    ← post-production
    brief/              pre-recording docs (prep archive; keep)   ← episode-preparation
    extras/             raw audio, parts, transcripts, segments.json, RTL .txt copies, temp files ← post-production
    promo/              shorts, teaser (and episode art, once defined) ← shorts, teaser
    video/              full video episode, only when there is one (cold open + intro + episode) ← post-production
```

The episode root holds **only** the three files above plus the three subfolders. Anything else goes in `extras/` (or `promo/` for promo material). `תוספות` is an accepted alternative name for `extras/` if a folder already uses it.

## Brand (video and graphics)
- **Palette:** black, emerald, white — from the dark show cover (`אחים להשקעות - קאבר מקצועי 3 - כהה.jpg`). On-screen emerald `#1FBF7A` (the cover's own green is too dark over video).
- **Logo:** the `אחים להשקעות` wordmark cut from that cover (`brand.py logo` in shorts/teaser). Don't redraw or recolour it.
- **Font:** Heebo, as static weights (SemiBold / ExtraBold / Black via `brand.py fonts`) — libass draws the variable font thin.
- **Intro clip:** `אחים להשקעות-Intro.mp4` — 6 s, 960×960, 24 fps, stereo music; ends with `עם אמתי ונדב רסקין`. In 16:9 it is padded on black. Drive location not recorded yet — ask Amitai, then write it here.
- **Loudness:** episode −16 LUFS, social clips −14 LUFS, true peak ≤ −1.5 dBTP. The two hosts within ~3 dB of each other.
- **YouTube thumbnails** have their own layout — dark cinematic scene, one focal object, one accent colour chosen per episode — see `investing-bros-cover-art`.
- **Recording layout:** Riverside side-by-side export, 1920×1080, 24 fps: Amitai in the left half, Nadav in the right half (as of episode 6). Check the first frame each episode — seats can change.

## Roles and accounts
| Role / account | Who / what | Notes |
|---|---|---|
| Approver | Amitai | Episode number, cuts, final title, publish, new destinations |
| WhatsApp owner | **Amitai Personal** (agent that owns WhatsApp Web) | No other agent opens WhatsApp Web or scans a QR. Agents without access to Amitai Personal: give Amitai the exact group, text and links and ask him (or whoever owns that account) to send. |
| RedCircle login | `ami.ruskin@gmail.com` | Password in env `REDCIRCLE_PASSWORD`. If missing, use the live page's own password form — never ask Amitai to paste it in chat. |
| Drive large-file uploads | browser, signed in as `ami.grokbot@gmail.com` | Use when a connector can't carry the file (base64 limits — impractical above a few MB). Connectors are fine for Docs, folders and moves. Claude in Chrome's file upload takes at most 10 MB per call: for bigger video, upload a 2-pass sub-10 MB review copy and tell Amitai, or ask him to drag the full file in. |
| Show cover art | **Location not recorded yet** — ask Amitai, then write the path here | Used for audiograms and WhatsApp artwork |
| Local working dir | `/workspace/investing-bros/episode-N/` | Or `episode-latest/` until N is confirmed. Agents on another machine: any scratch dir, same sub-layout. |

## WhatsApp
**Every** message sent to a show group ends with the line `sent by Grokbot` (a fixed show tag, whichever agent prepared it).

Hand-off to the WhatsApp owner always includes: exact group name, exact message text (with the tag), link(s), and one line of context. Then wait for a yes/no confirmation and report it.

Approved destinations — don't add new ones without Amitai's OK:
| Id | Group | Use |
|---|---|---|
| `achim` | `אחים להשקעות` | Prep docs, review-ready pings, draft links; live ping only when Amitai asks |
| `raskin-empire` | `רסקין אימפריה` (also seen as `רסקין אמפריה`) | Family promo of the published episode |

Prefer a **Doc or folder link** over pasting long text — long messages split badly in WhatsApp. Set Docs to anyone-with-link Viewer when the brothers need access.

## Pipeline
| Stage | Skill | Hands off |
|---|---|---|
| Before recording | `investing-bros-episode-preparation` | `brief/` docs + WhatsApp share |
| Recording lands | `investing-bros-post-production` | Edited audio + 2 Docs + review ping |
| Promo (optional, after edit) | `investing-bros-shorts`, `investing-bros-teaser`, `investing-bros-cover-art` | `promo/` files for review |
| Approved | `investing-bros-episode-upload` | RedCircle **draft** link |
| Published | `investing-bros-share-new-episode` | WhatsApp sends confirmed |
