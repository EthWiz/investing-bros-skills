import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {FONT, GOLD, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {Check, Cross} from './DoubleSpend';
import {Page, Piece, Rig, fanAngle, pageHeight, rigHeight} from './blocks';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: who writes the next page, as a simplified mining setup.
// A payment joins other transfers on a new page (the block); a row of mining rigs comes in and races
// on the puzzle (fans spin up, strips flicker, a power bolt); one solves it first and its piece flies
// into the page's slot; the other rigs check it (a tick each) and every rig gets a copy of the page;
// the payment is highlighted as the one that came first, and a second payment of the same coin is refused.
// content: block {label, at}, payment {label, at}, others {at}, miners {label, at}, puzzle {at},
//   winner {at, index?}, propose {at}, check {at}, accept {at}, second {label, at}, verdict {text, at};
//   optional: page {text, at} (the page metaphor), race {at}, work {text, at}, easy {text, at}, first {at}.
// Every word on screen comes from content. It lays itself out from the frame: 16:9 in the lesson
// (clear of his circle bottom right and the captions), 9:16 for a Short.

type P = {x: number; y: number};
type Layout = {page: P; pageW: number; rigs: P[]; rigW: number; label: P; pageLabel: P; head: {right: number; top: number};
  notes: [P, P]; second: P};

const WIDE: Layout = {
  page: {x: 940, y: 275}, pageW: 340, rigs: [{x: 1290, y: 715}, {x: 960, y: 715}, {x: 630, y: 715}, {x: 300, y: 715}], rigW: 250,
  label: {x: 1340, y: 140}, pageLabel: {x: 1340, y: 240}, head: {right: 1840, top: 60}, notes: [{x: 450, y: 190}, {x: 450, y: 300}],
  second: {x: 520, y: 300},
};
const TALL: Layout = {
  page: {x: 540, y: 460}, pageW: 360, rigs: [{x: 790, y: 1270}, {x: 290, y: 1270}, {x: 790, y: 1600}, {x: 290, y: 1600}], rigW: 300,
  label: {x: 540, y: 745}, pageLabel: {x: 540, y: 830}, head: {right: 1020, top: 120}, notes: [{x: 540, y: 935}, {x: 540, y: 1020}],
  second: {x: 880, y: 620},
};

const Label: React.FC<{p: P; text: string; at: number; size: number; bg?: string; out?: number}> = ({p, text, at, size, bg, out}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps);
  if (k <= 0) return null;
  return (
    <div style={{position: 'absolute', left: p.x - 300, top: p.y - size * 0.75, width: 600, opacity: out === undefined ? 1 : 1 - ease(t, out, out + 0.4)}}>
      <div style={{display: 'flex', justifyContent: 'center', ...enterRight(k, 40)}}>
        <Paper text={text} size={size} bg={bg} />
      </div>
    </div>
  );
};

