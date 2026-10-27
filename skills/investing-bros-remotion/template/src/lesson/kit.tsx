import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {CREAM, FONT, NAVY, clamp, seedOf, tornClip} from '../brand';

export const useTime = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return {f, fps, t: f / fps};
};

// spring that starts at time `at` (seconds); 0 before it
export const pop = (t: number, at: number, fps: number, damping = 14, stiffness = 170) =>
  t < at ? 0 : spring({frame: Math.round((t - at) * fps), fps, config: {damping, stiffness}});

export const ease = (t: number, a: number, b: number) =>
  interpolate(t, [a, b], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});

export const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

// Torn-paper strip (the show's look): navy Heebo Black on cream or mustard paper.
export const Paper: React.FC<{text?: string; bg?: string; color?: string; size: number; weight?: number;
  style?: React.CSSProperties; children?: React.ReactNode; seed?: string}> =
  ({text, bg = CREAM, color = NAVY, size, weight = 900, style, children, seed}) => (
    <div style={{filter: 'drop-shadow(0 6px 10px rgba(0,0,0,.35))', ...style}}>
      <div style={{background: bg, color, fontFamily: FONT, fontWeight: weight, fontSize: size, lineHeight: 1.15,
        padding: `${size * 0.16}px ${size * 0.42}px ${size * 0.24}px`, direction: 'rtl', whiteSpace: 'nowrap',
        clipPath: tornClip(seedOf(seed ?? text ?? 'x'))}}>
        {children ?? <bdi dir="auto">{text}</bdi>}
      </div>
    </div>
  );

// Navy paper with a little grain, used behind animations and panels.
export const NavyPaper: React.FC<{id: string; style?: React.CSSProperties; clip?: string}> = ({id, style, clip}) => (
  <div style={{position: 'absolute', inset: 0, background: NAVY, overflow: 'hidden', clipPath: clip, ...style}}>
    <svg width="100%" height="100%" style={{position: 'absolute', opacity: 0.16}}>
      <filter id={`grain-${id}`}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={4} /></filter>
      <rect width="100%" height="100%" filter={`url(#grain-${id})`} />
    </svg>
  </div>
);

// Graphics enter from the right (RTL) and settle.
export const enterRight = (k: number, dist = 70): React.CSSProperties => ({
  opacity: interpolate(k, [0, 0.35], [0, 1], clamp),
  transform: `translateX(${(1 - k) * dist}px)`,
});
