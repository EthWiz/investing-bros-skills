import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: double spending, as the problem and as the shared ledger's answer.
// One sender, two recipients, one coin; flows run right to left, from the sender on Amitai's side.
//  scenario 'copy':   the coin goes to the first recipient, is copied, and the copy goes to the second;
//                     both get it (a check each on `received`), then an X and the verdict.
//  scenario 'ledger': the bank's single ledger (`ledger`) splits into a copy for everyone (`split`);
//                     the first payment is written in every copy at once; the second payment stops
//                     halfway, every copy shows where the coin already is (`seen`), and it is refused.
// content: scenario, sender {label}, coin {label, at}, recipients [{label, at}, {label, at}],
//   payments [{at}, {at}], verdict {text, at}; copy: copy {at}, received? {at};
//   ledger: ledger {label, at}, split {at}, seen {at}. Every word on screen comes from content.
// It lays itself out from the frame: 16:9 in the lesson, 9:16 for a Short (the LessonScenes composition).

type P = {x: number; y: number};
type Layout = {sender: P; recipients: [P, P]; ledger: P; peers: P[]; cards: P[]; cross: P; node: number};

// cards: the ledger copies, in the order sender, recipients, peers
const WIDE: Layout = {
  sender: {x: 1560, y: 330}, recipients: [{x: 400, y: 230}, {x: 400, y: 640}], ledger: {x: 960, y: 250},
  peers: [{x: 1080, y: 720}, {x: 800, y: 430}],
  cards: [{x: 1330, y: 330}, {x: 630, y: 230}, {x: 630, y: 640}, {x: 1310, y: 720}, {x: 1030, y: 430}],
  cross: {x: 400, y: 435}, node: 150,
};
const TALL: Layout = {
  sender: {x: 540, y: 330}, recipients: [{x: 800, y: 1260}, {x: 280, y: 1260}], ledger: {x: 540, y: 720},
  peers: [{x: 200, y: 800}, {x: 880, y: 800}],
  cards: [{x: 800, y: 330}, {x: 800, y: 1480}, {x: 280, y: 1480}, {x: 200, y: 990}, {x: 880, y: 990}],
  cross: {x: 540, y: 1260}, node: 170,
};

const FLIGHT = 0.9;
const arc = (a: P, b: P, p: number): P => ({x: lerp(a.x, b.x, p), y: lerp(a.y, b.y, p) - Math.sin(p * Math.PI) * 60});

const Person: React.FC<{size: number}> = ({size}) => (
  <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 100 100">
    <circle cx="50" cy="32" r="18" fill={NAVY} />
    <path d="M18 92 C18 62 82 62 82 92 Z" fill={NAVY} />
  </svg>
);

const Node: React.FC<{p: P; size: number; label?: string; at: number; check?: number}> = ({p, size, label, at, check = 0}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 12, 180);
  if (k <= 0) return null;
  return (
    <div style={{position: 'absolute', left: p.x - 110, top: p.y - size / 2, width: 220, display: 'flex', flexDirection: 'column',
      alignItems: 'center', ...enterRight(k, 40)}}>
      <div style={{position: 'relative', width: size, height: size, borderRadius: size / 2, background: CREAM,
        display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 22px rgba(0,0,0,.45)',
        transform: `scale(${interpolate(k, [0, 1], [0.6, 1])})`}}>
        <Person size={size} />
        {check > 0 ? <Check k={check} /> : null}
      </div>
      {label ? <Paper text={label} size={40} style={{marginTop: 12}} /> : null}
    </div>
  );
};

