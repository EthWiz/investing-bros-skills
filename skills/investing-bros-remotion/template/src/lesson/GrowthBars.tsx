import React from 'react';
import {AbsoluteFill, interpolate, spring, useVideoConfig} from 'remotion';
import {CREAM, FONT, GOLD, HOOK_YELLOW, clamp} from '../brand';
import {NavyPaper, Paper, ease, enterRight, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: how much each asset grew, as bars on one linear scale, so one bar that
// grew a hundredfold dwarfs the ones that tripled. Bars sit right to left in the order Amitai names
// them (the first, on his side, in gold); each rises on its word and shows its multiple above it.
// content: heading? {text, at}, bars [{label, value, text, at, said? {at}}], highlight? {at} (the first bar glows).
// A bar rises on `at` (its name) and shows its multiple on `said` (when he says the number), else just after it rises.
// `value` sets the height (the multiple Amitai says); `text` and `label` are his words. It lays itself
// out from the frame: 16:9 in the lesson (left of his circle), 9:16 for a Short.

type Bar = {label: string; value: number; text: string; at: number; said?: {at: number}};
type Layout = {right: number; slot: number; barW: number; base: number; maxH: number; headY: number; headRight: number;
  textSize: number; firstTextSize: number; labelSize: number};

const WIDE: Layout = {right: 1410, slot: 320, barW: 200, base: 740, maxH: 450, headY: 70, headRight: 1440,
  textSize: 54, firstTextSize: 76, labelSize: 46};
const TALL: Layout = {right: 990, slot: 230, barW: 150, base: 1380, maxH: 820, headY: 230, headRight: 990,
  textSize: 46, firstTextSize: 64, labelSize: 40};

const MIN_H = 10;   // a bar that tripled next to one that grew 100x is still a visible sliver

export const GrowthBars: React.FC<SceneProps> = ({start, end, content}) => {
  const {t, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const bars: Bar[] = content.bars;
  const top = Math.max(...bars.map((b) => b.value));
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const glow = content.highlight ? interpolate(t, [content.highlight.at, content.highlight.at + 0.4], [0, 1], clamp) : 0;
  const axisW = (bars.length - 1) * L.slot + L.barW + 80;
  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`bars-${start}`} />
      {content.heading ? (
        <div style={{position: 'absolute', top: L.headY, right: width - L.headRight, ...enterRight(pop(t, content.heading.at, fps))}}>
          <Paper text={content.heading.text} size={58} />
        </div>
      ) : null}
      <div style={{position: 'absolute', left: L.right - axisW + 40, top: L.base, width: axisW, height: 4, background: CREAM, opacity: 0.45}} />
      {bars.map((b, i) => {
        const first = i === 0;
        // the big bar climbs slower, so the eye follows it up
        const grow = t < b.at ? 0 : spring({frame: Math.round((t - b.at) * fps), fps, config: {damping: 18, stiffness: first ? 40 : 120}});
        const h = Math.max(MIN_H, (b.value / top) * L.maxH) * grow;
        const cx = L.right - L.barW / 2 - i * L.slot;
        const textK = pop(t, b.said?.at ?? b.at + (first ? 0.9 : 0.3), fps);
        const nameK = pop(t, b.at, fps);
        // near the frame's right edge (9:16) the multiple aligns to the edge instead of running off it
        const edge = cx + 260 > width - 16;
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: cx - L.barW / 2, top: L.base - h, width: L.barW, height: h,
              borderRadius: '10px 10px 0 0', background: first ? GOLD : CREAM,
              boxShadow: first && glow > 0 ? `0 0 ${40 * glow}px ${12 * glow}px ${HOOK_YELLOW}` : '0 8px 16px rgba(0,0,0,.35)'}} />
            <div style={{position: 'absolute', left: edge ? width - 16 - 520 : cx - 260, width: 520, top: L.base - h - (first ? 110 : 84),
              display: 'flex', justifyContent: edge ? 'flex-end' : 'center', opacity: textK, transform: `translateY(${(1 - textK) * 24}px)`}}>
              <div style={{fontFamily: FONT, fontWeight: 900, fontSize: first ? L.firstTextSize : L.textSize, color: first ? GOLD : CREAM,
                direction: 'rtl', whiteSpace: 'nowrap', textShadow: '0 4px 10px rgba(0,0,0,.5)'}}><bdi dir="rtl">{b.text}</bdi></div>
            </div>
            <div style={{position: 'absolute', left: cx - 200, width: 400, top: L.base + 22, display: 'flex', justifyContent: 'center',
              opacity: nameK}}>
              <div style={{fontFamily: FONT, fontWeight: 800, fontSize: L.labelSize, color: CREAM, whiteSpace: 'nowrap', direction: 'rtl'}}>
                <bdi dir="auto">{b.label}</bdi>
              </div>
            </div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
