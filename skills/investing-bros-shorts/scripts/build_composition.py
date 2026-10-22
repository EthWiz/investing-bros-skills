#!/usr/bin/env python3
"""Build the HyperFrames composition (public/index.html) for an Investing Bros short.

Usage:
    python3 build_composition.py short.json --project DIR

DIR/public must already hold: input-video.mp4 (from make_input.py), logo.png
(brand wordmark), fonts/Heebo-{SemiBold,ExtraBold,Black}.woff2 and
vendor/gsap.min.js. Writes DIR/public/index.html, DIR/public/cards/*.html,
DIR/storyboard.json and DIR/transcript.json, then run
`npx hyperframes lint|snapshot|render` on DIR/public.

Layout (1080x1920): host video 1080x1216 at the top with the logo and a name
tag, proofread captions over the bottom of the video, one animated card at a
time in the band y=1250..1550 (above the Reels/Shorts UI, left of the side
buttons), an end card for the last seconds.

short.json (all times are seconds on the SOURCE timeline; they are mapped
through `pieces` to the clip's own time):
{
  "name": "short1_swift", "fps": 24,
  "pieces": [[843.69, 864.40], ...],                      # same as make_input.py
  "speaker": ["אמיתי רסקין", 843.69, 847.0],               # name tag + when
  "captions": [[843.69, 845.35, "אתה רוצה להעביר כסף|מישראל לארצות הברית —"], ...],
                                                         # | = line break, [..] = emerald
  "cards": [
    {"type": "route", "start": s, "end": e, "kicker": "...", "from": "ישראל", "to": "ארה״ב"},
    {"type": "stat", "start": s, "end": e, "kicker": "...", "value": 40, "suffix": "$",
     "value_at": t, "label": "עמלה|על העברה אחת", "note": "״...״", "note_at": t},
    {"type": "strike", "start": s, "end": e, "kicker": "...", "title": "SWIFT",
     "wrong": "מערכת תשלומים", "wrong_at": t, "right": "מערכת הודעות", "right_at": t},
    {"type": "statement", "start": s, "end": e, "kicker": "...", "chip": "מורכבת", "chip_at": t,
     "title": "לא בנויה|לעידן האינטרנט", "title_at": t},
    {"type": "list", "start": s, "end": e, "kicker": "...",
     "rows": [{"text": "...", "on": true, "at": t}, {"text": "...", "on": false, "at": t}],
     "conclusion": "...", "conclusion_at": t}
  ],
  "endcard": {"lines": ["הפרק המלא על טוקניזציה", "אחים להשקעות"], "seconds": 2.6}
}
Every on-screen word must be something the hosts said or a faithful label for
it (no invented numbers); every `*_at` should be when that word is spoken.
"""
import argparse
import html
import json
import os
import re
import sys

ACCENT = "#F5B71F"                  # house accent gold (investing-bros-show -> Brand)
BAND = "left:56px;top:1250px;width:840px;height:300px"
# "overlay" layout (house style): the input video is the finished full-screen short from
# investing-bros-shorts/build_fullbleed.py (captions and logo burned in); cards sit in a compact
# top panel, scaled to 0.74 so the host's eyes stay clear.
PANEL_BAND = "left:56px;top:262px;width:968px;height:420px;transform-origin:50% 0%"
PANEL_SCALE = 0.74
LATIN = re.compile(r"[A-Za-z][A-Za-z0-9&'’.\-]*(?:\s+[A-Za-z0-9][A-Za-z0-9&'’.\-]*)*")


def snap(t, fps):
    return round(t * fps) / fps


class Timeline:
    def __init__(self, pieces, fps):
        self.fps = fps
        self.pieces = [(snap(p[0], fps), snap(p[1], fps)) for p in pieces]
        self.duration = round(sum(b - a for a, b in self.pieces) * fps) / fps

    def map(self, t):
        o = 0.0
        for a, b in self.pieces:
            if a - 0.05 <= t <= b + 0.05:
                return min(max(o + t - a, o), o + b - a)
            o += b - a
        raise ValueError(f"time {t} is not inside any piece")

    def q(self, t):
        return round(round(t * self.fps) / self.fps, 4)


def text(s):
    """Escape, wrap Latin runs in <bdi>, [..] -> emerald span, | -> line break."""
    out, pos = [], 0
    for m in LATIN.finditer(s):
        out.append(html.escape(s[pos:m.start()], quote=False))
        out.append(f"<bdi>{html.escape(m.group(0), quote=False)}</bdi>")
        pos = m.end()
    out.append(html.escape(s[pos:], quote=False))
    return "".join(out).replace("[", '<span class="em">').replace("]", "</span>").replace("|", "<br/>")


