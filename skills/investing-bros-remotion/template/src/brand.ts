import {staticFile} from 'remotion';

// Values from investing-bros-brand (palette) and the approved Shorts template in
// investing-bros-shorts (hook yellow, caption/tag gold). Change them there first.
export const NAVY = '#09243B';
export const CREAM = '#F5EBD5';
export const MUSTARD = '#D8A52E';
export const HOOK_YELLOW = '#FAC828';
export const GOLD = '#F5B71F';
export const WHITE = '#FFFFFF';
export const FONT = 'Heebo';

// Static Heebo weights (brand.py fonts) are staged into public/fonts by render_short.py.
export const fontFaces = () =>
  ([['SemiBold', 600], ['ExtraBold', 800], ['Black', 900]] as const)
    .map(([name, weight]) =>
      `@font-face{font-family:${FONT};font-weight:${weight};font-display:block;` +
      `src:url(${staticFile(`fonts/Heebo-${name}.ttf`)}) format('truetype');}`)
    .join('');

// Fixed frame positions from the approved template (1080x1920).
export const LOGO_BOX = {left: 56, top: 150, width: 210};
export const TAG_RIGHT_EDGE = 1024;
export const CAPTION_Y = 1480;            // one-line captions (centre)
export const CAPTION_Y_TWO_LINES = 1410;  // two-line captions: centre raised so line 2 stays above the platform UI
export const CAPTION_Y_PUNCH = 1330;      // kinetic captions: a big word plus small ones, centred higher
export const CTA_Y = 1130;
export const HOOK_Y = 700;

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// Deterministic torn-paper edge as a CSS clip-path (same seed -> same edge every frame).
export const tornClip = (seed: number, jag = 6, step = 5) => {
  let s = seed * 7919 + 13;
  const r = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  const top: string[] = [];
  const bottom: string[] = [];
  for (let x = 0; x <= 100; x += step) top.push(`${x}% ${(r() * jag).toFixed(2)}%`);
  for (let x = 100; x >= 0; x -= step) bottom.push(`${x}% ${(100 - r() * jag).toFixed(2)}%`);
  return `polygon(${[...top, ...bottom].join(',')})`;
};

export const seedOf = (text: string) => [...text].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 100000, 7);
