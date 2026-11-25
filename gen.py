#!/usr/bin/env python3
"""news-image-20261124 — deterministic broadsheet front page for 24 Nov 2026.

Renders at 2048x2048 with Pillow, then downscales (LANCZOS) to 1024x1024.
No network, no timestamps, no randomness: re-running produces byte-identical
entry.png. Every headline is a verified 24 November 2026 event (see
../dev/STORY-POOL.md); one-party claims stay attributed; tempting
neighbour-day stories are named in the DATE CHECK box, not on the page.
Winner-pattern layout: 44 stories, 3 heroes, stat strip, numbered stories,
world map with pins, per-story sources, DATE CHECK box.
"""
import math
from PIL import Image, ImageDraw, ImageFont

CANVAS = 2048
EDGE = 36

PAPER = (246, 241, 230)
INK = (24, 24, 30)
NAVY = (18, 38, 74)
RED = (178, 34, 34)
DARKRED = (122, 20, 20)
GOLD = (201, 162, 39)
TEAL = (16, 96, 110)
GREY = (110, 110, 116)
WHITE = (255, 255, 255)
CREAM = (252, 248, 238)
DARK = (16, 26, 40)
SEA = (24, 52, 92)
LAND = (120, 160, 110)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def gradient(w, h, top, bottom):
    """Deterministic vertical gradient from a stretched 1x256 strip."""
    strip = Image.new("RGB", (1, 256))
    px = strip.load()
    for i in range(256):
        t = i / 255.0
        px[0, i] = tuple(int(top[c] + (bottom[c] - top[c]) * t)
                         for c in range(3))
    return strip.resize((w, h), Image.BILINEAR)


def wrap_text(d, text, fnt, max_w):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, text, fnt, fill, max_w, leading=None):
    """Draw wrapped text; returns (next_y, line_count)."""
    if leading is None:
        leading = int(fnt.size * 1.22)
    lines = wrap_text(d, text, fnt, max_w)
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y, len(lines)


def hline(d, x0, y, x1, color=INK, width=4):
    d.line([(x0, y), (x1, y)], fill=color, width=width)


def tag(d, x, y, text, color=RED, size=28):
    d.text((x, y), text, font=F(SANS_B, size), fill=color)


def badge(d, x, y, n, r=24, fill=RED, fg=WHITE, size=30):
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=INK, width=3)
    d.text((x, y), str(n), font=F(SANS_B, size), fill=fg, anchor="mm")


REGIONS = [
    ("MIDDLE EAST 6", (178, 34, 34)),
    ("EUROPE 11", (18, 60, 140)),
    ("ASIA 8", (16, 96, 110)),
    ("AMERICAS 16", (120, 60, 140)),
    ("AFRICA 2", (180, 120, 20)),
    ("SPACE 1", (90, 90, 110)),
]