def close_gaps(items, max_gap=0.35):
    items = [list(x) for x in items]
    for i in range(len(items) - 1):
        gap = items[i + 1][0] - items[i][1]
        if 0 < gap < max_gap or gap < 0:
            items[i][1] = items[i + 1][0]
    return items


BASE_CSS = """CARD .root{width:100%;height:100%;box-sizing:border-box;padding:28px 36px;display:flex;flex-direction:column;justify-content:center;gap:14px;font-family:'Heebo ExtraBold','Heebo Black';color:#fff;background:rgba(7,9,8,0.92);border:2px solid rgba(245,183,31,0.55);border-radius:28px}
CARD .kicker{font-family:'Heebo SemiBold';font-size:30px;color:var(--accent-0)}
CARD .title{font-family:'Heebo Black';font-size:76px;line-height:1.02;margin:0}
CARD .em{color:var(--accent-0)}"""

TYPE_CSS = {
    "route": """CARD .route{display:flex;flex-direction:row;align-items:center;gap:22px}
CARD .place{font-family:'Heebo Black';font-size:64px;line-height:1}
CARD .track{position:relative;flex:1;height:10px;background:rgba(255,255,255,0.12);border-radius:5px;overflow:hidden}
CARD .fill{position:absolute;right:0;top:0;height:10px;width:0;background:var(--accent-0);border-radius:5px}""",
    "stat": """CARD .row{display:flex;flex-direction:row;align-items:baseline;gap:22px}
CARD .num{opacity:0;font-family:'Heebo Black';font-size:150px;line-height:0.9;color:var(--accent-0);direction:ltr;unicode-bidi:isolate}
CARD .label{font-family:'Heebo ExtraBold';font-size:44px;line-height:1.1}
CARD .note{font-family:'Heebo SemiBold';font-size:36px;color:#C9D6CF;border-top:2px solid rgba(255,255,255,0.14);padding-top:14px}""",
    "strike": """CARD .title{font-size:96px;direction:ltr;unicode-bidi:isolate;letter-spacing:4px}
CARD .chips{display:flex;flex-direction:row;gap:18px}
CARD .chip{font-family:'Heebo ExtraBold';font-size:36px;padding:12px 24px;border-radius:999px}
CARD .no{background:rgba(255,255,255,0.08);color:#9AA6A0;text-decoration:line-through;text-decoration-thickness:4px}
CARD .yes{background:var(--accent-0);color:#06100B}""",
    "statement": """CARD .chip{align-self:flex-start;font-family:'Heebo ExtraBold';font-size:40px;padding:10px 26px;border-radius:999px;border:3px solid var(--accent-0);color:var(--accent-0)}""",
    "list": """CARD .rows{display:flex;flex-direction:column;gap:12px}
CARD .r{display:flex;flex-direction:row;align-items:center;gap:16px;font-family:'Heebo ExtraBold';font-size:40px}
CARD .dot{width:18px;height:18px;border-radius:9px;background:var(--accent-0);flex:0 0 auto}
CARD .off{color:#9AA6A0}
CARD .off .dot{background:transparent;border:3px solid #9AA6A0}
CARD .title{font-size:62px;color:var(--accent-0)}""",
    "fly": """CARD .root{display:block;padding:0;position:relative}
CARD svg{position:absolute;left:0;top:0;width:968px;height:420px}
CARD .kick{position:absolute;right:40px;top:26px;font-family:'Heebo SemiBold';font-size:34px;color:var(--accent-0);white-space:nowrap}
CARD .lab{position:absolute;font-family:'Heebo Black';font-size:46px;white-space:nowrap;opacity:0}
CARD .lab.gold{color:var(--accent-0)}""",
    "supply": """CARD .root{display:block;padding:0;position:relative}
CARD svg{position:absolute;left:0;top:0;width:968px;height:420px}
CARD .kick{position:absolute;top:26px;font-family:'Heebo SemiBold';font-size:34px;color:var(--accent-0);white-space:nowrap}
CARD .big{position:absolute;font-family:'Heebo Black';line-height:1;white-space:nowrap;direction:ltr;unicode-bidi:isolate;opacity:0}
CARD .lbl{position:absolute;font-family:'Heebo ExtraBold';font-size:40px;white-space:nowrap;opacity:0}
CARD .meter{position:absolute;left:130px;top:96px;width:110px;height:270px;border-radius:18px;background:rgba(255,255,255,0.08);border:2px solid rgba(255,255,255,0.18);overflow:hidden;opacity:0}
CARD .fill{position:absolute;left:0;bottom:0;width:100%;height:100%;background:linear-gradient(to top,#C98A0B,#F5B71F 60%,#FFE08A)}
CARD .half{position:absolute;left:-10px;right:-10px;top:50%;border-top:3px dashed rgba(255,255,255,0.55)}""",
    "end": """CARD .root{align-items:center;text-align:center;gap:10px;border-color:var(--accent-0);background:rgba(7,9,8,0.94)}
CARD .a{font-size:44px}
CARD .b{font-family:'Heebo Black';font-size:72px;color:var(--accent-0);line-height:1}""",
}


