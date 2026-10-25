import React from 'react';
import {Easing, interpolate, spring, useVideoConfig} from 'remotion';
import {CREAM, FONT, HOOK_YELLOW as YEL, NAVY, clamp} from '../brand';

// Brand icons for explainer cards. Flat, navy-outlined cream/yellow shapes, no emoji.
// Each icon gets lt (seconds since its step started), the step's value (a number the
// host said), and draws in a 260x210 viewBox. Add a new icon here and in ICONS, then
// list it in references/cards-and-icons.md.
export type IconProps = {lt: number; value?: number};

const draw = (lt: number, a = 0, b = 0.7) => interpolate(lt, [a, b], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});

const Line: React.FC<{d: string; p: number; stroke: string; fill?: string; fillOpacity?: number; w?: number}> =
  ({d, p, stroke, fill = 'none', fillOpacity = 0, w = 8}) => (
    <path d={d} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} stroke={stroke} strokeWidth={w}
          strokeLinejoin="round" strokeLinecap="round" fill={fill} fillOpacity={fillOpacity} />
  );

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg width={620} height={500} viewBox="0 0 260 210">{children}</svg>
);

const HouseShape: React.FC<{lt: number}> = ({lt}) => {
  const p = draw(lt);
  const fill = interpolate(lt, [0.45, 0.8], [0, 1], clamp);
  return (
    <>
      <Line d="M20 100 L130 20 L240 100 Z" p={p} stroke={YEL} fill={YEL} fillOpacity={fill} />
      <Line d="M45 100 L45 195 L215 195 L215 100" p={p} stroke={CREAM} />
      <rect x="45" y="100" width="170" height="95" fill={CREAM} opacity={fill} />
      <rect x="112" y="135" width="36" height="60" fill={NAVY} opacity={fill} />
      <rect x="65" y="118" width="30" height="26" fill={NAVY} opacity={fill} />
      <rect x="165" y="118" width="30" height="26" fill={NAVY} opacity={fill} />
    </>
  );
};

const House: React.FC<IconProps> = ({lt}) => <Svg><HouseShape lt={lt} /></Svg>;

// Illiquid / locked: the house with a padlock that pops on.
const HouseLock: React.FC<IconProps> = ({lt}) => {
  const {fps} = useVideoConfig();
  const k = spring({frame: Math.round(lt * fps) - 14, fps, config: {damping: 10}});
  return (
    <Svg>
      <HouseShape lt={lt} />
      {k > 0 && (
        <g transform={`translate(205 150) scale(${k})`}>
          <path d="M-18 -8 V-24 a18 18 0 0 1 36 0 V-8" stroke={NAVY} strokeWidth={9} fill="none" />
          <path d="M-18 -8 V-24 a18 18 0 0 1 36 0 V-8" stroke={YEL} strokeWidth={5} fill="none" />
          <rect x="-30" y="-10" width="60" height="50" rx="8" fill={YEL} stroke={NAVY} strokeWidth={4} />
          <circle cx="0" cy="12" r="7" fill={NAVY} />
        </g>
      )}
    </Svg>
  );
};

