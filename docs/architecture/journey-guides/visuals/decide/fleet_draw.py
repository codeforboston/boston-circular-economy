"""Shared drawing helpers for the Decide journey diagrams.

Fixed visual mapping, used in every diagram in this set:
  Card             = Optimistic Blue #1871BD, rounded rectangle
  Button           = Freedom Trail Red #FB4D42, pill shape
  List             = teal #0E7C7B, stacked horizontal rows
  Form             = light-blue #6FA8F5, rectangle with input lines
  Decision gate    = amber #FFD98A diamond
  Screen frame     = Charles Blue #091F2F header bar, pale #EDF2F9 body
  State/services   = navy #0B1524 with pale #DCE6F4

Symbols are drawn as vector shapes. No typed check or arrow glyphs.
"""

import cairosvg

CHARLES = "#091F2F"
OPTIMISTIC = "#1871BD"
FREEDOM = "#FB4D42"
DARK_RED = "#D22D23"
YELLOW = "#FCB61A"
BODY_GRAY = "#58585B"
MID_GRAY = "#828282"
BORDER_GRAY = "#C8C8C8"
DIVIDER_GRAY = "#E0E0E0"
BG_GRAY = "#F3F3F3"
WHITE = "#FFFFFF"
TEAL = "#0E7C7B"
LIGHT_BLUE = "#6FA8F5"
AMBER = "#FFD98A"
NAVY = "#0B1524"
PALE = "#DCE6F4"
PALE_BODY = "#EDF2F9"

SANS = "Noto Sans, Arial, sans-serif"


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def text(x, y, s, size, fill=CHARLES, weight="normal", anchor="start",
         family=SANS, spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{sp}>'
            f'{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke=None, sw=0, rx=0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}"{st}/>')


def line(x1, y1, x2, y2, stroke=CHARLES, sw=3):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')


def arrow(x1, y1, x2, y2, stroke=CHARLES, sw=3):
    """A straight arrow drawn as a line plus a polygon head."""
    import math
    parts = [line(x1, y1, x2, y2, stroke, sw)]
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 16
    a1 = ang + 2.6
    a2 = ang - 2.6
    px1 = x2 + L * math.cos(a1)
    py1 = y2 + L * math.sin(a1)
    px2 = x2 + L * math.cos(a2)
    py2 = y2 + L * math.sin(a2)
    parts.append(
        f'<polygon points="{x2},{y2} {px1:.1f},{py1:.1f} {px2:.1f},{py2:.1f}" '
        f'fill="{stroke}"/>')
    return "".join(parts)


def title_block(w, eyebrow, title, subtitle):
    """Org eyebrow, plain title, one-line subtitle, with a rule."""
    p = []
    p.append(rect(0, 0, w, 8, OPTIMISTIC))
    p.append(text(48, 52, eyebrow, 20, OPTIMISTIC, "bold", spacing="2"))
    p.append(text(48, 100, title, 40, CHARLES, "bold"))
    p.append(text(48, 138, subtitle, 22, BODY_GRAY))
    p.append(line(48, 158, w - 48, 158, DIVIDER_GRAY, 2))
    return "".join(p)


def legend_items():
    """(kind, label) pairs for the fixed mapping, in legend order."""
    return [
        ("card", "Card"),
        ("button", "Button"),
        ("list", "List"),
        ("form", "Form"),
        ("gate", "Decision gate"),
        ("frame", "Screen frame"),
        ("state", "State and services"),
    ]


def swatch(kind, x, y, s=1.0):
    """One legend swatch shape, drawn at (x, y), scaled by s."""
    w = int(34 * s)
    h = int(20 * s)
    if kind == "card":
        return rect(x, y, w, h, OPTIMISTIC, rx=int(5 * s))
    if kind == "button":
        return rect(x, y, w, h, FREEDOM, rx=int(10 * s))
    if kind == "list":
        rows = "".join(
            rect(x, y + int(i * 7 * s), w, int(4 * s), TEAL)
            for i in range(3))
        return rows
    if kind == "form":
        return (rect(x, y, w, h, LIGHT_BLUE)
                + rect(x + 4, y + 7, w - 8, 3, WHITE)
                + rect(x + 4, y + 13, int((w - 8) * 0.6), 3, WHITE))
    if kind == "gate":
        cx, cy = x + w // 2, y + h // 2
        rx, ry = w // 2, h // 2 + 4
        return (f'<polygon points="{cx},{cy - ry} {cx + rx},{cy} '
                f'{cx},{cy + ry} {cx - rx},{cy}" fill="{AMBER}" '
                f'stroke="{CHARLES}" stroke-width="1.5"/>')
    if kind == "frame":
        return (rect(x, y, w, h, PALE_BODY, stroke=CHARLES, sw=1.5)
                + rect(x, y, w, int(7 * s), CHARLES))
    if kind == "state":
        return rect(x, y, w, h, PALE, stroke=NAVY, sw=2)
    return ""


