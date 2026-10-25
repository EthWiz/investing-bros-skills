import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {
  CAPTION_Y, CREAM, CTA_Y, FONT, GOLD, HOOK_Y, HOOK_YELLOW, LOGO_BOX, TAG_RIGHT_EDGE, WHITE, clamp,
} from '../brand';
import type {ShortProps} from '../props';
import {Arrow, Strip} from './Strip';

const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return {f, fps, t: f / fps};
};

// Hook: on screen from frame 1 (no fade-in), second strip lands a beat later, 0.3 s fade-out.
export const Hook: React.FC<{hook: ShortProps['hook']}> = ({hook}) => {
  const {f, fps, t} = useT();
  if (t < hook.start || t >= hook.end) return null;
  const a = interpolate(t, [hook.end - 0.3, hook.end], [1, 0], clamp);
  const k1 = spring({frame: f, fps, config: {damping: 14}});
  const k2 = spring({frame: f - 3, fps, config: {damping: 14}});
  return (
    <AbsoluteFill style={{alignItems: 'center', top: HOOK_Y, opacity: a}}>
      <Strip text={hook.top} bg={CREAM} size={96} rotate={-1}
             style={{transform: `scale(${interpolate(k1, [0, 1], [1.06, 1])}) rotate(-1deg)`}} />
      <Strip text={hook.bottom} bg={HOOK_YELLOW} size={96}
             style={{marginTop: -18, transform: `translateX(${interpolate(k2, [0, 1], [-60, 0])}px) rotate(1deg)`}} />
    </AbsoluteFill>
  );
};

// Gold name tag top right; switches with the speaker.
export const NameTag: React.FC<{tags: ShortProps['tags']}> = ({tags}) => {
  const {f, fps, t} = useT();
  const tag = tags.find(([a, b]) => t >= a && t < b);
  if (!tag) return null;
  const k = spring({frame: f - Math.round(tag[0] * fps), fps, config: {damping: 16}});
  return (
    <div style={{
      position: 'absolute', right: 1080 - TAG_RIGHT_EDGE, top: 150, height: 64, padding: '0 24px', background: GOLD,
      display: 'flex', alignItems: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 38, color: '#0B1006',
      direction: 'rtl', transform: `translateY(${(1 - k) * -20}px)`, opacity: k,
    }}>{tag[2]}</div>
  );
};

// Captions: verbatim, 1-4 words on one line, white Heebo Black, keywords gold.
// With word timings each word pops in as it is spoken (the line builds up, space for the
// rest is kept so nothing shifts); without them the whole caption pops in at its start.
// highlight 'spoken': the word being said is gold and the rest white (keywords get no colour of their own).
export const Captions: React.FC<{captions: ShortProps['captions']; highlight?: ShortProps['captionHighlight']}> = ({captions, highlight = 'keywords'}) => {
  const {f, fps, t} = useT();
  const c = captions.find((x) => t >= x.start && t < x.end);
  if (!c) return null;
  const norm = (w: string) => w.replace(/[.,?!:;"'״׳]/g, '');
  const hl = new Set(c.highlight.flatMap((h) => h.split(' ').map(norm)));
  const words = c.words ?? c.text.split(' ').map((w) => ({w, start: c.start, end: c.end}));
  const spoken = words.reduce((acc, w, i) => (t >= w.start - 1e-6 ? i : acc), -1);
  const gold = (w: {w: string}, i: number) => (highlight === 'spoken' ? i === spoken : hl.has(norm(w.w)));
  return (
    <div style={{position: 'absolute', top: CAPTION_Y, width: '100%', display: 'flex', justifyContent: 'center'}}>
      <div style={{
        transform: 'translateY(-50%)', direction: 'rtl', textAlign: 'center', maxWidth: 940, whiteSpace: 'nowrap',
        fontFamily: FONT, fontWeight: 900, fontSize: 84, lineHeight: 1.25,
        textShadow: '0 4px 10px rgba(0,0,0,.6), 0 0 3px rgba(0,0,0,.9)',
      }}>
        {words.map((w, i) => {
          const k = spring({frame: f - Math.round(w.start * fps), fps, config: {damping: 13, stiffness: 240}});
          const shown = t >= w.start - 1e-6;
          return (
            <span key={i} style={{
              display: 'inline-block', marginLeft: 18, color: gold(w, i) ? GOLD : WHITE,
              opacity: shown ? interpolate(k, [0, 0.35], [0, 1], clamp) : 0,
              transform: `translateY(${shown ? (1 - k) * 14 : 14}px) scale(${shown ? interpolate(k, [0, 1], [0.82, 1]) : 0.82})`,
            }}>{w.w}</span>
          );
        })}
      </div>
    </div>
  );
};

// CTA over the chest for the last ~3 s of speech, with a bobbing arrow.
export const Cta: React.FC<{cta: ShortProps['cta']}> = ({cta}) => {
  const {f, fps, t} = useT();
  if (t < cta.start || t >= cta.end) return null;
  const k = spring({frame: f - Math.round(cta.start * fps), fps, config: {damping: 14}});
  return (
    <AbsoluteFill style={{alignItems: 'center', top: CTA_Y, opacity: k}}>
      <Strip text={cta.text} bg={CREAM} size={54} style={{transform: `scale(${interpolate(k, [0, 1], [0.9, 1])})`}} />
      <div style={{marginTop: -6, transform: `translateY(${Math.sin(t * 6) * 8}px)`}}><Arrow size={70} color={GOLD} /></div>
    </AbsoluteFill>
  );
};

// Logo redrawn on top of a card that covers it (the base video already carries it).
export const Logo: React.FC = () => (
  <Img src={staticFile('logo.png')} style={{position: 'absolute', left: LOGO_BOX.left, top: LOGO_BOX.top, width: LOGO_BOX.width}} />
);