def masthead(d):
    hline(d, EDGE, 46, CANVAS - EDGE, INK, 6)
    d.text((CANVAS // 2, 56), "THE WORLD IN ONE PICTURE",
           font=F(SERIF_B, 88), fill=INK, anchor="ma")
    d.text((CANVAS // 2, 146),
           "T U E S D A Y   2 4   N O V E M B E R   2 0 2 6   \u00b7   "
           "4 4   S T O R I E S   \u00b7   O N E   P A G E",
           font=F(SANS_B, 40), fill=RED, anchor="ma")
    fnt = F(SANS_B, 26)
    sep = "  \u00b7  "
    total = sum(d.textlength(t, font=fnt) for t, _ in REGIONS)
    total += d.textlength(sep, font=fnt) * (len(REGIONS) - 1)
    x = (CANVAS - total) / 2
    for i, (t, col) in enumerate(REGIONS):
        if i:
            d.text((x, 202), sep, font=fnt, fill=GREY)
            x += d.textlength(sep, font=fnt)
        d.text((x, 202), t, font=fnt, fill=col)
        x += d.textlength(t, font=fnt)
    hline(d, EDGE, 238, CANVAS - EDGE, RED, 5)


STATS = [
    ("-7%", "Nvidia on Tuesday"),
    ("56-44", "Senate, final count"),
    ("11", "hurt in Riyadh attack"),
    ("490,000", "Russian war deaths"),
    ("$8bn", "recovered by DOJ"),
    ("M5.6", "Nepal quake"),
    ("14", "US measles deaths"),
    ("6,803", "Myanmar returns set"),
]


def stats_band(d, y0, y1):
    d.rectangle([EDGE, y0, CANVAS - EDGE, y1], fill=NAVY, outline=INK,
                width=4)
    n = len(STATS)
    w = (CANVAS - 2 * EDGE) / n
    for i, (big, label) in enumerate(STATS):
        x = EDGE + i * w
        if i:
            d.line([(x, y0 + 12), (x, y1 - 12)], fill=(90, 120, 170), width=3)
        d.text((x + w / 2, y0 + 10), big, font=F(SERIF_B, 48),
               fill=GOLD, anchor="ma")
        d.text((x + w / 2, y0 + 66), label, font=F(SANS, 21),
               fill=(215, 220, 230), anchor="ma")


# ---- heroes ---------------------------------------------------------------
# Box height 356: illustration strip 158px, then kicker, headline
# (serif 38, max 2 lines), dek (sans 24, max 2 lines).

def hero(img, d, box, n, kick, head, dek, draw_fn):
    x0, y0, x1, y1 = box
    art = Image.new("RGB", (x1 - x0, 158), PAPER)
    a = ImageDraw.Draw(art, "RGBA")
    draw_fn(art, a, (0, 0, x1 - x0, 158))
    img.paste(art, (x0, y0))
    d.rectangle([x0, y0 + 158, x1, y1], fill=PAPER)
    d.rounded_rectangle(box, radius=14, outline=INK, width=4)
    badge(d, x0 + 40, y0 + 180, n)
    tag(d, x0 + 76, y0 + 166, kick, RED, 26)
    _, hl = block(d, x0 + 24, y0 + 206, head, F(SERIF_B, 38), INK,
                  x1 - x0 - 48, leading=42)
    assert hl <= 2, "hero headline overflow: " + head
    _, dl = block(d, x0 + 24, y0 + 294, dek, F(SANS, 24), INK,
                  x1 - x0 - 48, leading=28)
    assert dl <= 2, "hero dek overflow: " + dek
    d.rounded_rectangle(box, radius=14, outline=INK, width=4)


def draw_huawei(img, d, box):
    """Brooklyn courthouse steps: white columns, a gavel coming down on a
    sound block, and red bars behind bars — guilty on fraud, cleared of
    racketeering."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (36, 40, 58), (96, 100, 118)),
              (x0, y0))
    # pediment + columns, left half
    d.polygon([(x0 + 30, y0 + 34), (x0 + 170, y0 + 8), (x0 + 310, y0 + 34)],
              fill=(225, 224, 218))
    d.rectangle([x0 + 24, y0 + 34, x0 + 316, y0 + 44], fill=(210, 208, 200))
    for cx in (48, 108, 168, 228, 282):
        d.rectangle([x0 + cx, y0 + 44, x0 + cx + 22, y0 + 118],
                    fill=(228, 226, 220), outline=(150, 148, 140), width=2)
    d.rectangle([x0 + 24, y0 + 118, x1 - 24, y0 + 130], fill=(196, 194, 186))
    d.rectangle([x0 + 12, y0 + 130, x1 - 12, y0 + 142], fill=(170, 168, 160))
    # gavel, right of the columns
    d.line([(x0 + 420, y0 + 34), (x0 + 500, y0 + 96)], fill=(120, 82, 40),
           width=13)
    d.rectangle([x0 + 388, y0 + 16, x0 + 452, y0 + 50], fill=(150, 104, 52),
                outline=INK, width=3)
    d.rectangle([x0 + 396, y0 + 104, x0 + 496, y0 + 118], fill=(110, 76, 38),
                outline=INK, width=3)
    # red bars (a verdict behind bars), far right
    for bx in (548, 584, 620):
        d.rectangle([x0 + bx, y0 + 22, x0 + bx + 18, y0 + 128],
                    fill=(178, 34, 34))
    d.line([(x0 + 536, y0 + 44), (x0 + 652, y0 + 44)], fill=(200, 200, 205),
           width=5)
    d.line([(x0 + 536, y0 + 106), (x0 + 652, y0 + 106)], fill=(200, 200, 205),
           width=5)


def draw_hormuz(img, d, box):
    """The Strait of Hormuz at dawn: a tanker with fire at its bow, a naval
    mine bobbing in the channel, headlands closing in on both sides."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (216, 138, 78), (84, 66, 92)),
              (x0, y0))
    # headlands
    d.polygon([(x0, y0 + 62), (x0 + 120, y0 + 88), (x0, y0 + 118)],
              fill=(92, 70, 58))
    d.polygon([(x1, y0 + 58), (x1 - 130, y0 + 86), (x1, y0 + 116)],
              fill=(92, 70, 58))
    d.rectangle([x0, y0 + 104, x1, y1], fill=(26, 58, 86))
    # tanker, centre-left, fire at the bow
    d.polygon([(x0 + 150, y0 + 92), (x0 + 430, y0 + 92), (x0 + 414, y0 + 122),
               (x0 + 166, y0 + 122)], fill=(148, 34, 34))
    d.rectangle([x0 + 356, y0 + 64, x0 + 392, y0 + 92], fill=(208, 208, 202))
    d.rectangle([x0 + 180, y0 + 78, x0 + 330, y0 + 92], fill=(120, 28, 28))
    for fx, fh in [(196, 46), (238, 60), (280, 42)]:
        d.polygon([(x0 + fx - 15, y0 + 94), (x0 + fx, y0 + 94 - fh),
                   (x0 + fx + 15, y0 + 94)], fill=(255, 120, 20))
        d.polygon([(x0 + fx - 7, y0 + 94), (x0 + fx, y0 + 94 - fh // 2),
                   (x0 + fx + 7, y0 + 94)], fill=(255, 210, 60))
    for sx, sy, sr in [(452, 22, 15), (484, 12, 19), (514, 24, 13)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(62, 58, 58))
    # second hull low on the right
    d.polygon([(x0 + 470, y0 + 104), (x0 + 640, y0 + 96), (x0 + 626, y0 + 124),
               (x0 + 484, y0 + 128)], fill=(92, 92, 98))
    # naval mine between them
    d.ellipse([x0 + 420, y0 + 118, x0 + 448, y0 + 146], fill=INK)
    for ang in range(0, 360, 45):
        r = math.radians(ang)
        d.line([(x0 + 434 + 12 * math.cos(r), y0 + 132 + 12 * math.sin(r)),
                (x0 + 434 + 20 * math.cos(r), y0 + 132 + 20 * math.sin(r))],
               fill=INK, width=4)
    for wy in range(0, 660, 64):
        d.line([(x0 + wy, y0 + 140), (x0 + wy + 32, y0 + 140)],
               fill=(140, 200, 230), width=3)
    d.text((x0 + 24, y0 + 8), "STRAIT OF HORMUZ", font=F(SANS_B, 26),
           fill=(255, 232, 170))


def draw_nvidia_fall(img, d, box):
    """The day after the rally: the same green chip, now with a red chart
    line sliding off it and a -7% stamp."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (10, 22, 16), (16, 44, 30)),
              (x0, y0))
    for cy in (24, 60, 96, 132):
        d.line([(x0 + 10, y0 + cy), (x0 + 150, y0 + cy), (x0 + 170, y0 + cy - 14),
                (x0 + 220, y0 + cy - 14)], fill=(36, 100, 58), width=3)
        d.ellipse([x0 + 214, y0 + cy - 20, x0 + 226, y0 + cy - 8],
                  fill=(80, 170, 105))
    # the chip, left-centre
    d.rectangle([x0 + 250, y0 + 36, x0 + 400, y0 + 128], fill=(22, 82, 46),
                outline=GOLD, width=4)
    for px in range(262, 400, 24):
        d.rectangle([x0 + px, y0 + 26, x0 + px + 12, y0 + 36], fill=GOLD)
        d.rectangle([x0 + px, y0 + 128, x0 + px + 12, y0 + 138], fill=GOLD)
    for py in range(48, 128, 22):
        d.rectangle([x0 + 240, y0 + py, x0 + 250, y0 + py + 10], fill=GOLD)
        d.rectangle([x0 + 400, y0 + py, x0 + 410, y0 + py + 10], fill=GOLD)
    d.text((x0 + 325, y0 + 62), "NVDA", font=F(SANS_B, 32), fill=WHITE,
           anchor="ma")
    d.text((x0 + 325, y0 + 96), "TUESDAY", font=F(SANS_B, 20),
           fill=(150, 230, 175), anchor="ma")
    # falling chart line, right side
    pts = [(x0 + 440, y0 + 36), (x0 + 500, y0 + 52), (x0 + 540, y0 + 44),
           (x0 + 610, y0 + 108)]
    d.line(pts, fill=(255, 92, 92), width=7, joint="curve")
    d.polygon([(x0 + 610, y0 + 108), (x0 + 584, y0 + 100), (x0 + 596, y0 + 80)],
              fill=(255, 92, 92))
    d.text((x0 + 520, y0 + 112), "-7%", font=F(SANS_B, 34),
           fill=(255, 120, 120))
    d.text((x0 + 24, y0 + 10), "SANTA CLARA", font=F(SANS_B, 26),
           fill=(180, 230, 190))


# ---- generic panel -------------------------------------------------------
# Box height 238: illustration strip 74px, kicker, headline (max 2 lines),
# dek (max 2 lines). Illustrations are drawn at 140px height then scaled.

def panel(img, d, box, n, kick, head, dek, src, draw_fn, hsize=29,
          dsize=22, illu_h=74):
    x0, y0, x1, y1 = box
    art = Image.new("RGB", (x1 - x0, 140), PAPER)
    a = ImageDraw.Draw(art, "RGBA")
    draw_fn(art, a, (0, 0, x1 - x0, 140))
    img.paste(art.resize((x1 - x0, illu_h), Image.LANCZOS), (x0, y0))
    d.rectangle([x0, y0 + illu_h, x1, y1], fill=PAPER)
    d.rounded_rectangle(box, radius=12, outline=INK, width=4)
    badge(d, x0 + 30, y0 + illu_h + 22, n, r=19, size=25)
    tag(d, x0 + 58, y0 + illu_h + 12, kick, RED, 22)
    _, hl = block(d, x0 + 18, y0 + illu_h + 42, head, F(SERIF_B, hsize), INK,
                  x1 - x0 - 36, leading=int(hsize * 1.2))
    assert hl <= 2, "panel headline overflow: " + head
    dy = y0 + illu_h + 42 + 2 * int(hsize * 1.2) + 2
    _, dl = block(d, x0 + 18, dy, dek + " \u2014 " + src, F(SANS, dsize), INK,
                  x1 - x0 - 36, leading=int(dsize * 1.22))
    assert dl <= 2, "panel dek overflow: " + dek
    d.rounded_rectangle(box, radius=12, outline=INK, width=4)


def illu_riyadh(img, d, box):
    """Riyadh financial district at night: a glass tower with a burst of
    light at its crown, a drone silhouette closing in."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (12, 16, 40), (58, 66, 96)),
              (x0, y0))
    for bx, bh in [(30, 60), (90, 84), (330, 70), (400, 52)]:
        d.rectangle([x0 + bx, y0 + 130 - bh, x0 + bx + 52, y0 + 130],
                    fill=(34, 40, 66))
        for wy in range(0, bh - 12, 14):
            d.rectangle([x0 + bx + 9, y0 + 130 - bh + wy, x0 + bx + 21,
                         y0 + 130 - bh + wy + 7], fill=(255, 220, 110))
    # the hit tower, centre
    d.polygon([(x0 + 190, y0 + 130), (x0 + 205, y0 + 30), (x0 + 245, y0 + 12),
               (x0 + 262, y0 + 130)], fill=(52, 64, 96), outline=(150, 170, 210),
              width=2)
    for wy in range(36, 124, 16):
        d.line([(x0 + 204, y0 + wy), (x0 + 256, y0 + wy)],
               fill=(140, 180, 220), width=2)
    # burst at the crown
    cx, cy = x0 + 238, y0 + 26
    for ang in range(0, 360, 30):
        r = math.radians(ang)
        d.line([(cx, cy), (cx + 26 * math.cos(r), cy + 26 * math.sin(r))],
               fill=(255, 190, 70), width=4)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 230, 150))
    # drone, top right
    dx, dy = x0 + 392, y0 + 30
    d.ellipse([dx - 8, dy - 5, dx + 8, dy + 5], fill=INK)
    d.line([(dx - 20, dy), (dx + 20, dy)], fill=(200, 200, 210), width=3)
    d.line([(dx - 20, dy - 8), (dx - 20, dy + 8)], fill=(200, 200, 210),
           width=3)
    d.line([(dx + 20, dy - 8), (dx + 20, dy + 8)], fill=(200, 200, 210),
           width=3)
    d.rectangle([x0, y0 + 130, x1, y1], fill=(18, 20, 34))
    d.text((x0 + 24, y0 + 10), "RIYADH", font=F(SANS_B, 24),
           fill=(255, 220, 150))


