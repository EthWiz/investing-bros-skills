"""Reusable, source-timed illustrations for money roles, coin dilution and fiat trust.

These scenes show mechanisms without inventing rates or metal percentages.
Hebrew labels are supplied by the edit JSON and rendered as native HTML text.
"""

SCENE_TYPES = {"money_roles", "coin_dilution", "currency_trust"}
SCENE_CSS = """CARD .root{display:block;padding:0;position:relative;background:linear-gradient(135deg,rgba(9,24,46,0.98),rgba(3,11,24,0.98));border:2px solid #B98621;box-shadow:inset 0 1px 0 rgba(255,231,155,0.3);overflow:hidden}
CARD svg{position:absolute;inset:0;width:968px;height:420px}
CARD .scene-label{position:absolute;text-align:center;line-height:1.12;font-family:'Heebo ExtraBold',sans-serif;color:#fff}
CARD .scene-kicker{top:22px;left:34px;width:900px;font-size:48px;color:#F5B71F}
CARD .scene-heading{top:88px;width:390px;font-size:52px}
CARD .scene-foot{top:350px;left:36px;width:896px;font-size:50px;font-family:'Heebo Black',sans-serif}
CARD .scene-detail{font-size:44px;color:#E6D2A0}
CARD .scene-hidden{opacity:0}
CARD .scene-gold{color:#F5B71F}
"""


def _defs(cid):
    return f"""<defs>
<radialGradient id="{cid}-gold" cx="30%" cy="20%" r="90%"><stop stop-color="#FFF1B9"/><stop offset="0.34" stop-color="#F5B71F"/><stop offset="0.65" stop-color="#C38C18"/><stop offset="0.86" stop-color="#FFE8A2"/><stop offset="1" stop-color="#9D6713"/></radialGradient>
<linearGradient id="{cid}-steel" x2="0.85" y2="1"><stop stop-color="#EEF2F8"/><stop offset="0.3" stop-color="#748398"/><stop offset="0.58" stop-color="#D8DFE7"/><stop offset="1" stop-color="#4D5D73"/></linearGradient>
<linearGradient id="{cid}-navy" x2="1" y2="1"><stop stop-color="#263D5C"/><stop offset="1" stop-color="#0B1525"/></linearGradient>
<pattern id="{cid}-grain" width="11" height="11" patternUnits="userSpaceOnUse"><circle cx="2" cy="3" r="0.9" fill="#FFF3C6" opacity="0.26"/><circle cx="8" cy="7" r="0.7" fill="#161F31" opacity="0.28"/></pattern>
<filter id="{cid}-glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="5"/></filter>
</defs>"""


def _coin(cid, name, x, y, r=76):
    return f"""<g transform="translate({x},{y})"><g id="{cid}-{name}" opacity="0">
<ellipse cx="0" cy="{r + 10}" rx="{r * 0.8}" ry="10" fill="#000" opacity="0.3"/>
<circle r="{r}" fill="url(#{cid}-gold)" stroke="#8E6117" stroke-width="5"/>
<circle r="{r - 9}" fill="none" stroke="#FFE8A6" stroke-width="3" opacity="0.85"/>
<circle r="{r - 20}" fill="none" stroke="#835710" stroke-width="2" opacity="0.6"/>
<circle r="{r - 12}" fill="url(#{cid}-grain)"/>
<path d="M{-r * 0.55},{-r * 0.45} Q0,{-r * 0.88} {r * 0.55},{-r * 0.45}" fill="none" stroke="#FFF5CE" stroke-width="4" opacity="0.8"/>
</g></g>"""


def _label(text, cid, name, value, style="", classes=""):
    return f'<div id="{cid}-{name}" class="scene-label {classes}" style="{style}">{text(value)}</div>'


