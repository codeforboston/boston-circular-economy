#!/usr/bin/env python3
"""Generate the five large Find & swap diagrams as SVG, render 2x PNGs.

Fixed visual mapping (same for every diagram and every mock):
  Card            = Optimistic Blue #1871BD, rounded rectangle
  Button (primary)= Freedom Trail Red #FB4D42, pill shape
  List            = teal #0E7C7B, stacked horizontal rows
  Form            = light blue #6FA8F5, rectangle with input lines
  Decision gate   = amber #FFD98A diamond
  Screen frame    = Charles Blue #091F2F header bar with pale #EDF2F9 body
  State/service   = navy #0B1524 with pale #DCE6F4
Arrows and check marks are vector shapes. No glyphs are typed.
"""
import math
import os
import cairosvg

OUT = os.path.expanduser(
    "~/workspace/goals/boston-circular-economy-client-architecture/"
    "files/journey-guides/visuals/find-swap")
os.makedirs(OUT, exist_ok=True)

# Fleet palette
CHARLES = "#091F2F"
OPT = "#1871BD"
RED = "#FB4D42"
DARKRED = "#D22D23"
AMBER = "#FFD98A"
AMBER_EDGE = "#D9A400"
TEAL = "#0E7C7B"
LIGHTBLUE = "#6FA8F5"
NAVY = "#0B1524"
PALE = "#EDF2F9"
PALEBLUE = "#DCE6F4"
BODY = "#58585B"
WHITE = "#FFFFFF"
BORDER = "#C8C8C8"

MONTS = "Montserrat, Arial, sans-serif"
LORA = "Lora, Georgia, serif"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def text(x, y, s, size=16, fill=CHARLES, family=MONTS, weight="bold",
         anchor="middle", style="", spacing=None):
    sp = (f' letter-spacing="{spacing}"' if spacing else "")
    st = (f' font-style="{style}"' if style else "")
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{sp}{st}>'
            f'{esc(s)}</text>')


def lines(x, y, strs, size=15, fill=WHITE, family=MONTS, weight="bold",
          gap=22, anchor="middle"):
    return "".join(text(x, y + i * gap, s, size, fill, family, weight, anchor)
                   for i, s in enumerate(strs))


def rrect(x, y, w, h, fill, rx=10, stroke=None, sw=0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}"{st}/>')


def card(x, y, w, h, title, sub=None, fill=OPT):
    """Optimistic Blue rounded card with white text."""
    s = rrect(x, y, w, h, fill, rx=12)
    s += text(x + w / 2, y + 34, title, 17, WHITE, MONTS, "bold")
    if sub:
        s += lines(x + w / 2, y + 62, sub, 14, WHITE, LORA, "normal", 20)
    return s


def navy_box(x, y, w, h, title, sub=None):
    s = rrect(x, y, w, h, NAVY, rx=10)
    s += text(x + w / 2, y + 34, title, 17, PALEBLUE, MONTS, "bold")
    if sub:
        s += lines(x + w / 2, y + 62, sub, 14, PALEBLUE, LORA, "normal", 20)
    return s


def screen_frame(x, y, w, h, header, sub=None):
    """Charles Blue header bar with pale body."""
    s = rrect(x, y, w, h, PALE, rx=10)
    s += f'<path d="M {x} {y+34} L {x+w} {y+34} L {x+w} {y+10} Q {x+w} {y} {x+w-10} {y} L {x+10} {y} Q {x} {y} {x} {y+10} Z" fill="{CHARLES}"/>'
    s += text(x + w / 2, y + 23, header, 15, WHITE, MONTS, "bold")
    if sub:
        s += lines(x + w / 2, y + 66, sub, 14, CHARLES, LORA, "normal", 20)
    return s


def diamond(cx, cy, w, h, label_lines, fill=AMBER):
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    s = (f'<polygon points="{pts}" fill="{fill}" stroke="{AMBER_EDGE}" '
         f'stroke-width="3"/>')
    n = len(label_lines)
    y0 = cy - (n - 1) * 11
    for i, ln in enumerate(label_lines):
        s += text(cx, y0 + i * 22, ln, 15, CHARLES, MONTS, "bold")
    return s