def illu_cartagena(img, d, box):
    """A supermarket front at midday: awning, glass doors, a police cordon
    and a shield — everyone out alive."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (120, 170, 210), (220, 200, 150)),
              (x0, y0))
    # storefront
    d.rectangle([x0 + 60, y0 + 44, x0 + 360, y0 + 130], fill=(232, 228, 218),
                outline=INK, width=3)
    d.polygon([(x0 + 48, y0 + 44), (x0 + 372, y0 + 44), (x0 + 348, y0 + 66),
               (x0 + 72, y0 + 66)], fill=(200, 60, 50))
    for wx in (84, 150, 216, 282):
        d.rectangle([x0 + wx, y0 + 78, x0 + wx + 52, y0 + 118],
                    fill=(170, 205, 225), outline=INK, width=2)
    d.rectangle([x0 + 196, y0 + 78, x0 + 224, y0 + 130], fill=(90, 90, 96))
    d.text((x0 + 210, y0 + 50), "MARKET", font=F(SANS_B, 18), fill=WHITE,
           anchor="ma")
    # cordon tape
    for tx in range(20, 470, 56):
        d.polygon([(x0 + tx, y0 + 104), (x0 + tx + 28, y0 + 98),
                   (x0 + tx + 28, y0 + 110), (x0 + tx, y0 + 116)],
                  fill=(255, 205, 40), outline=INK)
    # shield, right
    d.polygon([(x0 + 396, y0 + 52), (x0 + 444, y0 + 52), (x0 + 444, y0 + 92),
               (x0 + 420, y0 + 116), (x0 + 396, y0 + 92)], fill=(30, 60, 140),
              outline=WHITE, width=3)
    d.text((x0 + 420, y0 + 68), "ALL", font=F(SANS_B, 16), fill=WHITE,
           anchor="ma")
    d.text((x0 + 420, y0 + 86), "OUT", font=F(SANS_B, 16), fill=WHITE,
           anchor="ma")
    d.rectangle([x0, y0 + 130, x1, y1], fill=(150, 140, 120))


def illu_gaza(img, d, box):
    """Gaza City skyline under a grey sky: rooftops, water tanks, and smoke
    rising from one struck building."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (96, 100, 108), (176, 168, 150)),
              (x0, y0))
    for bx, bw, bh in [(20, 70, 74), (100, 56, 96), (166, 80, 64),
                       (330, 64, 88), (404, 58, 70)]:
        d.rectangle([x0 + bx, y0 + 130 - bh, x0 + bx + bw, y0 + 130],
                    fill=(168, 158, 140), outline=(90, 84, 74), width=2)
        for wy in range(0, bh - 14, 16):
            for wx in range(8, bw - 14, 18):
                d.rectangle([x0 + bx + wx, y0 + 130 - bh + wy,
                             x0 + bx + wx + 9, y0 + 130 - bh + wy + 8],
                            fill=(90, 92, 96))
        d.rectangle([x0 + bx + 8, y0 + 122 - bh, x0 + bx + 24, y0 + 130 - bh],
                    fill=(70, 70, 74))
    # smoke over the struck block, centre-right
    for sx, sy, sr in [(272, 34, 17), (296, 20, 23), (322, 36, 15),
                       (300, 52, 19)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(74, 72, 72))
    d.polygon([(x0 + 262, y0 + 92), (x0 + 282, y0 + 58), (x0 + 302, y0 + 92)],
              fill=(255, 130, 30))
    d.rectangle([x0, y0 + 130, x1, y1], fill=(120, 112, 98))
    d.text((x0 + 24, y0 + 10), "GAZA CITY", font=F(SANS_B, 24),
           fill=(245, 240, 225))


