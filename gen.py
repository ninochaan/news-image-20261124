#!/usr/bin/env python3
"""Front page for Tuesday 24 November 2026, drawn with Pillow.

The page is a broadsheet: masthead, a strip of the day's key numbers,
three lead stories, thirteen smaller panels, a locator map, a briefs
column (items 17-44) and a box listing the neighbour-day stories that
were deliberately kept off the page.

Everything is drawn at twice size and shrunk with LANCZOS at the end.
No clock, no randomness, no network: the same bytes come out every run.
"""

from PIL import Image, ImageDraw, ImageFont

SIDE = 2048            # working canvas; final image is SIDE // 2
EDGE = 34              # page margin

PAPER = (247, 239, 221)
CARD = (252, 248, 238)
NAVY = (21, 41, 82)
NAVY_DARK = (13, 26, 54)
RED = (178, 49, 40)
RED_SOFT = (198, 84, 70)
GOLD = (216, 164, 44)
INK = (30, 30, 34)
GREY = (96, 92, 84)
WHITE = (255, 255, 255)
SEA = (38, 84, 124)
LAND = (110, 148, 92)

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-%s.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"

_font_cache = {}


def font(kind, style, size):
    key = (kind, style, size)
    if key not in _font_cache:
        path = (SERIF if kind == "serif" else SANS) % style
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


# ---------------------------------------------------------------- text

def wrap_words(draw, text, fnt, max_w):
    """Greedy word wrap; returns the list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, kind, style, start, max_w, max_lines, floor=10):
    """Largest size <= start whose wrap fits max_lines; returns (font, lines)."""
    size = start
    while size > floor:
        fnt = font(kind, style, size)
        lines = wrap_words(draw, text, fnt, max_w)
        if len(lines) <= max_lines:
            return fnt, lines
        size -= 2
    fnt = font(kind, style, floor)
    return fnt, wrap_words(draw, text, fnt, max_w)


def tracked(draw, cx, y, text, fnt, fill, tracking):
    """Letter-spaced text centred on cx; returns the height it used."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    asc, desc = fnt.getmetrics()
    return asc + desc


def block(draw, x, y, lines, fnt, fill, leading):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


# ---------------------------------------------------------------- data

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

REGIONS = ("MIDDLE EAST 6  ·  EUROPE 11  ·  ASIA 8  ·  "
           "AMERICAS 16  ·  AFRICA 2  ·  SPACE 1")

HEROES = [
    {
        "scene": "court",
        "kick": "1  ·  NEW YORK — JUSTICE",
        "head": "Huawei guilty of bank fraud and trade-secret theft",
        "dek": "Brooklyn jury convicts on bank fraud and conspiracy; "
               "acquitted of racketeering. — BBC",
    },
    {
        "scene": "tanker",
        "kick": "2  ·  HORMUZ — GULF",
        "head": "Tankers hit mines in Hormuz, Iran's Guards say",
        "dek": "Ships catch fire in the strait; Tehran rules out talks "
               "until its seven conditions are met. — One Turn",
    },
    {
        "scene": "chip",
        "kick": "3  ·  SANTA CLARA — TECH",
        "head": "Nvidia falls 7% as Huang return rally fades",
        "dek": "Lawmakers question Trump's role in the CEO's return; "
               "AI stocks slide. — One Turn",
    },
]

PANELS_A = [
    {
        "scene": "tower", "kick": "4  ·  RIYADH — WAR",
        "head": "Houthi drone attack on Riyadh tower injures 11",
        "dek": "Drone hits a financial-district tower; two of the "
               "injured are Indian. — Al Jazeera",
    },
    {
        "scene": "shop", "kick": "5  ·  CARTAGENA — COLOMBIA",
        "head": "Hostages freed as supermarket siege ends",
        "dek": "About 20 shoppers held; security forces freed every "
               "hostage. — One Turn",
    },
    {
        "scene": "skyline", "kick": "6  ·  GAZA CITY — WAR",
        "head": "Israeli strike kills Hamas security chief",
        "dek": "Abu Nahel killed; seven Palestinians reportedly "
               "killed. — One Turn",
    },
    {
        "scene": "bars", "kick": "7  ·  MOSCOW — WAR DATA",
        "head": "Leaked data: 490,000 Russian war deaths",
        "dek": "Leaked agency figures count the Ukraine war "
               "dead. — One Turn",
    },
]