export const Mining: React.FC<SceneProps> = ({start, end, content: c}) => {
  const {t, f, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const ph = pageHeight(L.pageW), rh = rigHeight(L.rigW);
  const wi = Math.min(L.rigs.length - 1, Math.max(0, c.winner.index ?? 1));
  const race = c.race?.at ?? c.miners.at + 0.6;
  const work = c.work?.at ?? race;
  const won = c.winner.at, propose = c.propose.at;

  // the race: fans spin up from the start of the race, harder from `work`, and stop after the winner
  const busy = (x: number) => ease(x, race, race + 0.6) * (1 - ease(x, won, won + 0.8));
  const speed = (x: number) => 0.25 + 1.2 * busy(x) + 1.4 * ease(x, work, work + 0.5) * (1 - ease(x, won, won + 0.8));
  const spin = fanAngle(t, start, fps, speed);
  const tick = Math.floor(f / 3);

  // the page and its slot for the winner's piece, at the page's corner on the rigs' side
  const slot = {x: L.page.x - L.pageW / 2 + 10, y: L.page.y + ph / 2 - 10};
  const winRig = L.rigs[wi];
  const fly = ease(t, propose, propose + 0.8);
  const pieceAt = {x: lerp(winRig.x, slot.x, fly), y: lerp(winRig.y - rh / 2, slot.y, fly) - Math.sin(fly * Math.PI) * 80};
  const sealed = fly >= 1;
  const glowPage = interpolate(t, [propose + 0.7, propose + 1.0, c.accept.at + 0.4, c.accept.at + 1.0], [0, 1, 1, 0], clamp);
  const rows = [
    {label: c.payment.label, k: pop(t, c.payment.at, fps), glow: c.first ? ease(t, c.first.at, c.first.at + 0.4) : 0},
    ...[0, 1, 2].map((i) => ({k: pop(t, c.others.at + i * 0.25, fps)})),
  ];
  const pageK = pop(t, start + 0.2, fps, 12, 170);
  const seal = 92;

  // the second payment of the same coin: comes in toward the page, stops, refused
  const secK = pop(t, c.second.at, fps, 12, 180);
  const secOut = 1 - 0.5 * ease(t, c.verdict.at + 1.2, c.verdict.at + 1.6);
  const secP = {x: lerp(L.second.x + 120, L.second.x, ease(t, c.second.at, c.second.at + 0.5)), y: L.second.y};

  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`mining-${start}`} />
      {/* rigs */}
      {L.rigs.map((r, i) => {
        const k = pop(t, c.miners.at + i * 0.12, fps, 12, 180);
        if (k <= 0) return null;
        const isWin = i === wi;
        const winK = isWin ? pop(t, won, fps, 10, 200) : 0;
        const checkK = !isWin ? pop(t, c.check.at + (i > wi ? i - 1 : i) * 0.15, fps, 10, 200) : 0;
        const copyK = ease(t, c.accept.at + i * 0.08, c.accept.at + 0.7 + i * 0.08);
        const copyP = {x: lerp(L.page.x, r.x + L.rigW * 0.32, copyK), y: lerp(L.page.y, r.y - rh / 2 - 34, copyK)};
        return (
          <React.Fragment key={i}>
            <div style={{position: 'absolute', left: r.x - L.rigW / 2, top: r.y - rh / 2, width: L.rigW, height: rh, ...enterRight(k, 40),
              filter: winK > 0 ? `drop-shadow(0 0 ${18 * winK}px ${GOLD})` : 'drop-shadow(0 10px 16px rgba(0,0,0,.45))'}}>
              <Rig w={L.rigW} spin={spin} busy={busy(t)} won={winK} tick={tick} id={i} />
              {/* while racing, each rig turns its own try of the piece */}
              {busy(t) > 0.05 && !(isWin && t >= propose) ? (
                <Piece size={L.rigW * 0.34} fill={isWin && winK > 0 ? HOOK_YELLOW : 'rgba(245,235,213,.9)'}
                  style={{position: 'absolute', left: L.rigW * 0.06, top: -L.rigW * 0.3, opacity: busy(t),
                    transform: `rotate(${winK > 0 ? 0 : ((tick * 47 + i * 90) % 360)}deg)`}} />
              ) : null}
              {checkK > 0 ? <div style={{position: 'absolute', left: L.rigW * 0.82, top: rh * 0.25}}><Check k={checkK} /></div> : null}
            </div>
            {copyK > 0 ? (
              <div style={{position: 'absolute', left: copyP.x - L.pageW * 0.13, top: copyP.y - pageHeight(L.pageW * 0.26) / 2}}>
                <Page w={L.pageW * 0.26} rows={rows.map((rw) => ({k: rw.k}))} />
              </div>
            ) : null}
          </React.Fragment>
        );
      })}
      {/* the check: a line from the page to each rig that checks it */}
      <svg width={width} height={height} style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
        {L.rigs.map((r, i) => {
          if (i === wi) return null;
          const k = ease(t, c.check.at + i * 0.1, c.check.at + 0.4 + i * 0.1) * (1 - ease(t, c.accept.at + 0.6, c.accept.at + 1.1));
          return k > 0 ? <line key={i} x1={L.page.x} y1={L.page.y + ph / 2} x2={lerp(L.page.x, r.x, k)} y2={lerp(L.page.y + ph / 2, r.y - rh / 2, k)}
            stroke={MUSTARD} strokeWidth={5} strokeDasharray="12 10" opacity={0.9} /> : null;
        })}
      </svg>
      {/* the new page */}
      {pageK > 0 ? (
        <div style={{position: 'absolute', left: L.page.x - L.pageW / 2, top: L.page.y - ph / 2, ...enterRight(pageK, 40)}}>
          <Page w={L.pageW} rows={rows} glow={glowPage} />
        </div>
      ) : null}
      {/* the puzzle: a slot on the page, filled by the winner's piece */}
      {t >= c.puzzle.at ? (
        <div style={{position: 'absolute', left: slot.x - seal / 2, top: slot.y - seal / 2, width: seal, height: seal, borderRadius: seal / 2,
          background: NAVY, border: `4px solid ${sealed ? GOLD : MUSTARD}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          transform: `scale(${pop(t, c.puzzle.at, fps, 10, 200)})`, boxShadow: '0 8px 14px rgba(0,0,0,.45)'}}>
          <Piece size={seal * 0.72} dashed={!sealed} />
        </div>
      ) : null}
      {t >= propose && !sealed ? (
        <Piece size={seal * 0.72} style={{position: 'absolute', left: pieceAt.x - seal * 0.36, top: pieceAt.y - seal * 0.36,
          filter: `drop-shadow(0 0 14px ${GOLD})`}} />
      ) : null}
      {/* words */}
      <Label p={L.label} text={c.block.label} at={c.block.at} size={56} bg={MUSTARD} />
      {c.page ? <Label p={L.pageLabel} text={c.page.text} at={c.page.at} size={40} /> : null}
      {pop(t, c.miners.at, fps) > 0 ? (
        <div style={{position: 'absolute', top: L.head.top, right: width - L.head.right, ...enterRight(pop(t, c.miners.at, fps))}}>
          <Paper text={c.miners.label} size={58} />
        </div>
      ) : null}
      {c.work ? <Label p={L.notes[0]} text={c.work.text} at={c.work.at} size={44} out={won} /> : null}
      {c.easy ? <Label p={L.notes[1]} text={c.easy.text} at={c.easy.at} size={44} bg={MUSTARD} out={won} /> : null}
      {secK > 0 ? (
        <div style={{position: 'absolute', left: secP.x - 110, top: secP.y - 36, width: 220, height: 72, borderRadius: 36, background: 'rgba(245,235,213,.95)',
          border: `4px solid ${NAVY}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14, direction: 'rtl', opacity: Math.min(secK, secOut),
          boxShadow: '0 8px 14px rgba(0,0,0,.45)'}}>
          <div style={{width: 38, height: 38, borderRadius: 19, background: HOOK_YELLOW, border: `4px solid ${NAVY}`}} />
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 42, color: NAVY}}><bdi dir="auto">{c.second.label}</bdi></div>
        </div>
      ) : null}
      <Cross p={{x: secP.x, y: secP.y + 115}} at={c.verdict.at} text={c.verdict.text} size={110} />
    </AbsoluteFill>
  );
};