// A value that changes by `value` percent: the bar moves, a dashed line keeps the old level,
// the number counts up. dir -1 = drop, +1 = rise.
const Change: React.FC<IconProps & {dir: 1 | -1}> = ({lt, value = 0, dir}) => {
  const {fps} = useVideoConfig();
  const grow = spring({frame: Math.round(lt * fps), fps, config: {damping: 15}});
  const u = interpolate(lt, [0.6, 1.5], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const FULL = dir < 0 ? 170 : 170 / (1 + value / 100);
  const base = 200, top0 = base - FULL;
  const h = FULL * grow * (1 + dir * (value / 100) * u), top = base - h;
  const on = interpolate(lt, [0.6, 0.8], [0, 1], clamp);
  const tip = dir < 0 ? top - 16 : top + 16;
  return (
    <Svg>
      <line x1="70" y1={top0} x2="250" y2={top0} stroke={CREAM} strokeWidth={3} strokeDasharray="8 7" opacity={on * 0.8} />
      <rect x="110" y={top} width="90" height={h} fill={CREAM} stroke={NAVY} strokeWidth={3} />
      <g opacity={on}>
        <line x1="228" y1={dir < 0 ? top0 + 6 : top0 - 6} x2="228" y2={dir < 0 ? Math.max(top - 12, top0 + 6) : Math.min(top + 12, top0 - 6)}
              stroke={YEL} strokeWidth={9} />
        <polygon points={`212,${tip} 244,${tip} 228,${dir < 0 ? top + 2 : top - 2}`} fill={YEL} />
        <text x="58" y={(top0 + top) / 2 + 16} fill={YEL} fontFamily={FONT} fontWeight={900} fontSize={46} textAnchor="middle">
          {`${Math.round(value * u)}%`}
        </text>
      </g>
    </Svg>
  );
};
const Drop: React.FC<IconProps> = (p) => <Change {...p} dir={-1} />;
const Rise: React.FC<IconProps> = (p) => <Change {...p} dir={1} />;

const Bars: React.FC<IconProps & {up: boolean}> = ({lt, up}) => {
  const hs = up ? [0.3, 0.5, 0.72, 1] : [1, 0.72, 0.5, 0.3];
  const arrow = draw(lt, 0.7, 1.2);
  const [x0, y0, x1, y1] = up ? [30, 150, 230, 30] : [30, 30, 230, 150];
  return (
    <Svg>
      {hs.map((h, i) => {
        const k = interpolate(lt, [0.15 + 0.12 * i, 0.45 + 0.12 * i], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.6))});
        const hh = 150 * h * k;
        return <rect key={i} x={45 + i * 48} y={200 - hh} width={36} height={hh} fill={CREAM} stroke={NAVY} strokeWidth={3} />;
      })}
      <Line d={`M${x0} ${y0} L${x1} ${y1}`} p={arrow} stroke={YEL} w={10} />
      {arrow > 0.98 && (
        <polygon fill={YEL} points={up ? `${x1 + 6},${y1 - 6} ${x1 - 26},${y1 - 2} ${x1 + 2},${y1 + 24}`
                                       : `${x1 + 6},${y1 + 6} ${x1 - 26},${y1 + 2} ${x1 + 2},${y1 - 24}`} />
      )}
    </Svg>
  );
};
const BarsUp: React.FC<IconProps> = (p) => <Bars {...p} up />;
const BarsDown: React.FC<IconProps> = (p) => <Bars {...p} up={false} />;

// A share of a whole: the pie fills to `value` percent and the number counts up.
const Pie: React.FC<IconProps> = ({lt, value = 0}) => {
  const u = interpolate(lt, [0.2, 1.4], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const ang = (value / 100) * u * 2 * Math.PI, r = 80, cx = 130, cy = 105;
  const x = cx + r * Math.sin(ang), y = cy - r * Math.cos(ang);
  return (
    <Svg>
      <circle cx={cx} cy={cy} r={92} fill={CREAM} stroke={NAVY} strokeWidth={5} />
      {u > 0 && <path d={`M${cx} ${cy} L${cx} ${cy - r} A${r} ${r} 0 ${ang > Math.PI ? 1 : 0} 1 ${x} ${y} Z`} fill={YEL} />}
      <text x={cx} y={cy + 16} fill={NAVY} fontFamily={FONT} fontWeight={900} fontSize={44} textAnchor="middle">
        {`${Math.round(value * u)}%`}
      </text>
    </Svg>
  );
};

// AI / compute: a chip whose traces draw in and pulse.
const Chip: React.FC<IconProps> = ({lt}) => {
  const p = draw(lt, 0, 0.6);
  const pulse = (lt * 1.5) % 1;
  const legs = [-30, 0, 30].flatMap((k) => [
    `M${130 + k} 45 V20`, `M${130 + k} 165 V190`, `M70 ${105 + k} H45`, `M190 ${105 + k} H215`]);
  return (
    <Svg>
      {legs.map((d, i) => <Line key={i} d={d} p={p} stroke={CREAM} w={8} />)}
      <rect x="70" y="45" width="120" height="120" rx="14" fill={CREAM} stroke={NAVY} strokeWidth={5} opacity={p} />
      <rect x="98" y="73" width="64" height="64" rx="8" fill={NAVY} opacity={p} />
      <circle cx="130" cy="105" r={14 + 20 * pulse} fill="none" stroke={YEL} strokeWidth={5} opacity={(1 - pulse) * p} />
      <circle cx="130" cy="105" r="10" fill={YEL} opacity={p} />
    </Svg>
  );
};

export const ICONS: Record<string, React.FC<IconProps>> = {
  house: House, house_lock: HouseLock, drop: Drop, rise: Rise,
  bars_up: BarsUp, bars_down: BarsDown, pie: Pie, chip: Chip,
};
