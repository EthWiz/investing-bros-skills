# Episode Docs

Two Google Docs in the episode root, both in Hebrew, both plain text (no direction marks — `investing-bros-episode-upload` adds those to the copy pasted into RedCircle).

Write only what was actually said in the episode (read the transcript). No invented numbers or claims.

## `תיאור הפרק`

Three blocks separated by blank lines:

1. **Intro** — one cohesive Hebrew paragraph on what the episode covers.
2. **Disclaimer** — exactly: `אין כאן המלצת השקעה. רק שיחה.`
3. **Chapters** — one per line, time first, on the **edited** timeline (example; real chapters come from the transcript):
   ```
   0:00 פתיחה
   1:05 חדשות השבוע
   11:30 צלילת עומק: <נושא>
   31:10 רעיון השקעה – אמיתי
   36:00 רעיון השקעה – נדב
   ```
   Convert from transcript (raw) times with `edited = raw − start` (`start` is in `extras/edit.json`). Use `M:SS`, or `H:MM:SS` past an hour.
   Chapters start at `0:00` on this edited timeline. If a cold open + intro (~28 s) is prepended in the video, offset every chapter by that length in the **video's** description. The Doc itself stays on the edited-audio timeline.

Fact-check every claim in the description (`investing-bros-show` → Hebrew).

## `אפשרויות כותרת`

```
1. פרק N – <title option>
2. פרק N – <title option>
3. פרק N – <title option>
4. פרק N – <title option>
5. פרק N – <title option>

בחירה סופית:
```

- Exactly five SEO-minded Hebrew titles, en dash `–` after the number.
- Leave `בחירה סופית:` empty for Amitai. Upload uses the text after it; if Amitai cut the Doc down to a single title, that title is the pick.