def illu_leak(img, d, box):
    """A leaked statistics sheet: ruled rows, a bar column climbing off the
    page, and a red stamp with the count."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (52, 54, 64), (96, 98, 108)),
              (x0, y0))
    d.rectangle([x0 + 36, y0 + 14, x0 + 330, y0 + 130], fill=(238, 236, 228),
                outline=INK, width=3)
    for ry in range(30, 126, 16):
        d.line([(x0 + 48, y0 + ry), (x0 + 318, y0 + ry)], fill=(170, 172, 180),
               width=2)
    bars = [(70, 26), (120, 38), (170, 52), (220, 74), (270, 100)]
    for bx, bh in bars:
        d.rectangle([x0 + bx, y0 + 126 - bh, x0 + bx + 34, y0 + 126],
                    fill=(120, 128, 150))
    d.rectangle([x0 + 270, y0 + 26, x0 + 304, y0 + 126], fill=RED)
    # stamp
    d.rounded_rectangle([x0 + 320, y0 + 52, x0 + 468, y0 + 102], radius=8,
                        outline=RED, width=5)
    d.text((x0 + 394, y0 + 62), "490,000", font=F(SANS_B, 30), fill=RED,
           anchor="ma")
    d.text((x0 + 394, y0 + 90), "LEAKED", font=F(SANS_B, 15), fill=RED,
           anchor="ma")
    d.text((x0 + 24, y0 + 10), "", font=F(SANS_B, 20), fill=WHITE)


def illu_myanmar(img, d, box):
    """Scales of justice over a map-gold field: five stars on the beam for
    the five sanctioned generals, a gavel rest beside."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (30, 52, 44), (84, 110, 84)),
              (x0, y0))
    cx = x0 + 200
    d.line([(cx, y0 + 22), (cx, y0 + 104)], fill=GOLD, width=7)
    d.line([(cx - 110, y0 + 34), (cx + 110, y0 + 34)], fill=GOLD, width=6)
    for px in (cx - 110, cx + 110):
        d.line([(px, y0 + 34), (px - 26, y0 + 84)], fill=GOLD, width=3)
        d.line([(px, y0 + 34), (px + 26, y0 + 84)], fill=GOLD, width=3)
        d.arc([px - 30, y0 + 76, px + 30, y0 + 100], 0, 180, fill=GOLD,
              width=5)
    d.rectangle([cx - 44, y0 + 104, cx + 44, y0 + 114], fill=GOLD)
    # five stars along the top
    for i, sx in enumerate((52, 116, 300, 364, 428)):
        cy = y0 + 26
        pts = []
        for k in range(10):
            ang = math.radians(-90 + k * 36)
            rr = 13 if k % 2 == 0 else 5.5
            pts.append((x0 + sx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon(pts, fill=GOLD)
    d.text((x0 + 330, y0 + 104), "ICJ RULING", font=F(SANS_B, 20),
           fill=(230, 240, 225))
    d.text((x0 + 24, y0 + 108), "14 NATIONS", font=F(SANS_B, 20),
           fill=(230, 240, 225))


def illu_measles(img, d, box):
    """A case curve turning up hard: pale dots swelling into red spots as
    the line climbs past 6,000."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(28, 30, 40))
    pts = [(x0 + 30, y0 + 116), (x0 + 110, y0 + 110), (x0 + 190, y0 + 104),
           (x0 + 270, y0 + 88), (x0 + 350, y0 + 56), (x0 + 430, y0 + 26)]
    d.line(pts, fill=(255, 110, 110), width=5, joint="curve")
    for i, (px, py) in enumerate(pts):
        r = 5 + i * 3
        d.ellipse([px - r, py - r, px + r, py + r], fill=(220, 60, 60),
                  outline=(255, 170, 170), width=2)
    for gx in range(30, 470, 55):
        d.line([(x0 + gx, y0 + 122), (x0 + gx, y0 + 126)], fill=(90, 95, 110),
               width=2)
    d.text((x0 + 24, y0 + 10), "CASES NEAR 6,000", font=F(SANS_B, 24),
           fill=(255, 200, 200))
    d.text((x0 + 330, y0 + 108), "14 DEAD", font=F(SANS_B, 24),
           fill=(255, 120, 120))


def illu_nepal(img, d, box):
    """A seismograph trace spiking M5.6 over a Himalayan ridge line."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (34, 46, 78), (110, 124, 148)),
              (x0, y0))
    # ridge
    d.polygon([(x0, y0 + 108), (x0 + 90, y0 + 66), (x0 + 150, y0 + 88),
               (x0 + 240, y0 + 52), (x0 + 320, y0 + 84), (x0 + 400, y0 + 62),
               (x1, y0 + 96), (x1, y1), (x0, y1)], fill=(52, 62, 88))
    d.polygon([(x0 + 216, y0 + 66), (x0 + 240, y0 + 52), (x0 + 264, y0 + 66),
               (x0 + 252, y0 + 62), (x0 + 240, y0 + 70), (x0 + 228, y0 + 62)],
              fill=WHITE)
    # trace paper, top
    d.rectangle([x0 + 20, y0 + 12, x0 + 330, y0 + 62], fill=(240, 238, 228),
                outline=INK, width=2)
    pts = [(x0 + 30, y0 + 37), (x0 + 80, y0 + 37), (x0 + 105, y0 + 32),
           (x0 + 130, y0 + 42), (x0 + 155, y0 + 37), (x0 + 180, y0 + 37),
           (x0 + 205, y0 + 16), (x0 + 222, y0 + 58), (x0 + 240, y0 + 37),
           (x0 + 280, y0 + 33), (x0 + 320, y0 + 37)]
    d.line(pts, fill=RED, width=3, joint="curve")
    d.text((x0 + 352, y0 + 20), "M5.6", font=F(SANS_B, 30), fill=(255, 214, 150))
    d.text((x0 + 352, y0 + 52), "KOSHI", font=F(SANS_B, 20),
           fill=(220, 228, 245))


def illu_tariffs(img, d, box):
    """A container port at dusk: stacked boxes, a crane, and a big percent
    sign stamped over the manifest."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (196, 128, 74), (88, 70, 96)),
              (x0, y0))
    cols = [(200, 60, 50), (40, 100, 170), (40, 140, 80), (210, 150, 40)]
    for i, cx in enumerate((36, 128, 220)):
        for j in range(3):
            d.rectangle([x0 + cx, y0 + 118 - j * 26, x0 + cx + 84,
                         y0 + 142 - j * 26], fill=cols[(i + j) % 4],
                        outline=INK, width=2)
    # crane
    d.line([(x0 + 350, y0 + 130), (x0 + 350, y0 + 30)], fill=INK, width=7)
    d.line([(x0 + 350, y0 + 30), (x0 + 452, y0 + 30)], fill=INK, width=7)
    d.line([(x0 + 428, y0 + 30), (x0 + 428, y0 + 66)], fill=INK, width=3)
    d.rectangle([x0 + 404, y0 + 66, x0 + 452, y0 + 90], fill=(200, 60, 50),
                outline=INK, width=2)
    d.text((x0 + 330, y0 + 96), "%", font=F(SERIF_B, 44), fill=WHITE)
    d.rectangle([x0, y0 + 130, x1, y1], fill=(40, 44, 56))
    d.text((x0 + 24, y0 + 8), "16 ECONOMIES", font=F(SANS_B, 24),
           fill=(255, 232, 180))


def illu_puigdemont(img, d, box):
    """A courthouse door opening: gold-and-red stripes of Catalonia on one
    side, a clear check mark on the other — case closed."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (70, 66, 60), (140, 132, 116)),
              (x0, y0))
    # striped banner, left
    for i in range(5):
        d.rectangle([x0 + 30, y0 + 22 + i * 22, x0 + 130, y0 + 44 + i * 22],
                    fill=(216, 40, 40) if i % 2 == 0 else (245, 200, 40))
    # door ajar, centre
    d.polygon([(x0 + 180, y0 + 18), (x0 + 252, y0 + 30), (x0 + 252, y0 + 132),
               (x0 + 180, y0 + 132)], fill=(96, 70, 44), outline=INK, width=3)
    d.polygon([(x0 + 252, y0 + 30), (x0 + 292, y0 + 22), (x0 + 292, y0 + 132),
               (x0 + 252, y0 + 132)], fill=(255, 240, 190))
    d.ellipse([x0 + 196, y0 + 70, x0 + 208, y0 + 82], fill=GOLD)
    # check mark, right
    d.line([(x0 + 300, y0 + 74), (x0 + 330, y0 + 104), (x0 + 372, y0 + 44)],
           fill=(50, 160, 80), width=10, joint="curve")
    d.text((x0 + 292, y0 + 112), "AMNESTY", font=F(SANS_B, 17),
           fill=(235, 245, 235))