def card_body(c, cid):
    """Return (html body, [(abs_or_rel, kind, selector, params)]) — times 'rel' to card start or ('src', t)."""
    k = f'<div class="kicker" id="{cid}-k">{text(c["kicker"])}</div>' if c.get("kicker") else ""
    an = [(0.10, "fade-in", f"#{cid}-k", {})] if k else []
    t = c["type"]
    if t == "route":
        body = (k + f'<div class="route"><div class="place" id="{cid}-a">{text(c["from"])}</div>'
                f'<div class="track"><div class="fill" id="{cid}-fill"></div></div>'
                f'<div class="place" id="{cid}-b">{text(c["to"])}</div></div>')
        an += [(0.30, "fade-in", f"#{cid}-a", {}), (0.55, "grow", f"#{cid}-fill", {"w": 380}),
               (1.60, "scale-pop", f"#{cid}-b", {})]
    elif t == "stat":
        body = (k + f'<div class="row"><div class="num" id="{cid}-numbox">{text(c.get("prefix", ""))}'
                f'<span id="{cid}-num">0</span>{text(c.get("suffix", ""))}</div>'
                f'<div class="label" id="{cid}-l">{text(c.get("label", ""))}</div></div>')
        at = ("src", c.get("value_at", c["start"]))
        an += [(at, "fade-in", f"#{cid}-numbox", {}), (at, "count", f"#{cid}-num", {"to": c["value"]}),
               (0.40, "slide-in", f"#{cid}-l", {})]
        if c.get("note"):
            body += f'<div class="note" id="{cid}-n">{text(c["note"])}</div>'
            an.append((("src", c.get("note_at", c["start"])), "fade-in", f"#{cid}-n", {}))
    elif t == "strike":
        body = (k + f'<div class="title" id="{cid}-t">{text(c["title"])}</div><div class="chips">'
                f'<div class="chip no" id="{cid}-no">{text(c["wrong"])}</div>'
                f'<div class="chip yes" id="{cid}-yes">{text(c["right"])}</div></div>')
        an += [(0.20, "scale-pop", f"#{cid}-t", {}),
               (("src", c.get("wrong_at", c["start"])), "slide-in", f"#{cid}-no", {}),
               (("src", c.get("right_at", c["start"])), "scale-pop", f"#{cid}-yes", {})]
    elif t == "statement":
        body = k
        if c.get("chip"):
            body += f'<div class="chip" id="{cid}-c">{text(c["chip"])}</div>'
            an.append((("src", c.get("chip_at", c["start"])), "scale-pop", f"#{cid}-c", {}))
        body += f'<h2 class="title" id="{cid}-t">{text(c["title"])}</h2>'
        an.append((("src", c.get("title_at", c["start"])), "mask", f"#{cid}-t", {}))
    elif t == "list":
        rows = "".join(
            f'<div class="r{"" if r.get("on", True) else " off"}" id="{cid}-r{i}"><span class="dot"></span>{text(r["text"])}</div>'
            for i, r in enumerate(c["rows"]))
        body = k + f'<div class="rows">{rows}</div>'
        an += [(("src", r.get("at", c["start"])), "slide-in", f"#{cid}-r{i}", {}) for i, r in enumerate(c["rows"])]
        if c.get("conclusion"):
            body += f'<div class="title" id="{cid}-t">{text(c["conclusion"])}</div>'
            an.append((("src", c.get("conclusion_at", c["start"])), "mask", f"#{cid}-t", {}))
    elif t == "fly":
        body, an = fly_card(c, cid)
    elif t == "supply":
        body, an = supply_card(c, cid)
    elif t == "end":
        a, b = (c["lines"] + ["", ""])[:2]
        body = f'<div class="a" id="{cid}-a">{text(a)}</div><div class="b" id="{cid}-b">{text(b)}</div>'
        an += [(0.10, "fade-in", f"#{cid}-a", {}), (0.30, "scale-pop", f"#{cid}-b", {})]
    else:
        raise ValueError(f"unknown card type {t}")
    return body, an


def _src(c, key):
    return ("src", c[key]) if key in c else None


