import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {CREAM, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {Check, Cross} from './DoubleSpend';
import {Page, Print, Rig, pageHeight, rigHeight} from './blocks';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: the chain, and what happens when someone changes an old page.
// Pages (blocks) come in one after another, oldest on the right (Amitai's side), newest on the left.
// Each page gets its fingerprint, and the next page carries a copy of it: a link joins the two.
// Then someone erases a payment from an old page: its fingerprint changes, it no longer matches the
// copy in the next page, and that link breaks. The network's computers, each with its own copy of
// the chain, see that the changed chain doesn't match theirs (an X on it); their chains keep growing,
// a new page on all of them at once, and the word for that agreement comes in.
// content: blocks {at}, prints {at}, name {text, at}, tamper {row, at, index?}, changed {at}, broken {at},
//   network {at}, consensus {text, at}; optional: heading {text, at}, chain {at}, erase {at},
//   link {at}, detect {at}, grow {at}. Every word on screen comes from content.
// It lays itself out from the frame: 16:9 in the lesson (clear of his circle and the captions), 9:16 for a Short.

type P = {x: number; y: number};
type Layout = {blocks: P[]; bw: number; badge: number; name: P; peers: P[]; rigW: number; mini: number; consensus: P;
  shift: {dy: number; scale: number}; head: {right: number; top: number}};

const WIDE: Layout = {
  blocks: [{x: 1600, y: 290}, {x: 1160, y: 290}, {x: 720, y: 290}, {x: 280, y: 290}], bw: 300, badge: 80, name: {x: 940, y: 580},
  peers: [{x: 1300, y: 775}, {x: 960, y: 775}, {x: 620, y: 775}, {x: 280, y: 775}], rigW: 170, mini: 46, consensus: {x: 940, y: 470},
  shift: {dy: -70, scale: 0.8}, head: {right: 1840, top: 40},
};
const TALL: Layout = {
  blocks: [{x: 915, y: 560}, {x: 665, y: 560}, {x: 415, y: 560}, {x: 165, y: 560}], bw: 200, badge: 56, name: {x: 540, y: 830},
  peers: [{x: 790, y: 1230}, {x: 290, y: 1230}, {x: 790, y: 1560}, {x: 290, y: 1560}], rigW: 240, mini: 50, consensus: {x: 540, y: 880},
  shift: {dy: -60, scale: 0.92}, head: {right: 1020, top: 160},
};

// the link between a page's fingerprint and its copy in the next page; `broken` pulls it apart
const Link: React.FC<{a: P; b: P; k: number; broken: number; hot: number}> = ({a, b, k, broken, hot}) => {
  if (k <= 0) return null;
  const mid = {x: (a.x + b.x) / 2, y: (a.y + b.y) / 2};
  const half = Math.abs(a.x - b.x) / 2;
  const w = half * 0.7, h = w * 0.5, gap = broken * 34;
  const color = broken > 0 || hot > 0 ? HOOK_YELLOW : CREAM;
  return (
    <g opacity={k} transform={`translate(${mid.x} ${mid.y}) scale(${interpolate(k, [0, 1], [0.6, 1])})`}>
      <rect x={-w * 0.85 - gap} y={-h / 2} width={w} height={h} rx={h / 2} fill="none" stroke={color} strokeWidth={9}
        transform={`rotate(${-broken * 24} ${-w * 0.35 - gap} 0)`} />
      <rect x={-w * 0.15 + gap} y={-h / 2} width={w} height={h} rx={h / 2} fill="none" stroke={color} strokeWidth={9}
        transform={`rotate(${broken * 24} ${w * 0.35 + gap} 0)`} />
      {broken > 0 ? (
        <path d={`M-10 ${-h * 1.3} L10 ${-h * 0.4} L-10 ${h * 0.3} L10 ${h * 1.3}`} stroke={HOOK_YELLOW} strokeWidth={7} fill="none" opacity={broken}
          strokeLinecap="round" strokeLinejoin="round" />
      ) : null}
    </g>
  );
};

// a print that flips over to a new one at `p` (0..1)
const FlipPrint: React.FC<{c: P; size: number; seed: number; next: number; p: number; k: number}> = ({c, size, seed, next, p, k}) => {
  if (k <= 0) return null;
  const sx = Math.max(0.05, Math.abs(Math.cos(p * Math.PI)));
  return (
    <div style={{position: 'absolute', left: c.x - size / 2, top: c.y - size / 2, width: size, height: size,
      transform: `scale(${k}) scaleX(${sx})`, filter: 'drop-shadow(0 6px 10px rgba(0,0,0,.45))'}}>
      <Print size={size} seed={p > 0.5 ? next : seed} ring={p > 0.5 ? 1 : 0} />
    </div>
  );
};

export const Chain: React.FC<SceneProps> = ({start, end, content: c}) => {
  const {t, f, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const n = L.blocks.length, bh = pageHeight(L.bw), b2 = L.badge;
  const ti = Math.min(n - 2, Math.max(0, c.tamper.index ?? 1));
  const chainAt = c.chain?.at ?? c.prints.at + 0.8;
  const eraseAt = c.erase?.at ?? c.tamper.at + 1.2;
  const linkAt = c.link?.at ?? c.broken.at - 0.6;
  const detectAt = c.detect?.at ?? c.network.at + 2.5;
  const growAt = c.grow?.at ?? c.consensus.at - 1.5;

  const wipe = ease(t, eraseAt, eraseAt + 1.0);
  const flip = ease(t, c.changed.at, c.changed.at + 0.5);
  const broken = ease(t, c.broken.at, c.broken.at + 0.35);
  const hot = interpolate(t, [linkAt, linkAt + 0.2], [0, 1], clamp);
  const net = ease(t, c.network.at, c.network.at + 0.8);
  const dim = ease(t, detectAt, detectAt + 0.5);

  // fingerprints, inside the page at its edges: a page's own on the left (toward the newer page), its copy
  // on the next page's right; the rows sit between them
  const edge = b2 / 2 + L.bw * 0.03;
  const own = (i: number) => ({x: L.blocks[i].x - L.bw / 2 + edge, y: L.blocks[i].y + bh * 0.08});
  const copy = (i: number) => ({x: L.blocks[i + 1].x + L.bw / 2 - edge, y: L.blocks[i].y + bh * 0.08});

  // the eraser, over the first row of the changed page
  const tb = L.blocks[ti];
  const rowY = tb.y - bh / 2 + bh * 0.2 + bh * 0.19 * 0.4;
  const pad = L.bw * 0.3;
  const eraserK = pop(t, c.tamper.at, fps, 12, 180) * (1 - ease(t, eraseAt + 1.2, eraseAt + 1.6));
  const eraserX = lerp(tb.x + L.bw / 2 - pad, tb.x - L.bw / 2 + pad, wipe);

  const origin = {x: (L.blocks[0].x + L.blocks[n - 1].x) / 2, y: L.blocks[0].y};
  const chainStyle: React.CSSProperties = {position: 'absolute', inset: 0,
    transformOrigin: `${origin.x}px ${origin.y}px`,
    transform: `translateY(${L.shift.dy * net}px) scale(${lerp(1, L.shift.scale, net)})`};

  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`chain-${start}`} />
      {c.heading ? (
        <div style={{position: 'absolute', top: L.head.top, right: width - L.head.right, ...enterRight(pop(t, c.heading.at, fps))}}>
          <Paper text={c.heading.text} size={56} />
        </div>
      ) : null}
      <div style={chainStyle}>
        <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
          {L.blocks.slice(0, -1).map((_, i) => (
            <Link key={i} a={own(i)} b={copy(i)} k={ease(t, chainAt + i * 0.2, chainAt + 0.4 + i * 0.2)}
              broken={i === ti ? broken : 0} hot={i === ti ? hot : 0} />
          ))}
        </svg>
        {L.blocks.map((b, i) => {
          const k = pop(t, c.blocks.at + i * 0.3, fps, 12, 170);
          if (k <= 0) return null;
          const rows = [0, 1, 2].map((r) => ({label: i === ti && r === 0 ? c.tamper.row : undefined, k: 1, wipe: i === ti && r === 0 ? wipe : 0}));
          return (
            <div key={i} style={{position: 'absolute', left: b.x - L.bw / 2, top: b.y - bh / 2, ...enterRight(k, 50)}}>
              <Page w={L.bw} rows={rows} inset={0.3} dim={dim} glow={i === ti ? interpolate(t, [c.changed.at, c.changed.at + 0.3], [0, 0.8], clamp) : 0} />
            </div>
          );
        })}
        {L.blocks.map((_, i) => {
          const k = pop(t, c.prints.at + i * 0.15, fps, 11, 190);
          return (
            <React.Fragment key={i}>
              <FlipPrint c={own(i)} size={b2} seed={i + 3} next={i + 103} p={i === ti ? flip : 0} k={k} />
              {i < n - 1 ? <FlipPrint c={copy(i)} size={b2} seed={i + 3} next={i + 3} p={0} k={pop(t, chainAt + i * 0.2, fps, 11, 190)} /> : null}
            </React.Fragment>
          );
        })}
        {eraserK > 0 ? (
          <div style={{position: 'absolute', left: eraserX - L.bw * 0.14, top: rowY - L.bw * 0.2, width: L.bw * 0.3, height: L.bw * 0.17,
            borderRadius: 8, background: MUSTARD, border: `4px solid ${NAVY}`, transform: `rotate(-14deg) scale(${eraserK})`,
            boxShadow: '0 8px 14px rgba(0,0,0,.45)'}}>
            <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: '35%', background: CREAM, borderRadius: '4px 0 0 4px'}} />
          </div>
        ) : null}
      </div>
      {/* the chain's name, under it until the network comes in */}
      <div style={{position: 'absolute', left: L.name.x - 400, top: L.name.y - 50, width: 800, opacity: 1 - ease(t, c.tamper.at - 0.4, c.tamper.at)}}>
        <div style={{display: 'flex', justifyContent: 'center', ...enterRight(pop(t, c.name.at, fps))}}>
          <Paper text={c.name.text} size={64} bg={MUSTARD} />
        </div>
      </div>
      {/* the network: computers, each with its own copy of the chain, which keeps growing */}
      {L.peers.map((p, i) => {
        const k = pop(t, c.network.at + 0.2 + i * 0.12, fps, 12, 180);
        if (k <= 0) return null;
        const rh = rigHeight(L.rigW), m = L.mini, step = m * 1.3;
        const grown = pop(t, growAt + i * 0.08, fps, 11, 190);
        const x0 = p.x + step * 1.5;   // the oldest copy on the right
        return (
          <div key={i} style={{position: 'absolute', inset: 0, ...enterRight(k, 40)}}>
            {[0, 1, 2, 3, 4].map((j) => {
              const kk = j < 4 ? 1 : grown;
              if (kk <= 0) return null;
              return (
                <div key={j} style={{position: 'absolute', left: x0 - j * step - m / 2, top: p.y - rh / 2 - pageHeight(m) - 16,
                  transform: `scale(${kk})`}}>
                  <Page w={m} rows={[]} glow={j === 4 ? 1 - ease(t, growAt + 0.8, growAt + 1.6) : 0} />
                </div>
              );
            })}
            <div style={{position: 'absolute', left: p.x - L.rigW / 2, top: p.y - rh / 2, filter: 'drop-shadow(0 8px 14px rgba(0,0,0,.45))'}}>
              <Rig w={L.rigW} spin={(t - start) * 110} busy={0} tick={Math.floor(f / 3)} id={i} />
              {grown > 0 ? <div style={{position: 'absolute', left: L.rigW * 0.8, top: rh * 0.3}}><Check k={grown} size={52} /></div> : null}
            </div>
          </div>
        );
      })}
      <Cross p={{x: origin.x + (tb.x - origin.x) * L.shift.scale, y: origin.y + L.shift.dy}} at={detectAt} size={150} />
      <div style={{position: 'absolute', left: L.consensus.x - 400, top: L.consensus.y - 50, width: 800, display: 'flex', justifyContent: 'center',
        ...enterRight(pop(t, c.consensus.at, fps))}}>
        <Paper text={c.consensus.text} size={64} bg={MUSTARD} />
      </div>
    </AbsoluteFill>
  );
};