def arrow(x1, y1, x2, y2, color=CHARLES, w=3):
    """Straight arrow as a vector line plus a filled triangle head."""
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    tip_x, tip_y = x2, y2
    base_x, base_y = x2 - ux * 14, y2 - uy * 14
    px, py = -uy, ux
    pts = (f"{tip_x},{tip_y} {base_x + px * 7},{base_y + py * 7} "
           f"{base_x - px * 7},{base_y - py * 7}")
    s = (f'<line x1="{x1}" y1="{y1}" x2="{base_x}" y2="{base_y}" '
         f'stroke="{color}" stroke-width="{w}"/>')
    s += f'<polygon points="{pts}" fill="{color}"/>'
    return s


def elbow(points, color=CHARLES, w=3):
    """Polyline with an arrowhead on the last segment."""
    pts = " ".join(f"{x},{y}" for x, y in points)
    s = (f'<polyline points="{pts}" fill="none" stroke="{color}" '
         f'stroke-width="{w}"/>')
    (x1, y1), (x2, y2) = points[-2], points[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    bx, by = x2 - ux * 14, y2 - uy * 14
    px, py = -uy, ux
    tri = (f"{x2},{y2} {bx + px * 7},{by + py * 7} "
           f"{bx - px * 7},{by - py * 7}")
    s += f'<polygon points="{tri}" fill="{color}"/>'
    return s


def title_block(svg, eyebrow, title, subtitle, W=1600):
    svg.append(text(W / 2, 46, eyebrow, 15, OPT, MONTS, "bold",
                    spacing="3"))
    svg.append(text(W / 2, 88, title, 34, CHARLES, MONTS, "bold"))
    svg.append(text(W / 2, 122, subtitle, 19, BODY, LORA, "normal",
                    style="italic"))
    svg.append(f'<line x1="60" y1="142" x2="{W-60}" y2="142" '
               f'stroke="{BORDER}" stroke-width="1"/>')


def legend(svg, y, W=1600):
    """Fixed mapping legend, two rows, centred."""
    items = [
        ("card", "Card", OPT, "rect"),
        ("button", "Button", RED, "pill"),
        ("list", "List", TEAL, "rows"),
        ("form", "Form", LIGHTBLUE, "form"),
        ("gate", "Decision gate", AMBER, "diamond"),
        ("screen", "Screen frame", CHARLES, "screen"),
        ("state", "State / service", NAVY, "navy"),
    ]
    svg.append(text(W / 2, y, "HOW TO READ THIS PICTURE", 14, CHARLES,
                    MONTS, "bold", spacing="2"))
    # lay out in one row of 7, centred
    widths = [150, 170, 150, 150, 210, 210, 220]
    total = sum(widths)
    x = (W - total) / 2
    yy = y + 34
    for (label, _, color, kind), w in zip(
            [(i[0], i[1], i[2], i[3]) for i in items], widths):
        cx = x + 24
        if kind == "rect":
            svg.append(rrect(cx, yy - 14, 34, 22, color, rx=6))
        elif kind == "pill":
            svg.append(rrect(cx, yy - 14, 34, 22, color, rx=11))
        elif kind == "rows":
            for i in range(3):
                svg.append(rrect(cx, yy - 14 + i * 8, 34, 5, color, rx=2))
        elif kind == "form":
            svg.append(rrect(cx, yy - 14, 34, 22, color, rx=3))
            svg.append(f'<line x1="{cx+6}" y1="{yy-6}" x2="{cx+28}" '
                       f'y2="{yy-6}" stroke="{WHITE}" stroke-width="2"/>')
            svg.append(f'<line x1="{cx+6}" y1="{yy+1}" x2="{cx+22}" '
                       f'y2="{yy+1}" stroke="{WHITE}" stroke-width="2"/>')
        elif kind == "diamond":
            svg.append(f'<polygon points="{cx+17},{yy-18} {cx+36},{yy-3} '
                       f'{cx+17},{yy+16} {cx-2},{yy-3}" fill="{color}" '
                       f'stroke="{AMBER_EDGE}" stroke-width="2"/>')
        elif kind == "screen":
            svg.append(rrect(cx, yy - 14, 34, 22, PALE, rx=3,
                             stroke=CHARLES, sw=1))
            svg.append(rrect(cx, yy - 14, 34, 8, CHARLES, rx=3))
        elif kind == "navy":
            svg.append(rrect(cx, yy - 14, 34, 22, NAVY, rx=3))
            svg.append(f'<line x1="{cx+6}" y1="{yy-6}" x2="{cx+28}" '
                       f'y2="{yy-6}" stroke="{PALEBLUE}" stroke-width="2"/>')
            svg.append(f'<line x1="{cx+6}" y1="{yy+1}" x2="{cx+22}" '
                       f'y2="{yy+1}" stroke="{PALEBLUE}" stroke-width="2"/>')
        svg.append(text(cx + 42, yy + 3, label, 14, CHARLES, MONTS, "bold",
                        anchor="start"))
        x += w


def render(name, W, H, body):
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
           f'height="{H}" viewBox="0 0 {W} {H}">']
    svg.append(f'<rect width="{W}" height="{H}" fill="{WHITE}"/>')
    svg.extend(body)
    svg.append("</svg>")
    path = os.path.join(OUT, name + ".svg")
    with open(path, "w") as f:
        f.write("\n".join(svg))
    cairosvg.svg2png(url=path, write_to=os.path.join(OUT, name + ".png"),
                     output_width=W * 2)
    print("wrote", name)