def money_roles(c, cid, text):
    """A payment moves between wallets; an abundant-gold hypothesis fails the saving test."""
    body = f"""<svg viewBox="0 0 968 420" xmlns="http://www.w3.org/2000/svg">{_defs(cid)}
<path d="M484,92 L484,322" stroke="#C69B3E" stroke-opacity="0.3" stroke-width="2"/>
<g id="{cid}-wallets">
<rect x="95" y="192" width="120" height="84" rx="16" fill="url(#{cid}-navy)" stroke="#C7D2E1" stroke-width="3"/>
<path d="M105,201 L201,201" stroke="#697B96" stroke-width="3"/>
<rect x="172" y="216" width="53" height="35" rx="9" fill="#334761" stroke="#CDD7E2" stroke-width="2"/>
<circle cx="188" cy="233" r="4" fill="#F5B71F"/>
<rect x="305" y="192" width="120" height="84" rx="16" fill="url(#{cid}-navy)" stroke="#C7D2E1" stroke-width="3"/>
<rect x="297" y="216" width="53" height="35" rx="9" fill="#334761" stroke="#CDD7E2" stroke-width="2"/>
<circle cx="333" cy="233" r="4" fill="#F5B71F"/>
<path id="{cid}-payment-path" d="M175,174 Q263,112 354,174" fill="none" stroke="#F5B71F" stroke-width="4" stroke-dasharray="220" stroke-dashoffset="220"/>
</g>
{_coin(cid, 'payment', 165, 156, 25)}
<g id="{cid}-vault"><rect x="634" y="160" width="170" height="144" rx="17" fill="url(#{cid}-navy)" stroke="#AEBBD0" stroke-width="4"/>
<rect x="646" y="172" width="146" height="120" rx="10" fill="none" stroke="#60748F" stroke-width="2"/>
<circle cx="718" cy="232" r="40" fill="url(#{cid}-steel)"/>
<circle cx="718" cy="232" r="25" fill="#17263D"/>
<path d="M718,198 V266 M684,232 H752 M694,208 L742,256 M694,256 L742,208" stroke="#B6C5D9" stroke-width="5"/>
</g>
{''.join(_coin(cid, f'abundant{i}', x, y, 18) for i, (x,y) in enumerate(((612,190),(831,180),(618,258),(840,251),(646,128),(800,129))))}
<path id="{cid}-save-cross" d="M657,170 L785,298 M785,170 L657,298" fill="none" stroke="#F5B71F" stroke-width="10" stroke-linecap="round" stroke-dasharray="370" stroke-dashoffset="370"/>
<path id="{cid}-trade-check" d="M360,303 L377,319 L411,283" fill="none" stroke="#F5B71F" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="80" stroke-dashoffset="80"/>
</svg>"""
    body += _label(text, cid, "k", c["kicker"], classes="scene-kicker")
    body += _label(text, cid, "trade", c["trade_label"], "left:63px;", "scene-heading")
    body += _label(text, cid, "save", c["save_label"], "left:521px;", "scene-heading")
    body += _label(text, cid, "conclusion", c["conclusion"], classes="scene-foot scene-hidden scene-gold")
    an = [(0.1, "tween", f"#{cid}-vault, #{cid}-wallets", {"from":{"opacity":0,"y":15}, "to":{"opacity":1,"y":0,"duration":0.6}})]
    for i in range(6):
        an.append((("src", c["abundant_at"] + i * 0.13), "tween", f"#{cid}-abundant{i}",
                   {"from":{"opacity":0,"y":-36,"rotation":-45,"svgOrigin":"0 0"},
                    "to":{"opacity":1,"y":0,"rotation":0,"duration":0.55,"ease":"back.out(1.5)"}}))
    an += [(("src", c["save_at"]), "to", f"#{cid}-save-cross", {"strokeDashoffset":0,"duration":0.8,"ease":"power2.inOut"}),
           (("src", c["trade_at"]), "to", f"#{cid}-payment-path", {"strokeDashoffset":0,"duration":0.8}),
           (("src", c["trade_at"]), "tween", f"#{cid}-payment", {"from":{"opacity":0,"x":0,"y":0,"svgOrigin":"0 0"}, "to":{"opacity":1,"x":185,"duration":1.3333,"ease":"power2.inOut"}}),
           (("src", c["trade_at"]), "to", f"#{cid}-payment", {"y":-24,"duration":0.625,"ease":"power1.out"}),
           (("src", c["trade_at"] + 0.6667), "to", f"#{cid}-payment", {"y":24,"duration":0.625,"ease":"power1.in"}),
           (("src", c["trade_at"] + 1.1), "to", f"#{cid}-trade-check", {"strokeDashoffset":0,"duration":0.55}),
           (("src", c["conclusion_at"]), "fade-in", f"#{cid}-conclusion", {})]
    return body, an


