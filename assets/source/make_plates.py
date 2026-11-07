#!/usr/bin/env python3
"""Profile shelf as plates. Light: each plugin is a numbered figure on an anatomical
plate. Dark: each plugin is a letterboxed film still with a credit line.
Writes assets/shelf/<slug>-<mode>.png, assets/shelf/web-<mode>.png and
assets/shelf/colophon-<mode>.png. Run from the repo root."""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTCollection

ROOT = Path(__file__).resolve().parents[1]
SUP = Path("/System/Library/Fonts/Supplemental")
W, H = 900, 560
PLUGINS = [  # slug, display, one line, leader label (what the plate points at), roman
    ("git-note-history", "Git Note History", "Find a sentence you deleted. Take back only that part.", "one sentence, not the file", "II"),
    ("ai-assistant-suite", "AI Assistant Suite", "AI suggests title, tags and folder. You tick what to apply.", "proposed, never applied", "III"),
    ("polyglot-helper", "Polyglot Helper", "Look up Japanese and English words, keep them for review.", "kept for review", "IV"),
    ("video-summary", "Video Summary", "A video link in, a finished note out.", "a note, not a transcript", "V"),
    ("japan-work-secretary", "Japan Work Secretary", "Part-time shifts in Japan, warned before 28 hours.", "warned at 28 h", "VI"),
    ("ai-accounting", "AI Accounting", "A receipt in, a checked ledger entry out.", "checked before it lands", "VII"),
    ("pass-countdown", "Pass Countdown", "Uses left, time left, and the pace to finish.", "the pace to finish", "VIII"),
    ("tasknotes-countdown", "TaskNotes Countdown", "Deadlines from TaskNotes, and whether you will make it.", "will you make it", "IX"),
]
ACCENT = {  # one colour per tool, taken from the piles: 蓝绿舞台光, 红光, 浓烈彩色, 深夜冷蓝
    "git-note-history": (122, 90, 240), "ai-assistant-suite": (10, 132, 255), "polyglot-helper": (48, 176, 199), "video-summary": (255, 55, 95),
    "japan-work-secretary": (255, 159, 10), "ai-accounting": (52, 199, 89), "pass-countdown": (94, 92, 230), "tasknotes-countdown": (191, 90, 242),
}
WEB_ACCENT = [(48, 176, 199), (255, 159, 10), (122, 90, 240)]
PRINCIPLE_ACCENT = [(10, 132, 255), (52, 199, 89), (191, 90, 242)]
LIGHT = dict(bg=(240, 239, 234), ink=(23, 22, 15), mute=(138, 134, 126), red=(200, 41, 28), hole=(217, 214, 206), page=(255, 255, 255))
DARK = dict(bg=(5, 5, 6), ink=(239, 230, 214), mute=(122, 117, 109), red=(214, 58, 42), still=(16, 14, 14), page=(13, 17, 23))


def ttc_index(fn, want):
    for i, f in enumerate(TTCollection(SUP / fn).fonts):
        if f["name"].getDebugName(4) == want:
            return i
    raise SystemExit(want)


IDX = {"didot": ttc_index("Didot.ttc", "Didot Italic"), "didotb": ttc_index("Didot.ttc", "Didot Bold"),
       "futura": ttc_index("Futura.ttc", "Futura Medium"), "snell": ttc_index("SnellRoundhand.ttc", "Snell Roundhand")}
FILES = {"didot": "Didot.ttc", "didotb": "Didot.ttc", "futura": "Futura.ttc", "snell": "SnellRoundhand.ttc", "hand": "Bradley Hand Bold.ttf"}


def font(name, size):
    return ImageFont.truetype(str(SUP / FILES[name]), size, index=IDX.get(name, 0))


def spaced(d, xy, text, f, fill, tracking, anchor="l"):
    """Letter-spaced text. Pillow has no tracking, so draw glyph by glyph."""
    x, y = xy
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    if anchor == "r":
        x -= total
    elif anchor == "m":
        x -= total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=f, fill=fill)
        x += w + tracking
    return total


def rough_rect(d, box, fill, width=2, seed=1, amp=1.6):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    pts = []
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        n = 24
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + rnd.uniform(-amp, amp), ay + (by - ay) * t + rnd.uniform(-amp, amp)))
    pts.append(pts[0])
    d.line(pts, fill=fill, width=width, joint="curve")


def rough_line(d, a, b, fill, width=1, seed=2, amp=1.2):
    rnd = random.Random(seed)
    n = 30
    pts = [(a[0] + (b[0] - a[0]) * i / n + rnd.uniform(-amp, amp), a[1] + (b[1] - a[1]) * i / n + rnd.uniform(-amp, amp)) for i in range(n + 1)]
    d.line(pts, fill=fill, width=width, joint="curve")


def shot(slug, mode, box_w, box_h):
    im = Image.open(ROOT / "plugins" / f"{slug}-{mode}.jpg").convert("RGB")
    s = min(box_w / im.width, box_h / im.height)
    return im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)


