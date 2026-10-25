// The data one short needs. scripts/make_props.py writes it; nothing here is episode-specific.
// All times are seconds on the OUTPUT timeline (after make_base.py's edit and 1.25x speed-up).

export type CardMode = 'inset' | 'full' | 'card';

export type Step = {
  at: number;          // when this step starts (the moment its words are spoken)
  visual: string;      // icon name, see components/icons.tsx -> ICONS
  title: string;       // spoken words only
  subtitle?: string;   // spoken words only; leave empty rather than repeat the caption
  value?: number;      // for value icons (drop, rise, pie): the number the host said, e.g. 30
};

export type CardSpec = {id: string; mode: CardMode; start: number; end: number; steps: Step[]};

export type Caption = {start: number; end: number; text: string; highlight: string[]};

export type ShortProps = {
  base: string;                 // clean base video in public/ (from make_base.py)
  baseDuration: number;         // seconds
  endcardSeconds: number;       // silent end card appended after the base
  episode: number;
  endTitle: [string, string];   // episode title in two lines for the end card
  hook: {start: number; end: number; top: string; bottom: string};
  tags: [number, number, string][];
  captions: Caption[];
  cards: CardSpec[];
  cta: {start: number; end: number; text: string};
};
