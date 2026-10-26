import React from 'react';
import {FONT, NAVY, seedOf, tornClip} from '../brand';

// Torn-paper strip: navy Heebo Black on cream / yellow paper, soft paper shadow.
export const Strip: React.FC<{
  text: string; bg: string; size: number; rotate?: number; style?: React.CSSProperties; children?: React.ReactNode;
}> = ({text, bg, size, rotate = 0, style, children}) => (
  <div style={{filter: 'drop-shadow(0 6px 10px rgba(0,0,0,.35))', transform: `rotate(${rotate}deg)`, ...style}}>
    <div style={{
      background: bg, color: NAVY, fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1.15,
      padding: `${size * 0.18}px ${size * 0.45}px ${size * 0.24}px`, direction: 'rtl', whiteSpace: 'nowrap',
      clipPath: tornClip(seedOf(text)),
    }}>{children ?? <bdi dir="auto">{text}</bdi>}</div>
  </div>
);

export const Arrow: React.FC<{size: number; color: string}> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <rect x="38" y="0" width="24" height="52" fill={color} />
    <polygon points="0,45 100,45 50,100" fill={color} />
  </svg>
);
