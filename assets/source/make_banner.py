#!/usr/bin/env python3
"""Profile banner, light and dark. Text in Didot, Futura and Snell Roundhand is
converted to paths so it renders the same on every platform.
Run: python3 assets/source/make_banner.py  (from the repo root)"""
from pathlib import Path
from fontTools.ttLib import TTCollection
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[2]
SUP = Path("/System/Library/Fonts/Supplemental")


def face(ttc, want):
    for f in TTCollection(SUP / ttc).fonts:
        if f["name"].getDebugName(4) == want:
            return f
    raise SystemExit(f"{want} not in {ttc}")


FONTS = {
    "didot": face("Didot.ttc", "Didot Italic"),
    "futura": face("Futura.ttc", "Futura Medium"),
    "snell": face("SnellRoundhand.ttc", "Snell Roundhand"),
}


def text_path(text, font, size, x, y, tracking=0.0):
    """Return an SVG path d for text at (x, y baseline). tracking is in em."""
    f = FONTS[font]
    upem = f["head"].unitsPerEm
    cmap = f.getBestCmap()
    glyphs = f.getGlyphSet()
    hmtx = f["hmtx"]
    s = size / upem
    pen = SVGPathPen(glyphs)
    cx = x
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            cx += size * 0.3
            continue
        tp = TransformPen(pen, (s, 0, 0, -s, cx, y))
        glyphs[name].draw(tp)
        cx += hmtx[name][0] * s + tracking * size
    return pen.getCommands(), cx


def banner(dark):
    bg, ink, body, mute, red = ("#0C0C0E", "#EFE6D6", "#CDC6BA", "#77726A", "#D63A2A") if dark else ("#FBFAF7", "#1D1C1A", "#4A4742", "#8A867E", "#C8291C")
    W, H = 1200, 320
    fig, _ = text_path("FIG. 01 · REXXALL · OBSIDIAN PLUGINS", "futura", 13, 72, 70, tracking=0.42)
    name, name_end = text_path("Rex", "didot", 118, 66, 178)
    sign, _ = text_path("R.", "snell", 30, 1118, 282)
    dots = [mute] * 7 + [red]  # one dot per tool; the newest one is the only colour on the page
    circles = "\n".join(f'    <circle cx="{946 + i * 26}" cy="168" r="9" fill="{c}" stroke="{bg}" stroke-width="3"/>' for i, c in enumerate(dots))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">Rex</title>
  <desc id="d">Rex: trained as a doctor, now building the tools his notes were missing. A heartbeat line turns into a row of commits, one dot for each tool.</desc>
  <rect width="{W}" height="{H}" rx="28" fill="{bg}"/>
  <path d="{fig}" fill="{mute}"/>
  <path d="{name}" fill="{ink}"/>
  <rect x="74" y="206" width="64" height="2" fill="{red}"/>
  <g font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif" font-size="22">
    <text x="74" y="246" fill="{body}">Trained as a doctor. Now I build the tools my notes were missing.</text>
    <text x="74" y="280" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" fill="{mute}">the tool proposes · you decide · undo always</text>
  </g>
  <g fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M700 168 H760 L772 156 L784 168 H800 L812 96 L828 222 L842 150 L852 168 H880 C892 168 896 146 912 146 C928 146 932 168 944 168 H1136" stroke="{mute}" stroke-width="3"/>
{circles}
  </g>
  <path d="{sign}" fill="{mute}"/>
</svg>
'''


for mode in ("light", "dark"):
    out = ROOT / "assets" / f"banner-{mode}.svg"
    out.write_text(banner(mode == "dark"), encoding="utf-8")
    print(out, out.stat().st_size, "bytes")
