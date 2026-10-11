"""Workflow figure (redesign). Run: python3 make_workflow.py out.svg"""
import sys
from fontTools.ttLib import TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

INK = "#1F2933"; ROUTE = "#475569"; SOFT = "#8A94A3"
LLM_C = "#2F5DB8"; HUM_C = "#C27C12"
W, H = 1600, 860
out = []
def add(s): out.append(s)

# ---------- text as Seravek outlines -------------------------------------
_TTC = TTCollection("/System/Library/Fonts/Supplemental/Seravek.ttc")
_FACES = {"400": _TTC.fonts[0], "500": _TTC.fonts[3], "700": _TTC.fonts[9]}
def _kern(font):
    pairs = {}
    if "GPOS" not in font: return pairs
    for lk in font["GPOS"].table.LookupList.Lookup:
        if lk.LookupType != 2: continue
        for st in lk.SubTable:
            fmt = getattr(st, "Format", None)
            if fmt == 1:
                for i, a in enumerate(st.Coverage.glyphs):
                    for r in st.PairSet[i].PairValueRecord:
                        v = getattr(r.Value1, "XAdvance", 0) if r.Value1 else 0
                        if v: pairs.setdefault((a, r.SecondGlyph), v)
            elif fmt == 2:
                c1, c2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs
                for a in st.Coverage.glyphs:
                    rec = st.Class1Record[c1.get(a, 0)]
                    for b, k in c2.items():
                        v1 = rec.Class2Record[k].Value1
                        v = getattr(v1, "XAdvance", 0) if v1 else 0
                        if v: pairs.setdefault((a, b), v)
    return pairs
_KERNS = {}
def text(x, y, s, size=26, weight="400", anchor="start", fill=INK):
    f = _FACES[weight]
    if id(f) not in _KERNS: _KERNS[id(f)] = _kern(f)
    kern, gs, cmap, hm = _KERNS[id(f)], f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    sc = size / f["head"].unitsPerEm
    names = [cmap.get(ord(c), ".notdef") for c in s]
    adv = [hm[g][0] + (kern.get((g, names[i+1]), 0) if i+1 < len(names) else 0) for i, g in enumerate(names)]
    wdt = sum(adv) * sc
    x0 = {"start": x, "middle": x - wdt/2, "end": x - wdt}[anchor]
    pen = SVGPathPen(gs); cur = 0
    for g, a in zip(names, adv):
        gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, x0 + cur*sc, y))); cur += a
    add(f'<path d="{pen.getCommands()}" fill="{fill}"/>')

def tw(s, size=26, weight="400"):
    f = _FACES[weight]
    if id(f) not in _KERNS: _KERNS[id(f)] = _kern(f)
    kern, cmap, hm = _KERNS[id(f)], f.getBestCmap(), f["hmtx"]
    names = [cmap.get(ord(c), ".notdef") for c in s]
    return sum(hm[g][0] + (kern.get((g, names[i+1]), 0) if i+1 < len(names) else 0)
               for i, g in enumerate(names)) * size / f["head"].unitsPerEm

# ---------- arrows ---------------------------------------------------------
def _marker(mid, col):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>')
ARROW = "#334155"
COLS = {"llm": ARROW, "human": ARROW, "route": ARROW}
def line(pts, who="route", head=True, width=None):
    w = width or 2.75
    d = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    mk = f' marker-end="url(#m-{who})"' if head else ""
    add(f'<path d="{d}" fill="none" stroke="{COLS[who]}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"{mk}/>')

# ---------- Human / LLM badges --------------------------------------------
BFS = 27                                   # badge font size (about 7 pt in print)
BH, BGAP = 40, 14
BADGE = {"human": ("#FBE9D0", "#C47F1A", "#7A4A06", "Human"),
         "llm":   ("#DCE5F7", "#3F64B0", "#1E3A73", "LLM")}
for _k, _v in BADGE.items():
    BADGE[_k] = _v + (tw(_v[3], BFS, "700") + 30,)