# ---------------------------------------------------------------- journey map
def journey_map():
    W, H = 1600, 1000
    b = []
    title_block(b, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
                "Marisol: find and swap",
                "From a clear-out to a match: search, board, results.")
    y = 250
    bw, bh = 168, 150
    xs = [60, 262, 464, 666, 868, 1070]
    # first three stages: cards
    b.append(card(xs[0], y, bw, bh, "1  CLEAR-OUT",
                  ["She clears", "out her home."]))
    b.append(card(xs[1], y, bw, bh, "2  DISCOVER",
                  ["Local orgs", "and friends."]))
    b.append(card(xs[2], y, bw, bh, "3  DECIDE",
                  ["Buys used,", "donates, pays", "for repair."]))
    # three build screens: screen frames
    b.append(screen_frame(xs[3], y, bw, bh, "/FIND",
                          ["Search,", "filters,", "Spanish."]))
    b.append(screen_frame(xs[4], y, bw, bh, "BOARD",
                          ["Wanted and", "offered", "side by side."]))
    b.append(screen_frame(xs[5], y, bw, bh, "RESULTS",
                          ["Cost, distance,", "instructions", "on each row."]))
    for i in range(5):
        b.append(arrow(xs[i] + bw + 4, y + bh / 2, xs[i + 1] - 6,
                       y + bh / 2))
    # decision gate
    dcx, dcy = 1355, y + bh / 2
    b.append(arrow(xs[5] + bw + 4, y + bh / 2, dcx - 95, dcy))
    b.append(diamond(dcx, dcy, 180, 150, ["MATCH", "FOUND?"]))
    # Yes branch: down to read-the-listing box
    b.append(text(dcx + 8, dcy + 108, "YES", 15, TEAL, MONTS, "bold",
                  anchor="start"))
    b.append(arrow(dcx, dcy + 78, dcx, 520))
    b.append(card(dcx - 130, 520, 260, 110, "READ THE LISTING",
                  ["Cost, distance, and", "clear instructions."], fill=TEAL))
    # No branch: down the far right edge, then back left to /FIND.
    # The line stays right of the READ THE LISTING box, so it never
    # crosses the box or its text.
    b.append(text(1482, 312, "NO", 15, DARKRED, MONTS, "bold"))
    b.append(elbow([(dcx + 90, dcy), (1520, dcy), (1520, 700),
                    (750, 700), (750, y + bh + 8)], color=DARKRED))
    b.append(text(1010, 690, "NO: WIDEN THE SEARCH, TRY ANOTHER WORD",
                  15, DARKRED, MONTS, "bold"))
    # barriers strip
    b.append(rrect(60, 760, 1480, 64, PALE, rx=10))
    b.append(text(800, 788, "Barriers at completion: cost, distance, "
                  "unclear instructions.", 17, CHARLES, MONTS, "bold"))
    b.append(text(800, 812, "Every listing shows all three in words.",
                  15, BODY, LORA, "normal", style="italic"))
    legend(b, 880, W)
    render("journey-map", W, H, b)


