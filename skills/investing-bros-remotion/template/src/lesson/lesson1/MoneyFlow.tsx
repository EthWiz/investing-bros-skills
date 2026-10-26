import React from 'react';
import {AbsoluteFill, interpolate} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../../brand';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from '../kit';
import type {SceneProps} from '../types';

// Lesson 1, beat 4: a hundred shekels go from you to a friend, right to left, through your bank, the
// system in the middle and his bank; the central bank sits above them all. Then the three
// things this means, and the stations in the middle grey out.
// Every element starts on the word that names it (`at` keys from the props).

const Y = 420;
const NODES = {
  you: {x: 1640, y: Y, label: 'אתם'},
  myBank: {x: 1295, y: Y, label: 'הבנק שלכם'},
  middle: {x: 960, y: Y, label: 'מערכת שמאשרת'},
  hisBank: {x: 625, y: Y, label: 'הבנק שלו'},
  friend: {x: 280, y: Y, label: 'החבר'},
  central: {x: 960, y: 105, label: 'בנק מרכזי'},
} as const;
type NodeKey = keyof typeof NODES;
const PATH: NodeKey[] = ['you', 'myBank', 'middle', 'hisBank', 'friend'];
const MIDDLE: NodeKey[] = ['myBank', 'middle', 'hisBank', 'central'];

const Person: React.FC = () => (
  <svg width={110} height={110} viewBox="0 0 100 100">
    <circle cx="50" cy="32" r="18" fill={NAVY} />
    <path d="M18 92 C18 62 82 62 82 92 Z" fill={NAVY} />
  </svg>
);
const Bank: React.FC<{big?: boolean}> = ({big}) => (
  <svg width={110} height={110} viewBox="0 0 100 100">
    <polygon points="8,34 50,10 92,34" fill={NAVY} />
    {[18, 36, 54, 72].map((x) => <rect key={x} x={x} y={40} width={10} height={38} fill={NAVY} />)}
    <rect x="8" y="80" width="84" height="10" fill={NAVY} />
    {big ? <circle cx="50" cy="26" r="6" fill={HOOK_YELLOW} /> : null}
  </svg>
);
const Gear: React.FC = () => (
  <svg width={110} height={110} viewBox="0 0 100 100">
    {[0, 45, 90, 135].map((a) => <rect key={a} x="44" y="8" width="12" height="84" rx="3" fill={NAVY} transform={`rotate(${a} 50 50)`} />)}
    <circle cx="50" cy="50" r="30" fill={NAVY} />
    <circle cx="50" cy="50" r="14" fill={CREAM} />
  </svg>
);
const ICON: Record<NodeKey, React.FC> = {
  you: Person, friend: Person, myBank: () => <Bank />, hisBank: () => <Bank />, middle: Gear, central: () => <Bank big />,
};

const Check: React.FC<{k: number}> = ({k}) => (
  <svg width={64} height={64} viewBox="0 0 64 64" style={{position: 'absolute', top: -14, left: -14, transform: `scale(${k})`, opacity: k}}>
    <circle cx="32" cy="32" r="30" fill={HOOK_YELLOW} stroke={NAVY} strokeWidth="4" />
    <path d="M18 33 L28 43 L46 22" stroke={NAVY} strokeWidth="7" fill="none" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const Node: React.FC<{id: NodeKey; at: number; check: number; grey: number}> = ({id, at, check, grey}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 12, 180);
  if (k <= 0) return null;
  const n = NODES[id];
  const Icon = ICON[id];
  return (
    <div style={{position: 'absolute', left: n.x - 90, top: n.y - 90, width: 180, display: 'flex', flexDirection: 'column',
      alignItems: 'center', ...enterRight(k, 40), filter: `grayscale(${grey}) brightness(${1 - 0.45 * grey})`}}>
      <div style={{position: 'relative', width: 180, height: 180, borderRadius: 34, background: CREAM,
        display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 10px 22px rgba(0,0,0,.45)',
        transform: `scale(${interpolate(k, [0, 1], [0.6, 1])})`}}>
        <Icon />
        {check > 0 ? <Check k={check} /> : null}
      </div>
      <Paper text={n.label} size={40} bg={id === 'central' ? MUSTARD : CREAM} style={{marginTop: 14}} />
    </div>
  );
};

// line between two nodes, drawn right to left as the second node arrives
const Edge: React.FC<{a: NodeKey; b: NodeKey; at: number; dashed?: boolean; grey: number}> = ({a, b, at, dashed, grey}) => {
  const {t} = useTime();
  const p = ease(t, at, at + 0.5);
  if (p <= 0) return null;
  const A = NODES[a], B = NODES[b];
  const r = 100;
  const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy);
  const x1 = A.x + (dx / len) * r, y1 = A.y + (dy / len) * r;
  const x2 = B.x - (dx / len) * r, y2 = B.y - (dy / len) * r;
  return (
    <line x1={x1} y1={y1} x2={lerp(x1, x2, p)} y2={lerp(y1, y2, p)} stroke={CREAM} strokeOpacity={1 - 0.6 * grey}
      strokeWidth={8} strokeLinecap="round" strokeDasharray={dashed ? '4 22' : undefined} />
  );
};

// the coin: its position along PATH (0 = you, 4 = friend)
const coinAt = (t: number, at: Record<string, number>) => {
  const legs: [number, number, number][] = [   // [from index, to index, start time]
    [0, 1, at.f_mybank + 0.6],
    [1, 3, at.f_hisbank + 0.5],
  ];
  let pos = 0;
  for (const [i0, i1, s] of legs) if (t >= s) pos = lerp(i0, i1, ease(t, s, s + 0.9));
  // the full trip, station by station, once the whole system is on screen
  if (t >= at.f_trip) pos = Math.min(4, (t - at.f_trip) / 0.7);
  return pos;
};