def illu_senate(img, d, box):
    """The Capitol dome in miniature and a seat bar: 56 blue, 44 red."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (196, 156, 108), (62, 72, 112)),
              (x0, y0))
    d.ellipse([x0 + 60, y0 + 6, x0 + 130, y0 + 76], fill=(255, 210, 120))
    d.polygon([(x0 + 130, y0 + 36), (x0 + 162, y0 + 6), (x0 + 194, y0 + 36)],
              fill=(230, 230, 225))
    d.rectangle([x0 + 136, y0 + 36, x0 + 188, y0 + 54], fill=(230, 230, 225))
    d.rectangle([x0 + 104, y0 + 54, x0 + 220, y0 + 60], fill=(210, 210, 205))
    for cx in range(106, 214, 24):
        d.rectangle([x0 + cx, y0 + 60, x0 + cx + 12, y0 + 100],
                    fill=(220, 220, 215), outline=INK, width=2)
    d.rectangle([x0 + 96, y0 + 100, x0 + 228, y0 + 108], fill=(200, 200, 195))
    # seat bar, right
    d.rectangle([x0 + 246, y0 + 56, x0 + 366, y0 + 84], fill=(180, 40, 40),
                outline=INK, width=2)
    d.rectangle([x0 + 246, y0 + 56, x0 + 313, y0 + 84], fill=(30, 60, 160))
    d.text((x0 + 246, y0 + 88), "56 - 44", font=F(SERIF_B, 30), fill=INK)


def illu_shanghai(img, d, box):
    """The Shanghai skyline at night — a pearl tower among slabs — under a
    magnifying glass."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (14, 20, 48), (66, 60, 96)),
              (x0, y0))
    for bx, bw, bh in [(24, 44, 70), (78, 36, 96), (250, 40, 80),
                       (300, 52, 62), (30, 60, 44)]:
        d.rectangle([x0 + bx, y0 + 132 - bh, x0 + bx + bw, y0 + 132],
                    fill=(36, 42, 70))
        for wy in range(0, bh - 12, 15):
            d.rectangle([x0 + bx + 7, y0 + 132 - bh + wy, x0 + bx + 17,
                         y0 + 132 - bh + wy + 7], fill=(255, 220, 110))
    # pearl tower: two spheres on a column
    d.rectangle([x0 + 168, y0 + 60, x0 + 180, y0 + 132], fill=(60, 70, 104))
    d.ellipse([x0 + 152, y0 + 78, x0 + 196, y0 + 110], fill=(190, 90, 110))
    d.ellipse([x0 + 158, y0 + 30, x0 + 190, y0 + 58], fill=(200, 110, 130))
    d.line([(x0 + 174, y0 + 30), (x0 + 174, y0 + 8)], fill=(200, 200, 215),
           width=3)
    # magnifier over the tower
    d.ellipse([x0 + 128, y0 + 12, x0 + 224, y0 + 108], outline=(255, 235, 170),
              width=6)
    d.line([(x0 + 208, y0 + 92), (x0 + 252, y0 + 128)], fill=(255, 235, 170),
           width=9)
    d.rectangle([x0, y0 + 132, x1, y1], fill=(16, 18, 30))


