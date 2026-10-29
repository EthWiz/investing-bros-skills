import React from 'react';
import {AbsoluteFill, interpolate, useVideoConfig} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW, MUSTARD, NAVY, clamp} from '../brand';
import {Cross} from './DoubleSpend';
import {NavyPaper, Paper, ease, enterRight, lerp, pop, useTime} from './kit';
import type {SceneProps} from './types';

// Reusable 'bubble' scene: the private key. A safe holds the coins; the key comes in with its name,
// turns in the lock and the door opens on the coins (the key is what lets you use the money). Then the
// key is lost: the door shuts, the key falls away, a padlock stays on the door, and there is no
// helpdesk to call (a headset with an X and Amitai's words for it).
// content: key {label, at}, unlock {at}, lost {at}, helpdesk {text, at}; optional: hold {at} (the safe
//   comes in; default the scene's start), coin {label} (a sign on the coins). Every word comes from content.
// It lays itself out from the frame: 16:9 in the lesson (clear of his circle and the captions), 9:16 for a Short.

type P = {x: number; y: number};
type Layout = {safe: P; size: number; key: P; keyW: number; keyLabel: P; desk: P; deskLabel: P};

const WIDE: Layout = {safe: {x: 680, y: 400}, size: 460, key: {x: 1240, y: 360}, keyW: 300, keyLabel: {x: 1240, y: 520},
  desk: {x: 1250, y: 330}, deskLabel: {x: 1270, y: 520}};
const TALL: Layout = {safe: {x: 540, y: 640}, size: 520, key: {x: 540, y: 1180}, keyW: 320, keyLabel: {x: 540, y: 1340},
  desk: {x: 540, y: 1180}, deskLabel: {x: 540, y: 1400}};

const Key: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w * 0.42} viewBox="0 0 250 105" style={{overflow: 'visible'}}>
    <g stroke={NAVY} strokeWidth="6" strokeLinejoin="round">
      <path d="M86 40 H236 V64 H214 V84 H196 V64 H180 V78 H162 V64 H86 Z" fill={HOOK_YELLOW} />
      <circle cx="52" cy="52" r="44" fill={HOOK_YELLOW} />
      <circle cx="44" cy="52" r="16" fill={NAVY} />
    </g>
  </svg>
);

const Headset: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w} viewBox="0 0 120 120">
    <circle cx="60" cy="60" r="56" fill={CREAM} stroke={NAVY} strokeWidth="5" />
    <path d="M30 66 V58 a30 30 0 0 1 60 0 V66" fill="none" stroke={NAVY} strokeWidth="8" strokeLinecap="round" />
    <rect x="22" y="58" width="18" height="28" rx="7" fill={NAVY} />
    <rect x="80" y="58" width="18" height="28" rx="7" fill={NAVY} />
    <path d="M89 86 Q86 98 66 98" fill="none" stroke={NAVY} strokeWidth="5" strokeLinecap="round" />
    <circle cx="62" cy="98" r="6" fill={MUSTARD} stroke={NAVY} strokeWidth="3" />
  </svg>
);

const Padlock: React.FC<{w: number}> = ({w}) => (
  <svg width={w} height={w * 1.1} viewBox="0 0 100 110">
    <path d="M26 50 V34 a24 24 0 0 1 48 0 V50" stroke={NAVY} strokeWidth="13" fill="none" />
    <path d="M26 50 V34 a24 24 0 0 1 48 0 V50" stroke={CREAM} strokeWidth="6" fill="none" />
    <rect x="10" y="48" width="80" height="58" rx="10" fill={MUSTARD} stroke={NAVY} strokeWidth="5" />
    <circle cx="50" cy="72" r="8" fill={NAVY} />
    <rect x="46" y="74" width="8" height="18" rx="3" fill={NAVY} />
  </svg>
);

