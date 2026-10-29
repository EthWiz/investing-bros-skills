import React from 'react';
import {interpolate} from 'remotion';
import {CREAM, FONT, GOLD, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';

// Shared drawings for the blockchain scenes (mining, chain): a block as a page of the ledger, its
// fingerprint, a mining rig and the puzzle piece. No words: labels come from the scene's content.

// one payment on a page: k = how far it has come in, wipe = how much of it has been erased,
// glow = highlighted. A row with a label shows the recipient's name; other transfers are a bar.
export type Row = {label?: string; k: number; wipe?: number; glow?: number};

export const pageHeight = (w: number) => w * 1.15;

// inset = the rows' margin each side, as a share of the width (wider when fingerprints sit at the edges)
export const Page: React.FC<{w: number; rows: Row[]; glow?: number; dim?: number; inset?: number; style?: React.CSSProperties; children?: React.ReactNode}> =
  ({w, rows, glow = 0, dim = 0, inset = 0.09, style, children}) => {
    const h = pageHeight(w), pad = w * inset, rh = h * 0.19, coin = rh * 0.5;
    return (
      <div style={{position: 'relative', width: w, height: h, ...style}}>
        <div style={{position: 'absolute', inset: 0, background: CREAM, borderRadius: w * 0.05, border: `${Math.max(3, w * 0.016)}px solid ${NAVY}`,
          boxShadow: glow > 0 ? `0 0 0 ${w * 0.04 * glow}px ${MUSTARD}, 0 10px 20px rgba(0,0,0,.45)` : '0 10px 20px rgba(0,0,0,.45)'}} />
        <div style={{position: 'absolute', left: w * 0.09, right: w * 0.09, top: h * 0.07, height: h * 0.055, borderRadius: 4, background: NAVY, opacity: 0.8}} />
        {rows.map((r, i) => {
          if (r.k <= 0) return null;
          const wipe = r.wipe ?? 0;
          return (
            <div key={i} style={{position: 'absolute', left: pad, right: pad, top: h * 0.2 + i * rh, height: rh * 0.8, opacity: Math.min(1, r.k)}}>
              {r.glow ? <div style={{position: 'absolute', inset: -4, borderRadius: 8, background: MUSTARD, opacity: 0.55 * r.glow}} /> : null}
              {/* what is left of the row; erased from the right, the way it reads */}
              <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', gap: w * 0.05, direction: 'rtl',
                clipPath: `inset(-6px ${wipe * 100}% -6px -6px)`, transform: `translateX(${(1 - Math.min(1, r.k)) * 18}px)`}}>
                <div style={{width: coin, height: coin, flex: 'none', borderRadius: coin / 2, background: HOOK_YELLOW, border: `${Math.max(2, coin * 0.1)}px solid ${NAVY}`}} />
                {r.label ? (
                  <div style={{fontFamily: FONT, fontWeight: 900, fontSize: rh * 0.52, color: NAVY, whiteSpace: 'nowrap'}}><bdi dir="auto">{r.label}</bdi></div>
                ) : <div style={{flex: 1, height: rh * 0.18, borderRadius: 4, background: NAVY, opacity: 0.25}} />}
              </div>
              {wipe > 0 && wipe < 1 ? <div style={{position: 'absolute', top: -6, bottom: -6, right: `${wipe * 100}%`, width: 3, background: MUSTARD}} /> : null}
            </div>
          );
        })}
        {dim > 0 ? <div style={{position: 'absolute', inset: 0, borderRadius: w * 0.05, background: NAVY, opacity: 0.55 * dim}} /> : null}
        {children}
      </div>
    );
  };

// A fingerprint: nested arcs whose gaps and tilt come from `seed`, so a different seed is visibly a
// different print. Cream on navy by default; `ring` = the mustard ring of a print that changed.
const rnd = (seed: number, i: number) => (((seed * 9301 + i * 49297 + 233) % 233280) + 233280) % 233280 / 233280;
const arcPath = (cx: number, cy: number, rx: number, ry: number, a0: number, a1: number) => {
  const p = (a: number) => `${(cx + rx * Math.cos(a)).toFixed(2)} ${(cy + ry * Math.sin(a)).toFixed(2)}`;
  return `M${p(a0)} A${rx} ${ry} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${p(a1)}`;
};

