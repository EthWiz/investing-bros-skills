---
name: investing-bros-episode-pipeline
description: >-
  Run an Investing Bros / אחים להשקעות episode from the finished recording to
  live on RedCircle, Spotify and YouTube, stage by stage: audio edit, titles
  and description .txt files, cold opens + intro + video episode, shorts with
  covers, mid-form highlights, thumbnail, Drive review, uploads, publish and
  platform check. Tracks every stage, its approver and its links in
  pipeline.json so any agent can resume. Use when Amitai says "the recording
  is in", "do the whole episode", "run episode N", "כל הפרק", "תריץ את הפרק",
  "מה הסטטוס של פרק N", or asks what is left on an episode.
---
# Investing Bros episode pipeline

Load `investing-bros-show` first. This skill is the order of work and the gates between stages. The work itself is done by the skill named in each stage, with that skill's scripts, checks and hand-back. Don't redo a stage's steps here.

## When to use
- The recording is in and Amitai wants the episode taken through (or a part of it).
- Picking up an episode another agent or session started: run `status` first.
- Amitai asks what's left on episode N.

Before recording is `investing-bros-episode-preparation`, outside this pipeline.

## Inputs
- Episode number N **as Amitai states it**.
- Working dir `$EP` (`/workspace/investing-bros/episode-N/`, show conventions → Roles and accounts).
- The episode's Drive folder (`פרק N` prefix match). If `extras/pipeline.json` is there, download it into `$EP` and continue from it instead of starting over.
- Which optional stages Amitai wants: video episode, mid-form, thumbnail, WhatsApp share. Ask once at the start if he didn't say. Shorts are always made.

## The stages

```
0 intake ─► 1 edit ─┬─► 2 copy ──► 6 thumbnail ─┐
                    ├─► 3 video (cold opens + intro + episode)
                    ├─► 4 shorts (+ covers) ────┼─► 7 review ─► 8 upload ─► 9 publish ─► 10 share ─► 11 learnings
                    └─► 5 mid-form highlights ──┘   (drafts)   (Amitai OK) (Spotify check)
```

| # | Stage | Skill | Done when | Approver |
|---|---|---|---|---|
| 0 | `intake` | `investing-bros-post-production` 1–2 | N confirmed; parts in `$EP/parts/`; host tracks in `extras/` if shorts use them | — |
| 1 | `edit` | `investing-bros-post-production` 3–5 | Leveled, transcribed; start/end + cut list approved; edited audio at −16 LUFS, hosts within 3 dB; `edit.json` | Nadav (cut list) |
| 2 | `copy` | `investing-bros-title-description` | `titles.txt` + `description.txt` pass `check_copy.py --spotify`; Amitai picked the title; both files in the episode root | Amitai (title) |
| 3 | `video` *(optional)* | `investing-bros-teaser` (cold opens), `investing-bros-post-production` 8 | Cold open(s) → intro → episode, joins checked; in `video/` with its YouTube description | Nadav |
| 4 | `shorts` | `investing-bros-shorts` (+ `investing-bros-hyperframes`) | ~5 shorts, each `.mp4` + `-cover.jpg` + `.srt` + `youtube-שורט-NN.md`, in `shorts/` | Nadav |
| 5 | `midform` *(optional)* | `investing-bros-shorts` → Mid-form | 1–3 highlights of 5–10 min, each with title + description, in `mid-form/` | Nadav |
| 6 | `thumbnail` *(optional)* | `investing-bros-cover-art` | Prompt + headline handed over; the finished image in `promo/` | Amitai |
| 7 | `review` | `investing-bros-post-production` 9–10 | Drive tree exactly as in show conventions; review ping sent | Amitai (OK to upload) |
| 8 | `upload` | `investing-bros-episode-upload` | RedCircle **draft**; YouTube episode, shorts, mid-form uploaded **private** | — |
| 9 | `publish` | `investing-bros-episode-upload` → Publish and check | Live only after Amitai's OK in chat; the Spotify, RedCircle and YouTube checks pass | **Amitai only** |
| 10 | `share` *(optional)* | `investing-bros-share-new-episode` | WhatsApp sends confirmed | Amitai |
| 11 | `learnings` | `AGENTS.md` → Editing the skills | PR with what this run taught | — |

Stages 2–5 can run in parallel once `edit` is done; they all read the raw-timeline transcript and `edit.json`. `review` waits for every stage before it that isn't skipped.

## Steps

### 1. Start or resume the tracker
```bash
python3 scripts/pipeline.py init "$EP" --episode N [--no-video] [--no-midform] [--no-thumbnail] [--no-share]
python3 scripts/pipeline.py status "$EP"      # resuming: shows what's done and what's next
```
`init` refuses to overwrite an existing `pipeline.json`.

### 2. Work each stage with its skill
For the next stage `status` prints: load its skill, do the work, then record it:
```bash
python3 scripts/pipeline.py set "$EP" edit doing
python3 scripts/pipeline.py set "$EP" edit review --note "cut list sent to Nadav" --link <Drive link>
python3 scripts/pipeline.py set "$EP" edit done --approved-by Nadav
```
- `review` = finished and waiting for the approver. `done` needs `--approved-by` on every stage that has an approver, and `publish` and `share` accept only Amitai.
- The script refuses a stage whose dependencies aren't done or skipped. Don't edit `pipeline.json` by hand to get past it.
- Record Drive links with `--link` and anything odd with `--note`: a retry, a word you couldn't verify, a one-time workaround Amitai OK'd.

### 3. Hand back after every stage
After each stage (or when you stop for an approval), upload `pipeline.json` to the episode's `extras/` (replace the old copy) and send Amitai the stage skill's hand-back plus the output of `pipeline.py report "$EP"`. Approvals arrive in chat; record them with `set … done --approved-by`.

### 4. Close with the learnings PR
Bugs, missing steps, new conventions and corrected spellings go into the skills as a PR (`AGENTS.md` → Editing the skills). Then `set "$EP" learnings done --link <PR URL>`.

## Hand back
- `pipeline.py report` output: every stage, its status, approver and links
- What is waiting on whom (Nadav: cuts and video; Amitai: title, upload, publish)
- The stage skill's own hand-back for the stage just finished
- The learnings PR link, at the end

## Never
- Skip `edit`, `copy`, `shorts`, `review`, `upload`, `publish` or `learnings`, or mark a stage done without its approver's OK in chat.
- Publish, set anything public on YouTube, or share on WhatsApp/Telegram without Amitai's explicit OK (show conventions → Hard rules).
- Start a second tracker for an episode that already has one in `extras/`.
- Do a stage's work from memory instead of loading its skill, or write your own code where a skill has a script (show conventions → Working rules).