def illu_awacs(img, d, box):
    """An AWACS in profile: fuselage, the great radar disc on struts, and
    a sweeping radar arc ahead of it."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (90, 130, 180), (190, 205, 225)),
              (x0, y0))
    # radar sweep arcs
    for r in (36, 62, 88):
        d.arc([x0 + 268 - r, y0 + 66 - r, x0 + 268 + r, y0 + 66 + r],
              -50, 50, fill=(240, 250, 255), width=4)
    # fuselage
    d.ellipse([x0 + 40, y0 + 62, x0 + 268, y0 + 92], fill=(232, 234, 238),
              outline=INK, width=3)
    d.polygon([(x0 + 44, y0 + 66), (x0 + 16, y0 + 40), (x0 + 52, y0 + 40),
               (x0 + 66, y0 + 62)], fill=(200, 60, 50), outline=INK, width=2)
    for wx in range(90, 250, 22):
        d.ellipse([x0 + wx, y0 + 70, x0 + wx + 9, y0 + 79], fill=(70, 100, 140))
    # wing + engines
    d.polygon([(x0 + 138, y0 + 88), (x0 + 196, y0 + 88), (x0 + 226, y0 + 118),
               (x0 + 168, y0 + 118)], fill=(200, 202, 208), outline=INK,
              width=2)
    d.rectangle([x0 + 158, y0 + 100, x0 + 182, y0 + 114], fill=(90, 96, 108))
    # radar disc
    d.line([(x0 + 138, y0 + 62), (x0 + 146, y0 + 40)], fill=INK, width=4)
    d.line([(x0 + 178, y0 + 62), (x0 + 170, y0 + 40)], fill=INK, width=4)
    d.ellipse([x0 + 112, y0 + 22, x0 + 204, y0 + 44], fill=(240, 240, 244),
              outline=INK, width=3)
    d.text((x0 + 24, y0 + 10), "AWACS", font=F(SANS_B, 22), fill=(30, 50, 80))


def illu_pharma(img, d, box):
    """A laboratory flask beside two capsules, and a rising arrow over a
    price tag — the biggest drug deal in three years."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (36, 60, 66), (96, 128, 118)),
              (x0, y0))
    # flask
    d.polygon([(x0 + 84, y0 + 30), (x0 + 116, y0 + 30), (x0 + 116, y0 + 62),
               (x0 + 146, y0 + 118), (x0 + 54, y0 + 118), (x0 + 84, y0 + 62)],
              fill=(210, 232, 228), outline=INK, width=3)
    d.polygon([(x0 + 74, y0 + 88), (x0 + 126, y0 + 88), (x0 + 140, y0 + 112),
               (x0 + 60, y0 + 112)], fill=(40, 170, 150))
    for bx, by, br in [(88, 98, 5), (104, 104, 4), (96, 78, 3)]:
        d.ellipse([x0 + bx - br, y0 + by - br, x0 + bx + br, y0 + by + br],
                  fill=(190, 240, 230))
    d.rectangle([x0 + 78, y0 + 22, x0 + 122, y0 + 32], fill=(170, 190, 185),
                outline=INK, width=2)
    # capsules
    for cx, cy, ang in [(210, 62, 0), (252, 92, 0)]:
        d.rounded_rectangle([x0 + cx, y0 + cy, x0 + cx + 64, y0 + cy + 26],
                            radius=13, fill=(240, 240, 235), outline=INK,
                            width=2)
        d.rounded_rectangle([x0 + cx + 32, y0 + cy, x0 + cx + 64, y0 + cy + 26],
                            radius=13, fill=(200, 60, 50), outline=INK,
                            width=2)
    # rising arrow + tag
    pts = [(x0 + 196, y0 + 122), (x0 + 250, y0 + 96), (x0 + 282, y0 + 104),
           (x0 + 330, y0 + 58)]
    d.line(pts, fill=(255, 214, 90), width=6, joint="curve")
    d.polygon([(x0 + 330, y0 + 58), (x0 + 306, y0 + 64), (x0 + 318, y0 + 82)],
              fill=(255, 214, 90))
    d.text((x0 + 24, y0 + 10), "SINCE 2023", font=F(SANS_B, 20),
           fill=(225, 245, 235))


# ---- world map -----------------------------------------------------------

CONTINENTS = [
    [(-170, 70), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    [(-80, 10), (-60, 5), (-50, 0), (-35, -8), (-40, -20), (-50, -30),
     (-60, -40), (-70, -55), (-75, -35), (-80, -15)],
    [(-10, 35), (10, 37), (30, 32), (35, 28), (43, 12), (51, 10), (40, -5),
     (35, -20), (20, -35), (15, -20), (10, -5), (-5, 5), (-17, 15),
     (-17, 25)],
    [(-10, 36), (-9, 43), (0, 48), (-5, 50), (5, 53), (8, 57), (18, 56),
     (21, 55), (28, 60), (30, 70), (40, 68), (45, 55), (40, 45), (30, 36),
     (23, 36), (19, 40), (12, 44), (3, 42), (-2, 37)],
    [(40, 68), (60, 70), (90, 75), (120, 77), (160, 70), (180, 66),
     (162, 60), (158, 52), (142, 45), (135, 35), (127, 35), (120, 30),
     (110, 20), (105, 10), (100, 8), (95, 16), (90, 22), (80, 8), (75, 20),
     (65, 25), (55, 25), (50, 29), (43, 12), (40, 30)],
    [(113, -22), (114, -30), (120, -34), (130, -32), (140, -38), (150, -37),
     (153, -27), (146, -19), (142, -11), (135, -12), (130, -13), (122, -17)],
]

# (story number, longitude, latitude). 25 and 29 are second stories in
# Washington and New York (pins 11 and 1); 43 is the US gas market.
PINS = [
    (1, -73.9, 40.7), (2, 56.5, 26.5), (3, -121.96, 37.35),
    (4, 46.7, 24.6), (5, -75.5, 10.4), (6, 34.3, 31.5),
    (7, 37.6, 55.8), (8, 96.2, 19.8), (9, -77.8, 40.9),
    (10, 87.0, 27.0), (11, -77.0, 38.9), (12, -3.7, 40.4),
    (13, -77.0, 38.9), (14, 121.5, 31.2), (15, 21.0, 52.2),
    (16, 2.35, 48.9), (17, 34.3, 31.5), (18, -82.4, 23.1),
    (19, -107.4, 24.8), (20, 4.35, 50.85), (21, 35.2, 47.8),
    (22, 32.5, 15.6), (23, 55.9, 25.8), (24, -73.6, 4.1),
    (26, -93.6, 41.9), (27, -122.4, 37.8), (28, -66.9, 10.5),
    (30, 100.3, 40.9), (31, 90.4, 23.8), (32, 24.7, 59.4),
    (33, 125.8, 39.0), (34, 127.0, 37.6), (35, 44.5, 40.2),
    (36, 12.6, 55.7), (37, 35.2, 31.8), (38, -0.1, 51.5),
    (39, -66.1, 18.5), (40, 2.35, 48.9), (41, 12.45, 41.9),
    (42, 13.2, 11.8), (44, 127.0, 37.6),
]
# Marker nudges (px) for pins that would otherwise sit on top of each
# other; a thin leader line joins the marker to its true spot.
PIN_OFFSETS = {
    11: (-40, -28), 13: (38, -26), 17: (-36, 24), 23: (36, 22),
    37: (36, -24), 40: (44, 24), 44: (40, -28),
}


def world_map(img, d, box):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=SEA, outline=INK, width=4)
    d.text((x0 + 20, y0 + 10), "WHERE IT HAPPENED",
           font=F(SANS_B, 30), fill=GOLD)
    mx0, my0, mx1, my1 = x0 + 16, y0 + 50, x1 - 16, y1 - 44
    mw, mh = mx1 - mx0, my1 - my0

    def proj(lon, lat):
        return (mx0 + (lon + 180) / 360 * mw,
                my0 + (90 - lat) / 180 * mh)

    for cont in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in cont],
                  fill=LAND, outline=(200, 210, 190))
    for n, lon, lat in PINS:
        px, py = proj(lon, lat)
        dx, dy = PIN_OFFSETS.get(n, (0, 0))
        if (dx, dy) != (0, 0):
            d.line([(px, py), (px + dx, py + dy)], fill=WHITE, width=3)
            px, py = px + dx, py + dy
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=RED,
                  outline=WHITE, width=2)
        d.text((px, py), str(n), font=F(SANS_B, 17), fill=WHITE, anchor="mm")
    d.text((x0 + 20, y1 - 36),
           "25, 29: Washington & New York again.  43: US gas.",
           font=F(SANS, 20), fill=(215, 220, 230))