const Check: React.FC<{k: number}> = ({k}) => (
  <svg width={64} height={64} viewBox="0 0 64 64" style={{position: 'absolute', top: -10, left: -10, transform: `scale(${k})`, opacity: k}}>
    <circle cx="32" cy="32" r="30" fill={HOOK_YELLOW} stroke={NAVY} strokeWidth="4" />
    <path d="M18 33 L28 43 L46 22" stroke={NAVY} strokeWidth="7" fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// the X of a refused or impossible payment, in the brand's hook yellow (the palette has no red)
const Cross: React.FC<{p: P; at: number; text?: string}> = ({p, at, text}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 9, 220);
  if (k <= 0) return null;
  return (
    <div style={{position: 'absolute', left: p.x - 160, top: p.y - 80, width: 320, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <svg width={160} height={160} viewBox="0 0 100 100" style={{transform: `scale(${k}) rotate(${(1 - k) * -25}deg)`,
        filter: 'drop-shadow(0 8px 14px rgba(0,0,0,.5))'}}>
        <path d="M18 18 L82 82 M82 18 L18 82" stroke={NAVY} strokeWidth="26" strokeLinecap="round" />
        <path d="M18 18 L82 82 M82 18 L18 82" stroke={HOOK_YELLOW} strokeWidth="16" strokeLinecap="round" />
      </svg>
      {text ? <Paper text={text} size={52} bg={MUSTARD} style={{marginTop: 10, opacity: interpolate(k, [0.3, 1], [0, 1], clamp)}} /> : null}
    </div>
  );
};

// the coin; `ghost` = the dashed outline a copy fills in
const Coin: React.FC<{p: P; label: string; k: number; ghost?: number; opacity?: number}> = ({p, label, k, ghost = 1, opacity = 1}) => (
  <div style={{position: 'absolute', left: p.x - 50, top: p.y - 50, width: 100, height: 100, borderRadius: 50,
    background: ghost >= 1 ? HOOK_YELLOW : `rgba(250,200,40,${ghost})`, border: `5px ${ghost >= 1 ? 'solid' : 'dashed'} ${NAVY}`,
    display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, fontWeight: 900, color: NAVY, whiteSpace: 'nowrap',
    fontSize: Math.min(32, Math.floor(120 / Math.max(1, label.length))),   // "100 ₪" wrapped and was cut off at 32
    transform: `scale(${k})`, opacity, boxShadow: ghost >= 1 ? '0 8px 16px rgba(0,0,0,.4)' : 'none'}}>
    <bdi dir="rtl" style={{opacity: ghost}}>{label}</bdi>
  </div>
);

// a ledger: a cream page with lines; `row` = the payment written in it, `glow` = the network checking it
const Ledger: React.FC<{p: P; scale: number; row?: string; rowK?: number; glow?: number; lock?: number; opacity?: number}> =
  ({p, scale, row, rowK = 0, glow = 0, lock = 0, opacity = 1}) => (
    <div style={{position: 'absolute', left: p.x - 90, top: p.y - 62, width: 180, height: 124, transform: `scale(${scale})`, opacity}}>
      <div style={{position: 'absolute', inset: 0, background: CREAM, borderRadius: 10, border: `4px solid ${NAVY}`,
        boxShadow: glow > 0 ? `0 0 0 ${8 * glow}px ${MUSTARD}, 0 8px 16px rgba(0,0,0,.4)` : '0 8px 16px rgba(0,0,0,.4)'}}>
        {[30, 58, 86].map((y) => <div key={y} style={{position: 'absolute', left: 18, right: 18, top: y, height: 4, background: NAVY, opacity: 0.25}} />)}
        {row && rowK > 0 ? (
          <div style={{position: 'absolute', right: 14, top: 14, display: 'flex', alignItems: 'center', gap: 10, direction: 'rtl',
            opacity: rowK, transform: `translateX(${(1 - rowK) * 20}px)`}}>
            <div style={{width: 30, height: 30, borderRadius: 15, background: HOOK_YELLOW, border: `3px solid ${NAVY}`}} />
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 34, color: NAVY}}>{row}</div>
          </div>
        ) : null}
      </div>
      {lock > 0 ? (
        <svg width={70} height={78} viewBox="0 0 70 78" style={{position: 'absolute', left: -26, top: -30, opacity: lock}}>
          <path d="M18 34 V22 a17 17 0 0 1 34 0 V34" stroke={NAVY} strokeWidth="9" fill="none" />
          <rect x="6" y="32" width="58" height="42" rx="8" fill={MUSTARD} stroke={NAVY} strokeWidth="4" />
        </svg>
      ) : null}
    </div>
  );

const flight = (t: number, at: number) => ease(t, at, at + FLIGHT);

const CopyScenario: React.FC<{c: SceneProps['content']; L: Layout}> = ({c, L}) => {
  const {t, fps} = useTime();
  const [r0, r1] = L.recipients;
  const [p0, p1] = [c.payments[0].at, c.payments[1].at];
  const received = c.received?.at ?? Infinity;
  const coinK = pop(t, c.coin.at, fps, 10, 200);
  const first = arc(L.sender, {x: r0.x, y: r0.y - L.node / 2 - 30}, flight(t, p0));
  const copyGhost = ease(t, c.copy.at, c.copy.at + 0.5);
  const second = arc(L.sender, {x: r1.x, y: r1.y - L.node / 2 - 30}, flight(t, p1));
  const startAt = {x: L.sender.x, y: L.sender.y - L.node / 2 - 30};
  return (
    <>
      <Node p={L.sender} size={L.node} label={c.sender.label} at={c.coin.at - 0.6} />
      <Node p={r0} size={L.node} label={c.recipients[0].label} at={c.recipients[0].at} check={pop(t, received, fps, 10, 200)} />
      <Node p={r1} size={L.node} label={c.recipients[1].label} at={c.recipients[1].at} check={pop(t, received + 0.25, fps, 10, 200)} />
      {t >= c.coin.at ? <Coin p={t < p0 ? startAt : first} label={c.coin.label} k={coinK} /> : null}
      {t >= c.copy.at ? (
        <Coin p={t < p1 ? startAt : second} label={c.coin.label} k={pop(t, c.copy.at, fps, 10, 200)} ghost={Math.max(0.15, copyGhost)} />
      ) : null}
      <Cross p={L.cross} at={c.verdict.at} text={c.verdict.text} />
    </>
  );
};

