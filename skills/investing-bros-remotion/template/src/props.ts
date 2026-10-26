// The data one short needs. scripts/make_props.py writes it; nothing here is episode-specific.
// All times are seconds on the OUTPUT timeline (after make_base.py's edit and 1.15x speed-up).

export type CardMode = 'inset' | 'full' | 'card';

export type Step = {
  at: number;          // when this step starts (the moment its words are spoken)
  visual: string;      // icon name, see components/icons.tsx -> ICONS
  title: string;       // spoken words only
  subtitle?: string;   // spoken words only; leave empty rather than repeat the caption
  value?: number;      // for value icons (drop, rise, pie): the number the host said, e.g. 30
};

export type CardSpec = {id: string; mode: CardMode; start: number; end: number; steps: Step[]};

export type Word = {w: string; start: number; end: number; emph?: boolean};   // emph: the big word ('punch')

// A caption is one phrase (house 'punch': 1-6 words, up for its reading time); `words` carry the
// spoken-word timings that move the highlight box.
export type Caption = {start: number; end: number; text: string; highlight: string[]; words?: Word[]};

export type ShortProps = {
  base: string;                 // clean base video in public/ (from make_base.py)
  baseDuration: number;         // seconds; the short ends here (no end card: the CTA runs to the last frame)
  episode: number;
  hook: {start: number; end: number; top: string; bottom: string};
  tags: [number, number, string][];
  captions: Caption[];
  captionHighlight: 'keywords' | 'spoken';   // house: 'spoken' (the word being said is boxed/gold); 'keywords' = older look
  captionStyle: 'build' | 'line' | 'punch';  // house: 'punch' (kinetic, one big word per phrase); 'line' / 'build' = older looks
  cards: CardSpec[];
  cta: {start: number; end: number; text: string};
};