def round_page(card, page_rgb, r=28):
    m = Image.new("L", card.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, card.width - 1, card.height - 1), r, fill=255)
    page = Image.new("RGB", card.size, page_rgb)
    page.paste(card, (0, 0), m)
    return page


def wash(im, center, rx, ry, rgb, alpha=90, blur=40):
    """A soft watercolour wash behind the specimen (红色晕染包住人, in the tool's colour)."""
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).ellipse((center[0] - rx, center[1] - ry, center[0] + rx, center[1] + ry), fill=alpha)
    im.paste(Image.new("RGB", im.size, rgb), (0, 0), m.filter(ImageFilter.GaussianBlur(blur)))


def plate(slug, name, line, leader, roman):
    c = LIGHT
    a = ACCENT[slug]
    im = Image.new("RGB", (W, H), c["bg"])
    wash(im, (330, 250), 330, 200, a, alpha=70, blur=48)
    d = ImageDraw.Draw(im)
    for y in (90, 280, 470):
        d.ellipse((22, y - 8, 38, y + 8), fill=c["hole"], outline=(196, 192, 183))
    d.text((70, 38), f"FIG. {roman}", font=font("didotb", 22), fill=a)
    spaced(d, (70 + d.textlength(f"FIG. {roman}", font=font("didotb", 22)) + 18, 46), "OBSIDIAN PLUGIN", font("futura", 11), c["mute"], 4.2)
    spaced(d, (W - 40, 44), f"ITH_PLATE_{roman}", font("futura", 9), c["mute"], 3, anchor="r")
    s = shot(slug, "light", 520, 330)
    x, y = 70, 84
    im.paste(s, (x, y))
    rough_rect(d, (x - 6, y - 6, x + s.width + 6, y + s.height + 6), c["ink"], 2, seed=hash(slug) % 1000)
    # leader from inside the specimen to a label on the right
    px, py = x + s.width - 40, y + 90
    lx, ly = x + s.width + 70, 150
    rough_line(d, (px, py), (lx, ly), c["ink"], 1, seed=3)
    d.line((lx, ly, lx + 40, ly), fill=c["ink"], width=1)
    d.ellipse((px - 3, py - 3, px + 3, py + 3), fill=c["ink"])
    spaced(d, (lx + 46, ly - 14), "WHAT IT DOES", font("futura", 10), c["mute"], 2.6)
    d.text((lx + 46, ly + 2), leader, font=font("hand", 17), fill=a)
    # name block, bottom
    d.text((68, 436), name, font=font("didot", 44), fill=c["ink"])
    d.text((70, 500), line, font=font("hand", 17), fill=c["mute"])
    d.text((W - 72, 486), "R.", font=font("snell", 30), fill=c["mute"])
    return round_page(im, c["page"])