def coin_dilution(c, cid, text):
    """Cheap-metal particles enter a coin, changing its composition without a made-up ratio."""
    body = f"""<svg viewBox="0 0 968 420" xmlns="http://www.w3.org/2000/svg">{_defs(cid)}
<defs><clipPath id="{cid}-face-clip"><circle cx="238" cy="218" r="66"/></clipPath></defs>
{_coin(cid, 'before-coin', 742, 218)}
{_coin(cid, 'after-coin', 238, 218)}
<g id="{cid}-mixture" clip-path="url(#{cid}-face-clip)" opacity="0">
<circle cx="238" cy="218" r="66" fill="url(#{cid}-steel)"/>
<path d="M180,216 Q198,181 219,194 T260,203 T291,248 M192,245 Q214,222 239,239 T270,254 M219,157 L233,190 M252,203 L275,176" fill="none" stroke="#F5B71F" stroke-width="10" stroke-linecap="round" opacity="0.88"/>
<circle cx="238" cy="218" r="65" fill="url(#{cid}-grain)"/>
</g>
<path id="{cid}-mix-arrow" d="M626,218 H358" fill="none" stroke="#F5B71F" stroke-width="6" stroke-dasharray="270" stroke-dashoffset="270"/>
<path id="{cid}-arrow-tip" d="M382,199 L355,218 L382,237" fill="none" stroke="#F5B71F" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>
<g id="{cid}-filings">{''.join(f'<rect id="{cid}-filing{i}" x="{420 + i * 23}" y="{143 + (i%2)*12}" width="14" height="20" rx="3" fill="url(#{cid}-steel)" opacity="0"/>' for i in range(6))}</g>
</svg>"""
    body += _label(text, cid, "k", c["kicker"], classes="scene-kicker")
    body += _label(text, cid, "before", c["before_label"], "left:546px;", "scene-heading")
    body += _label(text, cid, "after", c["after_label"], "left:42px;", "scene-heading")
    body += _label(text, cid, "metal", c["metal_label"], "left:339px;top:260px;width:290px;", "scene-detail scene-hidden")
    body += _label(text, cid, "conclusion", c["conclusion"], classes="scene-foot scene-hidden scene-gold")
    an = [(0.15, "tween", f"#{cid}-before-coin", {"from":{"opacity":0,"scale":0.8,"svgOrigin":"0 0"}, "to":{"opacity":1,"scale":1,"duration":0.6,"ease":"back.out(1.4)"}}),
          (("src", c["mix_at"]), "to", f"#{cid}-mix-arrow", {"strokeDashoffset":0,"duration":0.8,"ease":"power2.inOut"}),
          (("src", c["mix_at"] + 0.5), "to", f"#{cid}-arrow-tip", {"opacity":1,"duration":0.3}),
          (("src", c["mix_at"] + 0.1), "tween", f"#{cid}-after-coin", {"from":{"opacity":0,"scale":0.84,"svgOrigin":"0 0"}, "to":{"opacity":1,"scale":1,"duration":0.7,"ease":"back.out(1.4)"}}),
          (("src", c["mix_at"]), "fade-in", f"#{cid}-metal", {})]
    for i in range(6):
        an.append((("src", c["mix_at"] + i * 0.15), "tween", f"#{cid}-filing{i}",
                   {"from":{"opacity":0,"x":0,"y":-22}, "to":{"opacity":0.95,"x":-174-i*16,"y":40+(i%3)*18,"rotation":45+i*17,"duration":1.15,"ease":"power2.in"}}))
    an += [(("src", c["mix_at"] + 1.0), "to", f"#{cid}-mixture", {"opacity":1,"duration":1.2,"ease":"power2.inOut"}),
           (("src", c["mix_at"] + 2.4), "to", f"#{cid}-filings", {"opacity":0,"duration":0.4}),
           (("src", c["conclusion_at"]), "fade-in", f"#{cid}-conclusion", {})]
    return body, an