def fly_card(c, cid):
    """An asteroid in space: metal sheen, gold veins, then it flies down and lands on Earth.
    Keys: kicker, metal_at/metal_label, gold_at/gold_label, fly_at (+ fly_kicker), land_label; times = source."""
    P = lambda x: f"{cid}-{x}"  # noqa: E731
    rock = "M-78,-20 C-80,-60 -40,-88 0,-84 C40,-92 82,-60 86,-18 C92,26 64,74 18,82 C-24,90 -70,66 -84,26 Z"
    stars = "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in
                    ((60, 50, 2), (180, 120, 1.6), (300, 40, 2.2), (420, 90, 1.4), (540, 30, 1.8), (890, 60, 2),
                     (930, 200, 1.5), (600, 340, 1.6), (110, 230, 1.4), (470, 210, 1.8), (820, 370, 1.6), (240, 330, 1.3)))
    veins = "".join(f'<path class="v" d="{d}" stroke-dasharray="{n}" stroke-dashoffset="{n}"/>' for d, n in (
        ("M-60,10 C-30,0 -10,20 20,6 C40,-4 60,8 74,0", 160), ("M-40,-50 C-20,-30 10,-40 30,-20", 100),
        ("M-20,60 C0,40 30,50 50,34", 90)))
    body = f"""<svg viewBox="0 0 968 420" xmlns="http://www.w3.org/2000/svg"><defs>
<radialGradient id="{P('rk')}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#9A9A96"/><stop offset="0.6" stop-color="#5E5E5A"/><stop offset="1" stop-color="#2E2E2C"/></radialGradient>
<linearGradient id="{P('sh')}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="{P('ea')}" cx="50%" cy="20%" r="80%"><stop offset="0" stop-color="#2E7DD7"/><stop offset="0.55" stop-color="#1B4F8F"/><stop offset="1" stop-color="#0B1F3A"/></radialGradient>
<radialGradient id="{P('gl')}"><stop offset="0" stop-color="#FFE08A"/><stop offset="0.4" stop-color="#F5B71F" stop-opacity="0.7"/><stop offset="1" stop-color="#F5B71F" stop-opacity="0"/></radialGradient>
<linearGradient id="{P('tg')}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#F5B71F" stop-opacity="0"/><stop offset="1" stop-color="#FFE08A" stop-opacity="0.85"/></linearGradient>
<clipPath id="{P('cl')}"><path d="{rock}"/></clipPath></defs>
<g fill="#fff" opacity="0.55">{stars}</g>
<g id="{P('earth')}" opacity="0"><circle cx="330" cy="935" r="640" fill="url(#{P('ea')})"/><circle cx="330" cy="935" r="640" fill="none" stroke="#7CC4FF" stroke-opacity="0.55" stroke-width="5"/></g>
<g transform="translate(330,292)"><circle id="{P('glow')}" r="120" fill="url(#{P('gl')})" opacity="0"/><circle id="{P('ring')}" r="40" fill="none" stroke="#FFD66B" stroke-width="6" opacity="0"/></g>
<g transform="translate(720,190)"><g id="{P('ast')}">
<path id="{P('tail')}" d="M0,-34 L330,-6 L330,6 L0,34 Z" fill="url(#{P('tg')})" opacity="0" transform="rotate(-21)"/>
<g id="{P('rock')}"><path d="{rock}" fill="url(#{P('rk')})" stroke="#1E1E1C" stroke-width="3"/>
<circle cx="-30" cy="-30" r="14" fill="#3A3A37"/><circle cx="34" cy="10" r="20" fill="#3A3A37"/><circle cx="-14" cy="44" r="10" fill="#3A3A37"/><circle cx="46" cy="-44" r="8" fill="#3A3A37"/>
<g clip-path="url(#{P('cl')})"><rect id="{P('sheen')}" x="-260" y="-100" width="90" height="200" fill="url(#{P('sh')})" transform="skewX(-20)"/></g>
<g id="{P('veins')}" fill="none" stroke="#F5B71F" stroke-width="7" stroke-linecap="round">{veins}</g></g></g></g></svg>
<div class="kick" id="{P('k1')}">{text(c.get("kicker", ""))}</div>
<div class="kick" id="{P('k2')}" style="opacity:0">{text(c.get("fly_kicker", ""))}</div>
<div class="lab" id="{P('l1')}" style="right:520px;top:120px">{text(c.get("metal_label", ""))}</div>
<div class="lab gold" id="{P('l2')}" style="right:520px;top:200px">{text(c.get("gold_label", ""))}</div>
<div class="lab gold" id="{P('l3')}" style="right:40px;top:300px">{text(c.get("land_label", ""))}</div>"""
    fly = c["fly_at"]
    an = [(0.1, "tween", f"#{P('rock')}", {"from": {"scale": 0.4, "opacity": 0, "svgOrigin": "0 0"},
                                            "to": {"scale": 1, "opacity": 1, "duration": 0.6, "ease": "back.out(1.7)"}}),
          (0.1, "to", f"#{P('rock')}", {"rotation": 22, "svgOrigin": "0 0", "duration": 11, "ease": "none"})]
    if "metal_at" in c:
        an += [(_src(c, "metal_at"), "tween", f"#{P('sheen')}", {"from": {"attr": {"x": -260}}, "to": {"attr": {"x": 180}, "duration": 0.9, "ease": "power2.inOut"}}),
               (_src(c, "metal_at"), "slide-in", f"#{P('l1')}", {})]
    if "gold_at" in c:
        an += [(("src", c["gold_at"] - 1.7), "to", f"#{P('veins')} .v", {"strokeDashoffset": 0, "duration": 1.2, "ease": "power2.out", "stagger": 0.25}),
               (_src(c, "gold_at"), "slide-in", f"#{P('l2')}", {})]
    an += [(("src", fly - 0.3), "to", f"#{P('l1')}, #{P('l2')}, #{P('k1')}", {"opacity": 0, "duration": 0.3}),
           (("src", fly - 0.15), "to", f"#{P('k2')}", {"opacity": 1, "duration": 0.35}),
           (("src", fly - 0.3), "tween", f"#{P('earth')}", {"from": {"opacity": 0, "y": 160}, "to": {"opacity": 1, "y": 0, "duration": 0.9, "ease": "power3.out"}}),
           (("src", fly), "to", f"#{P('tail')}", {"opacity": 1, "duration": 0.4}),
           (("src", fly), "to", f"#{P('ast')}", {"x": -390, "duration": 3.7, "ease": "power1.inOut"}),
           (("src", fly), "to", f"#{P('ast')}", {"y": 98, "duration": 3.7, "ease": "power2.in"}),
           (("src", fly), "to", f"#{P('rock')}", {"scale": 0.62, "svgOrigin": "0 0", "duration": 3.7, "ease": "power1.in"}),
           (("src", fly + 3.5), "to", f"#{P('tail')}", {"opacity": 0, "duration": 0.25}),
           (("src", fly + 3.7), "tween", f"#{P('glow')}", {"from": {"opacity": 0, "scale": 0.2, "svgOrigin": "0 0"}, "to": {"opacity": 1, "scale": 1.6, "duration": 0.6, "ease": "power2.out"}}),
           (("src", fly + 3.7), "tween", f"#{P('ring')}", {"from": {"opacity": 0.95, "scale": 0.5, "svgOrigin": "0 0"}, "to": {"opacity": 0, "scale": 4.2, "duration": 1.1, "ease": "power2.out", "immediateRender": False}}),
           (("src", fly + 3.75), "scale-pop", f"#{P('l3')}", {})]
    return body, an


