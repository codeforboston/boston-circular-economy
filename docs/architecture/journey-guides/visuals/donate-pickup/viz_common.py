"""Shared drawing helpers for the Donate and pickup guide pictures.

Fixed visual language, used in every picture:
  Card            Optimistic Blue #1871BD, rounded rectangle
  Primary button  Freedom Trail Red #FB4D42, pill shape
  List            teal #0E7C7B, stacked horizontal rows
  Form            light-blue #6FA8F5, rectangle with input lines
  Decision gate   amber #FFD98A diamond
  Screen frame    Charles Blue #091F2F header bar, pale #EDF2F9 body
  State/service   navy #0B1524, pale #DCE6F4 text
Symbols are drawn as vector shapes. No typed glyphs are used.
"""

import textwrap

CHARLES = "#091F2F"
OPT = "#1871BD"
RED = "#FB4D42"
DARKRED = "#D22D23"
YELLOW = "#FCB61A"
GOLD = "#FFD98A"
TEAL = "#0E7C7B"
LIGHTBLUE = "#6FA8F5"
NAVY = "#0B1524"
PALE = "#EDF2F9"
PALEBLUE = "#DCE6F4"
BODY = "#58585B"
WHITE = "#FFFFFF"
BG = "#F3F3F3"
BORDER = "#C8C8C8"
MIDGREY = "#828282"

SANS = "Montserrat, Arial, sans-serif"
SERIF = "Lora, Georgia, serif"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def svg_open(w, h):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h)]


def svg_close():
    return ['</svg>']


def rect(p, x, y, w, h, fill, stroke=None, sw=0, rx=0):
    s = ' stroke="%s" stroke-width="%d"' % (stroke, sw) if stroke else ""
    p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" rx="%.0f" fill="%s"%s />'
             % (x, y, w, h, rx, fill, s))


def text(p, x, y, s, size, fill, family=SANS, weight="normal", anchor="start", spacing=None):
    ls = ' letter-spacing="%s"' % spacing if spacing else ""
    p.append('<text x="%.0f" y="%.0f" font-family="%s" font-size="%d" font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
             % (x, y, family, size, weight, fill, anchor, ls, esc(s)))


def para(p, x, y, s, size, fill, max_chars, family=SERIF, weight="normal", lh=None, anchor="start"):
    """Draw wrapped text. Returns the y of the last line."""
    lh = lh or int(size * 1.35)
    lines = textwrap.wrap(s, width=max_chars)
    for i, ln in enumerate(lines):
        text(p, x, y + i * lh, ln, size, fill, family, weight, anchor)
    return y + (len(lines) - 1) * lh


def arrow(p, x1, y1, x2, y2, color=CHARLES, sw=3):
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="%s" stroke-width="%d" />'
             % (x1, y1, x2, y2, color, sw))
    if x2 > x1:  # right-pointing head
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />'
                 % (x2, y2, x2 - 14, y2 - 7, x2 - 14, y2 + 7, color))
    elif y2 > y1:  # down-pointing head
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />'
                 % (x2, y2, x2 - 7, y2 - 14, x2 + 7, y2 - 14, color))
    elif y2 < y1:  # up-pointing head
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />'
                 % (x2, y2, x2 - 7, y2 + 14, x2 + 7, y2 + 14, color))
    else:  # left-pointing head
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />'
                 % (x2, y2, x2 + 14, y2 - 7, x2 + 14, y2 + 7, color))


def title_block(p, w, eyebrow, title, subtitle):
    text(p, 60, 46, eyebrow, 15, OPT, SANS, "bold", spacing="2")
    text(p, 60, 88, title, 33, CHARLES, SANS, "bold")
    para(p, 60, 122, subtitle, 19, BODY, 105, SERIF)
    p.append('<line x1="60" y1="140" x2="%d" y2="140" stroke="%s" stroke-width="2" />' % (w - 60, BORDER))


def _legend_swatch(p, kind, x, y):
    if kind == "card":
        rect(p, x, y, 40, 24, OPT, rx=6)
    elif kind == "button":
        rect(p, x, y, 40, 24, RED, rx=12)
    elif kind == "list":
        for i in range(3):
            rect(p, x, y + i * 8, 40, 5, TEAL, rx=2)
    elif kind == "form":
        rect(p, x, y, 40, 24, LIGHTBLUE, rx=2)
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2" />' % (x + 6, y + 8, x + 34, y + 8, WHITE))
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2" />' % (x + 6, y + 16, x + 28, y + 16, WHITE))
    elif kind == "decision":
        p.append('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1" />'
                 % (x + 20, y, x + 40, y + 12, x + 20, y + 24, x, y + 12, GOLD, CHARLES))
    elif kind == "frame":
        rect(p, x, y, 40, 24, PALE, stroke=CHARLES, sw=1)
        rect(p, x, y, 40, 8, CHARLES)
    elif kind == "state":
        rect(p, x, y, 40, 24, NAVY, rx=2)
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2" />' % (x + 6, y + 8, x + 34, y + 8, PALEBLUE))
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2" />' % (x + 6, y + 16, x + 28, y + 16, PALEBLUE))