PANELS_B = [
    {
        "scene": "scales", "kick": "8  ·  MYANMAR — JUSTICE",
        "head": "UK sanctions five Myanmar generals",
        "dek": "14 nations back the ICJ ruling; Malaysia to return "
               "6,803 people. — One Turn",
    },
    {
        "scene": "cross", "kick": "9  ·  UNITED STATES — HEALTH",
        "head": "US measles toll reaches 14 dead",
        "dek": "Cases near 6,000; Pennsylvania records its ninth "
               "death. — NXplace",
    },
    {
        "scene": "peaks", "kick": "10  ·  NEPAL — QUAKE",
        "head": "M5.6 quake strikes Nepal near China border",
        "dek": "Shallow tremor in Koshi province; no toll "
               "reported. — Horizon",
    },
    {
        "scene": "crates", "kick": "11  ·  WASHINGTON — TRADE",
        "head": "Trump readies tariffs on 16 economies",
        "dek": "Levies on China, the EU, Japan and others in "
               "preparation. — US media",
    },
]

PANELS_C = [
    {
        "scene": "flag_es", "kick": "12  ·  MADRID — SPAIN",
        "head": "Court amnesties Puigdemont",
        "dek": "Ends the case over the 2017 declaration. — One Turn",
    },
    {
        "scene": "dome", "kick": "13  ·  WASHINGTON — SENATE",
        "head": "Senate counts final: Democrats 56-44",
        "dek": "Final counts settle the Senate. — One Turn",
    },
    {
        "scene": "towers", "kick": "14  ·  SHANGHAI — CHINA",
        "head": "China probes Shanghai party chief",
        "dek": "Chen Jining faces a discipline probe. — One Turn",
    },
    {
        "scene": "awacs", "kick": "15  ·  POLAND — NATO",
        "head": "NATO sends AWACS to Poland",
        "dek": "After missiles fell on Polish soil; Rutte to meet "
               "Trump. — Horizon",
    },
    {
        "scene": "tower_paris", "kick": "16  ·  PARIS — PHARMA",
        "head": "Sanofi buys Insmed, a record deal",
        "dek": "The largest pharma acquisition in three years. "
               "— One Turn",
    },
]

BRIEFS = [
    "17. Oxfam: Gaza a 'toxic land'; children reach UK care — Horizon",
    "18. WHO chief visits Cuba as health system worsens — Horizon",
    "19. Mexico to try 'Chapo Isidro' at home — Horizon",
    "20. EU package would ban Russian symbols at sport — Horizon",
    "21. Zaporizhzhia night attacks kill 2, wound 30+ — Horizon",
    "22. Sudan army: RSF drone hit a UN building — Horizon",
    "23. Coach-truck crash kills 11 in Ras Al Khaimah — National",
    "24. Car bomb wrecks buildings in Villavicencio — Hindu",
    "25. DOJ recovers $8bn, charges 800+ in scam surge — Fox",
    "26. Army to detonate lead azide in Iowa — Wash. Post",
    "27. Record king tides flood Bay Area roads — ABC7",
    "28. Venezuela puts public debt at $237.5bn — NXplace",
    "29. Anthropic closes below its $83 IPO price — One Turn",
    "30. Pakistan's Ali named for Shenzhou-24 crew — Straits Times",
    "31. Hasina sets Dec 16 return to Bangladesh — BBC",
    "32. Estonia to close its border with Russia — Politico",
    "33. North Korea weighs closing Swiss office — Maverick",
    "34. South Korea scrambles jets over Russian planes — Japan Times",
    "35. Armenia drops Karabakh from constitution draft — Hindu",
    "36. Denmark's top court upholds 'ghetto plan' — Le Monde",
    "37. Eisenkot signs first coalition deal — One Turn",
    "38. PM Burnham reopens debate on closer EU ties — One Turn",
    "39. Miss Israel denies boos, blames edited audio — NMH",
    "40. Sarkozy and Carla Bruni to stand trial — One Turn",
    "41. Book: Pope Francis diary tells of devil — SCMP",
    "42. Borno school enrolment nearly doubles — Al Jazeera",
    "43. US natural gas jumps 12% to $3.57 — Horizon",
    "44. Seoul stocks rebound 6% on Wall Street surge — Horizon",
]

LEFT_OUT = [
    "Nvidia reinstates Huang as CEO — Monday 23 Nov",
    "COP31 ends without a deal — Sunday 22 Nov",
    "Senegal restored as AFCON champions — Wed 25 Nov",
    "Iran flogs singer Ahmadi — reported Monday 23 Nov",
    "Democrats' 258 House seats — settled Monday 23 Nov",
    "'Chapo Isidro' captured in Sinaloa — 23 Nov",
    "Guterres calls for global AI rules — Monday 23 Nov",
    "Shenzhou-24 launch — Wednesday 25 Nov",
    "Solomons–Australia treaty signed — Wednesday 25 Nov",
    "Asian tech tumbles, Nikkei -2.8% — Wednesday 25 Nov",
]

