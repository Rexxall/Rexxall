#!/usr/bin/env python3
"""Profile banner. Light mode is an anatomical plate of a note; dark mode is a
film credit. Display text is converted to paths so it renders the same on every
platform. Run from the repo root: python3 assets/source/make_banner.py"""
from pathlib import Path
from fontTools.ttLib import TTCollection, TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[2]
SUP = Path("/System/Library/Fonts/Supplemental")
W, H = 1200, 320


def face(fn, want=None):
    p = SUP / fn
    if fn.endswith(".ttc"):
        for f in TTCollection(p).fonts:
            if f["name"].getDebugName(4) == want:
                return f
        raise SystemExit(f"{want} not in {fn}")
    return TTFont(p)


F = {
    "didot": face("Didot.ttc", "Didot Italic"),
    "didotb": face("Didot.ttc", "Didot Bold"),
    "futura": face("Futura.ttc", "Futura Medium"),
    "snell": face("SnellRoundhand.ttc", "Snell Roundhand"),
    "hand": face("Bradley Hand Bold.ttf"),
}


def text_path(text, font, size, tracking=0.0):
    f = F[font]
    upem = f["head"].unitsPerEm
    cmap, gs, hm = f.getBestCmap(), f.getGlyphSet(), f["hmtx"]
    s = size / upem
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    cx = 0
    for ch in text:
        n = cmap.get(ord(ch))
        if n is None:
            cx += size * .3
            continue
        gs[n].draw(TransformPen(pen, (s, 0, 0, -s, cx, 0)))
        cx += hm[n][0] * s + tracking * size
    return pen.getCommands(), cx


def P(text, font, size, x, y, fill, tracking=0.0, anchor="start"):
    d, w = text_path(text, font, size, tracking)
    x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
    return f'<path d="{d}" fill="{fill}" transform="translate({x:.1f} {y:.1f})"/>'


ECG = "M0 0 H60 L72 -12 L84 0 H100 L112 -72 L128 54 L142 -18 L152 0 H180 C192 0 196 -22 212 -22 C228 -22 232 0 244 0 H{L}"
DESC = "Rex: trained as a doctor, now building the tools his notes were missing. The tool proposes, you decide, undo always."


def svg(body, bg, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">'
            f'<title id="t">Rex</title><desc id="d">{DESC}</desc><defs>{defs}</defs>'
            f'<rect width="{W}" height="{H}" rx="28" fill="{bg}"/>{body}</svg>\n')


