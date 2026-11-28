# ruff: noqa  (a drawing script: long coordinate lines on purpose)
"""Isometric cut-open house for the screen Stroom (fictional; ontwerpchat 28-11-2026).

Usage: python3 house_gen.py <out.svg> [2|3]
  2|3: number of storeys (3 = with attic, the default house; 2 = the alternative house)
Then: frontend/scripts/house_build.py turns both into house-3.webp and house-2.webp.

The positions in LAYOUTS (frontend/src/house.ts) come from the projection P(x, y, z) below;
whoever changes the drawing works them out again.
"""

import math
import sys

S = 33.0
C = math.cos(math.radians(30))
W, H = 1800, 1150
VERD = int(sys.argv[2]) if len(sys.argv) > 2 else 3
OX, OY = 800, 640 if VERD == 3 else 610
out = []


def P(x, y, z):
    return (OX + (x - y) * C * S, OY + (x + y) * 0.5 * S - z * S)


def hx(c):
    c = c.lstrip("#")
    return [int(c[i : i + 2], 16) for i in (0, 2, 4)]


def shade(c, f):
    r = hx(c)
    if f >= 1:
        r = [v + (255 - v) * (f - 1) for v in r]
    else:
        r = [v * f for v in r]
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in r)


def poly(pts, fill, stroke="none", sw=0.0, op=1.0, extra=""):
    d = " ".join("%.1f,%.1f" % P(*p) for p in pts)
    s = f'<polygon points="{d}" fill="{fill}"'
    if stroke != "none":
        s += f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'
    if op < 1:
        s += f' opacity="{op}"'
    out.append(s + extra + "/>")


def line(a, b, col, sw=1.0, extra=""):
    (x1, y1), (x2, y2) = P(*a), P(*b)
    out.append(
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"{extra}/>'
    )


def box(x, y, z, dx, dy, dz, col, top=None, edge=None, sw=0.6):
    x1, y1, z1 = x + dx, y + dy, z + dz
    e = edge or shade(col, 0.7)
    poly([(x, y1, z), (x1, y1, z), (x1, y1, z1), (x, y1, z1)], shade(col, 0.95), e, sw)
    poly([(x1, y, z), (x1, y1, z), (x1, y1, z1), (x1, y, z1)], shade(col, 0.8), e, sw)
    poly([(x, y, z1), (x1, y, z1), (x1, y1, z1), (x, y1, z1)], top or shade(col, 1.12), e, sw)


def rx(x, y0, y1, z0, z1, fill, **k):  # rectangle on the plane x = const
    poly([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], fill, **k)


def ry(y, x0, x1, z0, z1, fill, **k):  # rectangle on the plane y = const
    poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], fill, **k)


def rz(z, x0, x1, y0, y1, fill, **k):
    poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], fill, **k)


def ell_x(x, yc, zc, r, fill, n=36, **k):
    poly([(x, yc + r * math.cos(t), zc + r * math.sin(t)) for t in [2 * math.pi * i / n for i in range(n)]], fill, **k)


def ell_y(y, xc, zc, r, fill, n=36, **k):
    poly([(xc + r * math.cos(t), y, zc + r * math.sin(t)) for t in [2 * math.pi * i / n for i in range(n)]], fill, **k)


def window_y(y, x0, x1, z0, z1):
    ry(y, x0 - 0.08, x1 + 0.08, z0 - 0.08, z1 + 0.08, "#ffffff", stroke="#c9c4ba", sw=0.6)
    ry(y, x0, x1, z0, z1, "url(#sky)")
    xm = (x0 + x1) / 2
    line((xm, y, z0), (xm, y, z1), "#ffffff", 2.2)
    poly([(x0 + 0.15, y, z1 - 0.1), (x0 + 0.45, y, z1 - 0.1), (x0 + 0.15, y, z0 + 0.6)], "#ffffff", op=0.35)


def window_x(x, y0, y1, z0, z1):
    rx(x, y0 - 0.08, y1 + 0.08, z0 - 0.08, z1 + 0.08, "#ffffff", stroke="#c9c4ba", sw=0.6)
    rx(x, y0, y1, z0, z1, "url(#sky)")
    ym = (y0 + y1) / 2
    line((x, ym, z0), (x, ym, z1), "#ffffff", 2.2)
    poly([(x, y0 + 0.15, z1 - 0.1), (x, y0 + 0.45, z1 - 0.1), (x, y0 + 0.15, z0 + 0.6)], "#ffffff", op=0.35)