const Coin: React.FC<{at: Record<string, number>}> = ({at}) => {
  const {t, fps} = useTime();
  // the coin pops back at you for the full trip
  const k = t >= at.f_trip ? pop(t, at.f_trip, fps, 10, 200) : pop(t, at.f_coin, fps, 10, 200);
  if (t < at.f_coin) return null;
  const pos = coinAt(t, at);
  const i = Math.min(3, Math.floor(pos)), f = pos - i;
  const A = NODES[PATH[i]], B = NODES[PATH[Math.min(4, i + 1)]];
  const x = lerp(A.x, B.x, f), y = lerp(A.y, B.y, f) - 122 - Math.sin(f * Math.PI) * 30;
  const out = interpolate(t, [at.f_three - 0.4, at.f_three], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: x - 85, top: y - 46, width: 170, height: 92, whiteSpace: 'nowrap', borderRadius: 46, background: HOOK_YELLOW,
      border: `5px solid ${NAVY}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT,
      fontWeight: 900, fontSize: 46, color: NAVY, transform: `scale(${k})`, opacity: out, boxShadow: '0 8px 16px rgba(0,0,0,.4)'}}>
      <bdi dir="rtl">100 ₪</bdi>
    </div>
  );
};

// −100 / +100 next to the banks when they change the number in the account
const Delta: React.FC<{x: number; text: string; at: number; until: number}> = ({x, text, at, until}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 12, 200);
  const out = interpolate(t, [until - 0.3, until], [1, 0], clamp);
  if (k <= 0 || out <= 0) return null;
  return (
    <div style={{position: 'absolute', left: x - 70, width: 140, textAlign: 'center', top: Y + 160, fontFamily: FONT, fontWeight: 900, fontSize: 52,
      color: HOOK_YELLOW, opacity: k * out, transform: `translateY(${(1 - k) * 20}px)`, direction: 'ltr'}}>{text}</div>
  );
};

const CONSEQUENCES = [
  {key: 'f_print', text: 'להדפיס עוד כסף', node: 'central' as NodeKey},
  {key: 'f_freeze', text: 'להקפיא חשבון', node: 'myBank' as NodeKey},
  {key: 'f_fee', text: 'עמלה וזמן', node: 'middle' as NodeKey},
];

const Consequence: React.FC<{n: number; text: string; at: number}> = ({n, text, at}) => {
  const {t, fps} = useTime();
  const k = pop(t, at, fps, 13, 170);
  if (k <= 0) return null;
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 18, direction: 'rtl', ...enterRight(k)}}>
      <div style={{width: 66, height: 66, borderRadius: 33, background: MUSTARD, color: NAVY, fontFamily: FONT, fontWeight: 900,
        fontSize: 42, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{n}</div>
      <Paper text={text} size={46} seed={text} />
    </div>
  );
};

export const MoneyFlow: React.FC<SceneProps> = ({at, start, end}) => {
  const {t, fps} = useTime();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const sceneIn = ease(t, start - 0.1, start + 0.5);
  const sceneOut = 1 - ease(t, end, end + 0.6);
  const greyAt = at.f_grey;
  const grey = ease(t, greyAt, greyAt + 0.8);
  const checkAt = (id: NodeKey) => {
    const idx = PATH.indexOf(id);
    if (id === 'central') return pop(t, at.f_trip + 1.6, fps, 10, 200);
    if (idx <= 0) return 0;
    return pop(t, at.f_trip + idx * 0.7, fps, 10, 200);
  };
  // the diagram rises a little when the three consequences come in under it
  const lift = ease(t, at.f_three, at.f_three + 0.6) * 30;
  const nodeAt: Record<NodeKey, number> = {
    you: start + 0.3, friend: at.f_friend, myBank: at.f_mybank, hisBank: at.f_hisbank, middle: at.f_middle, central: at.f_central,
  };
  return (
    <AbsoluteFill style={{opacity: sceneIn * sceneOut}}>
      <NavyPaper id="flow" />
      <AbsoluteFill style={{transform: `translateY(${-lift}px)`}}>
        <svg width={1920} height={1080} style={{position: 'absolute'}}>
          <Edge a="you" b="myBank" at={nodeAt.myBank} grey={0} />
          <Edge a="myBank" b="middle" at={nodeAt.middle} grey={grey} />
          <Edge a="middle" b="hisBank" at={nodeAt.middle} grey={grey} />
          <Edge a="hisBank" b="friend" at={nodeAt.hisBank} grey={0} />
          <Edge a="central" b="myBank" at={nodeAt.central} dashed grey={grey} />
          <Edge a="central" b="hisBank" at={nodeAt.central} dashed grey={grey} />
        </svg>
        {(Object.keys(NODES) as NodeKey[]).map((id) => (
          <Node key={id} id={id} at={nodeAt[id]} check={checkAt(id)} grey={MIDDLE.includes(id) ? grey : 0} />
        ))}
        <Delta x={NODES.myBank.x} text="−100" at={at.f_mybank + 1.4} until={at.f_middle + 1.5} />
        <Delta x={NODES.hisBank.x} text="+100" at={at.f_hisbank + 1.3} until={at.f_middle + 1.5} />
        <Coin at={at} />
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 650, right: 470, display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end'}}>
        {CONSEQUENCES.map((c, i) => <Consequence key={c.key} n={i + 1} text={c.text} at={at[c.key]} />)}
      </div>
    </AbsoluteFill>
  );
};