def still(slug, name, line, roman):
    c = DARK
    a = ACCENT[slug]
    im = Image.new("RGB", (W, H), c["bg"])
    s = shot(slug, "dark", 820, 360)
    frame = Image.new("RGB", (W, 380), c["still"])
    wash(frame, (W // 2, 190), 520, 230, a, alpha=120, blur=70)  # stage light in the tool's colour
    fx = (W - s.width) // 2
    frame.paste(s, (fx, 10))
    im.paste(frame, (0, 64))
    wash(im, (W // 2, 500), 300, 60, a, alpha=60, blur=50)  # the light spills onto the caption
    noise = Image.effect_noise((W, 380), 18).convert("L").point(lambda v: 128 + (v - 128) // 3)
    im.paste(Image.new("RGB", (W, 380), (40, 40, 40)), (0, 64), noise.point(lambda v: max(0, v - 118)))
    d = ImageDraw.Draw(im)
    spaced(d, (40, 30), f"SCENE {roman}", font("futura", 10), c["mute"], 3.5)
    spaced(d, (W - 40, 30), "REXXALL / OBSIDIAN", font("futura", 10), c["mute"], 3.5, anchor="r")
    d.text((W / 2, 492), name, font=font("didot", 40), fill=c["ink"], anchor="mm")
    spaced(d, (W / 2, 520), line.upper(), font("futura", 10), tuple(min(255, v + 70) for v in a), 2.8, anchor="m")
    d.text((W - 40, 548), "R.", font=font("snell", 22), fill=c["mute"], anchor="rs")
    return round_page(im, c["page"])


def web(mode):
    apps = [("Noesis Paper Reader", "read a paper in three passes and come out able to explain it", "X"),
            ("Bunmyaku", "turn any Japanese material into a local study desk", "XI"),
            ("Evidence Inbox", "save a public post into Obsidian with its text, images and source link", "XII")]
    Wd, Hd = 1800, 300
    if mode == "light":
        c = LIGHT
        im = Image.new("RGB", (Wd, Hd), c["bg"]); d = ImageDraw.Draw(im)
        for y in (80, 220):
            d.ellipse((22, y - 8, 38, y + 8), fill=c["hole"], outline=(196, 192, 183))
        d.text((70, 36), "PLATE X–XII", font=font("didotb", 22), fill=c["ink"])
        spaced(d, (70 + d.textlength("PLATE X–XII", font=font("didotb", 22)) + 18, 44), "WEB · RUNS IN THE BROWSER, KEEPS NOTHING", font("futura", 11), c["mute"], 4.2)
        for i, (n, l, r) in enumerate(apps):
            x = 70 + i * 560
            rough_line(d, (x, 120), (x + 500, 120), c["ink"], 1, seed=10 + i)
            wa = WEB_ACCENT[i]
            wash(im, (x + 240, 190), 260, 90, wa, alpha=60, blur=40); d = ImageDraw.Draw(im)
            d.text((x, 136), f"FIG. {r}", font=font("didotb", 13), fill=wa)
            d.text((x, 160), n, font=font("didot", 34), fill=c["ink"])
            d.text((x, 212), l, font=font("hand", 17), fill=c["mute"])
        d.text((Wd - 60, 270), "R.", font=font("snell", 28), fill=c["mute"], anchor="rs")
    else:
        c = DARK
        im = Image.new("RGB", (Wd, Hd), c["bg"]); d = ImageDraw.Draw(im)
        d.rectangle((0, 50, Wd, 250), fill=c["still"])
        spaced(d, (40, 22), "SCENES X–XII · WEB", font("futura", 10), c["mute"], 3.5)
        for i, (n, l, r) in enumerate(apps):
            cx = 300 + i * 600
            wash(im, (cx, 150), 280, 110, WEB_ACCENT[i], alpha=110, blur=60); d = ImageDraw.Draw(im)
            d.text((cx, 128), n, font=font("didot", 36), fill=c["ink"], anchor="mm")
            spaced(d, (cx, 160), l.upper(), font("futura", 9.5), tuple(min(255, v + 70) for v in WEB_ACCENT[i]), 2.4, anchor="m")
        d.text((Wd - 40, 288), "R.", font=font("snell", 22), fill=c["mute"], anchor="rs")
    return round_page(im, c["page"], 36)


def colophon(mode):
    Wd, Hd = 1800, 220
    if mode == "light":
        c = LIGHT
        im = Image.new("RGB", (Wd, Hd), c["bg"]); d = ImageDraw.Draw(im)
        d.ellipse((22, 102, 38, 118), fill=c["hole"], outline=(196, 192, 183))
        d.text((70, 36), "HOW I BUILD", font=font("didotb", 22), fill=c["ink"])
        rough_line(d, (70, 76), (1730, 76), c["ink"], 1, seed=21)
        for i, t in enumerate(["start from a real chore", "keep data local, in Markdown and Git", "follow the host app's theme", "the tool proposes · you decide · undo always"]):
            x = 70 + i * 440
            fill = c["red"] if i == 3 else PRINCIPLE_ACCENT[i]
            d.text((x, 104), t, font=font("hand", 20), fill=fill)
        spaced(d, (70, 176), "CHINESE · UYGHUR · ENGLISH · JAPANESE", font("futura", 10), c["mute"], 3)
        d.text((Wd - 60, 196), "R.", font=font("snell", 28), fill=c["mute"], anchor="rs")
    else:
        c = DARK
        im = Image.new("RGB", (Wd, Hd), c["bg"]); d = ImageDraw.Draw(im)
        spaced(d, (Wd / 2, 40), "WRITTEN, BUILT AND TESTED BY", font("futura", 10), c["mute"], 4, anchor="m")
        d.text((Wd / 2, 100), "Rex", font=font("didot", 56), fill=c["ink"], anchor="mm")
        spaced(d, (Wd / 2, 140), "START FROM A REAL CHORE · KEEP DATA LOCAL, IN MARKDOWN AND GIT · FOLLOW THE HOST APP'S THEME", font("futura", 10), c["mute"], 2.8, anchor="m")
        spaced(d, (Wd / 2, 166), "THE TOOL PROPOSES · YOU DECIDE · UNDO ALWAYS", font("futura", 10), c["red"], 2.8, anchor="m")
        spaced(d, (Wd / 2, 198), "CHINESE · UYGHUR · ENGLISH · JAPANESE", font("futura", 9), c["mute"], 3, anchor="m")
    return round_page(im, c["page"], 36)


if __name__ == "__main__":
    out = ROOT / "shelf"
    for slug, name, line, leader, roman in PLUGINS:
        plate(slug, name, line, leader, roman).save(out / f"{slug}-light.png", optimize=True)
        still(slug, name, line, roman).save(out / f"{slug}-dark.png", optimize=True)
    for m in ("light", "dark"):
        web(m).save(out / f"web-{m}.png", optimize=True)
        colophon(m).save(out / f"colophon-{m}.png", optimize=True)
    print("ok")