# ------------------------------------------------------------------ build map
def build_map():
    W, H = 1600, 1000
    b = []
    title_block(b, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
                "Find and swap: build map",
                "Shared parts first, then one screen at a time, each ending in a check.")
    cols = [
        ("STAGE 0 — SHARED PARTS",
         [("Shell", ["skip link, main,", "live region"], True),
          ("Search query", ["searchQueryOptions", "one API call"], True),
          ("Query client", ["caches the answer", "ten minutes"], True),
          ("Four states", ["loading, error,", "empty, success"], True)]),
        ("SCREEN 1 — SEARCH",
         [("Search input", ["W-06, type", "and match"], False),
          ("Filter bar", ["W-07, category,", "nearby, pickup"], False),
          ("Language switcher", ["W-17, English", "and Spanish"], False),
          ("State wiring", ["URL, query", "client, page"], False)]),
        ("SCREEN 2 — BOARD",
         [("Listing card", ["cost, distance,", "instructions"], False),
          ("Board", ["W-18, Wanted", "and Offered"], False),
          ("Board filter", ["one side, both,", "or one category"], False),
          ("Empty states", ["empty columns", "in words"], False)]),
        ("SCREEN 3 — RESULTS",
         [("Results list", ["W-05, first ten", "in order"], False),
          ("Count text", ["count and", "first-ten cut"], False),
          ("Pagination", ["W-16, pages", "in the URL"], False),
          ("Phone dialog", ["W-15, FILTER", "on a phone"], False)]),
    ]
    col_w, gap = 330, 60
    x0 = 60
    box_h, box_gap = 92, 14
    top = 210
    diamonds = []
    for ci, (head, boxes) in enumerate(cols):
        x = x0 + ci * (col_w + gap)
        b.append(text(x + col_w / 2, 178, head, 16, CHARLES, MONTS, "bold"))
        yy = top
        for title, sub, navy in boxes:
            if navy:
                b.append(navy_box(x, yy, col_w, box_h, title, sub))
            else:
                b.append(card(x, yy, col_w, box_h, title, sub))
            yy += box_h + box_gap
        dcx = x + col_w / 2
        dcy = yy + 62
        diamonds.append((dcx, dcy))
        b.append(diamond(dcx, dcy, 170, 118, ["CHECK", "PASSES?"]))
        b.append(arrow(x + col_w / 2, yy - 6, dcx, dcy - 62))
    for i in range(3):
        x1, y1 = diamonds[i]
        x2, y2 = diamonds[i + 1]
        b.append(arrow(x1 + 88, y1, x2 - 88, y2))
    legend(b, 880, W)
    render("build-map", W, H, b)


# ------------------------------------------------------------- wiring: search
def wiring_search():
    W, H = 1600, 900
    b = []
    title_block(b, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
                "Wiring: the search screen",
                "Search input, filter bar, and language switcher feed the page state.")
    y = 250
    # Marisol
    b.append(card(40, y, 150, 130, "MARISOL", ["types,", "picks,", "reads."]))
    # components column: three form boxes, 44 tall
    b.append(text(330, y - 18, "COMPONENTS", 15, CHARLES, MONTS, "bold"))
    b.append(rrect(220, y, 220, 44, LIGHTBLUE, rx=6))
    b.append(text(330, y + 28, "Search input  .sf", 15, CHARLES, MONTS,
                  "bold"))
    b.append(rrect(220, y + 60, 220, 44, LIGHTBLUE, rx=6))
    b.append(text(330, y + 88, "Filter bar  .fl", 15, CHARLES, MONTS,
                  "bold"))
    b.append(rrect(220, y + 120, 220, 44, LIGHTBLUE, rx=6))
    b.append(text(330, y + 148, "Language  .tr", 15, CHARLES, MONTS,
                  "bold"))
    b.append(arrow(190, y + 65, 214, y + 22))
    b.append(arrow(190, y + 65, 214, y + 82))
    b.append(arrow(190, y + 65, 214, y + 142))
    # page state column: three navy boxes, 92 tall, room for title + sub
    b.append(text(600, y - 18, "PAGE STATE", 15, CHARLES, MONTS, "bold"))
    b.append(navy_box(480, y, 240, 92, "URL params",
                       ["category, page"]))
    b.append(navy_box(480, y + 108, 240, 92, "Board filter",
                       ["wanted / offered / all"]))
    b.append(navy_box(480, y + 216, 240, 92, "Language",
                       ["provider, at entry"]))
    for yy in (y + 46, y + 154, y + 262):
        b.append(arrow(440, y + 82, 474, yy))
    # diamond
    dcx, dcy = 830, y + 106
    b.append(arrow(720, y + 154, dcx - 92, dcy))
    b.append(diamond(dcx, dcy, 170, 150, ["PARAMS", "VALID?"]))
    # No branch
    b.append(text(dcx - 28, dcy + 124, "NO", 15, DARKRED, MONTS, "bold",
                  anchor="start"))
    b.append(arrow(dcx - 40, dcy + 78, dcx - 40, 560))
    b.append(card(dcx - 175, 560, 270, 96, "PLAIN-WORD ALERT",
                  ["No fetch runs.", "The page says why."], fill=DARKRED))
    # services column: three navy boxes, 92 tall
    b.append(text(1100, y - 18, "SERVICES", 15, CHARLES, MONTS, "bold"))
    b.append(navy_box(980, y, 240, 92, "searchQueryOptions",
                       ["the one API call"]))
    b.append(navy_box(980, y + 108, 240, 92, "Query client",
                       ["caches the answer"]))
    b.append(navy_box(980, y + 216, 240, 92, "Route loader",
                       ["warms the cache"]))
    for yy in (y + 46, y + 154, y + 262):
        b.append(arrow(dcx + 92, dcy, 974, yy))
    # API
    b.append(navy_box(1280, y + 60, 260, 96, "API",
                       ["GET /api/v1/search"]))
    b.append(arrow(1220, y + 154, 1274, y + 106))
    b.append(text(1410, y + 186, "Every location", 14, BODY, LORA,
                  "normal", style="italic"))
    # bottom strip
    b.append(rrect(60, 700, 1480, 56, PALE, rx=10))
    b.append(text(800, 734, "The route shows loading and error. "
                  "The page writes only the success view.",
                  16, CHARLES, MONTS, "bold"))
    legend(b, 800, W)
    render("wiring-search", W, H, b)