def currency_trust(c, cid, text):
    """A spoken dollar example lights a connection to a central bank as 'trust' is explained."""
    value = c["value"]
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("currency_trust value must be a positive spoken amount")
    body = f"""<svg viewBox="0 0 968 420" xmlns="http://www.w3.org/2000/svg">{_defs(cid)}
<g id="{cid}-bill" opacity="0">
<rect x="80" y="142" width="278" height="135" rx="12" fill="#152943" stroke="#8C9AAD" stroke-width="3" transform="rotate(-5 219 210)"/>
<rect x="87" y="153" width="278" height="135" rx="12" fill="#1C3350" stroke="#B9C2CF" stroke-width="3" transform="rotate(3 226 220)"/>
<rect x="92" y="166" width="278" height="135" rx="12" fill="url(#{cid}-navy)" stroke="#E2D39C" stroke-width="4"/>
<rect x="104" y="178" width="254" height="111" rx="5" fill="none" stroke="#778CA5" stroke-width="2"/>
<path d="M115,212 Q175,174 225,212 T347,212 M115,250 Q175,212 225,250 T347,250" fill="none" stroke="#B4A879" stroke-width="2" opacity="0.35"/>
<circle cx="127" cy="193" r="8" fill="#F5B71F" opacity="0.55"/><circle cx="335" cy="274" r="8" fill="#F5B71F" opacity="0.55"/>
<text x="231" y="254" text-anchor="middle" font-family="Heebo Black" font-size="68" fill="#F5B71F">$</text>
</g>
<g id="{cid}-bank" opacity="0"><path d="M623,186 L750,124 L877,186 Z" fill="url(#{cid}-navy)" stroke="#AABCD3" stroke-width="3"/>
<path d="M640,290 H863 V311 H640 Z M629,313 H874" fill="url(#{cid}-navy)" stroke="#AABCD3" stroke-width="3"/>
{''.join(f'<rect x="{x}" y="194" width="26" height="96" rx="4" fill="url(#{cid}-steel)"/>' for x in (652,709,766,823))}
<path id="{cid}-bank-light" d="M623,186 L750,124 L877,186 M629,313 H874 M665,194 V290 M722,194 V290 M779,194 V290 M836,194 V290" fill="none" stroke="#F5B71F" stroke-width="5" opacity="0"/>
</g>
<path id="{cid}-connection" d="M387,229 H610" stroke="#394F6E" stroke-width="8" stroke-linecap="round"/>
<path id="{cid}-trust-line" d="M387,229 H610" stroke="#F5B71F" stroke-width="8" stroke-linecap="round" stroke-dasharray="225" stroke-dashoffset="225"/>
<circle id="{cid}-pulse" cx="390" cy="229" r="11" fill="#FFF1B9" opacity="0"/>
</svg>"""
    body += _label(text, cid, "k", c["kicker"], classes="scene-kicker")
    # The spoken total sits above the cash stack; do not depict a fictitious
    # banknote denomination or add unspoken denomination labels.
    body += _label(text, cid, "amount", f"${value:g}", "left:118px;top:78px;width:228px;font-size:70px;direction:ltr;opacity:0;", "scene-gold")
    body += _label(text, cid, "bank-label", c["bank_label"], "left:550px;top:71px;width:400px;font-size:44px;", "scene-hidden")
    body += _label(text, cid, "trust-label", c["trust_label"], "left:389px;top:269px;width:222px;font-size:48px;", "scene-hidden scene-gold")
    body += _label(text, cid, "conclusion", c["conclusion"], classes="scene-foot scene-hidden")
    an = [(("src", c["amount_at"]), "tween", f"#{cid}-bill", {"from":{"opacity":0,"y":24,"rotation":-5,"transformOrigin":"231px 234px"}, "to":{"opacity":1,"y":0,"rotation":0,"duration":0.7,"ease":"back.out(1.3)"}}),
          (("src", c["amount_at"] + 0.25), "fade-in", f"#{cid}-amount", {}),
          (("src", c["bank_at"]), "tween", f"#{cid}-bank", {"from":{"opacity":0,"y":24}, "to":{"opacity":1,"y":0,"duration":0.7,"ease":"power3.out"}}),
          (("src", c.get("bank_label_at", c["bank_at"]) + 0.15), "fade-in", f"#{cid}-bank-label", {}),
          (("src", c["trust_at"]), "to", f"#{cid}-trust-line", {"strokeDashoffset":0,"duration":1.0,"ease":"power2.inOut"}),
          (("src", c["trust_at"]), "tween", f"#{cid}-pulse", {"from":{"opacity":0,"attr":{"cx":390}}, "to":{"opacity":1,"attr":{"cx":608},"duration":1.0,"ease":"power2.inOut"}}),
          (("src", c["trust_at"] + 0.9), "to", f"#{cid}-bank-light", {"opacity":1,"duration":0.5}),
          (("src", c["trust_at"] + 1.125), "to", f"#{cid}-pulse", {"opacity":0,"duration":0.45}),
          (("src", c["trust_at"]), "fade-in", f"#{cid}-trust-label", {}),
          (("src", c["conclusion_at"]), "fade-in", f"#{cid}-conclusion", {})]
    return body, an


def scene_card(c, cid, text):
    return {"money_roles": money_roles, "coin_dilution": coin_dilution,
            "currency_trust": currency_trust}[c["type"]](c, cid, text)