BRIEFS = [
    (17, "Oxfam: Gaza a 'toxic land'; children reach UK care \u2014 Horizon"),
    (18, "WHO chief visits Cuba as health system deteriorates \u2014 Horizon"),
    (19, "Mexico to try 'Chapo Isidro' at home, not extradite \u2014 Horizon"),
    (20, "EU package would ban Russian symbols at sport \u2014 Horizon"),
    (21, "Zaporizhzhia night attacks kill 2, wound 30-plus \u2014 Horizon"),
    (22, "Sudan army: RSF drone hit a UN building \u2014 Horizon"),
    (23, "Coach-truck crash kills 11 in Ras Al Khaimah \u2014 The National"),
    (24, "Car bomb wrecks buildings in Villavicencio \u2014 The Hindu"),
    (25, "DOJ recovers $8bn, charges 800+ in anti-scam surge \u2014 Fox News"),
    (26, "Army to detonate lead azide in Iowa; evacuations \u2014 Wash. Post"),
    (27, "Record king tides flood Bay Area roads \u2014 ABC7"),
    (28, "Venezuela puts public debt at $237.5bn \u2014 NXplace"),
    (29, "Anthropic closes below its $83 IPO price \u2014 One Turn"),
    (30, "Pakistan's Ali named for Shenzhou-24 crew \u2014 Straits Times"),
    (31, "Hasina sets Dec 16 return to Bangladesh \u2014 BBC"),
    (32, "Estonia to close its border with Russia \u2014 Politico Europe"),
    (33, "North Korea weighs closing Swiss office \u2014 Daily Maverick"),
    (34, "South Korea scrambles jets over Russian planes \u2014 Japan Times"),
    (35, "Armenia drops Karabakh from draft constitution \u2014 The Hindu"),
    (36, "Denmark's top court upholds 'ghetto plan' \u2014 Le Monde"),
    (37, "Eisenkot signs first coalition deal \u2014 One Turn"),
    (38, "PM Burnham reopens debate on closer EU ties \u2014 One Turn"),
    (39, "Miss Israel denies boos, blames edited audio \u2014 NMH"),
    (40, "Sarkozy and Carla Bruni to stand trial \u2014 One Turn"),
    (41, "Book: Pope Francis diary tells of seeing the devil \u2014 SCMP"),
    (42, "Borno school enrolment nearly doubles \u2014 Al Jazeera"),
    (43, "US natural gas jumps 12% to $3.57 on cold wave \u2014 Horizon"),
    (44, "Seoul stocks rebound 6% after Wall Street surge \u2014 Horizon"),
]


def briefs_band(d, x0, y0, x1, y1):
    d.text((x0, y0 + 6), "IN BRIEF  \u2014  17\u201344",
           font=F(SERIF_B, 32), fill=INK)
    hline(d, x0, y0 + 50, x1, RED, 4)
    col_w = (x1 - x0 - 40) / 2
    fnt = F(SANS, 19)
    for i, (n, text) in enumerate(BRIEFS):
        col = i // 14
        row = i % 14
        bx = x0 + col * (col_w + 40)
        by = y0 + 60 + row * 20
        line = f"{n}. {text}"
        assert d.textlength(line, font=fnt) <= col_w, \
            "brief overflow: " + line
        d.text((bx, by), line, font=fnt, fill=INK)


EXCLUDED_LEFT = [
    "Nvidia reinstates Huang as CEO \u2014 Monday 23 Nov",
    "COP31 ends without a deal \u2014 Sunday 22 Nov",
    "Senegal restored as AFCON champions \u2014 Wed 25 Nov",
    "Iran flogs singer Ahmadi \u2014 reported Monday 23 Nov",
    "Democrats' 258 House seats \u2014 settled Monday 23 Nov",
]
EXCLUDED_RIGHT = [
    "'Chapo Isidro' captured in Sinaloa \u2014 23 Nov",
    "Guterres calls for global AI rules \u2014 Monday 23 Nov",
    "Shenzhou-24 launch coverage \u2014 Wednesday 25 Nov",
    "Solomons\u2013Australia treaty signed \u2014 Wed 25 Nov",
    "Asian tech tumbles, Nikkei -2.8% \u2014 Wednesday 25 Nov",
]


