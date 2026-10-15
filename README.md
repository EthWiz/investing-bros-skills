# Investing Bros skills (אחים להשקעות)

Shared, versioned agent skills for producing the **Investing Bros / אחים להשקעות** podcast (Amitai & Nadav Raskin).
Any agent — Claude, Codex, Grokbot — can read and follow these.

## Pipeline

```
prep ──► record ──► post-production ──► review ──► upload (draft) ──► publish ──► share
                         │
                         └──► promo: shorts / teaser   (+ cover art: YouTube thumbnail prompt)
```

| Skill | Use it for |
|---|---|
| `investing-bros-show` | **Shared conventions** — load with every other skill: hosts, format, naming, Drive tree, roles/accounts, WhatsApp destinations |
| `investing-bros-episode-preparation` | Before recording: episode folder + `brief/`, news ideas, deep dive, share prep docs |
| `investing-bros-post-production` | After recording: combine, level the hosts, transcribe, trim, Hebrew Docs, full video episode, Drive filing, review ping |
| `investing-bros-title-description` | Five question-led Hebrew title options + the description Doc (intro, disclaimer, chapters), checked by `check_copy.py`: concise, no clickbait, no em dashes |
| `investing-bros-shorts` | Branded vertical shorts: speaker close-ups, hook headline, burned-in Hebrew captions, a sized cover each, uploaded to Drive `promo/` |
| `investing-bros-hyperframes` | Explainer shorts with animated cards rendered by HyperFrames (HTML/GSAP) on top of the ffmpeg-cut clip |
| `investing-bros-teaser` | Promo teaser (30–60 s) or per-host cold-open teasers for the video episode |
| `investing-bros-cover-art` | YouTube thumbnail: AI image prompt + headline options — channel layout, one accent colour |
| `investing-bros-episode-upload` | RedCircle draft upload, incl. the Hebrew RTL + `?` fix |
| `investing-bros-share-new-episode` | WhatsApp distribution of the published episode |

## Layout

```
.claude-plugin/          plugin + marketplace manifests (Claude Code)
AGENTS.md                agent instructions (CLAUDE.md imports it)
skills/<name>/
  SKILL.md               frontmatter (name, description) + steps
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
- **Claude app (web/desktop/Cowork)**: the repo is private, so it can't be added as a plugin marketplace there. Upload each skill folder as a ZIP under Customize → Skills (the ZIP's root is the skill folder), starting with `investing-bros-show`; re-upload the changed ones after each merge.
- **Claude Code, manual**: symlink the folders under `skills/` into `~/.claude/skills/` (personal) or `.claude/skills/` (project). Install all of them — they reference `investing-bros-show`.
- **Codex**: symlink into `~/.codex/skills/` (or point Codex at this repo; it reads `AGENTS.md`).
- **Grokbot**: keeps its own copy in sync with this repo.

Script dependencies: `ffmpeg` (with libass for captions), Python 3 with numpy, `faster-whisper` for transcription (fallback: `sherpa-onnx` + `soundfile` when Hugging Face is unreachable), Pillow + fontTools for brand frames and static Heebo weights, Node 18+ and the `hyperframes` npm CLI (Chrome Headless Shell) for HyperFrames renders, an installed Hebrew font (Heebo or Rubik) for the quick caption path.

## Contributing

See `AGENTS.md` → *Editing the skills*. In short: shared facts only in `investing-bros-show`, one skill per folder, code in `scripts/` with tests, never commit secrets. Run `python3 tools/validate_skills.py && python3 -m pytest skills` before pushing. Open a PR (or push to `main` for trivial fixes) and note what changed and why.
