import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {CREAM, GOLD, MUSTARD, NAVY, clamp} from '../brand';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: a fall from a peak, on a price chart. Axes, then the peak, then the line
// drops diagonally to the trough with an arrow, a bracket shows how much of the height was lost, and
// Amitai's words for it come in beside the bracket. The trough sits at (100 - percent)% of the peak's
// height above the time axis, so the picture keeps the true proportion; there are no prices on the
// axes, since he doesn't say them. Drops are mustard, not red (the palette has no red).
// content: heading? {text, at}, period {text, at} (under the time axis), drop {percent, text, at}.
// It lays itself out from the frame: 16:9 in the lesson (left of his circle), 9:16 for a Short.

type P = {x: number; y: number};
type Layout = {origin: P; yTop: number; xEnd: number; peak: P; troughX: number; bracketX: number; label: P; labelSize: number;
  headY: number; headRight: number; stroke: number};

const WIDE: Layout = {origin: {x: 200, y: 800}, yTop: 150, xEnd: 1440, peak: {x: 330, y: 230}, troughX: 1250, bracketX: 1330,
  label: {x: 1120, y: 360}, labelSize: 76, headY: 70, headRight: 1440, stroke: 12};
const TALL: Layout = {origin: {x: 110, y: 1400}, yTop: 380, xEnd: 990, peak: {x: 210, y: 520}, troughX: 860, bracketX: 940,
  label: {x: 600, y: 640}, labelSize: 64, headY: 230, headRight: 990, stroke: 11};

const DRAW = 1.3;   // seconds for the line to fall

export const PriceDrop: React.FC<SceneProps> = ({start, end, content}) => {
  const {t, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const {origin, peak} = L;
  const trough = {x: L.troughX, y: origin.y - (1 - content.drop.percent / 100) * (origin.y - peak.y)};
  const axes = ease(t, start, start + 0.6);
  const peakK = pop(t, content.period.at, fps, 10, 200);
  const fall = ease(t, content.drop.at, content.drop.at + DRAW);
  const tip = {x: lerp(peak.x, trough.x, fall), y: lerp(peak.y, trough.y, fall)};
  const angle = (Math.atan2(trough.y - peak.y, trough.x - peak.x) * 180) / Math.PI;
  const after = content.drop.at + DRAW;
  const bracket = ease(t, after - 0.2, after + 0.4);
  const labelK = pop(t, after, fps);
  const a = L.stroke;
  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`drop-${start}`} />
      {content.heading ? (
        <div style={{position: 'absolute', top: L.headY, right: width - L.headRight, ...enterRight(pop(t, content.heading.at, fps))}}>
          <Paper text={content.heading.text} size={58} />
        </div>
      ) : null}
      <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
        {/* axes: price up, time to the right */}
        <g stroke={CREAM} strokeWidth={5} strokeLinecap="round" opacity={0.55 * axes}>
          <line x1={origin.x} y1={origin.y} x2={origin.x} y2={lerp(origin.y, L.yTop, axes)} />
          <line x1={origin.x} y1={origin.y} x2={lerp(origin.x, L.xEnd, axes)} y2={origin.y} />
        </g>
        <g fill={CREAM} opacity={0.55 * interpolate(axes, [0.9, 1], [0, 1], clamp)}>
          <path d={`M${origin.x - 14} ${L.yTop + 18} L${origin.x} ${L.yTop - 6} L${origin.x + 14} ${L.yTop + 18} Z`} />
          <path d={`M${L.xEnd - 18} ${origin.y - 14} L${L.xEnd + 6} ${origin.y} L${L.xEnd - 18} ${origin.y + 14} Z`} />
        </g>
        {/* the peak's level, dashed, for the bracket to measure from */}
        {peakK > 0 ? (
          <line x1={peak.x} y1={peak.y} x2={lerp(peak.x, L.bracketX, bracket)} y2={peak.y} stroke={CREAM} strokeWidth={3}
            strokeDasharray="14 12" opacity={0.5} />
        ) : null}
        {fall > 0 ? (
          <>
            <line x1={peak.x} y1={peak.y} x2={tip.x} y2={tip.y} stroke={NAVY} strokeWidth={a + 8} strokeLinecap="round" />
            <line x1={peak.x} y1={peak.y} x2={tip.x} y2={tip.y} stroke={MUSTARD} strokeWidth={a} strokeLinecap="round" />
            <g transform={`translate(${tip.x} ${tip.y}) rotate(${angle})`}>
              <path d={`M${-a * 3.4} ${-a * 2.6} L${a * 1.2} 0 L${-a * 3.4} ${a * 2.6} Z`} fill={MUSTARD} stroke={NAVY} strokeWidth={4}
                strokeLinejoin="round" />
            </g>
          </>
        ) : null}
        {peakK > 0 ? <circle cx={peak.x} cy={peak.y} r={16 * peakK} fill={GOLD} stroke={NAVY} strokeWidth={5} /> : null}
        {/* the bracket: how much of the peak's height is gone */}
        {bracket > 0 ? (
          <g stroke={GOLD} strokeWidth={6} strokeLinecap="round" opacity={bracket}>
            <line x1={L.bracketX} y1={peak.y} x2={L.bracketX} y2={lerp(peak.y, trough.y, bracket)} />
            <line x1={L.bracketX - 18} y1={peak.y} x2={L.bracketX + 18} y2={peak.y} />
            <line x1={L.bracketX - 18} y1={trough.y} x2={L.bracketX + 18} y2={trough.y} opacity={interpolate(bracket, [0.8, 1], [0, 1], clamp)} />
            <line x1={trough.x} y1={trough.y} x2={L.bracketX} y2={trough.y} strokeDasharray="10 10" strokeWidth={3} />
          </g>
        ) : null}
      </svg>
      <div style={{position: 'absolute', left: lerp(peak.x, trough.x, 0.5) - 200, width: 400, top: origin.y + 18, display: 'flex',
        justifyContent: 'center', ...enterRight(peakK, 30)}}>
        <Paper text={content.period.text} size={48} />
      </div>
      {labelK > 0 ? (
        <div style={{position: 'absolute', left: L.label.x - 300, width: 600, top: L.label.y - L.labelSize, display: 'flex',
          justifyContent: 'center', ...enterRight(labelK)}}>
          <Paper text={content.drop.text} size={L.labelSize} bg={MUSTARD} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