SOURCES = ("Sources: One Turn · Horizon · BBC · Al Jazeera · Fox News · "
           "Washington Post · ABC7 · Straits Times · The Hindu · Le Monde · "
           "Politico · Japan Times · SCMP · EMSC")


# ---------------------------------------------------------------- scenes
# Each painter fills the box it is given with one flat, simple picture.

def _flame(d, cx, base, h, w, colour=(232, 116, 36)):
    d.polygon([(cx - w, base), (cx, base - h), (cx + w, base)], fill=colour)
    d.polygon([(cx - w // 2, base), (cx, base - h * 2 // 3),
               (cx + w // 2, base)], fill=(244, 178, 52))


def scene_court(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(233, 226, 205))
    cx = (x0 + x1) // 2
    # pediment, beam, columns, steps — a courthouse in five shapes
    d.polygon([(x0 + w * 0.08, y0 + h * 0.34), (cx, y0 + h * 0.06),
               (x1 - w * 0.08, y0 + h * 0.34)], fill=NAVY)
    d.rectangle([x0 + w * 0.10, y0 + h * 0.38, x1 - w * 0.10, y0 + h * 0.46],
                fill=NAVY)
    for i in range(6):
        cx_i = x0 + w * (0.16 + 0.115 * i)
        d.rectangle([cx_i, y0 + h * 0.48, cx_i + w * 0.055, y0 + h * 0.82],
                    fill=NAVY)
    d.rectangle([x0 + w * 0.08, y0 + h * 0.84, x1 - w * 0.08, y0 + h * 0.90],
                fill=NAVY)
    d.rectangle([x0 + w * 0.04, y0 + h * 0.92, x1 - w * 0.04, y1],
                fill=NAVY_DARK)


def scene_tanker(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=SEA)
    d.rectangle([x0, y0, x1, y0 + h * 0.30], fill=NAVY_DARK)
    f = font("sans", "Bold", int(h * 0.20))
    d.text((x0 + w * 0.05, y0 + h * 0.05), "STRAIT OF HORMUZ", font=f,
           fill=GOLD)
    deck = y0 + h * 0.62
    hull = [(x0 + w * 0.10, deck), (x1 - w * 0.06, deck),
            (x1 - w * 0.14, y1 - h * 0.06), (x0 + w * 0.20, y1 - h * 0.06)]
    d.polygon(hull, fill=(196, 74, 44))
    d.rectangle([x1 - w * 0.30, deck - h * 0.16, x1 - w * 0.16, deck],
                fill=(240, 234, 220))
    for fx in (0.34, 0.48, 0.62):
        _flame(d, x0 + w * fx, deck, h * 0.30, w * 0.035)


def scene_chip(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(16, 34, 26))
    # falling line first, chip on top of it
    pts = [(x0 + w * fx, y0 + h * fy) for fx, fy in
           ((0.55, 0.16), (0.68, 0.30), (0.78, 0.28), (0.90, 0.52),
            (0.985, 0.72))]
    d.line(pts, fill=RED_SOFT, width=max(3, int(h * 0.035)))
    ex, ey = pts[-1]
    d.polygon([(ex, ey), (ex - w * 0.05, ey - h * 0.02),
               (ex - w * 0.01, ey + h * 0.09)], fill=RED_SOFT)
    f = font("sans", "Bold", int(h * 0.30))
    d.text((x1 - w * 0.30, y1 - h * 0.36), "-7%", font=f, fill=RED_SOFT)
    # the chip
    cw, chh = w * 0.36, h * 0.62
    cx0, cy0 = x0 + w * 0.07, y0 + h * 0.19
    for i in range(5):  # pins
        px = cx0 + cw * (0.12 + 0.19 * i)
        d.rectangle([px, cy0 - h * 0.07, px + cw * 0.07, cy0], fill=GOLD)
        d.rectangle([px, cy0 + chh, px + cw * 0.07, cy0 + chh + h * 0.07],
                    fill=GOLD)
    d.rectangle([cx0, cy0, cx0 + cw, cy0 + chh], fill=(24, 92, 56),
                outline=GOLD, width=max(2, int(h * 0.02)))
    f1 = font("sans", "Bold", int(h * 0.26))
    f2 = font("sans", "Bold", int(h * 0.15))
    d.text((cx0 + cw * 0.14, cy0 + chh * 0.16), "NVDA", font=f1, fill=WHITE)
    d.text((cx0 + cw * 0.14, cy0 + chh * 0.52), "TUESDAY", font=f2, fill=GOLD)


def scene_tower(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=NAVY_DARK)
    tx = x0 + w * 0.42
    d.polygon([(tx, y1), (tx + w * 0.05, y0 + h * 0.18),
               (tx + w * 0.10, y1)], fill=(70, 92, 138))
    for r in range(4):
        for c in range(2):
            d.rectangle([tx + w * (0.018 + 0.045 * c),
                         y0 + h * (0.34 + 0.15 * r),
                         tx + w * (0.045 + 0.045 * c),
                         y0 + h * (0.42 + 0.15 * r)], fill=GOLD)
    dx, dy = x0 + w * 0.16, y0 + h * 0.30   # a small drone: x with a dot
    s = w * 0.035
    d.line([dx - s, dy - s, dx + s, dy + s], fill=WHITE, width=3)
    d.line([dx - s, dy + s, dx + s, dy - s], fill=WHITE, width=3)
    d.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=RED_SOFT)
    f = font("sans", "Bold", int(h * 0.42))
    d.text((x0 + w * 0.62, y0 + h * 0.26), "RIYADH", font=f, fill=WHITE)


def scene_shop(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(226, 216, 192))
    d.rectangle([x0, y1 - h * 0.18, x1, y1], fill=(120, 110, 96))
    n = 9
    for i in range(n):  # striped awning
        sx = x0 + w * 0.06 + (w * 0.88 / n) * i
        col = RED if i % 2 == 0 else (244, 240, 228)
        d.polygon([(sx, y0 + h * 0.30), (sx + w * 0.88 / n, y0 + h * 0.30),
                   (sx + w * 0.88 / n + w * 0.02, y0 + h * 0.52),
                   (sx + w * 0.02, y0 + h * 0.52)], fill=col)
    d.rectangle([x0 + w * 0.10, y0 + h * 0.56, x1 - w * 0.10, y1 - h * 0.18],
                fill=(90, 104, 122))
    f = font("sans", "Bold", int(h * 0.20))
    d.text((x0 + w * 0.06, y0 + h * 0.05), "MARKET", font=f, fill=NAVY)


def scene_skyline(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(214, 178, 128))
    d.ellipse([x1 - w * 0.30, y0 + h * 0.10, x1 - w * 0.12, y0 + h * 0.46],
              fill=(240, 200, 90))
    base = y1 - h * 0.06
    heights = (0.52, 0.72, 0.44, 0.64, 0.38, 0.56, 0.48)
    for i, hh in enumerate(heights):
        bx = x0 + w * (0.03 + 0.135 * i)
        d.rectangle([bx, base - h * hh, bx + w * 0.11, base],
                    fill=(84, 66, 58))
    d.rectangle([x0, base, x1, y1], fill=(64, 50, 44))
    f = font("sans", "Bold", int(h * 0.20))
    d.text((x0 + w * 0.05, y0 + h * 0.06), "GAZA CITY", font=f, fill=NAVY_DARK)


def scene_bars(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(30, 30, 36))
    base = y1 - h * 0.14
    for i, hh in enumerate((0.30, 0.45, 0.40, 0.60, 0.55, 0.78)):
        bx = x0 + w * (0.06 + 0.155 * i)
        d.rectangle([bx, base - h * hh, bx + w * 0.10, base],
                    fill=RED_SOFT if i == 5 else (150, 148, 142))
    d.line([x0 + w * 0.04, base, x1 - w * 0.04, base], fill=WHITE, width=3)
    f = font("sans", "Bold", int(h * 0.20))
    d.text((x0 + w * 0.06, y0 + h * 0.05), "WAR DATA", font=f, fill=GOLD)


def scene_scales(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(228, 220, 198))
    cx = x0 + w * 0.30
    top = y0 + h * 0.16
    d.line([cx - w * 0.16, top, cx + w * 0.16, top], fill=NAVY, width=5)
    d.line([cx, top, cx, y1 - h * 0.22], fill=NAVY, width=5)
    d.rectangle([cx - w * 0.05, y1 - h * 0.22, cx + w * 0.05, y1 - h * 0.14],
                fill=NAVY)
    for sgn in (-1, 1):
        px = cx + sgn * w * 0.16
        d.line([px, top, px - w * 0.05, y0 + h * 0.52], fill=NAVY, width=3)
        d.line([px, top, px + w * 0.05, y0 + h * 0.52], fill=NAVY, width=3)
        d.arc([px - w * 0.055, y0 + h * 0.40, px + w * 0.055, y0 + h * 0.64],
              0, 180, fill=NAVY, width=4)
    f = font("sans", "Bold", int(h * 0.19))
    d.text((x0 + w * 0.52, y0 + h * 0.18), "14 NATIONS", font=f, fill=NAVY)
    d.text((x0 + w * 0.52, y0 + h * 0.44), "ICJ RULING", font=f, fill=RED)


def scene_cross(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(238, 232, 218))
    cx, cy = x0 + w * 0.16, y0 + h * 0.50
    d.rectangle([cx - w * 0.035, cy - h * 0.30, cx + w * 0.035, cy + h * 0.30],
                fill=RED)
    d.rectangle([cx - w * 0.10, cy - h * 0.10, cx + w * 0.10, cy + h * 0.10],
                fill=RED)
    pts = [(x0 + w * fx, y0 + h * fy) for fx, fy in
           ((0.34, 0.68), (0.52, 0.55), (0.68, 0.60), (0.86, 0.30))]
    d.line(pts, fill=NAVY, width=4)
    f = font("sans", "Bold", int(h * 0.19))
    d.text((x0 + w * 0.34, y0 + h * 0.08), "CASES NEAR 6,000", font=f,
           fill=NAVY)
    d.text((x0 + w * 0.60, y0 + h * 0.70), "14 DEAD", font=f, fill=RED)


def scene_peaks(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(196, 214, 226))
    base = y1 - h * 0.08
    for cx, hh, ww in ((0.28, 0.66, 0.34), (0.58, 0.82, 0.40),
                       (0.84, 0.58, 0.30)):
        px, py = x0 + w * cx, base - h * hh
        d.polygon([(px - w * ww / 2, base), (px, py),
                   (px + w * ww / 2, base)], fill=(96, 108, 122))
        d.polygon([(px - w * ww * 0.14, py + h * hh * 0.30), (px, py),
                   (px + w * ww * 0.14, py + h * hh * 0.30)], fill=WHITE)
    f = font("sans", "Bold", int(h * 0.24))
    d.text((x0 + w * 0.05, y0 + h * 0.06), "M5.6", font=f, fill=NAVY)
    d.text((x1 - w * 0.24, y0 + h * 0.06), "KOSHI", font=f, fill=NAVY)


def scene_crates(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(36, 52, 84))
    cols = [(196, 74, 44), (216, 164, 44), (84, 128, 92), (70, 110, 160)]
    cw, chh = w * 0.20, h * 0.30
    for r in range(2):
        for c in range(4):
            bx = x0 + w * 0.05 + c * (cw + w * 0.02)
            by = y1 - h * 0.12 - (r + 1) * (chh + h * 0.03)
            d.rectangle([bx, by, bx + cw, by + chh],
                        fill=cols[(r * 4 + c) % 4], outline=NAVY_DARK,
                        width=2)
    f = font("sans", "Bold", int(h * 0.30))
    d.text((x1 - w * 0.17, y0 + h * 0.06), "%", font=f, fill=GOLD)


def scene_flag_es(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y0 + h * 0.30], fill=(196, 60, 50))
    d.rectangle([x0, y0 + h * 0.30, x1, y0 + h * 0.70], fill=(240, 196, 60))
    d.rectangle([x0, y0 + h * 0.70, x1, y1], fill=(196, 60, 50))
    f = font("sans", "Bold", int(h * 0.22))
    d.text((x0 + w * 0.06, y0 + h * 0.40), "AMNESTY", font=f, fill=NAVY_DARK)


def scene_dome(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(206, 216, 230))
    cx = (x0 + x1) // 2
    base = y1 - h * 0.10
    d.rectangle([x0 + w * 0.14, base - h * 0.16, x1 - w * 0.14, base],
                fill=(70, 92, 138))
    d.pieslice([cx - w * 0.20, base - h * 0.78, cx + w * 0.20,
                base - h * 0.02], 180, 360, fill=(70, 92, 138))
    d.rectangle([cx - 3, base - h * 0.86, cx + 3, base - h * 0.62],
                fill=(70, 92, 138))
    f = font("sans", "Bold", int(h * 0.26))
    d.text((x0 + w * 0.06, y0 + h * 0.08), "56 - 44", font=f, fill=NAVY)


def scene_towers(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(188, 204, 220))
    base = y1 - h * 0.06
    for bx, bw, bh in ((0.08, 0.16, 0.55), (0.30, 0.14, 0.72),
                       (0.62, 0.15, 0.62), (0.82, 0.13, 0.45)):
        d.rectangle([x0 + w * bx, base - h * bh, x0 + w * (bx + bw), base],
                    fill=(84, 100, 128))
    # the pearl tower: a mast with two spheres
    tx = x0 + w * 0.52
    d.line([tx, base, tx, y0 + h * 0.10], fill=(150, 60, 70), width=5)
    d.ellipse([tx - w * 0.05, y0 + h * 0.30, tx + w * 0.05, y0 + h * 0.52],
              fill=(178, 84, 96))
    d.ellipse([tx - w * 0.035, y0 + h * 0.08, tx + w * 0.035, y0 + h * 0.24],
              fill=(178, 84, 96))


def scene_awacs(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(168, 198, 224))
    cy = y0 + h * 0.52
    d.polygon([(x0 + w * 0.14, cy), (x0 + w * 0.72, cy - h * 0.10),
               (x1 - w * 0.06, cy), (x0 + w * 0.72, cy + h * 0.10)],
              fill=(240, 242, 244))
    d.polygon([(x0 + w * 0.14, cy), (x0 + w * 0.05, cy - h * 0.22),
               (x0 + w * 0.22, cy + h * 0.02)], fill=(200, 60, 50))
    d.polygon([(x0 + w * 0.14, cy), (x0 + w * 0.05, cy + h * 0.22),
               (x0 + w * 0.22, cy - h * 0.02)], fill=(200, 60, 50))
    d.ellipse([x0 + w * 0.40, cy - h * 0.30, x0 + w * 0.62, cy - h * 0.10],
              fill=(90, 100, 116))
    f = font("sans", "Bold", int(h * 0.20))
    d.text((x0 + w * 0.05, y0 + h * 0.05), "AWACS", font=f, fill=NAVY)


def scene_tower_paris(d, b):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    d.rectangle(b, fill=(214, 204, 188))
    cx = x0 + w * 0.24
    base = y1 - h * 0.08
    top = y0 + h * 0.10
    d.polygon([(cx - w * 0.13, base), (cx, top), (cx + w * 0.13, base),
               (cx + w * 0.045, base), (cx, y0 + h * 0.52),
               (cx - w * 0.045, base)], fill=(96, 84, 74))
    d.line([cx - w * 0.085, y0 + h * 0.60, cx + w * 0.085, y0 + h * 0.60],
           fill=(96, 84, 74), width=4)
    f = font("sans", "Bold", int(h * 0.19))
    d.text((x0 + w * 0.46, y0 + h * 0.16), "PHARMA", font=f, fill=NAVY)
    d.text((x0 + w * 0.46, y0 + h * 0.42), "DEAL", font=f, fill=RED)


SCENES = {
    "court": scene_court, "tanker": scene_tanker, "chip": scene_chip,
    "tower": scene_tower, "shop": scene_shop, "skyline": scene_skyline,
    "bars": scene_bars, "scales": scene_scales, "cross": scene_cross,
    "peaks": scene_peaks, "crates": scene_crates, "flag_es": scene_flag_es,
    "dome": scene_dome, "towers": scene_towers, "awacs": scene_awacs,
    "tower_paris": scene_tower_paris,
}


# ---------------------------------------------------------------- map
# Continents as rough polygons in a 100 x 58 space, pins for story spots.

CONTINENTS = [
    [(3, 12), (10, 5), (20, 3), (28, 4), (33, 8), (32, 13), (28, 16),
     (29, 21), (25, 25), (22, 29), (19, 27), (16, 31), (12, 27), (8, 21),
     (4, 16)],                                            # North America
    [(36, 3), (42, 2), (44, 6), (40, 10), (35, 7)],       # Greenland
    [(23, 34), (29, 32), (33, 36), (32, 43), (29, 51), (26, 55),
     (24, 47), (22, 39)],                                 # South America
    [(47, 8), (52, 4), (57, 5), (59, 9), (56, 14), (52, 16), (48, 14),
     (46, 10)],                                           # Europe
    [(44, 6), (46, 5), (46, 9), (44, 10)],                # Britain
    [(49, 19), (56, 17), (61, 20), (61, 27), (58, 35), (55, 41),
     (52, 36), (50, 28), (48, 23)],                       # Africa
    [(58, 5), (72, 2), (90, 3), (96, 8), (93, 14), (87, 16), (84, 13),
     (78, 15), (72, 12), (66, 15), (62, 11), (59, 9)],    # Asia north
    [(67, 16), (72, 16), (71, 23), (69, 28), (67, 21)],   # India
    [(76, 18), (80, 20), (79, 27), (76, 24)],             # South-East Asia
    [(84, 11), (87, 10), (88, 14), (86, 16)],             # Japan / Korea
    [(80, 36), (90, 35), (94, 39), (89, 45), (82, 44), (79, 39)],
    # Australia
]

ISLANDS = [(52, 30, 1.6), (77, 30, 1.4), (81, 31, 1.2), (85, 31, 1.4),
           (89, 32, 1.1), (95, 47, 1.2), (55, 42, 1.3)]

PINS = [
    (1, 29, 19), (3, 7, 21), (5, 24, 31), (9, 19, 21), (11, 28, 18),
    (18, 22, 27), (19, 13, 28), (24, 25, 33), (26, 18, 20), (27, 6, 20),
    (28, 26, 32), (43, 21, 24), (25, 27, 20),
    (2, 66, 18), (4, 63, 20), (6, 57, 17), (7, 59, 8), (12, 48, 14),
    (15, 54, 9), (16, 50, 11), (20, 51, 10), (21, 58, 11), (22, 54, 25),
    (23, 65, 19), (32, 56, 6), (36, 52, 7), (37, 57, 18), (38, 47, 9),
    (41, 53, 13), (42, 50, 27),
    (8, 75, 21), (10, 72, 18), (14, 85, 17), (30, 82, 15), (31, 74, 20),
    (33, 87, 13), (34, 88, 14), (35, 61, 13), (44, 89, 15),
]


def locator_map(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=NAVY_DARK)
    f = font("sans", "Bold", 30)
    d.text((x0 + 22, y0 + 14), "WHERE IT HAPPENED", font=f, fill=GOLD)
    mx0, my0 = x0 + 18, y0 + 62
    mx1, my1 = x1 - 18, y1 - 52
    sx = (mx1 - mx0) / 100.0
    sy = (my1 - my0) / 58.0

    def pt(px, py):
        return (mx0 + px * sx, my0 + py * sy)

    for poly in CONTINENTS:
        d.polygon([pt(px, py) for px, py in poly], fill=LAND)
    for px, py, r in ISLANDS:
        cx, cy = pt(px, py)
        d.ellipse([cx - r * sx, cy - r * sy, cx + r * sx, cy + r * sy],
                  fill=LAND)
    pf = font("sans", "Bold", 17)
    for num, px, py in PINS:
        cx, cy = pt(px, py)
        r = 14
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                  outline=WHITE, width=2)
        label = str(num)
        tw = d.textlength(label, font=pf)
        d.text((cx - tw / 2, cy - 11), label, font=pf, fill=WHITE)
    cf = font("sans", "Regular", 21)
    d.text((x0 + 22, y1 - 38), "25, 29: Washington & New York again.  "
                              "43: US gas", font=cf, fill=WHITE)


# ---------------------------------------------------------------- cards

def badge(d, cx, cy, r, num):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
    f = font("sans", "Bold", int(r * 1.15))
    label = str(num)
    tw = d.textlength(label, font=f)
    asc, desc = f.getmetrics()
    d.text((cx - tw / 2, cy - (asc + desc) / 2 + 2), label, font=f,
           fill=WHITE)


def story_card(d, x, y, w, h, item, scene_h, head_start, dek_start):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=NAVY, width=3)
    SCENES[item["scene"]](d, (x + 5, y + 5, x + w - 5, y + 5 + scene_h))
    num, kick = item["kick"].split("·", 1)
    cy = y + scene_h + 26
    badge(d, x + 30, cy, 21, num.strip())
    kf = font("sans", "Bold", 25)
    d.text((x + 62, cy - 15), kick.strip(), font=kf, fill=RED)
    tx = x + 18
    tw = w - 36
    ty = y + scene_h + 56
    hf, hlines = fit(d, item["head"], "serif", "Bold", head_start, tw, 3)
    ty = block(d, tx, ty, hlines, hf, NAVY, int(head_start * 1.13))
    df, dlines = fit(d, item["dek"], "sans", "Regular", dek_start, tw, 2)
    block(d, tx, ty + 4, dlines, df, INK, int(dek_start * 1.22))