export const PrivateKey: React.FC<SceneProps> = ({start, end, content: c}) => {
  const {t, fps} = useTime();
  const {width, height} = useVideoConfig();
  if (t < start - 0.1 || t > end + 0.8) return null;
  const L = width >= height ? WIDE : TALL;
  const o = ease(t, start - 0.1, start + 0.5) * (1 - ease(t, end, end + 0.6));
  const s = L.size, hold = c.hold?.at ?? start + 0.2;
  const safeK = pop(t, hold, fps, 12, 170);
  const u = c.unlock.at, lost = c.lost.at;

  // the key: in on its name, into the lock and a quarter turn, out again when it's lost, then falling
  const keyIn = pop(t, c.key.at, fps, 12, 170);
  const hole = {x: L.safe.x + s * 0.3, y: L.safe.y};
  const toLock = ease(t, u, u + 0.6);
  const turn = ease(t, u + 0.6, u + 0.9);
  const fall = ease(t, lost, lost + 1.1);
  const keyP = {x: lerp(L.key.x, hole.x + L.keyW * 0.42, toLock), y: lerp(L.key.y, hole.y, toLock) + fall * fall * 700};
  const keyRot = turn * 90 * (1 - ease(t, lost - 0.01, lost + 0.2)) + fall * 160;
  const keyO = 1 - ease(t, lost + 0.6, lost + 1.1);

  // the door: opens after the turn, shuts when the key is lost
  const open = ease(t, u + 0.9, u + 1.4) * (1 - ease(t, lost, lost + 0.4));
  const coinsK = ease(t, u + 1.1, u + 1.6) * (1 - ease(t, lost, lost + 0.3));
  const lockK = pop(t, lost + 0.5, fps, 9, 200);
  const labelOut = 1 - ease(t, lost, lost + 0.4);

  return (
    <AbsoluteFill style={{opacity: o}}>
      <NavyPaper id={`key-${start}`} />
      {safeK > 0 ? (
        <div style={{position: 'absolute', left: L.safe.x - s / 2, top: L.safe.y - s / 2, width: s, height: s, ...enterRight(safeK, 50)}}>
          {/* the body and what's inside */}
          <div style={{position: 'absolute', inset: 0, borderRadius: 26, background: CREAM, border: `8px solid ${NAVY}`,
            boxShadow: '0 16px 28px rgba(0,0,0,.5)'}} />
          <div style={{position: 'absolute', left: s * 0.1, top: s * 0.1, width: s * 0.8, height: s * 0.8, borderRadius: 14, background: '#0E2E4A',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: s * 0.04}}>
            {[0, 1, 2].map((i) => (
              <div key={i} style={{width: s * 0.18, height: s * 0.18, borderRadius: s * 0.09, background: HOOK_YELLOW, border: `5px solid ${NAVY}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT, fontWeight: 900, fontSize: s * 0.09, color: NAVY,
                opacity: coinsK, transform: `translateY(${(1 - coinsK) * 30 - Math.sin((t - u) * 3 + i) * 6 * coinsK}px)`}}>
                {c.coin?.label ?? ''}
              </div>
            ))}
          </div>
          {/* the door, hinged on the left */}
          <div style={{position: 'absolute', left: s * 0.1, top: s * 0.1, width: s * 0.8, height: s * 0.8, borderRadius: 14,
            background: CREAM, border: `6px solid ${NAVY}`, transformOrigin: 'left center',
            transform: `perspective(${s * 3}px) rotateY(${-open * 78}deg)`, boxShadow: open > 0 ? '8px 0 18px rgba(0,0,0,.35)' : 'none'}}>
            <div style={{position: 'absolute', left: '50%', top: '50%', width: s * 0.3, height: s * 0.3, marginLeft: -s * 0.15, marginTop: -s * 0.15,
              borderRadius: '50%', border: `6px solid ${NAVY}`, background: MUSTARD, opacity: 0.9}} />
            <div style={{position: 'absolute', right: s * 0.04, top: '50%', width: s * 0.06, height: s * 0.12, marginTop: -s * 0.06, borderRadius: 6,
              background: NAVY}} />
          </div>
          {lockK > 0 ? (
            <div style={{position: 'absolute', left: s / 2 - s * 0.17, top: s / 2 - s * 0.2, transform: `scale(${lockK})`,
              filter: 'drop-shadow(0 8px 14px rgba(0,0,0,.5))'}}>
              <Padlock w={s * 0.34} />
            </div>
          ) : null}
        </div>
      ) : null}
      {keyIn > 0 && keyO > 0 ? (
        <div style={{position: 'absolute', left: keyP.x - L.keyW / 2, top: keyP.y - L.keyW * 0.21, opacity: keyO,
          transform: `scale(${interpolate(keyIn, [0, 1], [0.5, 1])}) rotate(${keyRot}deg) scaleX(-1)`,
          filter: 'drop-shadow(0 10px 16px rgba(0,0,0,.5))'}}>
          <Key w={L.keyW} />
        </div>
      ) : null}
      <div style={{position: 'absolute', left: L.keyLabel.x - 300, top: L.keyLabel.y, width: 600, opacity: labelOut}}>
        <div style={{display: 'flex', justifyContent: 'center', ...enterRight(pop(t, c.key.at, fps))}}>
          <Paper text={c.key.label} size={54} bg={MUSTARD} />
        </div>
      </div>
      {pop(t, c.helpdesk.at, fps) > 0 ? (
        <>
          <div style={{position: 'absolute', left: L.desk.x - 110, top: L.desk.y - 110, transform: `scale(${pop(t, c.helpdesk.at, fps)})`,
            filter: 'drop-shadow(0 10px 16px rgba(0,0,0,.5))'}}>
            <Headset w={220} />
          </div>
          <Cross p={{x: L.desk.x + 95, y: L.desk.y + 85}} at={c.helpdesk.at + 0.4} size={110} />
          <div style={{position: 'absolute', left: L.deskLabel.x - 450, top: L.deskLabel.y, width: 900, display: 'flex', justifyContent: 'center',
            ...enterRight(pop(t, c.helpdesk.at + 0.2, fps))}}>
            <Paper text={c.helpdesk.text} size={50} />
          </div>
        </>
      ) : null}
    </AbsoluteFill>
  );
};
