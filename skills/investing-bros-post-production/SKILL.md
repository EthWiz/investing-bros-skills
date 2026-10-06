---
name: Investing Bros post-production
description: >-
  Use this for Investing Bros / אחים להשקעות post-production after recording:
  stitch/trim/transcribe, lean Drive folder, Hebrew RTL + ? fix for host
  title/description; WhatsApp fetch/review pings go through Amitai Personal
  (owns WhatsApp).
---
# Investing Bros post-production

Use after a Zoom/voice/video recording lands for **Investing Bros** (Hebrew: **אחים להשקעות**). Co-hosts: Amitai and Nadav. Run on **my computer** (shared box). Do **not** invent numbers, quotes, or events.

Episode shape: ~10 min news, ~20 min deep dive, ~5 min each sharing an investment idea.

**Episode number:** use the number Amitai states. Do **not** auto-increment from old workspace folders or prior Drive names.

## WhatsApp ownership
**Amitai Personal owns WhatsApp Web.** For fetch or send: message Amitai Personal with the ask (download parts / send review bubble). Do **not** QR-login or drive WhatsApp on Investing Bros desktop.

## Drive layout (keep the episode folder lean)

Episode folder root may contain **only**:
1. **Edited upload-ready audio** (one file) — e.g. `הקלטה-ערוכה-פרק-N.m4a`
2. **Google Doc** `תיאור הפרק` — description + disclaimer + chapters
3. **Google Doc** `אפשרויות כותרת` — five SEO titles + `בחירה סופית:`

Everything else goes in a subfolder named **`extras`** (Hebrew `תוספות` is OK if preferred; default English `extras`):
- Raw / untrimmed combined audio
- Part files, wavs, segments.json
- Transcript `.txt` / `.srt`
- Local drafts, canaries, temp tests
- Duplicate `.txt` copies of Docs

Do **not** leave stray files at the episode root.

## Pipeline (order matters)

### 1. Fetch from WhatsApp
1. Ask **Amitai Personal** to pull latest parts from group `אחים להשקעות` only (`חלק 1` / `חלק 2`) onto shared disk / path you specify (prefer `m4a`).
2. Local work: `/workspace/investing-bros/episode-latest/` (or `episode-N/` only when Amitai confirms N).

### 2. Normalize to audio + combine
- Video → extract audio with `ffmpeg`.
- Multiple parts → concat demuxer in order.
- Keep **raw pre-edit** master locally: `investing-bros-episode-raw-untrimmed.m4a` (never overwrite with edited).

### 3. Create Drive episode folder
1. Under existing show tree (`אחים להשקעות` — do not invent a second root).
2. New Hebrew folder: `פרק N — נושא` (confirmed N).
3. Create subfolder **`extras`** inside it immediately.

### 4. Transcribe raw combined audio
1. 16 kHz mono wav of **raw** master.
2. faster-whisper `ivrit-ai/whisper-large-v3-turbo-ct2` (Hebrew).
3. Local outputs: `segments.json`, transcript txt/srt (these later go to Drive `extras` only).

### 5. Clip start/end from transcript
- Start: first real open (ברוכים הבאים / אחים להשקעות / פרק).
- End: after real outro.
- Export edited: `investing-bros-episode-edited.m4a` (or 192k mp3).

### 6. Hebrew Google Docs (canonical — two Docs only)
Create **Google Docs** (not root-level `.txt`) in the **episode folder root**:

#### A. `תיאור הפרק`
1. One cohesive Hebrew paragraph on the episode subject (what was said only).
2. `אין כאן המלצת השקעה. רק שיחה.`
3. Chapters on **edited** timeline (`0:00 נושא`, …), time first.

#### B. `אפשרויות כותרת`
- Exactly five SEO Hebrew titles (1–5).
- Line `בחירה סופית:` for Amitai’s pick.

Keep the Docs themselves plain (no invisible marks). The RTL + `?` fix below is applied only to the copy pasted into the podcast host.

Local `.txt` drafts OK while working; do not leave them at Drive root — put in `extras` or delete after Docs exist.