# -------------------------------------------------------------- wiring: board
def wiring_board():
    W, H = 1600, 980
    b = []
    title_block(b, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
                "Wiring: the wanted and offered board",
                "One fetch, one split, two columns, cards that show cost, distance, instructions.")
    # left: query client
    b.append(navy_box(40, 380, 200, 120, "QUERY CLIENT",
                       ["listings", "from the API"]))
    # board
    b.append(card(300, 380, 210, 120, "BOARD  .wo",
                  ["WantedOffered", "Board"]))
    b.append(arrow(240, 440, 294, 440))
    # columns
    b.append(text(680, 240, "WANTED COLUMN  .wo-col", 15, CHARLES, MONTS,
                  "bold"))
    b.append(rrect(560, 260, 240, 150, TEAL, rx=10))
    b.append(rrect(576, 280, 208, 52, OPT, rx=8))
    b.append(text(680, 300, "Listing card", 15, WHITE, MONTS, "bold"))
    b.append(text(680, 322, "cost · distance", 13, WHITE, LORA, "normal"))
    b.append(rrect(576, 344, 208, 52, OPT, rx=8))
    b.append(text(680, 364, "Listing card", 15, WHITE, MONTS, "bold"))
    b.append(text(680, 386, "cost · distance", 13, WHITE, LORA, "normal"))
    b.append(text(680, 600, "OFFERED COLUMN  .wo-col", 15, CHARLES, MONTS,
                  "bold"))
    b.append(rrect(560, 620, 240, 150, TEAL, rx=10))
    b.append(rrect(576, 640, 208, 52, OPT, rx=8))
    b.append(text(680, 660, "Listing card", 15, WHITE, MONTS, "bold"))
    b.append(text(680, 682, "cost · distance", 13, WHITE, LORA, "normal"))
    b.append(rrect(576, 704, 208, 52, OPT, rx=8))
    b.append(text(680, 724, "Listing card", 15, WHITE, MONTS, "bold"))
    b.append(text(680, 746, "cost · distance", 13, WHITE, LORA, "normal"))
    b.append(elbow([(510, 420), (530, 420), (530, 335), (554, 335)]))
    b.append(elbow([(510, 460), (530, 460), (530, 695), (554, 695)]))
    # board filter state above board
    b.append(navy_box(300, 200, 210, 96, "BOARD FILTER",
                       ["wanted / offered / all"]))
    b.append(arrow(405, 296, 405, 374))
    # diamond: column empty?
    dcx, dcy = 1000, 515
    b.append(elbow([(800, 335), (900, 335), (900, 470), (955, 470)]))
    b.append(elbow([(800, 695), (900, 695), (900, 560), (955, 560)]))
    b.append(diamond(dcx, dcy, 190, 160, ["COLUMN", "EMPTY?"]))
    b.append(text(dcx + 8, dcy - 125, "EACH COLUMN", 13, BODY, MONTS,
                  "bold"))
    b.append(text(dcx + 8, dcy - 103, "CHECKS ITS OWN LIST", 13, BODY,
                  MONTS, "bold"))
    # No branch: cards show
    b.append(text(dcx + 105, dcy - 8, "NO", 15, TEAL, MONTS, "bold",
                  anchor="start"))
    b.append(arrow(dcx + 98, dcy, 1220, dcy))
    b.append(card(1226, 440, 320, 150, "CARDS SHOW",
                  ["Cost, distance, and", "clear instructions", "in words."],
                  fill=TEAL))
    # Yes branch: empty words
    b.append(text(dcx + 12, dcy + 110, "YES", 15, DARKRED, MONTS, "bold",
                  anchor="start"))
    b.append(arrow(dcx - 20, dcy + 82, dcx - 20, 700))
    b.append(card(dcx - 160, 700, 320, 96, "EMPTY WORDS",
                  ["“No wanted items yet.”", "Never a blank column."]))
    legend(b, 860, W)
    render("wiring-board", W, H, b)


