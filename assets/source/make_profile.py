"""Render the profile banner (SVG, light/dark) and the plugin shelf tiles (PNG, light/dark)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, monospace"
THEMES = {
    "light": dict(bg="#F5F5F7", fg="#1D1D1F", muted="#6E6E73", line="#E3E3E8", card="#FFFFFF", page=(255, 255, 255)),
    "dark": dict(bg="#16161A", fg="#F2F2F5", muted="#9A9AA3", line="#2C2C33", card="#1F1F25", page=(13, 17, 23)),
}
PLUGINS = [  # slug, accent
    ("git-note-history", "#7A5AF0"), ("ai-assistant-suite", "#0A84FF"),
    ("polyglot-helper", "#30B0C7"), ("video-summary", "#FF375F"),
    ("japan-work-secretary", "#FF9F0A"), ("ai-accounting", "#34C759"),
    ("pass-countdown", "#5E5CE6"), ("tasknotes-countdown", "#BF5AF2"),
]

BANNER = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="320" viewBox="0 0 1200 320" role="img" aria-labelledby="t d">
  <title id="t">Rex</title>
  <desc id="d">Rex: trained as a doctor, now building the tools his notes were missing. A heartbeat line turns into a row of commits, one dot for each tool.</desc>
  <rect width="1200" height="320" rx="28" fill="{bg}"/>
  <g font-family="{sans}">
    <text x="72" y="132" font-size="72" font-weight="700" letter-spacing="-2" fill="{fg}">Rex</text>
    <text x="74" y="186" font-size="28" fill="{fg}">Trained as a doctor.</text>
    <text x="74" y="224" font-size="28" fill="{muted}">Now I build the tools my notes were missing.</text>
    <text x="74" y="272" font-family="{mono}" font-size="17" fill="{muted}">the tool proposes · you decide · undo always</text>
  </g>
  <g id="pulse-to-commits" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M700 168 H760 L772 156 L784 168 H800 L812 96 L828 222 L842 150 L852 168 H880 C892 168 896 146 912 146 C928 146 932 168 944 168 H1136" stroke="{muted}" stroke-width="3"/>
{dots}
  </g>
</svg>
"""


def banner():
    for name, c in THEMES.items():
        dots = "\n".join(f'    <circle cx="{946 + i * 26}" cy="168" r="9" fill="{accent}" stroke="{c["bg"]}" stroke-width="3"/>' for i, (_, accent) in enumerate(PLUGINS))
        (ROOT / f"banner-{name}.svg").write_text(BANNER.format(sans=SANS, mono=MONO, dots=dots, **c), encoding="utf-8")


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def tile(slug, accent, mode):
    W, H, R = 900, 560, 36
    c = THEMES[mode]
    a = hex_rgb(accent)
    base = hex_rgb(c["card"])
    mix = 0.14 if mode == "light" else 0.22
    top = tuple(round(b + (x - b) * mix) for b, x in zip(base, a))
    card = Image.new("RGB", (W, H), top)
    shade = Image.linear_gradient("L").resize((W, H)).point(lambda v: v * 0.55)
    card.paste(base, (0, 0), shade)  # fades toward the card colour at the bottom
    shot = Image.open(ROOT / "plugins" / f"{slug}-{mode}.jpg").convert("RGB")
    scale = min(760 / shot.width, 430 / shot.height)  # fit inside the card, below the accent tab
    sw, sh = round(shot.width * scale), round(shot.height * scale)
    shot = shot.resize((sw, sh), Image.LANCZOS)
    x, y = (W - sw) // 2, 82
    shadow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((x, y + 10, x + sw, y + shot.height + 10), 18, fill=90 if mode == "light" else 160)
    card.paste((20, 16, 40), (0, 0), shadow.filter(ImageFilter.GaussianBlur(20)))
    m = Image.new("L", shot.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, shot.width - 1, shot.height - 1), 18, fill=255)
    card.paste(shot, (x, y), m)
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((x, y, x + sw - 1, y + shot.height - 1), 18, outline=hex_rgb(c["line"]), width=2)
    d.rounded_rectangle((40, 36, 40 + 56, 36 + 12), 6, fill=a)  # accent tab
    outer = Image.new("L", (W, H), 0)
    ImageDraw.Draw(outer).rounded_rectangle((0, 0, W - 1, H - 1), R, fill=255)
    page = Image.new("RGB", (W, H), c["page"])
    page.paste(card, (0, 0), outer)
    page.save(ROOT / "shelf" / f"{slug}-{mode}.png", optimize=True)


if __name__ == "__main__":
    banner()
    for slug, accent in PLUGINS:
        for mode in THEMES:
            tile(slug, accent, mode)
    print("ok")