LEGEND_ITEMS = [
    ("card", "Card"),
    ("button", "Primary button"),
    ("list", "List"),
    ("form", "Form"),
    ("decision", "Decision gate"),
    ("frame", "Screen frame"),
    ("state", "State / service"),
]


def legend(p, w, y, h=104):
    rect(p, 40, y, w - 80, h, WHITE, stroke=BORDER, sw=1)
    text(p, 60, y + 28, "LEGEND  —  THE SAME SHAPES IN EVERY PICTURE", 14, CHARLES, SANS, "bold", spacing="1")
    cols = 4
    cell_w = (w - 80 - 40) / cols
    for i, (kind, label) in enumerate(LEGEND_ITEMS):
        cx = 60 + (i % cols) * cell_w
        cy = y + 44 + (i // cols) * 34
        _legend_swatch(p, kind, cx, cy)
        text(p, cx + 50, cy + 18, label, 15, BODY, SANS)


def card(p, x, y, w, h, title, lines, title_size=19, body_size=16, body_chars=26):
    rect(p, x, y, w, h, OPT, rx=10)
    text(p, x + 18, y + 34, title, title_size, WHITE, SANS, "bold")
    yy = y + 62
    for ln in lines:
        yy = para(p, x + 18, yy, ln, body_size, WHITE, body_chars, SERIF) + 24
    return yy


def button_shape(p, x, y, w, h, label, size=17):
    rect(p, x, y, w, h, RED, rx=h / 2)
    text(p, x + w / 2, y + h / 2 + size / 2 - 1, label, size, WHITE, SANS, "bold", "middle")


def list_rows(p, x, y, w, rows, row_h=44, size=16):
    for i, r in enumerate(rows):
        rect(p, x, y + i * (row_h + 8), w, row_h, TEAL, rx=6)
        text(p, x + 16, y + i * (row_h + 8) + row_h / 2 + size / 2 - 1, r, size, WHITE, SANS, "bold")


def form_box(p, x, y, w, h, title, fields):
    rect(p, x, y, w, h, LIGHTBLUE, rx=4)
    text(p, x + 16, y + 30, title, 17, CHARLES, SANS, "bold")
    yy = y + 52
    for label in fields:
        text(p, x + 16, yy, label, 14, CHARLES, SANS, "bold")
        rect(p, x + 16, yy + 6, w - 32, 26, WHITE, rx=2)
        yy += 52
    return yy


def diamond(p, cx, cy, rx, ry, lines, size=17, fill=GOLD):
    p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" stroke="%s" stroke-width="2" />'
             % (cx, cy - ry, cx + rx, cy, cx, cy + ry, cx - rx, cy, fill, CHARLES))
    n = len(lines)
    for i, ln in enumerate(lines):
        text(p, cx, cy - (n - 1) * (size + 4) / 2 + i * (size + 4) + size / 2 - 2, ln, size, CHARLES, SANS, "bold", "middle")


def frame_box(p, x, y, w, h, header, body_lines, body_size=15, body_chars=30):
    rect(p, x, y, w, h, PALE, stroke=CHARLES, sw=2)
    rect(p, x, y, w, 44, CHARLES)
    text(p, x + 16, y + 29, header, 16, WHITE, SANS, "bold")
    yy = y + 72
    for ln in body_lines:
        yy = para(p, x + 16, yy, ln, body_size, BODY, body_chars, SERIF) + 22
    return yy


def state_box(p, x, y, w, h, title, lines, title_size=18, body_size=15, body_chars=30):
    rect(p, x, y, w, h, NAVY, rx=4)
    text(p, x + 18, y + 34, title, title_size, PALEBLUE, SANS, "bold")
    yy = y + 62
    for ln in lines:
        yy = para(p, x + 18, yy, ln, body_size, PALEBLUE, body_chars, SERIF) + 22
    return yy


def step_dot(p, cx, cy, n):
    p.append('<circle cx="%.0f" cy="%.0f" r="16" fill="%s" stroke="%s" stroke-width="2" />' % (cx, cy, WHITE, CHARLES))
    text(p, cx, cy + 6, str(n), 17, CHARLES, SANS, "bold", "middle")


def render_svg(parts, path, w, h, scale=2):
    import cairosvg
    svg = "\n".join(parts)
    with open(path.replace(".png", ".svg"), "w") as f:
        f.write(svg)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=path,
                     output_width=int(w * scale), output_height=int(h * scale))