# ------------------------------------------------------------ wiring: results
def wiring_results():
    W, H = 1600, 900
    b = []
    title_block(b, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
                "Wiring: results with pagination",
                "The query client feeds the list, the count, and the pages.")
    y = 250
    b.append(navy_box(40, y, 210, 120, "QUERY CLIENT",
                       ["listings,", "cached under", "one key: search"]))
    b.append(card(290, y, 210, 120, "FOUR STATES",
                  ["loading, error,", "empty, success"]))
    b.append(arrow(250, y + 60, 284, y + 60))
    # list as teal rows
    b.append(text(620, y - 18, "RESULTS LIST  .sr-list", 15, CHARLES,
                  MONTS, "bold"))
    b.append(rrect(540, y, 190, 120, TEAL, rx=10))
    for i in range(3):
        b.append(rrect(556, y + 16 + i * 36, 158, 26, WHITE, rx=5))
        b.append(text(635, y + 34 + i * 36, f"Result {i+1}", 13, TEAL,
                      MONTS, "bold"))
    b.append(arrow(500, y + 60, 534, y + 60))
    # count
    b.append(card(770, y, 190, 120, "COUNT  .sr-count",
                  ["“Displaying 1 – 10", "of 22 results.”"]))
    b.append(arrow(730, y + 60, 764, y + 60))
    # pagination
    b.append(rrect(1000, y, 210, 120, RED, rx=60))
    b.append(text(1105, y + 52, "PAGINATION", 17, WHITE, MONTS, "bold"))
    b.append(text(1105, y + 80, "First · 1 · 2 · Next", 14, WHITE, LORA,
                  "normal"))
    b.append(text(1105, y + 104, "?page= in the URL", 13, WHITE, LORA,
                  "normal", style="italic"))
    b.append(arrow(960, y + 60, 994, y + 60))
    # diamond
    dcx, dcy = 1345, y + 60
    b.append(arrow(1210, y + 60, dcx - 88, dcy))
    b.append(diamond(dcx, dcy, 170, 150, ["MORE", "PAGES?"]))
    # No branch: end of results
    b.append(text(dcx + 8, dcy + 100, "NO", 15, TEAL, MONTS, "bold",
                  anchor="start"))
    b.append(arrow(dcx, dcy + 78, dcx, 500))
    b.append(card(dcx - 120, 500, 240, 96, "END OF RESULTS",
                  ["The last page.", "No blank page."], fill=TEAL))
    # Yes branch: next page, return arrow to list. The line runs up from
    # the diamond top vertex, right of the END box, then back left to
    # the list, so it never crosses the END box or its text.
    b.append(text(1420, 188, "YES", 15, DARKRED, MONTS, "bold"))
    b.append(elbow([(dcx, dcy - 75), (dcx, 200), (1500, 200),
                    (1500, 640), (635, 640), (635, y + 126)],
                   color=DARKRED))
    b.append(text(1000, 630, "NEXT PAGE: ?page=2 SHOWS ITEMS 11 TO 20",
                  15, DARKRED, MONTS, "bold"))
    # bottom strip
    b.append(rrect(60, 700, 1480, 56, PALE, rx=10))
    b.append(text(800, 734, "The count sits in a live region. "
                  "The screen reader announces each page change.",
                  16, CHARLES, MONTS, "bold"))
    legend(b, 800, W)
    render("wiring-results", W, H, b)


if __name__ == "__main__":
    journey_map()
    build_map()
    wiring_search()
    wiring_board()
    wiring_results()
