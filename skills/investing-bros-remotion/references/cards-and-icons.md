# Cards and icons

Part of `investing-bros-remotion`. A card is an animated explainer laid over the short
for a few seconds. Cards live in the short's config under `cards` (times are output
seconds, after the 1.25x speed-up):

```jsonc
"cards": [{
  "id": "drop",                    // unique per short
  "mode": "inset",                 // inset (default) | full | card
  "start": 8.99, "end": 14.18,     // the card's whole window
  "steps": [                       // one or more; each replaces the last with a crossfade
    {"at": 8.99,  "visual": "house", "title": "לא קמים בבוקר"},
    {"at": 10.95, "visual": "drop", "value": 30, "title": "צניחה של 30%"}
  ]
}]
```
The older key `hyperframes` (with `panel` for the mode, `pct` for the value, `clock` as
an icon name) is still read, so configs from `build_amitai_short.py` convert as they are.

## Modes
| mode | where | motion | use for |
|---|---|---|---|
| `inset` | 1000×1840 at x 40, y 40: most of the frame, a thin frame of the host video around it; logo, name tag and captions on top | springs up from below, fades out | the default; most explainers |
| `full` | the whole frame; logo, name tag and captions stay on top | paper slides up over the host, then up and away | a big moment, 2–4 s at most |
| `card` | 1000×700 in the middle | as `inset` | small asides |

## Icons
Drawn in `template/src/components/icons.tsx` (flat navy-outlined cream and yellow
shapes; no emoji, no stock art). `make_props.py` keeps the same list and a test checks
they match.

| icon | shows | value |
|---|---|---|
| `house` | a house drawing itself in, then filling | — |
| `house_lock` | the house, then a padlock pops on (illiquid, locked in) | — |
| `drop` | a bar falls by `value`%; a dashed line keeps the old level; the number counts up | required |
| `rise` | the same, rising | required |
| `bars_up` / `bars_down` | four bars pop up, then an arrow draws across | — |
| `pie` | a pie fills to `value`% and the number counts up | required |
| `chip` | a chip whose traces draw in and pulse (AI, compute) | — |

**Adding an icon:** write a component in `icons.tsx` that takes `{lt, value}` (seconds
since its step began, the spoken number) and draws in the 260×210 viewBox; add it to
`ICONS` there and in `make_props.py`; add a row here; render `--stills` on a config
that uses it and look at the sheet; run the tests. One PR.

## Good practice
1. **One idea per card**, at most 4–5 words in the title; numbers big.
2. **On the word.** Each step's `at` is when its words are spoken (word timings from
   `transcribe_clip.py`), not before.
3. **Add, don't repeat.** The card shows the picture; captions carry the sentence.
   `make_props.py` refuses a `subtitle` that repeats the captions under it; use one only
   for words the picture needs.
4. **Faces back.** About one card per 20 s; `full` for 2–4 s; keep cards to roughly a
   third of the short.
5. **One motion per short.** Stick to one mode per short unless one moment truly needs `full`.
6. **Platform safe zone.** Titles stay within x 60–940 (long titles drop a size
   automatically); nothing important below y ≈ 1540.
7. **Honest numbers.** A value icon shows only a number the host said; illustrative
   shapes (bars, house) must not read as real data.