def card_row(d, y, h, items, scene_h, head_start, dek_start, gap=14):
    n = len(items)
    w = (SIDE - 2 * EDGE - gap * (n - 1)) // n
    for i, item in enumerate(items):
        story_card(d, EDGE + i * (w + gap), y, w, h, item, scene_h,
                   head_start, dek_start)


# ---------------------------------------------------------------- page

def masthead(d, y):
    f = font("serif", "Bold", 96)
    y += tracked(d, SIDE // 2, y, "THE WORLD IN ONE PICTURE", f, NAVY, 4)
    y += 6
    d.line([EDGE, y, SIDE - EDGE, y], fill=RED, width=5)
    y += 10
    f2 = font("sans", "Bold", 37)
    y += tracked(d, SIDE // 2, y,
                 "TUESDAY 24 NOVEMBER 2026 · 44 STORIES · ONE PAGE",
                 f2, RED, 7)
    y += 8
    f3 = font("sans", "Bold", 27)
    y += tracked(d, SIDE // 2, y, REGIONS, f3, (150, 44, 38), 2)
    y += 8
    d.line([EDGE, y, SIDE - EDGE, y], fill=NAVY, width=3)
    return y + 12


def stat_strip(d, y, h):
    d.rectangle([EDGE, y, SIDE - EDGE, y + h], fill=NAVY)
    n = len(STATS)
    w = (SIDE - 2 * EDGE) / n
    nf = font("sans", "Bold", 44)
    cf = font("sans", "Regular", 21)
    for i, (num, cap) in enumerate(STATS):
        cx = EDGE + w * (i + 0.5)
        tw = d.textlength(num, font=nf)
        d.text((cx - tw / 2, y + 10), num, font=nf, fill=GOLD)
        lines = wrap_words(d, cap, cf, w - 14)
        ly = y + h - 8 - len(lines) * 24
        for line in lines:
            lw = d.textlength(line, font=cf)
            d.text((cx - lw / 2, ly), line, font=cf, fill=WHITE)
            ly += 24
        if i:
            d.line([EDGE + w * i, y + 10, EDGE + w * i, y + h - 10],
                   fill=(90, 110, 160), width=2)
    return y + h


def briefs(d, x, y, w, h):
    tf = font("serif", "Bold", 30)
    d.text((x, y), "IN BRIEF — 17–44", font=tf, fill=NAVY)
    d.line([x, y + 42, x + w, y + 42], fill=RED, width=3)
    top = y + 56
    col_w = (w - 26) // 2
    bf = font("sans", "Regular", 18)
    for ci, half in enumerate((BRIEFS[:14], BRIEFS[14:])):
        cx = x + ci * (col_w + 26)
        cy = top
        for item in half:
            lines = wrap_words(d, item, bf, col_w)
            cy = block(d, cx, cy, lines, bf, INK, 20)
    return y + h


def date_check(d, y, h):
    d.rectangle([EDGE, y, SIDE - EDGE, y + h], outline=RED, width=3)
    tf = font("sans", "Bold", 24)
    d.text((EDGE + 20, y + 10), "DATE CHECK — LEFT OUT ON PURPOSE",
           font=tf, fill=RED)
    note = ("Every story on this page happened, or was first reported, "
            "on Tuesday 24 November 2026.")
    nf = font("sans", "Bold", 18)
    nw = d.textlength(note, font=nf)
    d.text((SIDE - EDGE - 20 - nw, y + 14), note, font=nf, fill=NAVY)
    f = font("sans", "Regular", 19)
    col_w = (SIDE - 2 * EDGE - 60) // 2
    top = y + 46
    for i, item in enumerate(LEFT_OUT):
        cx = EDGE + 20 + (col_w + 20) * (i // 5)
        cy = top + (i % 5) * 20
        lines = wrap_words(d, "×  " + item, f, col_w)
        block(d, cx, cy, lines[:1], f, INK, 20)
    return y + h


def build():
    img = Image.new("RGB", (SIDE, SIDE), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([12, 12, SIDE - 12, SIDE - 12], outline=NAVY, width=5)
    d.rectangle([22, 22, SIDE - 22, SIDE - 22], outline=NAVY, width=2)

    y = masthead(d, 40)
    y = stat_strip(d, y, 78) + 12
    card_row(d, y, 360, HEROES, 120, 46, 27)
    y += 372
    card_row(d, y, 256, PANELS_A, 54, 37, 25)
    y += 268
    card_row(d, y, 256, PANELS_B, 54, 37, 25)
    y += 268
    card_row(d, y, 212, PANELS_C, 34, 30, 20)
    y += 224
    # bottom block: map on the left, briefs on the right
    map_w = 660
    locator_map(d, (EDGE, y, EDGE + map_w, y + 348))
    briefs(d, EDGE + map_w + 24, y, SIDE - EDGE - (EDGE + map_w + 24), 348)
    y += 360
    date_check(d, y, 156)

    img = img.resize((SIDE // 2, SIDE // 2), Image.LANCZOS)
    img.save("entry.png", optimize=True)


if __name__ == "__main__":
    build()