def plate():
    """Light: a note pinned to an anatomical plate, each leader a plugin promise."""
    bg, ink, mute, red = "#F0EFEA", "#17160F", "#8A867E", "#C8291C"
    rough = ('<filter id="r" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".05" numOctaves="3" seed="3"/>'
             '<feDisplacementMap in="SourceGraphic" scale="3"/></filter>')
    b = "".join(f'<circle cx="34" cy="{y}" r="8" fill="#D9D6CE" stroke="#C4C0B7"/>' for y in (70, 160, 250))
    b += P("PLATE I", "didotb", 22, 92, 62, ink, tracking=.08)
    b += P("THE NOTE, DISSECTED · REXXALL · OBSIDIAN PLUGINS", "futura", 10.5, 206, 62, mute, tracking=.4)
    b += P("ITH_PLATE_01_V1", "futura", 8.5, W - 70, 48, mute, tracking=.3, anchor="end")

    nx, ny, nw, nh = 450, 92, 280, 196
    b += f'<g filter="url(#r)"><rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" fill="none" stroke="{ink}" stroke-width="1.6"/>'
    b += f'<rect x="{nx+18}" y="{ny+18}" width="150" height="10" fill="{ink}" opacity=".85"/>'
    for i, w in enumerate([236, 206, 226, 120, 232, 176]):
        b += f'<rect x="{nx+18}" y="{ny+46+i*18}" width="{w}" height="4" fill="{ink}" opacity=".35"/>'
    b += f'<rect x="{nx+18}" y="{ny+162}" width="44" height="14" rx="7" fill="none" stroke="{ink}" stroke-width="1.2"/>'
    b += f'<rect x="{nx+70}" y="{ny+162}" width="58" height="14" rx="7" fill="none" stroke="{ink}" stroke-width="1.2"/></g>'

    def lead(x1, y1, x2, y2, label, sub, fill, right=False):
        tx = x2 + (-66 if right else 66)
        s = f'<path d="M{x1} {y1} L{x2} {y2} H{x2 + (-60 if right else 60)}" fill="none" stroke="{fill}" stroke-width="1" filter="url(#r)"/>'
        s += f'<circle cx="{x1}" cy="{y1}" r="2.4" fill="{fill}"/>'
        a = "end" if right else "start"
        s += P(label, "futura", 11, tx, y2 - 4, fill, tracking=.22, anchor=a)
        return s + (P(sub, "hand", 15, tx, y2 + 16, fill, anchor=a) if sub else "")

    b += lead(nx + 90, ny + 23, 850, 100, "TITLE · TAGS · FOLDER", "proposed, never applied", ink)
    b += lead(nx + 200, ny + 120, 850, 172, "EVERY SENTENCE", "kept in git, one line back", ink)
    b += lead(nx + 40, ny + 169, 850, 246, "UNDO", "always", red)
    b += lead(nx, ny + 70, 330, 128, "YOU DECIDE", "", ink, right=True)
    b += f'<ellipse cx="{nx+40}" cy="{ny+169}" rx="30" ry="14" fill="none" stroke="{red}" stroke-width="2" transform="rotate(-6 {nx+40} {ny+169})" filter="url(#r)"/>'

    b += P("Rex", "didot", 60, 92, 222, ink)
    b += P("trained as a doctor,", "hand", 15, 94, 254, mute)
    b += P("now building the tools my notes were missing", "hand", 15, 94, 278, mute)
    b += P("R.", "snell", 30, W - 70, 288, mute, anchor="end")
    return svg(b, bg, rough)


def credits():
    """Dark: a film credit on a letterboxed still, one red line."""
    bg, ink, mute, red = "#050506", "#EFE6D6", "#7A756D", "#D63A2A"
    defs = ('<linearGradient id="still" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#1a1210"/><stop offset=".5" stop-color="#0a0809"/><stop offset="1" stop-color="#101418"/></linearGradient>'
            '<filter id="gr" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>'
            '<feColorMatrix values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 .05 0"/></filter>')
    b = f'<rect x="0" y="44" width="{W}" height="232" fill="url(#still)"/><rect x="0" y="44" width="{W}" height="232" filter="url(#gr)"/>'
    b += (f'<g opacity=".28" fill="none" stroke="{ink}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
          f'<path d="{ECG.format(L=420)}" transform="translate(100 160)"/><path d="M700 160 H1100"/></g>')
    b += P("A PLUGIN SHELF BY", "futura", 11, 600, 100, mute, tracking=.5, anchor="middle")
    b += P("Rex", "didot", 92, 600, 178, ink, anchor="middle")
    b += P("TRAINED AS A DOCTOR · NOW BUILDING THE TOOLS HIS NOTES WERE MISSING", "futura", 10.5, 600, 214, mute, tracking=.3, anchor="middle")
    b += P("THE TOOL PROPOSES · YOU DECIDE · UNDO ALWAYS", "futura", 10.5, 600, 250, red, tracking=.3, anchor="middle")
    b += P("FIG. 01", "futura", 9, 40, 30, mute, tracking=.4)
    b += P("REXXALL / OBSIDIAN", "futura", 9, W - 40, 30, mute, tracking=.4, anchor="end")
    b += P("R.", "snell", 24, W - 40, 304, mute, anchor="end")
    return svg(b, bg, defs)


if __name__ == "__main__":
    for mode, fn in (("light", plate), ("dark", credits)):
        out = ROOT / "assets" / f"banner-{mode}.svg"
        out.write_text(fn(), encoding="utf-8")
        print(out.name, out.stat().st_size, "bytes")