def date_check(d, box):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=(232, 226, 208), outline=INK,
                        width=4)
    d.text((x0 + 24, y0 + 10), "DATE CHECK \u2014 LEFT OUT ON PURPOSE",
           font=F(SANS_B, 28), fill=DARKRED)
    fnt = F(SANS, 22)
    for i, t in enumerate(EXCLUDED_LEFT):
        d.text((x0 + 24, y0 + 48 + i * 22), "\u2715  " + t, font=fnt, fill=INK)
    for i, t in enumerate(EXCLUDED_RIGHT):
        d.text((x0 + 1010, y0 + 48 + i * 22), "\u2715  " + t, font=fnt,
               fill=INK)
    d.text((x0 + 24, y0 + 162),
           "Every story on this page happened, or was first reported, on "
           "Tuesday 24 November 2026.",
           font=F(SANS_B, 23), fill=INK)
    d.text((x0 + 24, y0 + 190),
           "Sources: One Turn \u00b7 Horizon \u00b7 BBC \u00b7 "
           "Al Jazeera \u00b7 Fox News \u00b7 Washington Post "
           "\u00b7 ABC7 \u00b7 Straits Times \u00b7 The Hindu "
           "\u00b7 Le Monde \u00b7 Politico \u00b7 Japan Times "
           "\u00b7 SCMP \u00b7 EMSC",
           font=F(SANS, 18), fill=GREY)


def main():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    masthead(d)
    stats_band(d, 250, 342)
    # three heroes
    hero(img, d, (EDGE, 354, 700, 710), 1, "NEW YORK \u2014 JUSTICE",
         "Huawei guilty of bank fraud and trade-secret theft",
         "Brooklyn jury convicts on bank fraud and conspiracy; "
         "acquitted of racketeering. \u2014 BBC",
         draw_huawei)
    hero(img, d, (716, 354, 1380, 710), 2, "HORMUZ \u2014 GULF",
         "Tankers hit mines in Hormuz, Iran's Guards say",
         "Ships catch fire in the strait; Tehran rules out talks "
         "until its seven conditions are met. \u2014 One Turn",
         draw_hormuz)
    hero(img, d, (1396, 354, 2012, 710), 3, "SANTA CLARA \u2014 TECH",
         "Nvidia falls 7% as Huang return rally fades",
         "Lawmakers question Trump's role in the CEO's return; "
         "AI stocks slide. \u2014 One Turn",
         draw_nvidia_fall)
    # panel row 1: four panels
    xs1 = [36, 534, 1032, 1530]
    xe1 = [518, 1016, 1514, 2012]
    panel(img, d, (xs1[0], 722, xe1[0], 960), 4, "RIYADH \u2014 WAR",
          "Houthi drone attack on Riyadh tower injures 11",
          "Drone hits a financial-district tower; two of the "
          "injured are Indian.",
          "Al Jazeera", illu_riyadh)
    panel(img, d, (xs1[1], 722, xe1[1], 960), 5, "CARTAGENA \u2014 COLOMBIA",
          "Hostages freed as supermarket siege ends",
          "About 20 shoppers held; security forces freed every "
          "hostage.",
          "One Turn", illu_cartagena)
    panel(img, d, (xs1[2], 722, xe1[2], 960), 6, "GAZA CITY \u2014 WAR",
          "Israeli strike kills Hamas security chief",
          "Abu Nahel killed; seven Palestinians reportedly "
          "killed.",
          "One Turn", illu_gaza)
    panel(img, d, (xs1[3], 722, xe1[3], 960), 7, "MOSCOW \u2014 WAR DATA",
          "Leaked data: 490,000 Russian war deaths",
          "Leaked agency figures count the Ukraine war dead.",
          "One Turn", illu_leak)
    # panel row 2: four panels
    panel(img, d, (xs1[0], 972, xe1[0], 1210), 8, "MYANMAR \u2014 JUSTICE",
          "UK sanctions five Myanmar generals",
          "14 nations back the ICJ ruling; Malaysia to return "
          "6,803 people.",
          "One Turn", illu_myanmar)
    panel(img, d, (xs1[1], 972, xe1[1], 1210), 9, "UNITED STATES \u2014 HEALTH",
          "US measles toll reaches 14 dead",
          "Cases near 6,000; Pennsylvania records its ninth "
          "death.",
          "NXplace", illu_measles)
    panel(img, d, (xs1[2], 972, xe1[2], 1210), 10, "NEPAL \u2014 QUAKE",
          "M5.6 quake strikes Nepal near China border",
          "Shallow tremor in Koshi province; no toll reported.",
          "Horizon", illu_nepal)
    panel(img, d, (xs1[3], 972, xe1[3], 1210), 11, "WASHINGTON \u2014 TRADE",
          "Trump readies tariffs on 16 economies",
          "Levies on China, the EU, Japan and others in "
          "preparation.",
          "US media", illu_tariffs)
    # panel row 3: five panels
    xs3 = [36, 434, 832, 1230, 1628]
    xe3 = [418, 816, 1214, 1612, 2012]
    panel(img, d, (xs3[0], 1222, xe3[0], 1460), 12, "MADRID \u2014 SPAIN",
          "Court amnesties Puigdemont",
          "Ends the case over the 2017 declaration.",
          "One Turn", illu_puigdemont, hsize=28, dsize=21)
    panel(img, d, (xs3[1], 1222, xe3[1], 1460), 13, "WASHINGTON \u2014 SENATE",
          "Senate counts final: Democrats 56-44",
          "Final counts settle the Senate.",
          "One Turn", illu_senate, hsize=28, dsize=21)
    panel(img, d, (xs3[2], 1222, xe3[2], 1460), 14, "SHANGHAI \u2014 CHINA",
          "China probes Shanghai party chief",
          "Chen Jining faces a discipline probe.",
          "One Turn", illu_shanghai, hsize=28, dsize=21)
    panel(img, d, (xs3[3], 1222, xe3[3], 1460), 15, "POLAND \u2014 NATO",
          "NATO sends AWACS to Poland",
          "After missiles fell on Polish soil; Rutte to meet "
          "Trump.",
          "Horizon", illu_awacs, hsize=28, dsize=21)
    panel(img, d, (xs3[4], 1222, xe3[4], 1460), 16, "PARIS \u2014 PHARMA",
          "Sanofi buys Insmed, a record deal",
          "The largest pharma acquisition in three years.",
          "One Turn", illu_pharma, hsize=28, dsize=21)
    # map + briefs band
    world_map(img, d, (EDGE, 1472, 560, 1816))
    briefs_band(d, 580, 1472, 2012, 1816)
    # date check footer
    date_check(d, (EDGE, 1828, 2012, 2036))
    small = img.resize((1024, 1024), Image.LANCZOS)
    small.save("entry.png", optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
