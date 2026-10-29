import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {Chip, Page, pageHeight} from './blocks';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: the trap in a shared ledger. Two computers hear about two payments of the
// same coin in a different order: the first writes one payment first and refuses the other, the
// second does the opposite, so their ledgers no longer match (a ≠ between them). Then the question
// the network has to agree on, and, as the way out, a short chain of blocks with its name.
// content: a {at}, b {at} (each computer comes in), first {label, at} (what computer a hears first),
//   second {label, at} (what computer b hears first), differ {at} (the ledgers part), agree {text, at};
//   optional: heading {text, at}, blocks {at}, name {text, at}. Every word on screen comes from content.
// It lays itself out from the frame: 16:9 in the lesson (clear of his circle and the captions), 9:16 for a Short.

type P = {x: number; y: number};
type Layout = {a: P; b: P; w: number; source: P; neq: P; neqSize: number; agree: P; chain: P; mini: number; name: P;
  head: {right: number; top: number}};

const WIDE: Layout = {
  a: {x: 1180, y: 330}, b: {x: 480, y: 330}, w: 520, source: {x: 830, y: 30}, neq: {x: 830, y: 330}, neqSize: 140,
  agree: {x: 830, y: 690}, chain: {x: 830, y: 690}, mini: 120, name: {x: 830, y: 840}, head: {right: 1840, top: 60},
};
const TALL: Layout = {
  a: {x: 785, y: 560}, b: {x: 295, y: 560}, w: 410, source: {x: 540, y: 200}, neq: {x: 540, y: 930}, neqSize: 150,
  agree: {x: 540, y: 1130}, chain: {x: 540, y: 1330}, mini: 110, name: {x: 540, y: 1520}, head: {right: 1020, top: 60},
};

const FLY = 0.8;