### 7. Hebrew RTL + `?` fix for the podcast host (approved by Amitai)
The host editor (RedCircle) is left-to-right, so Hebrew lines with a trailing `?` or embedded English names (Robinhood, NVIDIA, GPU…) render with the `?` on the wrong side and text jumbled. Plain text alone and "Hebrew-first" rewrites did **not** fix it. What worked is adding invisible Unicode direction marks:

- **RLM** = `U+200F` (right-to-left mark), **LRM** = `U+200E` (left-to-right mark).
- **Title:** append one RLM right after the final `?` (e.g. `פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?` + RLM).
- **Description:**
  1. Put an RLM right after **every** `?`, including mid-line ones (`מה זה NeoCloud?` + RLM + ` הכירו את…`).
  2. Start every chapter line (the ones beginning with a timestamp) with an LRM, so the time stays pinned.
  3. End every other Hebrew prose line (intro paragraph, disclaimer) with an RLM.
  4. Keep blank lines between intro, chapters, and disclaimer.
- Generate the marked copy from the plain Doc text with a script, never by hand:

```python
RLM, LRM = '\u200f', '\u200e'
def rtl_fix_title(t):
    t = t.rstrip()
    return t + RLM if not t.endswith(RLM) else t
def rtl_fix_desc(text):
    out = []
    for s in text.splitlines():
        if s and s[0].isdigit() and ':' in s[:6] and not s.startswith(LRM):
            s = LRM + s                       # chapter line
        s = s.replace('?' + RLM, '?').replace('?', '?' + RLM)  # RLM after every ?
        if s and not s.startswith(LRM) and any('\u0590' <= c <= '\u05FF' for c in s) and not s.endswith(RLM):
            s += RLM                          # Hebrew prose line
        out.append(s)
    return '\n'.join(out) + '\n'
```

- Save the results as files (e.g. `title-rtl.txt`, `description-rtl.txt` in the local episode folder) and have the browser paste the **file contents** via clipboard (select-all, then paste). Retyping strips the marks. Do not wrap in HTML or `dir="rtl"`; the editor ignores it.
- If an existing draft has been edited back and forth and still looks broken, create a **fresh draft** with the marked copy instead of patching the old one (that is what finally worked for פרק 4). Leave the old draft for Amitai to decide about.
- Verify with a screenshot of title + description before sharing the draft link.

### 8. Upload to Drive (placement rules)
**Episode root:**
- Edited audio only
- Doc `תיאור הפרק`
- Doc `אפשרויות כותרת`

**`extras/`:**
- Raw untrimmed audio
- Transcript txt + srt
- Marked RTL `.txt` copies and any other working files

Large audio: browser upload as `ami.grokbot@gmail.com` when connector base64 cannot carry the file. Connector is fine for Docs/folders/moves.

### 9. WhatsApp — ready for review
After root layout is correct (edited + 2 Docs; extras populated):
1. Shareable link to the **episode folder**.
2. Ask **Amitai Personal** to send one bubble to `אחים להשקעות`: ready for review + link; end with `sent by Grokbot`.
3. Do not delete prior bubbles.

### 10. Podcast host
- After review: [Investing Bros episode upload](../investing-bros-episode-upload/SKILL.md) (RedCircle, draft by default), using the RTL + `?` marked title/description from step 7.
- If the host rejects `.m4a`, a byte-identical copy renamed to `.mp3` uploads fine.
- Never publish without Amitai’s explicit OK.

### 11. Done when / hand back
Report:
- Episode folder link
- Confirmation root has only edited audio + 2 Docs; extras holds the rest
- Doc links
- WhatsApp ping status (via Amitai Personal)
- Edited duration
- Blockers

## Not in this recipe
- Mac-local editing as primary path
- Deleting WhatsApp bubbles without explicit OK
- Genesis / Hyperliquid / Nanex
- Ambiguous cuts without asking
- Auto-numbering episodes
- Leaving description/titles only as `.txt` at Drive root
- Cluttering episode root with raw/transcript/temps
- Driving WhatsApp Web / QR on Investing Bros desktop
- Pasting host copy without the RTL + `?` marks