export const Print: React.FC<{size: number; seed: number; ring?: number; style?: React.CSSProperties}> = ({size, seed, ring = 0, style}) => {
  const tilt = (rnd(seed, 99) - 0.5) * 50;
  const arcs: string[] = [];
  for (let i = 0; i < 5; i++) {
    const r = 8 + i * 7.5, gap = 0.5 + rnd(seed, i) * 1.4, at = rnd(seed, i + 10) * Math.PI * 2;
    arcs.push(arcPath(50, 52, r * 0.78, r, at + gap / 2, at + Math.PI * 2 - gap / 2));
  }
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" style={style}>
      <circle cx="50" cy="50" r="47" fill={NAVY} stroke={ring > 0 ? MUSTARD : CREAM} strokeWidth={4 + 4 * ring} />
      <g transform={`rotate(${tilt} 50 52)`} stroke={ring > 0 ? HOOK_YELLOW : CREAM} strokeWidth="4.2" fill="none" strokeLinecap="round">
        {arcs.map((d, i) => <path key={i} d={d} />)}
      </g>
    </svg>
  );
};

// A jigsaw piece: the puzzle a miner solves.
export const PIECE = 'M20 32 H40 a10 10 0 1 1 20 0 H80 V52 a10 10 0 1 1 0 20 V88 H20 Z';
export const Piece: React.FC<{size: number; fill?: string; dashed?: boolean; style?: React.CSSProperties}> = ({size, fill = HOOK_YELLOW, dashed, style}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={style}>
    <path d={PIECE} fill={dashed ? 'none' : fill} stroke={dashed ? CREAM : NAVY} strokeWidth={dashed ? 4 : 5}
      strokeDasharray={dashed ? '8 7' : undefined} strokeLinejoin="round" />
  </svg>
);

// A simplified mining rig: a cream case with two fans and an activity strip. spin = fan angle in
// degrees, busy = 0..1 how hard it is working (the strip flickers, a bolt shows), won = its strip
// turns gold. `tick` drives the flicker so every rig flickers differently.
export const rigHeight = (w: number) => w * 0.85;

export const Rig: React.FC<{w: number; spin: number; busy: number; won?: number; tick: number; id: number}> = ({w, spin, busy, won = 0, tick, id}) => {
  const fan = (cx: number) => (
    <g transform={`translate(${cx} 108)`}>
      <circle r="36" fill={NAVY} />
      <g transform={`rotate(${spin + id * 37})`} fill={CREAM} opacity={0.9}>
        {[0, 72, 144, 216, 288].map((a) => <ellipse key={a} cx="0" cy="-17" rx="8" ry="16" transform={`rotate(${a})`} />)}
      </g>
      <circle r="8" fill={MUSTARD} />
    </g>
  );
  const cells = Array.from({length: 8}, (_, i) => {
    const lit = won > 0 ? won : busy * (rnd(tick + id * 131, i) > 0.5 ? 1 : 0.15);
    return <rect key={i} x={28 + i * 18.5} y="54" width="13" height="14" rx="2" fill={won > 0 ? GOLD : CREAM} opacity={0.2 + 0.8 * lit} />;
  });
  return (
    <svg width={w} height={rigHeight(w)} viewBox="0 0 200 170" style={{overflow: 'visible'}}>
      <rect x="8" y="38" width="184" height="126" rx="14" fill={CREAM} stroke={NAVY} strokeWidth="5" />
      <rect x="20" y="48" width="160" height="26" rx="5" fill={NAVY} />
      {cells}
      {fan(62)}
      {fan(138)}
      {/* power: the bolt shows while it works hard */}
      <path d="M104 2 L86 24 H100 L92 40 L116 14 H102 Z" fill={HOOK_YELLOW} stroke={NAVY} strokeWidth="3" strokeLinejoin="round"
        opacity={interpolate(busy, [0.4, 1], [0, 1], clamp)} />
    </svg>
  );
};

// Fan angle at time t for a rig whose speed (turns a second) follows `speed(t)`: summed frame by
// frame from the scene's start, so a change of speed never makes the fans jump.
export const fanAngle = (t: number, from: number, fps: number, speed: (t: number) => number) => {
  let a = 0;
  for (let x = from; x < t; x += 1 / fps) a += (360 * speed(x)) / fps;
  return a;
};