def supply_card(c, cid):
    """More supply -> less value: a stack of gold bars, a second stack (xN), then a value meter that drops.
    Keys: kicker, factor (e.g. "×2"), factor_label, more_at, value_kicker, value_at, drop_at, drop_to (0-1),
    drop_mark (e.g. "½"), drop_label; times = source."""
    P = lambda x: f"{cid}-{x}"  # noqa: E731
    ingot = lambda x, y: f'<use href="#{P("ing")}" x="{x}" y="{y}"/>'  # noqa: E731
    pile = ingot(0, 68) + ingot(104, 68) + ingot(52, 34)
    body = f"""<svg viewBox="0 0 968 420" xmlns="http://www.w3.org/2000/svg"><defs>
<linearGradient id="{P('bar')}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE08A"/><stop offset="0.5" stop-color="#F5B71F"/><stop offset="1" stop-color="#B57A06"/></linearGradient>
<g id="{P('ing')}"><path d="M10,0 L90,0 L100,34 L0,34 Z" fill="url(#{P('bar')})" stroke="#8A5A00" stroke-width="2"/><path d="M14,4 L86,4" stroke="#FFF3C4" stroke-width="3" opacity="0.8"/></g>
<marker id="{P('ah')}" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#F5B71F"/></marker></defs>
<g transform="translate(736,96)"><g id="{P('pa')}">{pile}</g></g>
<g transform="translate(520,96)"><g id="{P('pb')}">{pile}</g></g>
<path id="{P('arrow')}" d="M500,150 L425,150" stroke="#F5B71F" stroke-width="8" stroke-linecap="round" marker-end="url(#{P('ah')})" stroke-dasharray="80" stroke-dashoffset="80"/></svg>
<div class="kick" style="right:40px">{text(c.get("kicker", ""))}</div>
<div class="big" id="{P('x')}" style="right:56px;top:214px;font-size:96px;color:var(--accent-0)">{text(c.get("factor", "×2"))}</div>
<div class="lbl" id="{P('xl')}" style="right:236px;top:236px">{text(c.get("factor_label", ""))}</div>
<div class="kick" id="{P('k2')}" style="left:110px;opacity:0">{text(c.get("value_kicker", ""))}</div>
<div class="meter" id="{P('m')}"><div class="fill" id="{P('f')}"></div><div class="half"></div></div>
<div class="big" id="{P('h')}" style="left:262px;top:104px;font-size:110px;color:#FF5A5F">{text(c.get("drop_mark", "½"))}</div>
<div class="lbl" id="{P('hl')}" style="left:262px;top:236px">{text(c.get("drop_label", ""))}</div>"""
    drop = c.get("drop_to", 0.5)
    an = [(0.25, "tween", f"#{P('pa')}", {"from": {"opacity": 0, "y": 30}, "to": {"opacity": 1, "y": 0, "duration": 0.45, "ease": "back.out(1.6)"}}),
          (_src(c, "more_at"), "tween", f"#{P('pb')}", {"from": {"opacity": 0, "x": 200}, "to": {"opacity": 1, "x": 0, "duration": 0.55, "ease": "power3.out"}}),
          (_src(c, "more_at"), "scale-pop", f"#{P('x')}", {}),
          (("src", c["more_at"] + 0.3), "slide-in", f"#{P('xl')}", {}),
          (("src", c["value_at"] - 0.4), "to", f"#{P('arrow')}", {"strokeDashoffset": 0, "duration": 0.5, "ease": "power2.out"}),
          (_src(c, "value_at"), "to", f"#{P('k2')}", {"opacity": 1, "duration": 0.4}),
          (_src(c, "value_at"), "tween", f"#{P('m')}", {"from": {"opacity": 0, "y": 20}, "to": {"opacity": 1, "y": 0, "duration": 0.4}}),
          (_src(c, "value_at"), "tween", f"#{P('f')}", {"from": {"height": "0%"}, "to": {"height": "100%", "duration": 0.7, "ease": "power2.out"}}),
          (_src(c, "drop_at"), "to", f"#{P('f')}", {"height": f"{round(drop * 100)}%", "background": "linear-gradient(to top,#8E1F23,#FF5A5F)", "duration": 0.9, "ease": "power3.inOut"}),
          (("src", c["drop_at"] + 0.3), "scale-pop", f"#{P('h')}", {}),
          (("src", c["drop_at"] + 0.5), "fade-in", f"#{P('hl')}", {})]
    return body, an


