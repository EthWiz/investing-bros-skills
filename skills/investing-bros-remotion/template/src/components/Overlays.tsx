import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {
  CAPTION_Y, CREAM, CTA_Y, FONT, GOLD, HOOK_Y, HOOK_YELLOW, LOGO_BOX, NAVY, TAG_RIGHT_EDGE, WHITE, clamp,
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

// Captions: verbatim, 1-4 words, white Heebo Black, keywords gold, small pop on each change.
export const Captions: React.FC<{captions: ShortProps['captions']}> = ({captions}) => {
  const {f, fps, t} = useT();
  const c = captions.find((x) => t >= x.start && t < x.end);
  if (!c) return null;
  const k = spring({frame: f - Math.round(c.start * fps), fps, config: {damping: 13, stiffness: 220}});
  const norm = (w: string) => w.replace(/[.,?!:;"'״׳]/g, '');
  const hl = new Set(c.highlight.flatMap((h) => h.split(' ').map(norm)));
  return (
    <div style={{position: 'absolute', top: CAPTION_Y, width: '100%', display: 'flex', justifyContent: 'center'}}>
      <div style={{
        transform: `translateY(-50%) scale(${interpolate(k, [0, 1], [0.86, 1])})`,
        opacity: interpolate(k, [0, 0.4], [0, 1], clamp), direction: 'rtl', textAlign: 'center', maxWidth: 940,
        fontFamily: FONT, fontWeight: 900, fontSize: 84, lineHeight: 1.25, color: WHITE,
        textShadow: '0 4px 10px rgba(0,0,0,.6), 0 0 3px rgba(0,0,0,.9)',
      }}>
        {c.text.split(' ').map((w, i) => (
          <span key={i} style={{color: hl.has(norm(w)) ? GOLD : WHITE}}>{w}{' '}</span>
        ))}
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

// Logo redrawn on top (only needed above a full-screen card; the base already carries it).
export const Logo: React.FC = () => (
  <Img src={staticFile('logo.png')} style={{position: 'absolute', left: LOGO_BOX.left, top: LOGO_BOX.top, width: LOGO_BOX.width}} />
);

// End card: hard cut, silent, navy; logo, episode pill, title, CTA and arrow.
export const EndCard: React.FC<{episode: number; title: [string, string]}> = ({episode, title}) => {
  const {f, fps, t} = useT();
  const k = spring({frame: f, fps, config: {damping: 14}});
  return (
    <AbsoluteFill style={{background: NAVY, alignItems: 'center', paddingTop: 420, direction: 'rtl', fontFamily: FONT}}>
      <Img src={staticFile('logo.png')} style={{width: 520, transform: `scale(${interpolate(k, [0, 1], [0.85, 1])})`}} />
      <div style={{marginTop: 30, background: CREAM, color: NAVY, fontWeight: 900, fontSize: 48, padding: '6px 34px', borderRadius: 40}}>
        פרק {episode}
      </div>
      <div style={{marginTop: 34, color: WHITE, fontWeight: 800, fontSize: 64, textAlign: 'center', lineHeight: 1.35}}>
        {title[0]}<br />{title[1]}
      </div>
      <div style={{marginTop: 50, color: GOLD, fontWeight: 800, fontSize: 48}}>הקישור לפרק המלא בתיאור</div>
      <div style={{marginTop: 10, transform: `translateY(${Math.sin(t * 6) * 10}px)`}}><Arrow size={90} color={GOLD} /></div>
    </AbsoluteFill>
  );
};