// a monitor showing its ledger page
const Computer: React.FC<{p: P; w: number; k: number; rows: React.ComponentProps<typeof Page>['rows']; glow: number}> = ({p, w, k, rows, glow}) => {
  if (k <= 0) return null;
  const h = w * 0.72, pw = w * 0.54;
  return (
    <div style={{position: 'absolute', left: p.x - w / 2, top: p.y - h / 2, width: w, height: h + w * 0.16, ...enterRight(k, 50)}}>
      <div style={{position: 'absolute', left: 0, top: 0, width: w, height: h, borderRadius: 18, background: '#163A5C',
        border: `8px solid ${CREAM}`, boxShadow: glow > 0 ? `0 0 0 ${10 * glow}px ${MUSTARD}, 0 14px 24px rgba(0,0,0,.5)` : '0 14px 24px rgba(0,0,0,.5)',
        display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Page w={pw} rows={rows} />
      </div>
      <div style={{position: 'absolute', left: w * 0.42, top: h, width: w * 0.16, height: w * 0.1, background: CREAM}} />
      <div style={{position: 'absolute', left: w * 0.3, top: h + w * 0.1, width: w * 0.4, height: w * 0.05, borderRadius: 8, background: CREAM}} />
    </div>
  );
};

export const Conflict: React.FC<SceneProps> = ({start, end, content: c}) => {
  const {t, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const ph = pageHeight(L.w * 0.54);
  const rowAt = (p: P, i: number) => ({x: p.x, y: p.y - ph / 2 + ph * 0.2 + i * ph * 0.19 + ph * 0.076});

  // each computer writes what it heard first, then the other payment, refused
  const d = c.differ.at;
  const aRows = [{label: c.first.label, k: ease(t, c.first.at + FLY - 0.1, c.first.at + FLY + 0.2)},
    {label: c.second.label, k: ease(t, d, d + 0.3), strike: ease(t, d + 0.5, d + 0.9)}];
  const bRows = [{label: c.second.label, k: ease(t, c.second.at + FLY - 0.1, c.second.at + FLY + 0.2)},
    {label: c.first.label, k: ease(t, d, d + 0.3), strike: ease(t, d + 0.5, d + 0.9)}];
  const glow = interpolate(t, [d + 0.6, d + 1.0], [0, 1], clamp);

  const fly = (label: string, at: number, to: P) => {
    const k = ease(t, at, at + FLY);
    if (t < at || k >= 1) return null;
    const p = {x: lerp(L.source.x, to.x, k), y: lerp(L.source.y, to.y, k) - Math.sin(k * Math.PI) * 50};
    return <Chip key={label + at} p={p} label={label} k={pop(t, at, fps, 12, 180)} />;
  };

  const neqK = pop(t, d + 0.6, fps, 9, 200);
  const blocksAt = c.blocks?.at;
  const agreeOut = blocksAt === undefined ? 1 : 1 - ease(t, blocksAt - 0.3, blocksAt);
  const m = L.mini, mh = pageHeight(m), step = m * 1.6;

  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`conflict-${start}`} />
      {c.heading ? (
        <div style={{position: 'absolute', top: L.head.top, right: width - L.head.right, ...enterRight(pop(t, c.heading.at, fps))}}>
          <Paper text={c.heading.text} size={58} bg={MUSTARD} />
        </div>
      ) : null}
      <Computer p={L.a} w={L.w} k={pop(t, c.a.at, fps, 12, 170)} rows={aRows} glow={glow} />
      <Computer p={L.b} w={L.w} k={pop(t, c.b.at, fps, 12, 170)} rows={bRows} glow={glow} />
      {fly(c.first.label, c.first.at, rowAt(L.a, 0))}
      {fly(c.second.label, c.second.at, rowAt(L.b, 0))}
      {neqK > 0 ? (
        <div style={{position: 'absolute', left: L.neq.x - L.neqSize / 2, top: L.neq.y - L.neqSize / 2, width: L.neqSize, height: L.neqSize,
          borderRadius: L.neqSize / 2, background: HOOK_YELLOW, border: `6px solid ${NAVY}`, display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontFamily: FONT, fontWeight: 900, fontSize: L.neqSize * 0.7, color: NAVY, lineHeight: 1,
          transform: `scale(${neqK})`, opacity: 1 - 0.6 * (1 - agreeOut), boxShadow: '0 10px 18px rgba(0,0,0,.5)'}}>≠</div>
      ) : null}
      <div style={{position: 'absolute', left: L.agree.x - 450, top: L.agree.y - 45, width: 900, opacity: agreeOut}}>
        <div style={{display: 'flex', justifyContent: 'center', ...enterRight(pop(t, c.agree.at, fps))}}>
          <Paper text={c.agree.text} size={60} />
        </div>
      </div>
      {/* the way out: a short chain of blocks */}
      {blocksAt !== undefined ? (
        <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
          {[0, 1].map((i) => {
            const k = ease(t, blocksAt + 0.5 + i * 0.2, blocksAt + 0.8 + i * 0.2);
            const x = L.chain.x + step - i * step - step / 2;
            return k > 0 ? <line key={i} x1={x - m * 0.2} y1={L.chain.y} x2={x - m * 0.2 - (step - m * 0.6) * k} y2={L.chain.y}
              stroke={CREAM} strokeWidth={8} strokeLinecap="round" /> : null;
          })}
        </svg>
      ) : null}
      {blocksAt !== undefined ? [0, 1, 2].map((i) => {
        const k = pop(t, blocksAt + i * 0.25, fps, 12, 180);
        if (k <= 0) return null;
        return (
          <div key={i} style={{position: 'absolute', left: L.chain.x + step - i * step - m / 2, top: L.chain.y - mh / 2, transform: `scale(${k})`}}>
            <Page w={m} rows={[{k: 1}, {k: 1}, {k: 1}]} />
          </div>
        );
      }) : null}
      {c.name ? (
        <div style={{position: 'absolute', left: L.name.x - 400, top: L.name.y - 45, width: 800, display: 'flex', justifyContent: 'center',
          ...enterRight(pop(t, c.name.at, fps))}}>
          <Paper text={c.name.text} size={60} bg={MUSTARD} />
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