def card_html(cid, ctype, body):
    css = (BASE_CSS + "\n" + TYPE_CSS[ctype]).replace("CARD", f'.card[data-card-id="{cid}"]')
    return f'<div class="card" data-card-id="{cid}">\n<style>\n{css}\n</style>\n<div class="root" dir="rtl">\n{body}\n</div>\n</div>\n'


def gsap(kind, sel, t, p):
    if kind == "fade-in":
        return f"tl.fromTo('{sel}',{{opacity:0}},{{opacity:1,duration:0.4,ease:'power2.out'}},{t});"
    if kind == "slide-in":
        return f"tl.fromTo('{sel}',{{opacity:0,x:60}},{{opacity:1,x:0,duration:0.45,ease:'power2.out'}},{t});"
    if kind == "scale-pop":
        return f"tl.fromTo('{sel}',{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.45,ease:'back.out(1.6)'}},{t});"
    if kind == "mask":
        return f"tl.fromTo('{sel}',{{clipPath:'inset(0 0 0 100%)'}},{{clipPath:'inset(0 0 0 0%)',duration:0.6,ease:'power2.inOut'}},{t});"
    if kind == "grow":
        return f"tl.fromTo('{sel}',{{width:0}},{{width:{p['w']},duration:1.0,ease:'power2.inOut'}},{t});"
    if kind == "count":
        return (f"(function(){{const o={{v:0}};tl.to(o,{{v:{p['to']},duration:0.9,ease:'power2.out',onUpdate:function(){{"
                f"const el=document.querySelector('{sel}');if(el)el.textContent=__fmt(o.v);}}}},{t});}})();")
    if kind == "tween":
        return f"tl.fromTo('{sel}',{json.dumps(p['from'], ensure_ascii=False)},{json.dumps(p['to'], ensure_ascii=False)},{t});"
    if kind == "to":
        return f"tl.to('{sel}',{json.dumps(p, ensure_ascii=False)},{t});"
    raise ValueError(kind)