def legend_row(x, y, width, size=18, gap=None):
    """One-row legend across the given width."""
    items = legend_items()
    n = len(items)
    cell = width / n
    p = []
    for i, (kind, label) in enumerate(items):
        cx = x + i * cell
        p.append(swatch(kind, int(cx), int(y), s=size / 18.0))
        p.append(text(int(cx + 42 * (size / 18.0)), int(y + size - 2),
                      label, size, BODY_GRAY))
    return "".join(p)


def legend_block(x, y, width, size=13):
    """Two-column legend for the small phone-width mocks.

    Four rows, two items per row. Fits long labels such as
    "State and services" at phone width.
    """
    items = legend_items()
    rows = [items[i:i + 2] for i in range(0, len(items), 2)]
    p = []
    cell = width / 2
    for r, row in enumerate(rows):
        yy = y + r * 30
        for i, (kind, label) in enumerate(row):
            cx = x + i * cell
            p.append(swatch(kind, int(cx), int(yy), s=size / 18.0))
            p.append(text(int(cx + 32), int(yy + size), label, size,
                          BODY_GRAY))
    return "".join(p)


def screen_frame(x, y, w, h, header_text, header_size=20):
    """A screen frame: Charles Blue header bar, pale body."""
    p = []
    p.append(rect(x, y, w, h, PALE_BODY, stroke=CHARLES, sw=2))
    p.append(rect(x, y, w, 46, CHARLES))
    p.append(text(x + 16, y + 30, header_text, header_size, WHITE, "bold"))
    return "".join(p)


def card(x, y, w, h, label, size=20, lines=None):
    """An Optimistic Blue rounded card with white text."""
    p = [rect(x, y, w, h, OPTIMISTIC, rx=10)]
    if lines:
        p.append(text(x + w // 2, y + h // 2 - (len(lines) - 1) * (size // 2),
                      lines[0], size, WHITE, "bold", "middle"))
        for i, ln in enumerate(lines[1:]):
            p.append(text(x + w // 2, y + h // 2 + (i + 1) * size,
                          ln, size - 2, WHITE, "normal", "middle"))
    else:
        p.append(text(x + w // 2, y + h // 2 + size // 3, label, size,
                      WHITE, "bold", "middle"))
    return "".join(p)


def button_pill(x, y, w, h, label, size=20):
    """A Freedom Trail Red pill button with white text."""
    return (rect(x, y, w, h, FREEDOM, rx=h // 2)
            + text(x + w // 2, y + h // 2 + size // 3, label, size,
                   WHITE, "bold", "middle"))


def list_rows(x, y, w, row_h, n, gap=8, labels=None, size=18):
    """Teal stacked rows, optionally labelled in white."""
    p = []
    for i in range(n):
        yy = y + i * (row_h + gap)
        p.append(rect(x, yy, w, row_h, TEAL, rx=4))
        if labels:
            p.append(text(x + 14, yy + row_h // 2 + size // 3,
                          labels[i], size, WHITE, "normal"))
    return "".join(p)


def form_box(x, y, w, h, label=None, size=18):
    """A light-blue form rectangle with white input lines."""
    p = [rect(x, y, w, h, LIGHT_BLUE, rx=6)]
    if label:
        p.append(text(x + 16, y + 30, label, size, CHARLES, "bold"))
        top = y + 44
    else:
        top = y + 18
    p.append(rect(x + 16, top, w - 32, 10, WHITE, rx=5))
    p.append(rect(x + 16, top + 26, int((w - 32) * 0.62), 10, WHITE, rx=5))
    return "".join(p)


def diamond(x, y, w, h, lines, size=20):
    """An amber diamond gate with dark centred text lines."""
    cx, cy = x + w // 2, y + h // 2
    p = [f'<polygon points="{cx},{y} {x + w},{cy} {cx},{y + h} {x},{cy}" '
         f'fill="{AMBER}" stroke="{CHARLES}" stroke-width="3"/>']
    n = len(lines)
    for i, ln in enumerate(lines):
        p.append(text(cx, cy + (i - (n - 1) / 2) * (size + 6) + size // 3,
                      ln, size, CHARLES, "bold", "middle"))
    return "".join(p)


def state_box(x, y, w, h, title, lines, size=18, title_size=20):
    """A state/services box: pale fill, navy border, navy text."""
    p = [rect(x, y, w, h, PALE, stroke=NAVY, sw=3, rx=6)]
    p.append(rect(x, y, w, 40, NAVY, rx=6))
    p.append(rect(x, y + 28, w, 12, NAVY))
    p.append(text(x + 16, y + 27, title, title_size, WHITE, "bold"))
    for i, ln in enumerate(lines):
        p.append(text(x + 16, y + 40 + 30 + i * (size + 10), ln, size,
                      NAVY))
    return "".join(p)


def doc(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
            f'height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect x="0" y="0" width="{w}" height="{h}" fill="{WHITE}"/>'
            f'{body}</svg>')


def write_pair(svg_text, base_path, width):
    """Write the SVG and a 2x PNG next to it."""
    svg_path = base_path + ".svg"
    png_path = base_path + ".png"
    with open(svg_path, "w") as f:
        f.write(svg_text)
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"),
                     write_to=png_path, output_width=width * 2)
    return svg_path, png_path