def plant(x, y, z, h=0.9, r=0.38):
    box(x - 0.18, y - 0.18, z, 0.36, 0.36, 0.38, "#c8a27a")
    cx, cy = P(x, y, z + 0.38 + h * 0.55)
    out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * S:.1f}" fill="url(#leaf)"/>')
    cx2, cy2 = P(x + 0.1, y - 0.1, z + 0.38 + h * 0.95)
    out.append(f'<circle cx="{cx2:.1f}" cy="{cy2:.1f}" r="{r * S * 0.7:.1f}" fill="url(#leaf)"/>')


def tree(x, y, h=4.2, r=1.5):
    sx, sy = P(x, y, 0)
    out.append(f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{r * S * 1.1:.1f}" ry="{r * S * 0.55:.1f}" fill="#000" opacity="0.10"/>')
    box(x - 0.13, y - 0.13, 0, 0.26, 0.26, h * 0.55, "#7a5a40")
    for dx, dy, dz, rr in [
        (0, 0, h * 0.62, r),
        (-0.4, 0.5, h * 0.82, r * 0.78),
        (0.45, -0.3, h * 0.92, r * 0.7),
        (0, 0, h * 1.08, r * 0.6),
    ]:
        cx, cy = P(x + dx, y + dy, dz)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * S:.1f}" fill="url(#leaf)"/>')


def shrub(x, y, r=0.55):
    for dx, dy, rr in [(0, 0, r), (0.5, 0.2, r * 0.8), (-0.3, 0.45, r * 0.75)]:
        cx, cy = P(x + dx, y + dy, rr * 0.8)
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{rr * S:.1f}" fill="url(#leaf2)"/>')


# ---------------------------------------------------------------- defs (transparent background)
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
out.append("""<defs>
<linearGradient id="sky" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#bfe0f5"/><stop offset="1" stop-color="#7fb6dc"/></linearGradient>
<radialGradient id="leaf" cx="0.35" cy="0.3" r="0.75"><stop offset="0" stop-color="#9fd27a"/><stop offset="0.6" stop-color="#5fa548"/><stop offset="1" stop-color="#3f7d35"/></radialGradient>
<radialGradient id="leaf2" cx="0.35" cy="0.3" r="0.75"><stop offset="0" stop-color="#9fd27a"/><stop offset="1" stop-color="#3f7d35"/></radialGradient>
<linearGradient id="pv" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2d4f8f"/><stop offset="0.5" stop-color="#1d3567"/><stop offset="1" stop-color="#2d4f8f"/></linearGradient>
<linearGradient id="grass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9fd07a"/><stop offset="1" stop-color="#7fbc5e"/></linearGradient>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>""")
out.append("<g>")

# shadow under the island
cx, cy = P(1, 6, -3.2)
out.append(f'<ellipse cx="{cx:.0f}" cy="{cy:.0f}" rx="560" ry="120" fill="#5a6b7a" opacity="0.22" filter="url(#soft)"/>')

# ---------------------------------------------------------------- island
IX0, IX1, IY0, IY1 = -10.0, 11.6, -2.2, 14.6
poly([(IX0, IY1, -1.3), (IX1, IY1, -1.3), (IX1, IY1, 0), (IX0, IY1, 0)], "#8b6a4c")
poly([(IX1, IY0, -1.3), (IX1, IY1, -1.3), (IX1, IY1, 0), (IX1, IY0, 0)], "#735638")
poly([(IX0, IY1, -0.25), (IX1, IY1, -0.25), (IX1, IY1, 0), (IX0, IY1, 0)], "#6fae52")
poly([(IX1, IY0, -0.25), (IX1, IY1, -0.25), (IX1, IY1, 0), (IX1, IY0, 0)], "#5e9a45")
rz(0, IX0, IX1, IY0, IY1, "url(#grass)")
# drive and path
rz(0.01, 0.6, 7.6, 9.0, 14.6, "#cfcac1")
for i in range(1, 12):
    line((0.6, 9.0 + i * 0.5, 0.012), (7.6, 9.0 + i * 0.5, 0.012), "#bdb7ac", 0.7)
for i in range(1, 14):
    line((0.6 + i * 0.5, 9.0, 0.012), (0.6 + i * 0.5, 14.6, 0.012), "#bdb7ac", 0.7)
rz(0.01, -4.7, 0.6, 3.6, 4.8, "#d8d3ca")  # path to the shed
rz(0.01, -0.3, 10.4, 7.2, 9.0, "#d8d3ca")  # terrace in front of the house
for i in range(1, 21):
    line((-0.3 + i * 0.53, 7.2, 0.012), (-0.3 + i * 0.53, 9.0, 0.012), "#c6c0b5", 0.7)

tree(-8.2, -0.6, 4.6, 1.6)
tree(10.6, -1.3, 3.8, 1.3)
shrub(10.4, 2.6)
shrub(10.3, 5.0, 0.45)

# ---------------------------------------------------------------- shed
SX0, SX1, SY0, SY1 = -9.6, -4.9, 1.6, 5.8
box(SX0, SY0, 0, SX1 - SX0, SY1 - SY0, 0.18, "#b9b6b0", top="#c9c6c0")
WOOD = "#9a6b45"
box(SX0, SY0 - 0.15, 0.18, SX1 - SX0, 0.15, 2.5, WOOD, top="#7d5536")  # back wall
box(SX0 - 0.15, SY0, 0.18, 0.15, SY1 - SY0, 2.5, WOOD, top="#7d5536")  # side wall
for i in range(1, 16):
    xx = SX0 + i * (SX1 - SX0) / 16
    line((xx, SY0, 0.18), (xx, SY0, 2.68), "#86593a", 0.8)
for i in range(1, 14):
    yy = SY0 + i * (SY1 - SY0) / 14
    line((SX0, yy, 0.18), (SX0, yy, 2.68), "#86593a", 0.8)
window_x(SX0 + 0.001, SY0 + 0.6, SY0 + 1.8, 1.2, 2.1)
# shelf with things
box(SX0 + 2.6, SY0, 1.4, 1.6, 0.5, 0.06, "#c49a6c")
box(SX0 + 2.6, SY0, 0.8, 1.6, 0.5, 0.06, "#c49a6c")
box(SX0 + 2.7, SY0 + 0.05, 1.46, 0.4, 0.35, 0.3, "#d9534f")
box(SX0 + 3.3, SY0 + 0.05, 1.46, 0.5, 0.35, 0.22, "#5a7d9a")
box(SX0 + 2.8, SY0 + 0.05, 0.86, 0.7, 0.38, 0.25, "#e2b44b")
# battery: 3 modules with the SolarFlow inverter on top
AX, AY = SX0, SY0 + 2.3
for i in range(3):
    box(AX, AY, 0.18 + i * 0.27, 0.45, 0.8, 0.26, "#3b3f46", edge="#22252a")
    rx(AX + 0.451, AY + 0.1, AY + 0.4, 0.18 + i * 0.27 + 0.1, 0.18 + i * 0.27 + 0.14, "#6fe08a")
box(AX, AY - 0.02, 0.99, 0.47, 0.84, 0.3, "#d5d9de", edge="#8f969e")
rx(AX + 0.471, AY + 0.08, AY + 0.74, 1.04, 1.24, "#2b2f35")
rx(AX + 0.472, AY + 0.12, AY + 0.32, 1.1, 1.16, "#58c4ff")
line((AX + 0.2, AY + 0.4, 1.29), (AX + 0.0, AY + 0.4, 2.0), "#2b2f35", 1.6)
# bicycle
for wx in (-7.4, -6.3):
    ell_y(SY0 + 3.3, wx, 0.52, 0.34, "none", stroke="#30343a", sw=2.2)
line((-7.4, SY0 + 3.3, 0.52), (-6.85, SY0 + 3.3, 0.95), "#2f80c4", 2.4)
line((-6.85, SY0 + 3.3, 0.95), (-6.3, SY0 + 3.3, 0.52), "#2f80c4", 2.4)
line((-7.4, SY0 + 3.3, 0.52), (-6.9, SY0 + 3.3, 0.52), "#2f80c4", 2.4)
line((-6.9, SY0 + 3.3, 0.52), (-6.85, SY0 + 3.3, 0.95), "#2f80c4", 2.4)
line((-6.4, SY0 + 3.3, 1.0), (-6.3, SY0 + 3.3, 0.52), "#2f80c4", 2.4)
line((-7.0, SY0 + 3.3, 1.05), (-6.7, SY0 + 3.3, 1.05), "#30343a", 2.4)

# shed roof (floating) with panels, sloping down to the front
SL = 1.7
zb_, zf_ = 2.95 + SL, 2.35 + SL


def sroof(x, y):
    return zb_ + (zf_ - zb_) * (y - (SY0 - 0.35)) / ((SY1 + 0.35) - (SY0 - 0.35))


rx0, rx1, ry0, ry1 = SX0 - 0.4, SX1 + 0.4, SY0 - 0.35, SY1 + 0.35
poly([(rx0, ry1, sroof(0, ry1) - 0.18), (rx1, ry1, sroof(0, ry1) - 0.18), (rx1, ry1, sroof(0, ry1)), (rx0, ry1, sroof(0, ry1))], "#2e3238")
poly([(rx1, ry0, sroof(0, ry0) - 0.18), (rx1, ry1, sroof(0, ry1) - 0.18), (rx1, ry1, sroof(0, ry1)), (rx1, ry0, sroof(0, ry0))], "#25282d")
poly([(rx0, ry0, sroof(0, ry0)), (rx1, ry0, sroof(0, ry0)), (rx1, ry1, sroof(0, ry1)), (rx0, ry1, sroof(0, ry1))], "#4a4f57")


def spanel(x0, x1, y0, y1):
    e = 0.04
    pts = [(x0, y0, sroof(0, y0) + e), (x1, y0, sroof(0, y0) + e), (x1, y1, sroof(0, y1) + e), (x0, y1, sroof(0, y1) + e)]
    poly(pts, "url(#pv)", "#c9d2dc", 1.0)
    for k in range(1, 4):
        xx = x0 + (x1 - x0) * k / 4
        line((xx, y0, sroof(0, y0) + e), (xx, y1, sroof(0, y1) + e), "#4b6aa3", 0.6)
    ym = (y0 + y1) / 2
    line((x0, ym, sroof(0, ym) + e), (x1, ym, sroof(0, ym) + e), "#4b6aa3", 0.6)
    poly(
        [(x0 + 0.1, y0 + 0.05, sroof(0, y0) + e), (x0 + 0.5, y0 + 0.05, sroof(0, y0) + e), (x0 + 0.1, y1 - 0.4, sroof(0, y1 - 0.4) + e)],
        "#ffffff",
        op=0.12,
    )


for r in range(2):
    for c in range(3):
        spanel(SX0 - 0.15 + c * 1.72, SX0 - 0.15 + c * 1.72 + 1.65, SY0 + r * 2.15, SY0 + r * 2.15 + 2.0)
for px, py in [(rx1, ry1), (rx0, ry1), (rx1, ry0)]:
    line((px, py, 0.2), (px, py, sroof(0, py) - 0.2), "#8a96a3", 1.0, ' stroke-dasharray="3 5" opacity="0.6"')

# ---------------------------------------------------------------- house
HX0, HX1, HY0, HY1 = -0.3, 10.2, -0.3, 7.2
WALL_H = 2.7
GAP = 2.7
Z0 = 0.35
Z1 = Z0 + WALL_H + GAP
Z2 = Z1 + WALL_H + GAP
WALL = "#f4f1ea"
CUT = "#d9d3c8"


def slab(zb, floor_col):
    box(HX0, HY0, zb - 0.35, HX1 - HX0, HY1 - HY0, 0.35, "#ebe7e0", top=floor_col, edge="#cfc9bf")
    for i in range(1, 19):
        yy = HY0 + i * (HY1 - HY0) / 19
        line((0.0, yy, zb + 0.002), (HX1, yy, zb + 0.002), shade(floor_col, 0.9), 0.6)


def walls(zb, h=WALL_H):
    box(HX0, HY0, zb, HX1 - HX0, 0.3, h, WALL, top=CUT, edge="#d6d0c5")
    box(HX0, HY0 + 0.3, zb, 0.3, HY1 - HY0 - 0.3, h, WALL, top=CUT, edge="#d6d0c5")


def guides(za, zb):
    for px, py in [(HX1, HY1), (HX0, HY1), (HX1, HY0)]:
        line((px, py, za), (px, py, zb), "#8a96a3", 1.0, ' stroke-dasharray="3 5" opacity="0.6"')


def machine(y0, ring, panel, Z):
    box(0.0, y0, Z, 0.62, 0.6, 0.86, "#f7f8f9", edge="#b9bec3")
    rx(0.621, y0 + 0.03, y0 + 0.57, Z + 0.7, Z + 0.83, "#e4e7ea")
    rx(0.622, y0 + 0.36, y0 + 0.54, Z + 0.73, Z + 0.8, panel)
    ell_x(0.623, y0 + 0.3, Z + 0.38, 0.22, ring)
    ell_x(0.624, y0 + 0.3, Z + 0.38, 0.16, "#8fb7d6")
    ell_x(0.625, y0 + 0.27, Z + 0.42, 0.06, "#ffffff", op=0.5)


# --- ground floor
box(HX0 - 0.1, HY0 - 0.1, 0, HX1 - HX0 + 0.2, HY1 - HY0 + 0.2, 0.0001, "#b8b2a7")
slab(Z0, "#d9b88f")
walls(Z0)
window_y(0.001, 3.6, 5.2, Z0 + 0.9, Z0 + 2.2)
# kitchen along the left wall
KF = "#9fb5a0"
K0 = 2.6
box(0, K0, Z0, 0.65, 0.65, 2.1, "#eef0f1", edge="#b9bec3")  # fridge
rx(0.651, K0 + 0.05, K0 + 0.6, Z0 + 1.3, Z0 + 1.32, "#b9bec3")
for y0, y1 in [(K0 + 0.65, K0 + 1.25), (K0 + 1.85, K0 + 2.45), (K0 + 2.45, K0 + 3.05), (K0 + 3.05, K0 + 3.65)]:
    box(0, y0, Z0, 0.65, y1 - y0, 0.88, KF, edge="#7f9681")
    rx(0.651, y0 + 0.05, y1 - 0.05, Z0 + 0.74, Z0 + 0.77, "#6f8571")
VW = K0 + 1.25  # dishwasher
box(0, VW, Z0, 0.65, 0.6, 0.88, "#c6ccd2", edge="#8c949c")
rx(0.651, VW + 0.03, VW + 0.57, Z0 + 0.72, Z0 + 0.84, "#9aa3ab")
rx(0.652, VW + 0.1, VW + 0.5, Z0 + 0.66, Z0 + 0.69, "#5d656d")
rx(0.652, VW + 0.43, VW + 0.49, Z0 + 0.77, Z0 + 0.8, "#6fe08a")
box(0, K0 + 0.65, Z0 + 0.88, 0.68, 3.0, 0.06, "#3d3f45")  # worktop
box(0.18, K0 + 2.1, Z0 + 0.94, 0.3, 0.45, 0.02, "#9aa3ab")  # sink
box(0, K0 + 0.75, Z0 + 1.55, 0.36, 2.8, 0.7, KF, edge="#7f9681")  # wall cupboards
window_x(0.001, 0.8, 2.0, Z0 + 0.9, Z0 + 2.2)
# dining table
box(2.0, 3.9, Z0 + 0.72, 1.6, 2.2, 0.06, "#b9875a")
for lx, ly in [(2.1, 4.0), (3.45, 4.0), (2.1, 5.95), (3.45, 5.95)]:
    box(lx, ly, Z0, 0.07, 0.07, 0.72, "#8c6040")
for cy_ in (4.2, 5.3):
    box(3.75, cy_, Z0, 0.45, 0.45, 0.45, "#e5e1d8")
    box(4.12, cy_, Z0 + 0.45, 0.08, 0.45, 0.5, "#e5e1d8")
# sofa against the back wall
box(5.6, 0.0, Z0, 2.9, 0.95, 0.42, "#6c8fb3")
box(5.6, 0.0, Z0 + 0.42, 2.9, 0.28, 0.45, "#5f82a6")
box(5.6, 0.0, Z0 + 0.42, 0.25, 0.95, 0.22, "#5f82a6")
box(8.25, 0.0, Z0 + 0.42, 0.25, 0.95, 0.22, "#5f82a6")
for kx in (6.1, 7.2):
    box(kx, 0.3, Z0 + 0.42, 0.9, 0.55, 0.14, "#7fa0c2")
rz(Z0 + 0.003, 5.4, 8.8, 1.3, 3.4, "#e9dcc5")  # rug
box(6.3, 1.7, Z0, 1.4, 0.8, 0.38, "#f2efe8")  # coffee table
# meter cupboard
box(9.15, 0.0, Z0, 0.95, 0.5, 2.3, "#ffffff", edge="#b9bec3")
ry(0.501, 9.25, 10.0, Z0 + 0.25, Z0 + 2.15, "#e9ecef", stroke="#c3c8cd", sw=0.6)
ry(0.502, 9.35, 9.9, Z0 + 1.55, Z0 + 2.0, "#d4d8dc")
ry(0.503, 9.45, 9.8, Z0 + 1.72, Z0 + 1.88, "#3a8f5c")
for i in range(5):
    ry(0.503, 9.36 + i * 0.11, 9.44 + i * 0.11, Z0 + 1.1, Z0 + 1.35, "#2b2f35")
ry(0.503, 9.36, 9.9, Z0 + 0.5, Z0 + 0.85, "#cfd4d9")
plant(4.8, 0.4, Z0, 1.0, 0.36)

# --- first floor
guides(Z0 + WALL_H, Z1 - 0.35)
slab(Z1, "#e1c59f")
walls(Z1)
window_y(0.001, 5.2, 6.6, Z1 + 0.9, Z1 + 2.2)
window_x(0.001, 4.6, 5.6, Z1 + 0.9, Z1 + 2.2)
box(0.0, 0.4, Z1, 0.62, 2.2, 2.2, "#efe9df", edge="#c9c1b4")  # wardrobe
for yy in (1.13, 1.86):
    line((0.621, yy, Z1 + 0.05), (0.621, yy, Z1 + 2.15), "#c9c1b4", 0.8)
BX = 6.3  # bed
box(BX, 0.0, Z1, 1.7, 0.14, 1.05, "#7a8e6e")
box(BX, 0.14, Z1, 1.7, 2.0, 0.42, "#c6a37f")
box(BX, 0.14, Z1 + 0.42, 1.7, 2.0, 0.18, "#ffffff", edge="#cfcfcf")
box(BX - 0.02, 0.8, Z1 + 0.6, 1.74, 1.36, 0.08, "#e3a86b", edge="#c98a4f")
box(BX + 0.12, 0.22, Z1 + 0.6, 0.65, 0.45, 0.14, "#f4f4f4", edge="#d0d0d0")
box(BX + 0.95, 0.22, Z1 + 0.6, 0.65, 0.45, 0.14, "#f4f4f4", edge="#d0d0d0")
box(BX + 1.85, 0.0, Z1, 0.45, 0.45, 0.5, "#c6a37f")
rz(Z1 + 0.003, 5.6, 8.8, 2.4, 4.2, "#c9d6e3")
DY = 0.0 if VERD == 3 else -0.1  # desk with screen
box(0.0, 3.3 + DY, Z1 + 0.72, 0.75, 1.9, 0.05, "#b9875a")
for ly in (3.35 + DY, 5.1 + DY):
    box(0.05, ly, Z1, 0.65, 0.06, 0.72, "#555a61")
box(0.12, 3.9, Z1 + 0.77, 0.06, 0.7, 0.45, "#2b2f35")
rx(0.181, 3.94, 4.56, Z1 + 0.82, Z1 + 1.18, "#58a6e0")
box(1.0, 3.95, Z1, 0.5, 0.5, 0.45, "#3b3f46")
box(1.42, 3.95, Z1 + 0.45, 0.08, 0.5, 0.55, "#3b3f46")
AY1 = 5.5 if VERD == 3 else 3.5  # air conditioner
box(0.0, AY1, Z1 + 2.0, 0.28, 1.25, 0.36, "#fbfbfb", edge="#c6cbd0")
rx(0.281, AY1 + 0.08, AY1 + 1.17, Z1 + 2.04, Z1 + 2.08, "#aab2ba")
rx(0.282, AY1 + 1.0, AY1 + 1.07, Z1 + 2.27, Z1 + 2.3, "#58c4ff")
plant(9.6, 0.5, Z1, 1.2, 0.42)
if VERD == 3:
    plant(0.5, 6.6, Z1, 1.0, 0.38)
else:
    machine(5.6, "#aab2ba", "#58c4ff", Z1)  # washer and dryer
    machine(6.25, "#c3c8ce", "#ffb347", Z1)
    box(1.0, 6.4, Z1, 0.5, 0.5, 0.42, "#d8c29a", edge="#b39c72")
    box(1.05, 6.45, Z1 + 0.42, 0.4, 0.4, 0.08, "#ffffff", edge="#d0d0d0")

KNEE, RIDGE_H, RY = 0.9, 3.2, 3.45
if VERD == 3:
    # --- attic
    guides(Z1 + WALL_H, Z2 - 0.35)
    slab(Z2, "#d7b98f")
    box(HX0, HY0, Z2, HX1 - HX0, 0.3, KNEE, WALL, top=CUT, edge="#d6d0c5")  # back knee wall

    def zr(y):  # roof height above the attic floor
        return KNEE + (RIDGE_H - KNEE) * (1 - abs(y - RY) / (RY + 0.3 if y < RY else HY1 - RY))

    gy = [HY0 + 0.3 + i * (HY1 - HY0 - 0.3) / 40 for i in range(41)]
    poly([(0.0, HY0 + 0.3, Z2)] + [(0.0, y, Z2 + zr(y)) for y in gy] + [(0.0, HY1, Z2)], WALL, "#d6d0c5", 0.6)
    poly([(HX0, HY0, Z2)] + [(HX0, y, Z2 + zr(y)) for y in [HY0] + gy] + [(HX0, HY1, Z2)], WALL, op=0)
    for i in range(40):
        a, b = gy[i], gy[i + 1]
        poly([(HX0, a, Z2 + zr(a)), (0.0, a, Z2 + zr(a)), (0.0, b, Z2 + zr(b)), (HX0, b, Z2 + zr(b))], CUT)
    rx(0.001, HY1 - 0.001, HY1, Z2, Z2 + 0.01, CUT)
    window_x(0.002, 2.6, 3.7, Z2 + 1.1, Z2 + 2.1)
    poly([(HX0, HY1, Z2), (0.0, HY1, Z2), (0.0, HY1, Z2 + zr(HY1)), (HX0, HY1, Z2 + zr(HY1))], "#e6e0d5")
    machine(5.05, "#aab2ba", "#58c4ff", Z2)  # washer and dryer
    machine(5.7, "#c3c8ce", "#ffb347", Z2)
    box(1.0, 6.4, Z2, 0.5, 0.5, 0.42, "#d8c29a", edge="#b39c72")  # laundry basket
    box(1.05, 6.45, Z2 + 0.42, 0.4, 0.4, 0.08, "#ffffff", edge="#d0d0d0")
    for a, b in [
        ((2.2, 4.6, Z2), (3.2, 4.6, Z2 + 1.0)),
        ((3.2, 4.6, Z2), (2.2, 4.6, Z2 + 1.0)),
        ((2.2, 6.0, Z2), (3.2, 6.0, Z2 + 1.0)),
        ((3.2, 6.0, Z2), (2.2, 6.0, Z2 + 1.0)),
    ]:
        line(a, b, "#9aa3ab", 1.6)  # drying rack
    for k in range(4):
        zz = Z2 + 0.9
        line((2.3 + k * 0.27, 4.6, zz), (2.3 + k * 0.27, 6.0, zz), "#9aa3ab", 1.0)
    box(2.35, 4.9, Z2 + 0.55, 0.05, 0.7, 0.35, "#e3a86b")
    box(2.62, 5.0, Z2 + 0.5, 0.05, 0.6, 0.4, "#7fa0c2")
    box(7.8, 4.6, Z2, 0.9, 0.9, 0.7, "#c8a27a")  # boxes
    box(8.0, 5.6, Z2, 0.7, 0.7, 0.5, "#d4b088")
else:
    Z2 = Z1 + WALL_H + 0.25 - KNEE

# --- roof (floating)
L = 3.2 if VERD == 3 else 4.3
DX0, DX1 = HX0 - 0.35, HX1 + 0.35
YB, YF = HY0 - 0.45, HY1 + 0.45
ZR = Z2 + RIDGE_H + L
slope_b = (RIDGE_H - KNEE) / (RY - HY0)
slope_f = (RIDGE_H - KNEE) / (HY1 - RY)


def zroof(y):
    return ZR - (RY - y) * slope_b if y < RY else ZR - (y - RY) * slope_f


T = 0.22
guides(Z2 + KNEE, zroof(HY1) - 0.3)
poly([(DX0, YB, zroof(YB)), (DX1, YB, zroof(YB)), (DX1, RY, ZR), (DX0, RY, ZR)], "#2f3339")
poly([(DX1, YB + 0.3, zroof(YB + 0.3) - T), (DX1, RY, ZR - T - 0.25), (DX1, YF - 0.3, zroof(YF - 0.3) - T)], "#6b5242", op=0.0)
poly(
    [(DX1, YB, zroof(YB) - T), (DX1, YB, zroof(YB)), (DX1, RY, ZR), (DX1, YF, zroof(YF)), (DX1, YF, zroof(YF) - T), (DX1, RY, ZR - T)],
    "#25282d",
)
poly([(DX0, YF, zroof(YF) - T), (DX1, YF, zroof(YF) - T), (DX1, YF, zroof(YF)), (DX0, YF, zroof(YF))], "#25282d")
poly([(DX0, RY, ZR), (DX1, RY, ZR), (DX1, YF, zroof(YF)), (DX0, YF, zroof(YF))], "#454a52")
for i in range(1, 9):
    yy = RY + i * (YF - RY) / 9
    line((DX0, yy, zroof(yy) + 0.001), (DX1, yy, zroof(yy) + 0.001), "#3a3e45", 0.8)
box(DX0, RY - 0.12, ZR - 0.05, DX1 - DX0, 0.24, 0.14, "#2a2d33")  # ridge


def rpanel(x0, x1, y0, y1):
    e = 0.05
    pts = [(x0, y0, zroof(y0) + e), (x1, y0, zroof(y0) + e), (x1, y1, zroof(y1) + e), (x0, y1, zroof(y1) + e)]
    poly(pts, "url(#pv)", "#c9d2dc", 1.0)
    for k in range(1, 3):
        xx = x0 + (x1 - x0) * k / 3
        line((xx, y0, zroof(y0) + e), (xx, y1, zroof(y1) + e), "#4b6aa3", 0.6)
    for k in range(1, 5):
        yy = y0 + (y1 - y0) * k / 5
        line((x0, yy, zroof(yy) + e), (x1, yy, zroof(yy) + e), "#4b6aa3", 0.6)
    poly(
        [(x0 + 0.08, y0 + 0.05, zroof(y0) + e), (x0 + 0.45, y0 + 0.05, zroof(y0) + e), (x0 + 0.08, y1 - 0.8, zroof(y1 - 0.8) + e)],
        "#ffffff",
        op=0.12,
    )


cols = 9
pw = 1.08
startx = DX0 + ((DX1 - DX0) - cols * pw) / 2 + 0.02
for r in range(2):
    y0 = RY + 0.3 + r * 1.95
    for c in range(cols):
        x0 = startx + c * pw
        rpanel(x0, x0 + pw - 0.06, y0, y0 + 1.88)
box(1.2, 1.4, zroof(1.4) - 0.2, 0.35, 0.35, 0.9, "#3a3e45")  # vent pipe

# ---------------------------------------------------------------- car + charge point
sx, sy = P(4.1, 11.9, 0)
out.append(f'<ellipse cx="{sx:.0f}" cy="{sy:.0f}" rx="{2.6 * S:.0f}" ry="{1.25 * S:.0f}" fill="#000" opacity="0.13"/>')
CY0, CY1 = 10.9, 12.75
CAR = "#e9eef3"
box(1.7, CY0, 0.3, 4.6, CY1 - CY0, 0.62, CAR, edge="#9aa6b2")
cab = [(2.5, 0.92), (3.25, 1.48), (4.85, 1.48), (5.55, 0.92)]
poly([(x, CY1 - 0.08, z) for x, z in cab], "#2b3a4a", "#9aa6b2", 0.6)
poly([(5.55, CY0 + 0.08, 0.92), (5.55, CY1 - 0.08, 0.92), (4.85, CY1 - 0.08, 1.48), (4.85, CY0 + 0.08, 1.48)], "#34506b", "#9aa6b2", 0.6)
poly([(3.25, CY0 + 0.08, 1.48), (4.85, CY0 + 0.08, 1.48), (4.85, CY1 - 0.08, 1.48), (3.25, CY1 - 0.08, 1.48)], CAR, "#9aa6b2", 0.6)
line((4.05, CY1 - 0.08, 0.92), (4.05, CY1 - 0.08, 1.48), CAR, 3)
poly([(3.4, CY1 - 0.079, 1.4), (3.7, CY1 - 0.079, 1.4), (3.1, CY1 - 0.079, 1.0), (2.85, CY1 - 0.079, 1.0)], "#ffffff", op=0.25)
for wx in (2.6, 5.35):
    ell_y(CY1 + 0.01, wx, 0.36, 0.36, "#24272c")
    ell_y(CY1 + 0.02, wx, 0.36, 0.18, "#aab2ba")
rx(6.301, CY0 + 0.15, CY0 + 0.5, 0.62, 0.75, "#fff6c9")
rx(6.301, CY1 - 0.5, CY1 - 0.15, 0.62, 0.75, "#fff6c9")
rx(6.302, 11.55, 11.8, 0.66, 0.8, "#2b2f35")
LPX, LPY = 7.0, 10.0
box(LPX, LPY, 0, 0.42, 0.42, 0.06, "#9aa3ab")
box(LPX + 0.06, LPY + 0.06, 0.06, 0.3, 0.3, 1.45, "#f4f6f8", edge="#a9b0b7")
ry(LPY + 0.361, LPX + 0.1, LPX + 0.32, 1.0, 1.3, "#2b2f35")
ry(LPY + 0.362, LPX + 0.13, LPX + 0.29, 1.18, 1.24, "#6fe08a")
rx(LPX + 0.361, LPY + 0.1, LPY + 0.32, 0.75, 0.9, "#3ba55c")
a = P(LPX + 0.2, LPY + 0.37, 0.82)
b = P(6.31, 11.68, 0.73)
out.append(
    f'<path d="M{a[0]:.1f},{a[1]:.1f} C{a[0] - 4:.1f},{a[1] + 40:.1f} {b[0] + 18:.1f},{b[1] + 30:.1f} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="#2b2f35" stroke-width="3.2" stroke-linecap="round"/>'
)

tree(-8.4, 12.0, 3.6, 1.25)
shrub(-5.0, 13.6, 0.5)
shrub(9.6, 13.4, 0.5)
shrub(-1.8, 8.4, 0.4)

out.append("</g>")
out.append("</svg>")
open(sys.argv[1], "w").write("\n".join(out))
