import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {clamp, tornClip} from '../brand';
import {NavyPaper, ease, enterRight, pop, useTime} from './kit';

// Shared by every lesson's 'side' scenes: the navy panel on the left while Amitai sits on the right.
// It wipes in from his side (right edge first) and back out the same way.
export const PANEL_W = 960;

export const SidePanel: React.FC<{start: number; end: number; id: string; children: React.ReactNode}> = ({start, end, id, children}) => {
  const {t} = useTime();
  if (t < start - 0.1 || t > end + 0.7) return null;
  const k = ease(t, start, start + 0.6) * (1 - ease(t, end, end + 0.6));
  return (
    <div style={{position: 'absolute', left: -16, top: -14, width: PANEL_W + 16, height: 1108,   // overshoot: the torn clip stops short of the bottom edge
      transform: `translateX(${(1 - k) * -PANEL_W}px)`, filter: 'drop-shadow(10px 0 24px rgba(0,0,0,.45))'}}>
      <NavyPaper id={id} clip={tornClip(11, 1.2, 3).replace(/(\d+(?:\.\d+)?)% (\d+(?:\.\d+)?)%/g, (_m, x, y) => `${y}% ${x}%`)} />
      <AbsoluteFill style={{opacity: interpolate(k, [0.5, 1], [0, 1], clamp)}}>{children}</AbsoluteFill>
    </div>
  );
};

// a scene inside a panel, visible from `from` until `to`, cross-fading
export const Scene: React.FC<{from: number; to: number; children: React.ReactNode; style?: React.CSSProperties}> = ({from, to, children, style}) => {
  const {t} = useTime();
  if (t < from || t > to + 0.35) return null;
  const o = ease(t, from, from + 0.3) * (1 - ease(t, to, to + 0.35));
  return <AbsoluteFill style={{opacity: o, alignItems: 'center', justifyContent: 'center', direction: 'rtl', ...style}}>{children}</AbsoluteFill>;
};

export const In: React.FC<{at: number; children: React.ReactNode; style?: React.CSSProperties; dist?: number}> = ({at, children, style, dist}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps);
  return <div style={{...enterRight(k, dist), ...style}}>{children}</div>;
};
