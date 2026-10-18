# Investing Bros skills (אחים להשקעות)

Shared, versioned agent skills for producing the **Investing Bros / אחים להשקעות** podcast (Amitai & Nadav Raskin). Any agent — Claude, Codex, Grokbot — can read and follow them.

## Episode flow

From the finished recording to live on RedCircle, Spotify and YouTube. Each step is one skill; the Drive episode folder shows what's done.

```
1 audio edit ──┬──► 2 titles + description (.txt) + thumbnail ──┐
               ├──► 3 cold opens + intro + video episode ────────┼──► 5 review ► upload ► publish ► check Spotify ► share
               └──► 4 shorts + covers, mid-form highlights ──────┘
```

| # | Step | Skill | Leaves in the Drive folder `פרק N — נושא/` | Approves |
|---|---|---|---|---|
| 0 | Before recording: news ideas, deep dive | `investing-bros-episode-preparation` | `brief/` | — |
| 1 | Audio edit: combine, level the hosts, transcribe, cut start/end and silences, trim, loudness | `investing-bros-post-production` | `הקלטה-ערוכה-פרק-N.m4a`, `extras/` (transcript, `edit.json`) | Nadav (cuts) |
| 2 | Five question-led titles, description with chapters, thumbnail prompt | `investing-bros-title-description` | `כותרות-פרק-N.txt`, `תיאור-פרק-N.txt`, `promo/` thumbnail | Amitai (title) |
| 3 | Per-host cold opens + intro + episode as one video; promo teaser | `investing-bros-video` | `video/`, `promo/` | Nadav |
| 4 | ~5 shorts with a cover each; 5–10 min mid-form highlights | `investing-bros-shorts` | `shorts/`, `mid-form/` | Nadav |
| 5 | Review ping, RedCircle draft, YouTube (private), then publish, check Spotify/YouTube/RedCircle, WhatsApp | `investing-bros-episode-upload` | — | **Amitai (anything public)** |

- Steps 2–4 only need step 1's transcript and `edit.json`, so different agents can run them at the same time.
- Every skill ends with a **Done when** list of the files it leaves. To see where an episode stands, list its folder.
- `investing-bros-show` holds what all of them share: hosts, naming, the Drive tree, brand, accounts, WhatsApp/Telegram destinations, working rules. Load it with every skill.
- **Nothing goes public without Amitai's explicit OK in chat.**

## Improving the skills

The skills get better a little after every run, from whichever agent did the work. When a run teaches something:

| What happened | Where it goes |
|---|---|
| A mistake a script could catch (a dash, a timestamp, a file size) | A check in that skill's script, with a test |
| A step that was missing or wrong | One line in the skill that owns the step |
| A fact (spelling, account, size limit, a decision) | `investing-bros-show` only |
| Something you couldn't verify or fix yet | A GitHub issue |

Small PRs, one fix each, merged the same day. Details in `AGENTS.md`.

## Layout

```
.claude-plugin/          plugin + marketplace manifests (Claude Code)
AGENTS.md                agent instructions (CLAUDE.md imports it)
skills/<name>/
  SKILL.md               frontmatter (name, description) + When to use, Inputs, Steps, Done when, Hand back, Never
  scripts/               code the agent runs (+ test_*.py)
  references/            detail loaded only when needed
tools/validate_skills.py frontmatter/layout checks (run in CI)
```

## Installing

- **Claude Code** (recommended — keeps all skills together and updatable):
  ```
  /plugin marketplace add EthWiz/investing-bros-skills
  /plugin install investing-bros@investing-bros
  ```
  Skills then appear as `investing-bros:<skill-name>`.
- **Claude app (web/desktop/Cowork)**: the repo is private, so it can't be added as a plugin marketplace there. After every merge, GitHub builds one ZIP per skill on the [`skills-latest` release](https://github.com/EthWiz/investing-bros-skills/releases/tag/skills-latest). Upload them under Customize → Skills, starting with `investing-bros-show`. Each skill carries a `VERSION` file; if it doesn't match the release notes, re-upload.
- **Claude Code, manual**: symlink the folders under `skills/` into `~/.claude/skills/` (personal) or `.claude/skills/` (project). Install all of them — they reference `investing-bros-show`.
- **Codex**: symlink into `~/.codex/skills/` (or point Codex at this repo; it reads `AGENTS.md`).
- **Grokbot**: keeps its own copy in sync with this repo.

Version 3.0 merged eleven skills into seven. If an agent still lists `investing-bros-teaser`, `-hyperframes`, `-cover-art` or `-share-new-episode`, it has an old copy: remove those and install the current set.

Script dependencies: `ffmpeg` (with libass for captions), Python 3 with numpy, `faster-whisper` for transcription (fallback: `sherpa-onnx` + `soundfile` when Hugging Face is unreachable), Pillow + fontTools for brand frames and static Heebo weights, Node 18+ and the `hyperframes` npm CLI (Chrome Headless Shell) for HyperFrames renders, an installed Hebrew font (Heebo or Rubik) for the quick caption path.

## Contributing

See `AGENTS.md` → *Editing the skills*. Run `python3 tools/validate_skills.py && python3 -m pytest skills tools` before pushing, and open a small PR saying what changed and why.
