# Hebrew RTL + `?` fix for RedCircle (approved by Amitai)

## Problem
RedCircle's title and description editors are left-to-right. Hebrew lines that end in `?`, or contain English names (Robinhood, NVIDIA, GPU…), render with the `?` on the wrong side and the words jumbled.

What did **not** work:
- plain text alone
- "Hebrew-first" rewrites
- wrapping in HTML or `dir="rtl"` (the editor ignores it)

## What works: invisible Unicode direction marks
- **RLM** = `U+200F` (right-to-left mark)
- **LRM** = `U+200E` (left-to-right mark)

**Title:** one RLM right after the final `?`.
Example: `פרק 4 – ניו קלאודס: מי ינצח במלחמת העננים?` + RLM.

**Description:**
1. An RLM right after **every** `?`, including mid-line ones (`מה זה NeoCloud?` + RLM + ` הכירו את…`).
2. Every chapter line (starts with a timestamp) begins with an LRM, so the time stays pinned.
3. Every other Hebrew prose line (intro, disclaimer) ends with an RLM.
4. Blank lines between intro, disclaimer and chapters stay.

`scripts/rtl_fix.py` does exactly this and is idempotent (running it twice doesn't double the marks). `scripts/test_rtl_fix.py` has the פרק 4 cases.

## Pasting
- Paste the **file contents** via clipboard (select-all in the field, then paste). Typing the text, or a browser tool that types, drops the marks.
- The Google Docs stay plain; only the host copy is marked.

## When a draft is still broken
If a draft has been edited back and forth and still renders wrong, make a **fresh draft** with the marked copy instead of patching (that's what finally fixed פרק 4). Leave the old draft for Amitai.

## Verify
Screenshot the title and description before sharing the draft link.