def badge(cx, cy, who):
    fill, stroke, tc, lab, w = BADGE[who]
    add(f'<rect x="{cx-w/2:.1f}" y="{cy-BH/2:.1f}" width="{w:.1f}" height="{BH}" rx="{BH/2}" fill="{fill}" stroke="{stroke}" stroke-width="2.2"/>')
    text(cx, cy + BFS*0.36, lab, BFS, weight="700", anchor="middle", fill=tc)
def hbadge(x1, x2, y, who):  badge((x1 + x2) / 2, y - BGAP - BH/2, who)
def vbadge(x, y1, y2, who):  badge(x + BGAP + BADGE[who][4] / 2, (y1 + y2) / 2, who)

# ---------- icons (drawn on an 86 x 110 base, scaled by K) ---------------
K = 0.80
IW, IH = 86 * K, 110 * K
SW = 4                                       # base stroke (renders as 3.2)
def _page(dashed=False, faint=False):
    f, r, w, h = 22, 7, 86, 110
    o = (f"M{r},0 H{w-f} L{w},{f} V{h-r} Q{w},{h} {w-r},{h} H{r} Q0,{h} 0,{h-r} V{r} Q0,0 {r},0 Z")
    if faint:
        add(f'<path d="{o}" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
        add(f'<path d="M{w-f},0 V{f} H{w}" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    elif dashed:
        add(f'<path d="{o}" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}" stroke-dasharray="10 7" stroke-linecap="round"/>')
        add(f'<path d="M{w-f},0 V{f} H{w} Z" fill="#E2E8F0" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    else:
        add(f'<path d="{o}" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
        add(f'<path d="M{w-f},0 V{f} H{w}" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
def _bar(x1, y, x2, w=4):
    add(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" stroke-width="{w}" stroke-linecap="round"/>')
def _schema():
    _page()
    for i in range(5):
        y = 40 + i*15; _bar(15, y, 30); _bar(39, y, 70 - (i % 2)*12)
def _code(dashed=False):
    _page(dashed=dashed); cx, cy = 43, 62
    add(f'<path d="M{cx-11},{cy-13} L{cx-25},{cy} L{cx-11},{cy+13} M{cx+11},{cy-13} L{cx+25},{cy} L{cx+11},{cy+13} '
        f'M{cx+5},{cy-17} L{cx-5},{cy+17}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
def _person():
    add(f'<circle cx="43" cy="26" r="25" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}"/>')
    add(f'<path d="M0,110 V94 Q0,56 43,56 Q86,56 86,94 V110 Z" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
def _manuscript():
    for dx, dy in [(14, -10), (7, -5)]:
        add(f'<rect x="{dx}" y="{dy}" width="80" height="110" rx="7" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}"/>')
    add(f'<rect x="0" y="0" width="80" height="110" rx="7" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}"/>')
    _bar(14, 26, 56, 7)
    for i, r in enumerate([14, 14, 26, 14, 14, 34]):
        _bar(14, 46 + i*11, 80 - r, 3.2)
def _alternatives():
    add(f'<rect x="0" y="0" width="86" height="110" rx="12" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}"/>')
    for i in range(3):
        y = 32 + i*25
        _bar(38, y, 70)
        add(f'<circle cx="21" cy="{y}" r="8.5" fill="none" stroke="{INK}" stroke-width="3"/>')
def _estimates():
    add(f'<rect x="0" y="0" width="86" height="110" rx="12" fill="#FFFFFF" stroke="{INK}" stroke-width="{SW}"/>')
    _bar(14, 92, 72, 3)
    for i, (a, b) in enumerate([(22, 54), (32, 64), (20, 44)]):
        y = 26 + i*22
        add(f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="{INK}" stroke-width="3"/>')
        add(f'<circle cx="{a}" cy="{y}" r="7" fill="{INK}"/>')
        add(f'<circle cx="{b}" cy="{y}" r="7" fill="#FFFFFF" stroke="{INK}" stroke-width="3"/>')
DRAW = {"schema": _schema, "code": lambda: _code(False), "gencode": lambda: _code(True),
        "person": _person, "manuscript": _manuscript, "alternatives": _alternatives,
        "estimates": _estimates, "faint": lambda: _page(faint=True), "dashback": lambda: _page(dashed=True)}
def icon(kind, x, y):
    add(f'<g transform="translate({x:.1f} {y:.1f}) scale({K})">'); DRAW[kind](); add('</g>')
FAN = 13
def _thinback(dashed):
    # back copy in a stack: same ink, finer line, no content
    f, r, w, h = 22, 7, 86, 110
    o = (f"M{r},0 H{w-f} L{w},{f} V{h-r} Q{w},{h} {w-r},{h} H{r} Q0,{h} 0,{h-r} V{r} Q0,0 {r},0 Z")
    dash = ' stroke-dasharray="9 7"' if dashed else ''
    add(f'<path d="{o}" fill="#FFFFFF" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"{dash}/>')
    add(f'<path d="M{w-f},0 V{f} H{w}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"{dash}/>')
DRAW["thin"] = lambda: _thinback(False)
DRAW["thindash"] = lambda: _thinback(True)
def stack(kind, x, y):
    back = "thindash" if kind == "gencode" else "thin"
    for k in (2, 1): icon(back, x + k*FAN, y - k*FAN)
    icon(kind, x, y)

# ---------- type scale (print sizes at full text width, ~0.25 pt per unit)
T_TITLE, T_SUB, T_LAB, T_LEG = 42, 31, 32, 31     # ~10.5, 8, 8, 8 pt
LINE = 36                                          # line spacing for two-line labels

# ---------- canvas ---------------------------------------------------------
W, H = 1600, 914
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add("<defs>" + "".join(_marker(f"m-{k}", c) for k, c in COLS.items()) + "</defs>")
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

G = 12
def panel(x, y, w, h, fill, stroke, title, sub):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    text(x + 26, y + 50, title, T_TITLE, weight="700", fill="#1E293B")
    text(x + 26, y + 88, sub, T_SUB, fill="#5A6578")

LX, LW = 10, 540
RX = LX + LW + 16; RW = 1590 - RX
TOPY, TOPH = 10, 360
BOTY, BOTH = TOPY + TOPH + 16, 454
PANEL_BOT = BOTY + BOTH
panel(LX, 10, LW, PANEL_BOT - 10, "#EEF2F8", "#D5DDEA", "Create the schema", "by hand or from a manuscript")
panel(RX, TOPY, RW, TOPH, "#ECF5EF", "#D2E5D8", "Reproduce the analysis", "generate, validate and compare")
panel(RX, BOTY, RW, BOTH, "#F4F0F8", "#E1D8EC", "Explore alternatives", "expand the schema into a multiverse")

# ---------- left column ---------------------------------------------------
CX = 352
VLEN = 84
LABX = CX - IW/2 - 22                       # right edge of the column labels
P_TOP = 224
p_bot = P_TOP + IH
icon("person", CX - IW/2, P_TOP)
text(LABX, P_TOP + IH/2 - 6, "Authored", T_LAB, anchor="end")
text(LABX, P_TOP + IH/2 - 6 + LINE, "manually", T_LAB, anchor="end")
SCH_Y = p_bot + G + VLEN + G
SCH_C = SCH_Y + IH/2
line([(CX, p_bot + G), (CX, SCH_Y - G)], "human"); vbadge(CX, p_bot + G, SCH_Y - G, "human")
icon("schema", CX - IW/2, SCH_Y)
text(LABX, SCH_C + 12, "Schema", T_LAB, weight="700", anchor="end")
M_Y = SCH_Y + IH + G + VLEN + G + 10 * K
line([(CX, M_Y - 10*K - G), (CX, SCH_Y + IH + G)], "llm"); vbadge(CX, SCH_Y + IH + G, M_Y - 10*K - G, "llm")
icon("manuscript", CX - IW/2, M_Y)
mc = M_Y + IH/2
text(LABX, mc - 6, "Generated from", T_LAB, anchor="end")
text(LABX, mc - 6 + LINE, "manuscript", T_LAB, anchor="end")

BUS = LX + LW - 24
line([(CX + IW/2 + G, SCH_C), (BUS, SCH_C)], head=False)

# ---------- columns shared by both paths ---------------------------------
PITCH = 305
C3 = 1590 - 40 - tw("Generated code", T_LAB)/2 - IW/2      # keep labels inside the panel
C2 = C3 - PITCH; C1 = C2 - PITCH
# top path
TC = TOPY + 196
TY = TC - IH/2
LAB_Y = TY + IH + 44
line([(BUS, SCH_C), (BUS, TC)], head=False)
line([(BUS, TC), (C1 - G, TC)], "llm"); hbadge(C1 - PITCH + IW + G, C1 - G, TC, "llm")
icon("gencode", C1, TY);   text(C1 + IW/2, LAB_Y, "Generated code", T_LAB, anchor="middle")
line([(C1 + IW + G, TC), (C2 - G, TC)], "llm"); hbadge(C1 + IW + G, C2 - G, TC, "llm")
icon("code", C2, TY);      text(C2 + IW/2, LAB_Y, "Validated code", T_LAB, anchor="middle")
line([(C2 + IW + G, TC), (C3 - G, TC)], "human"); hbadge(C2 + IW + G, C3 - G, TC, "human")
icon("estimates", C3, TY); text(C3 + IW/2, LAB_Y, "Estimates vs.", T_LAB, anchor="middle")
text(C3 + IW/2, LAB_Y + LINE, "reported", T_LAB, anchor="middle")

# bottom path: alternatives below the branch
MID = BOTY + 196
NX, NR = RX + 128, 13
line([(BUS, SCH_C), (BUS, MID), (NX - NR, MID)], head=False)
add(f'<circle cx="{NX}" cy="{MID}" r="{NR}" fill="#FFFFFF" stroke="{ARROW}" stroke-width="2.5"/>')
add(f'<path d="M{NX-7},{MID} H{NX+7} M{NX},{MID-7} V{MID+7}" stroke="{ARROW}" stroke-width="2.5" stroke-linecap="round"/>')
line([(NX + NR, MID), (C1 - G, MID)], "route")
ALEN = 112                                 # long enough that the badge clears the stacks
AY = MID + NR + 3 + ALEN + G
icon("alternatives", NX - IW/2, AY)
line([(NX, AY - G), (NX, MID + NR + 3)], "human")
badge(NX + BGAP + BADGE["human"][4] / 2, (MID + NR + 3 + AY - G) / 2 + 16, "human")   # nudged down, clear of the stack
text(NX + IW/2 + 20, AY + IH/2 - 4, "Alternatives", T_LAB)
text(NX + IW/2 + 20, AY + IH/2 - 4 + 36, "three options", T_SUB, fill="#5A6578")
SY = MID - IH/2
stack("schema", C1, SY); stack("gencode", C2, SY); stack("code", C3, SY)
line([(C1 + IW + 2*FAN + G, MID), (C2 - G, MID)], "llm"); hbadge(C1 + IW + 2*FAN + G, C2 - G, MID, "llm")
line([(C2 + IW + 2*FAN + G, MID), (C3 - G, MID)], "llm"); hbadge(C2 + IW + 2*FAN + G, C3 - G, MID, "llm")

# ---------- legend (one line, below the panels) --------------------------
LY = PANEL_BOT + 44
text(36, LY + 11, "Who performs each step:", T_LEG, weight="500", fill=INK)
x = 36 + tw("Who performs each step:", T_LEG, "500") + 28
for who, lab in [("human", "analyst or reader"), ("llm", "language model")]:
    w = BADGE[who][4]; badge(x + w/2, LY, who)
    text(x + w + 14, LY + 11, lab, T_LEG, fill=INK)
    x += w + 14 + tw(lab, T_LEG) + 48

add("</svg>")
open(sys.argv[1], "w").write("\n".join(out))