def build(cfg):
    fps = cfg.get("fps", 24)
    tl = Timeline(cfg["pieces"], fps)
    D = tl.duration
    cards = []
    for i, c in enumerate(cfg["cards"]):
        cards.append((c.get("id", f"c{i + 1}"), c, tl.q(tl.map(c["start"])), tl.q(tl.map(c["end"]))))
    if cfg.get("endcard"):
        secs = cfg["endcard"].get("seconds", 2.6)
        cards.append(("end", {"type": "end", "lines": cfg["endcard"]["lines"]}, tl.q(D - secs), tl.q(D)))
    for (a_id, _, _, a_end), (b_id, _, b_start, _) in zip(cards, cards[1:]):
        if b_start < a_end:
            raise ValueError(f"cards {a_id} and {b_id} overlap")

    overlay = cfg.get("layout") == "overlay"
    band = PANEL_BAND if overlay else BAND
    host_from = "{opacity:0,y:-24,scale:%.2f}" % (PANEL_SCALE - 0.04) if overlay else "{opacity:0,y:30}"
    host_to = "{opacity:1,y:0,scale:%.2f,duration:0.45,ease:'power3.out'}" % PANEL_SCALE if overlay else "{opacity:1,y:0,duration:0.4,ease:'power2.out'}"
    js = ["const tl=window.gsap.timeline({paused:true});",
          "window.__fmt=function(v){return String(Math.round(v));};"]
    hosts, files = [], {}
    for cid, c, s, e in cards:
        body, an = card_body(c, cid)
        files[cid] = card_html(cid, c["type"], body)
        hosts.append(f'<div class="card-host clip" id="card-{cid}" data-card-id="{cid}" data-start="{s:.4f}" '
                     f'data-duration="{e - s:.4f}" data-track-index="2" style="{band};visibility:hidden;opacity:0;">\n{files[cid]}</div>')
        host = f".card-host[data-card-id=\"{cid}\"]"
        js.append(f"tl.set('{host}',{{visibility:'visible'}},{s});")
        js.append(f"tl.fromTo('{host}',{host_from},{host_to},{s});")
        for when, kind, el, p in an:
            t = tl.q(tl.map(when[1])) if isinstance(when, tuple) else tl.q(s + when)
            t = min(max(t, s), e)
            js.append(gsap(kind, f'.card[data-card-id="{cid}"] {el}', t, p))
        if cid != "end":
            js.append(f"tl.to('{host}',{{opacity:0,duration:0.3,ease:'power2.in'}},{tl.q(e - 0.3)});")
            js.append(f"tl.set('{host}',{{visibility:'hidden'}},{e});")

    caps = close_gaps([(tl.map(a), tl.map(b), t) for a, b, t in cfg.get("captions", [])])
    capdivs = [f'<div class="cap clip" id="cap-{i}" data-start="{tl.q(s):.4f}" data-duration="{tl.q(e) - tl.q(s):.4f}" '
               f'data-track-index="3"><span dir="rtl">{text(t)}</span></div>' for i, (s, e, t) in enumerate(caps)]

    tag = ""
    if cfg.get("speaker"):
        name, ts, te = cfg["speaker"]
        tag = f'<div id="name-tag" dir="rtl">{text(name)}</div>'
        js.append(f"tl.fromTo('#name-tag',{{opacity:0,x:40}},{{opacity:1,x:0,duration:0.4,ease:'power2.out'}},{tl.q(tl.map(ts))});")
        js.append(f"tl.to('#name-tag',{{opacity:0,duration:0.3}},{tl.q(tl.map(te) - 0.3)});")
    js.append("window.__timelines=window.__timelines||{};window.__timelines['talking-head-recut']=tl;")

    index = f"""<!doctype html>
<html lang="he">
<head>
<meta charset="utf-8" />
<style>
@font-face{{font-family:'Heebo ExtraBold';src:url('fonts/Heebo-ExtraBold.woff2') format('woff2');font-display:block}}
@font-face{{font-family:'Heebo Black';src:url('fonts/Heebo-Black.woff2') format('woff2');font-display:block}}
@font-face{{font-family:'Heebo SemiBold';src:url('fonts/Heebo-SemiBold.woff2') format('woff2');font-display:block}}
:root{{--bg:#070908;--text:#ffffff;--accent-0:{ACCENT};--accent-1:#E8F5EE;--accent-2:#9AA6A0;--accent-3:#7A5A0E;--accent-4:#C9D6CF}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#070908;font-family:'Heebo ExtraBold','Heebo Black'}}
#stage{{position:relative;width:100%;height:100%;overflow:hidden;background:#070908}}
.video-wrapper{{position:absolute;left:0;top:0;width:1080px;height:{1920 if overlay else 1216}px;overflow:hidden}}
.video-wrapper video{{width:100%;height:100%;object-fit:cover}}
#topfade{{position:absolute;left:0;top:0;width:1080px;height:380px;background:linear-gradient(to bottom,rgba(7,9,8,0.75),rgba(7,9,8,0))}}
#fade{{position:absolute;left:0;top:936px;width:1080px;height:280px;background:linear-gradient(to bottom,rgba(7,9,8,0),rgba(7,9,8,1))}}
#logo{{position:absolute;left:56px;top:150px;width:210px;height:auto;filter:drop-shadow(0 4px 14px rgba(0,0,0,0.6))}}
#name-tag{{position:absolute;right:56px;top:170px;font-family:'Heebo ExtraBold';font-size:34px;color:#06100B;background:{ACCENT};padding:8px 22px;border-radius:999px;opacity:0}}
.card-host{{position:absolute;pointer-events:none;overflow:hidden}}
.card-host .card{{position:relative;width:100%;height:100%;overflow:hidden}}
.cap{{position:absolute;left:56px;top:1010px;width:860px;height:220px;display:flex;align-items:center;justify-content:center;text-align:center;font-family:'Heebo ExtraBold';font-size:60px;line-height:1.15;color:#fff;text-shadow:0 3px 0 #000,0 0 18px rgba(0,0,0,0.85)}}
.cap .em{{color:{ACCENT}}}
</style>
</head>
<body>
<div id="stage" data-composition-id="talking-head-recut" data-start="0" data-duration="{D:.4f}" data-fps="{fps}" data-width="1080" data-height="1920">
<div class="video-wrapper" id="video-wrap">
<video id="bg-video" src="input-video.mp4" playsinline data-has-audio="true" data-start="0" data-duration="{D:.4f}" data-track-index="1"></video>
</div>
{'' if overlay else '<div id="fade"></div>' + chr(10) + '<div id="topfade"></div>'}
{'' if overlay else '<img id="logo" src="logo.png" alt="אחים להשקעות" />'}
{tag}
{chr(10).join(hosts)}
{chr(10).join(capdivs)}
<script src="vendor/gsap.min.js"></script>
<script>
(function(){{
{chr(10).join(js)}
}})();
</script>
</div>
</body>
</html>
"""
    words = []
    for s, e, t in caps:
        ws = re.sub(r"[\[\]|]", " ", t).split()
        total = sum(len(w) for w in ws) or 1
        cur = s
        for w in ws:
            d = (e - s) * len(w) / total
            words.append({"text": w, "start": round(cur, 3), "end": round(cur + d, 3)})
            cur += d
    storyboard = {"schemaVersion": 3,
                  "composition": {"fps": fps, "width": 1080, "height": 1920, "durationSeconds": D,
                                  "layout": "portrait", "themeId": "investing-bros-gold", "seed": 6},
                  "videoTrack": {"sourcePath": "input-video.mp4", "startSec": 0, "endSec": D,
                                 "bounds": {"x": 0, "y": 0, "width": 1080, "height": 1920 if overlay else 1216}},
                  "subtitles": {"enabled": True},
                  "cards": [{"id": cid, "type": c["type"], "startSec": s, "endSec": e, "zone": "lower-third", "accentIndex": 0}
                            for cid, c, s, e in cards]}
    return index, files, storyboard, words


REQUIRED = ["input-video.mp4", "logo.png", "vendor/gsap.min.js", "fonts/Heebo-ExtraBold.woff2",
            "fonts/Heebo-Black.woff2", "fonts/Heebo-SemiBold.woff2"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    pub = os.path.join(a.project, "public")
    missing = [f for f in REQUIRED if not os.path.exists(os.path.join(pub, f))]
    if missing:
        sys.exit("error: missing in public/: " + ", ".join(missing) + " (see the skill's Steps 2–3)")
    index, files, sb, words = build(cfg)
    os.makedirs(os.path.join(pub, "cards"), exist_ok=True)
    for cid, h in files.items():
        open(os.path.join(pub, "cards", f"{cid}.html"), "w", encoding="utf-8").write(h)
    open(os.path.join(pub, "index.html"), "w", encoding="utf-8").write(index)
    json.dump(sb, open(os.path.join(a.project, "storyboard.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(words, open(os.path.join(a.project, "transcript.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{cfg['name']}: {sb['composition']['durationSeconds']:.2f} s, {len(files)} card(s), "
          f"{len(cfg.get('captions', []))} caption(s) -> {pub}/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
