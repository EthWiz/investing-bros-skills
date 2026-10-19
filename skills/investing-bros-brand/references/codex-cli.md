# Codex CLI image backend (Amitai's Mac)

Used for episode 1 short 01's dedicated cover (approved, published). One cover per short.

1. On the Mac (find it with ListMachines), make a work folder for the task, e.g.
   `/Users/<user>/investing-bros-covers/epN-shortNN/`. Change nothing else on the Mac.
2. Put there: `prompt.txt` (filled from [prompts.md](prompts.md), vertical Shorts layout,
   exact Hebrew headline = the short's hook, `פרק N` pill, show logo) and 1–2 reference
   PNGs (a brand reference from `assets/` and a frame of the host from the short).
3. Run (non-interactive; `--` is required because `-i` takes several values and would
   swallow the prompt; `env -u OPENAI_API_KEY` makes Codex use the Mac's signed-in account):
   ```
   env -u OPENAI_API_KEY ~/.nvm/versions/node/<ver>/bin/codex exec --skip-git-repo-check \
     -i ref1.png -i ref2.png -- "$(cat prompt.txt)" < /dev/null
   ```
   Codex reads the Mac's local skill copies in `~/.agents/skills`; keep them in sync with this repo.
4. The image lands in `~/.codex/generated_images/<id>/`. Copy it to the box with an
   **absolute** path (`/Users/<user>/.codex/...`; the copy tools don't expand `~`).
5. Resize to 1080×1920 JPEG, check every Hebrew letter at full and ~200 px size, and
   re-run with a targeted edit prompt if any letter is wrong.

Never print or copy `~/.codex/auth.json` or any token.
