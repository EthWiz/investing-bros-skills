# Investing Bros skills (אחים להשקעות)

Shared, versioned agent skills for producing the **Investing Bros / אחים להשקעות** podcast (Amitai & Nadav Raskin). Any agent — Claude, Codex, Grokbot — can read and follow them.

## Episode flow

From the finished recording to live on RedCircle, Spotify and YouTube. Each step is one skill; the Drive episode folder shows what's done.

```
1 audio edit ──┬──► 2 titles + description (.txt) + artwork brief ──┐
               ├──► 3 cold opens + intro + video episode ────────┼──► 5 review ► upload ► publish ► check Spotify ► share
               ├──► 4 exactly 3 shorts + covers, mid-form ───────┤
               └──► 4b 2 segments (01 deep dive + 02 next-best) ┘
```

| # | Step | Skill | Leaves in the Drive folder `פרק N — נושא/` | Approves |
|---|---|---|---|---|
| 0 | Before recording: news ideas, deep dive | `investing-bros-episode-preparation` | `brief/` | — |
| 1 | Start the standing bundle; combine, level, transcribe and trim the audio | `investing-bros-post-production` | `הקלטה-ערוכה-פרק-N.m4a`, `extras/` (transcript, `edit.json`) | Nadav (cuts) |
| 2 | Five question-led titles, description with chapters, artwork brief | `investing-bros-title-description` | `כותרות-פרק-N.txt`, `תיאור-פרק-N.txt`, artwork brief for brand | Amitai (title) |
| 3 | Per-host cold opens + intro + episode as one video; promo teaser | `investing-bros-video` | `video/`, `promo/` | Nadav |
| 4 | Exactly 3 shorts with a Codex cover each; optional 5–10 min mid-form highlights | `investing-bros-shorts` | `Shorts/`, `mid-form/` | Nadav |
| 4b | Exactly 2 standalone search-first segment videos: 01 is the deep-dive sub-question; 02 is the next-best deep-dive sub-question or strongest other self-contained topic | `investing-bros-segment-video` | `segments/` | Amitai |
| 5 | Review ping, RedCircle draft, YouTube review uploads, then publish in order, check Spotify/YouTube/RedCircle, WhatsApp | `investing-bros-episode-upload` | — | **Amitai (anything public)** |
| 6 | After publish, weekly (Sunday): read-only Studio/RedCircle stats, report Page, Telegram summary, history CSV | `investing-bros-analytics` | `investing-bros-youtube-weekly.csv` in Drive (analytics folder TBD) | — (weekly post pre-approved) |

- Starting step 1 commits every episode to the main flow plus exactly 2 complete segment videos and exactly 3 complete shorts. The post-production checklist remains open until all three tracks finish their owning skills.
- Steps 2–4b only need step 1's transcript and `edit.json`, so different agents can run them at the same time.
- Every skill ends with a **Done when** list of the files it leaves. To see where an episode stands, list its folder.
- `investing-bros-analytics` reads YouTube Studio stats (read-only) for the weekly Sunday report and ad-hoc analyses; posts a short text to Telegram.
- `investing-bros-show` holds shared show facts: hosts, naming, the Drive tree, accounts, WhatsApp/Telegram destinations and working rules. Load it with every skill; load `investing-bros-brand` for visual work and `investing-bros-remotion` for anything animated.
- **Nothing goes public without Amitai's explicit OK in chat.**

## Crypto course

`investing-bros-crypto-course` runs the free five-lesson Hebrew crypto course on the YouTube channel, outside the episode flow: the lesson plan, one slide deck and script per lesson, and `קורס קריפטו/שיעור N — נושא/` folders in Drive.

## Design ownership

`investing-bros-brand` is the single source for design rules, templates, selected artwork,
prompts and visual QA. It serves the episode workflow across stages rather than adding
another chronological stage. It owns every cover, including Shorts covers, and the only
typeface is Heebo. Its reference images live in Drive (`Brand Resources/references`),
indexed by file ID; the repo keeps only the rules, the layout specs, the solid video
logo and the cover scripts.

| Owner | Responsibility |
|---|---|
| `investing-bros-show` | Names, show facts, folders, approvals and publication rules |
| `investing-bros-brand` | Visual identity, reference art, templates and artwork production |
| `investing-bros-remotion` | Animation: the Remotion template that renders shorts and animated explainer cards |
| `investing-bros-title-description` | Titles, descriptions and approved artwork headlines |
| `investing-bros-video` / `investing-bros-shorts` / `investing-bros-segment-video` | Video/clip production using the shared design system |

GitHub holds the canonical design system. Episode files stay in the established Drive
folders, with an `extras/artwork-register.json` recording version, status and source.
Installed skill copies must be refreshed after merges. The approved full-frame teaser is
implemented in `investing-bros-video`, the Shorts video hook in `investing-bros-shorts`,
and the Shorts cover title in `investing-bros-brand` (`make_cover_title.py`). The
discussion card and lower third remain proposed adaptations, not editable Canva/Figma
files or implemented renderers.

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

Version 3.0 merged eleven production skills into seven. This change adds a shared brand capability. If an agent still lists `investing-bros-teaser`, `-hyperframes`, `-cover-art`, `-share-new-episode` or `-short-covers` (folded into `investing-bros-brand` in October 2026), it has an old copy: remove those and install the current set.

Script dependencies: `ffmpeg` (with libass for captions), Python 3 with numpy, `faster-whisper` for transcription (fallback: `sherpa-onnx` + `soundfile` when Hugging Face is unreachable), Pillow + fontTools for brand frames and static Heebo weights, Node 18+ and the `hyperframes` npm CLI (Chrome Headless Shell), and installed Heebo for every caption and graphics path.

## Contributing

See `AGENTS.md` → *Editing the skills*. Run `python3 tools/validate_skills.py && python3 -m pytest skills tools` before pushing, and open a small PR saying what changed and why.
