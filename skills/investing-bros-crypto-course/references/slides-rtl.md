# Hebrew in a Claude Slides deck

The Slides format has no `direction` or `dir` support: every text box is laid out left to right. These workarounds were used on the lesson 1 deck (2026-10-26). They follow the Unicode bidi rules but were not yet checked in the rendered deck, so look at each slide before calling a deck done, and record here what turned out wrong.

- **Alignment:** `text-align:right` on every `<section>` (it inherits).
- **Order of side-by-side items:** `flex-direction:row-reverse` on every row, so the first item in the source sits on the right and is read first. In a grid (which fills left to right) list each row's items right-hand item last.
- **Arrows in a flow** point left (`arrow-left`), toward the next step.
- **Punctuation at the end of a line** (`?`, `!`, `.`, `)`) jumps to the right end. Avoid a trailing period, and put `&#8207;` (the right-to-left mark) right after a trailing `?`, `!` or `)`.
- **A line that starts with a number** (`21 מיליון`) reads backwards. Start it with `&#8207;`, or start the line with a Hebrew word (as the show's copy rules require anyway).
- **No English inside a Hebrew sentence.** A Latin word between Hebrew words reorders the sentence. Put English names (`BITCOIN · BTC`) on their own line, or write them in Hebrew.
- **Geresh:** write `׳` (U+05F3), not `'`, in words like את׳ריום and בלוקצ׳יין.
- **Tables:** columns run left to right, so put the label column last (rightmost) and set `text-align:right` on each header cell.
- **Bullets:** don't use `<ul>`/`<ol>`; their markers sit on the left. Use rows with a number or an icon placed with `row-reverse`.
- **Speaker notes** are plain text and are not affected; write them in normal Hebrew.