const LedgerScenario: React.FC<{c: SceneProps['content']; L: Layout; start: number}> = ({c, L, start}) => {
  const {t, fps} = useTime();
  const [r0, r1] = L.recipients;
  const holders = [L.sender, r0, r1, ...L.peers];
  const split = c.split.at, [p0, p1] = [c.payments[0].at, c.payments[1].at];
  const big = pop(t, c.ledger.at, fps, 12, 170);
  const unlock = 1 - ease(t, split, split + 0.3);
  const bigOut = 1 - ease(t, split + 0.5, split + 0.9);
  const written = ease(t, p0 + FLIGHT, p0 + FLIGHT + 0.3);
  const glow = interpolate(t, [c.seen.at, c.seen.at + 0.3, c.verdict.at + 0.6, c.verdict.at + 1.2], [0, 1, 1, 0.35], clamp);
  // the second payment: out halfway, held while the network checks, then back to the sender
  const out = 0.45 * ease(t, p1, p1 + 0.6);
  const back = ease(t, c.verdict.at + 0.3, c.verdict.at + 1.0);
  const stopAt = arc(L.sender, {x: r1.x, y: r1.y - L.node / 2 - 30}, 0.45);
  const startAt = {x: L.sender.x, y: L.sender.y - L.node / 2 - 30};
  const secondP = t < c.verdict.at + 0.3 ? arc(L.sender, {x: r1.x, y: r1.y - L.node / 2 - 30}, out)
    : {x: lerp(stopAt.x, startAt.x, back), y: lerp(stopAt.y, startAt.y, back)};
  return (
    <>
      <Node p={L.sender} size={L.node} label={c.sender.label} at={start + 0.3} />
      <Node p={r0} size={L.node} label={c.recipients[0].label} at={c.recipients[0].at} />
      <Node p={r1} size={L.node} label={c.recipients[1].label} at={c.recipients[1].at} />
      {L.peers.map((p, i) => <Node key={i} p={p} size={L.node * 0.8} at={split + 0.2 + i * 0.1} />)}
      {bigOut > 0 && big > 0 ? (
        <div style={{position: 'absolute', left: L.ledger.x - 160, top: L.ledger.y - 100, width: 320, display: 'flex', flexDirection: 'column',
          alignItems: 'center', opacity: bigOut, ...enterRight(big, 40)}}>
          <Ledger p={{x: 160, y: 62}} scale={1.5 * big} lock={unlock} />
          <Paper text={c.ledger.label} size={42} bg={MUSTARD} style={{marginTop: 175}} />
        </div>
      ) : null}
      {holders.map((h, i) => {
        const go = ease(t, split + 0.15 + i * 0.08, split + 0.95 + i * 0.08);
        if (go <= 0) return null;
        const card = L.cards[i];
        const p = {x: lerp(L.ledger.x, card.x, go), y: lerp(L.ledger.y, card.y, go)};
        return <Ledger key={i} p={p} scale={lerp(1.2, 0.72, go)} row={c.recipients[0].label} rowK={written} glow={glow} />;
      })}
      {t >= c.coin.at ? (
        <Coin p={t < p0 ? startAt : arc(L.sender, {x: r0.x, y: r0.y - L.node / 2 - 30}, flight(t, p0))} label={c.coin.label}
          k={pop(t, c.coin.at, fps, 10, 200)} />
      ) : null}
      {t >= p1 - 0.4 ? (
        <Coin p={t < p1 ? startAt : secondP} label={c.coin.label} k={pop(t, p1 - 0.4, fps, 10, 200)}
          opacity={1 - ease(t, c.verdict.at + 0.9, c.verdict.at + 1.3)} />
      ) : null}
      <Cross p={stopAt} at={c.verdict.at} text={c.verdict.text} />
    </>
  );
};

export const SCENARIOS = ['copy', 'ledger'] as const;

export const DoubleSpend: React.FC<SceneProps> = ({start, end, content}) => {
  const {t} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`double-${start}`} />
      {content.scenario === 'ledger' ? <LedgerScenario c={content} L={L} start={start} /> : <CopyScenario c={content} L={L} />}
    </AbsoluteFill>
  );
};
