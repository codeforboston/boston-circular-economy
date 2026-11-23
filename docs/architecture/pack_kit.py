#!/usr/bin/env python3
"""Shared drawing kit for the Developer Guide pack edition.

Same canvas (1560x1140) and palette as the approved pilot page.
All text is hand-wrapped by callers; no auto-layout, no overflow.
"""
import html as H
import math

INK = "#1F2937"; MUTED = "#5B6B7F"; NAVY = "#14263F"; NAVY2 = "#0B1B30"
LIGHTNAVY = "#B9C6D8"; FAINT = "#9CA3AF"
CLIENT = ("#2563EB", "#DBEAFE"); API = ("#0F766E", "#CCFBF1")
DATA = ("#B45309", "#FEF3C7"); CONTRACT = ("#7C3AED", "#EDE9FE")
ADMIN = ("#9D174D", "#FCE7F3"); GREY = ("#4B5563", "#F3F4F6")
GOF = ("#6D28D9", "#EDE9FE"); FOWLER = ("#475569", "#E2E8F0"); IDIOM = ("#64748B", "#F1F5F9")
RED = ("#DC2626", "#FEF2F2"); GREEN = ("#15803D", "#F0FDF4")
FONT = "DejaVu Sans, Helvetica, Arial, sans-serif"
MONO = "DejaVu Sans Mono, monospace"
W, Hh = 1560, 1140


def esc(s):
    return H.escape(s, quote=False)


class Page:
    def __init__(self):
        self.p = [f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" '
                  f'width="{W}" height="{Hh}">']
        self.p.append(f'<rect x="0" y="0" width="{W}" height="{Hh}" fill="white"/>')

    def raw(self, s):
        self.p.append(s)

    def text(self, x, y, s, size=14, fill=INK, anchor="start", weight="normal", font=FONT):
        self.p.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
                      f'text-anchor="{anchor}" font-weight="{weight}" '
                      f'font-family="{font}">{esc(s)}</text>')

    def rect(self, x, y, w, h, fill, stroke=None, sw=2, rx=10, dash=False):
        d = ' stroke-dasharray="7 5"' if dash else ""
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                      f'fill="{fill}"{st}{d}/>')

    def line(self, x1, y1, x2, y2, color="#374151", sw=2.5, dash=False):
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                      f'stroke-width="{sw}"{d}/>')

    def arrow(self, x1, y1, x2, y2, color="#374151", sw=2.5, dash=False):
        """Rightward arrow with a filled head. Flows read left to right."""
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - 12}" y2="{y2}" stroke="{color}" '
                      f'stroke-width="{sw}"{d}/>')
        self.p.append(f'<polygon points="{x2 - 13},{y2 - 7} {x2 - 13},{y2 + 7} {x2},{y2}" '
                      f'fill="{color}"/>')

    def down_arrow(self, x, y1, y2, color="#374151", sw=2.5, dash=False):
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.p.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 12}" stroke="{color}" '
                      f'stroke-width="{sw}"{d}/>')
        self.p.append(f'<polygon points="{x - 7},{y2 - 13} {x + 7},{y2 - 13} {x},{y2}" '
                      f'fill="{color}"/>')

    def label(self, x, y, s, size=12.5, color="#374151"):
        """Arrow label on a white backing plate (cairosvg lacks paint-order)."""
        w = len(s) * size * 0.60 + 14
        self.p.append(f'<rect x="{x - w / 2}" y="{y - size - 3}" width="{w}" '
                      f'height="{size + 9}" rx="4" fill="white"/>')
        self.text(x, y, s, size=size, fill=color, anchor="middle", weight="bold")

    def chip(self, x, y, w, label, scheme, size=12.5):
        stroke, fill = scheme
        self.rect(x, y, w, 26, fill, stroke, 1.6, rx=13)
        self.text(x + w / 2, y + 17.5, label, size=size, fill=stroke,
                  anchor="middle", weight="bold")

    def num_badge(self, cx, cy, n, r=17):
        self.p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{NAVY}"/>')
        self.text(cx, cy + 7, str(n), size=19, fill="white", anchor="middle", weight="bold")

    def diamond(self, cx, cy, n, r=14):
        self.p.append(f'<polygon points="{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} '
                      f'{cx - r},{cy}" fill="#111827" stroke="white" stroke-width="2"/>')
        self.text(cx, cy + 5, str(n), size=13, fill="white", anchor="middle", weight="bold")

    def header(self, title, subtitle, page_no):
        self.rect(0, 0, W, 96, NAVY, rx=0)
        self.text(40, 46, title, size=31, fill="white", weight="bold")
        self.text(40, 76, subtitle, size=15.5, fill=LIGHTNAVY)
        self.rect(1466, 14, 68, 68, NAVY2, "white", 2, rx=8)
        self.text(1500, 62, str(page_no), size=36, fill="white", anchor="middle", weight="bold")

    def panel(self, x, y, w, h, title, title_size=17, fill="white", stroke=NAVY):
        self.rect(x, y, w, h, fill, stroke, 2.5, rx=12)
        self.rect(x, y, w, 46, stroke, rx=12)
        self.rect(x, y + 24, w, 22, stroke, rx=0)
        self.text(x + 20, y + 30, title, size=title_size, fill="white", weight="bold")
        return y + 46

    def panel_plain(self, x, y, w, h, scheme, title=None, title_size=15):
        stroke, fill = scheme
        self.rect(x, y, w, h, fill, stroke, 2, rx=10)
        if title:
            self.text(x + 16, y + 28, title, size=title_size, fill=stroke, weight="bold")
            return y + 28
        return y

    def rule_strip(self, y, bold_line, sub_line, icon_kind="info"):
        self.rect(36, y, 1488, 88, NAVY, rx=12)
        self.icon(icon_kind, 84, y + 44, "white")
        self.text(122, y + 34, bold_line, size=16.5, fill="white", weight="bold")
        self.text(122, y + 60, sub_line, size=13.5, fill=LIGHTNAVY)

    def footer(self, page_no, total, note):
        ly = 1044
        self.text(40, ly + 4, "LEGEND", size=12.5, fill=MUTED, weight="bold")
        items = [(130, GOF, "Gang of Four, 1994"), (330, FOWLER, "Fowler"),
                 (440, IDIOM, "React idiom"), (580, None, "◆ = DI seam, Views 2 and 5"),
                 (860, None, "▸ = flow runs left to right")]
        for lx, sch, lab in items:
            if sch:
                self.rect(lx, ly - 11, 18, 18, sch[1], sch[0], 1.6, rx=4)
                self.text(lx + 26, ly + 4, lab, size=12.5, fill=MUTED)
            else:
                self.text(lx, ly + 4, lab, size=12.5, fill=MUTED)
        self.text(40, 1084, note, size=12, fill=FAINT)
        self.text(1520, 1084, f"Page {page_no} of {total}", size=12, fill=FAINT,
                  anchor="end")

    def icon(self, kind, cx, cy, color, s=1.0):
        g = [f'<g transform="translate({cx} {cy}) scale({s})" fill="{color}" stroke="none">']
        if kind == "screen":
            g.append('<rect x="-15" y="-12" width="30" height="21" rx="3"/>'
                     '<rect x="-12" y="-9" width="24" height="15" fill="white"/>'
                     '<rect x="-6" y="12" width="12" height="3"/>')
        elif kind == "server":
            for dy in (-11, 3):
                g.append(f'<rect x="-14" y="{dy}" width="28" height="11" rx="2"/>'
                         f'<circle cx="-8" cy="{dy + 5.5}" r="2.2" fill="white"/>')
        elif kind == "gear":
            for a in range(0, 360, 45):
                rad = math.radians(a)
                x, y = 12.5 * math.cos(rad), 12.5 * math.sin(rad)
                g.append(f'<rect x="{x - 3}" y="{y - 3}" width="6.5" height="6.5" '
                         f'transform="rotate({a} {x} {y})"/>')
            g.append('<circle r="10"/><circle r="4.4" fill="white"/>')
        elif kind == "db":
            g.append('<path d="M-13 -12 h26 v22 c0 4.5 -5.8 8 -13 8 c-7.2 0 -13 -3.5 -13 -8 z"/>'
                     '<ellipse cx="0" cy="-12" rx="13" ry="4.6" fill="white" opacity=".55"/>')
        elif kind == "stack":
            for i, dy in enumerate((8, -1, -10)):
                g.append(f'<rect x="{-13 + i * 2}" y="{dy}" width="26" height="7" rx="2" '
                         f'opacity="{0.55 + 0.22 * i}"/>')
        elif kind == "funnel":
            g.append('<path d="M-15 -13 h30 l-11 12 v9 l-8 5 v-14 l-11 -12 z"/>')
        elif kind == "adapter":
            g.append('<path d="M-16 -10 h20 v-5 l11 8 -11 8 v-5 h-20 z"/>'
                     '<path d="M16 10 h-20 v5 l-11 -8 11 -8 v5 h20 z" opacity=".55"/>')
        elif kind == "skeleton":
            g.append('<rect x="-15" y="-14" width="30" height="6" rx="2"/>'
                     '<rect x="-15" y="-3" width="21" height="6" rx="2" opacity=".7"/>'
                     '<rect x="-15" y="8" width="13" height="6" rx="2" opacity=".45"/>')
        elif kind == "branch":
            g.append('<circle cx="-13" cy="0" r="4.5"/>')
            for dy in (-12, 0, 12):
                g.append(f'<path d="M-9 0 C 0 {dy * 0.4}, 2 {dy}, 8 {dy}" stroke="{color}" '
                         f'stroke-width="2.6" fill="none"/><circle cx="12" cy="{dy}" r="4"/>')
        elif kind == "factory":
            g.append('<path d="M-16 15 V-3 l9 -6 v6 l9 -6 v24 z"/>'
                     '<rect x="-9" y="5" width="7" height="10" fill="white"/>')
        elif kind == "plug":
            g.append('<rect x="-5" y="-4" width="10" height="13" rx="3"/>'
                     '<rect x="-9" y="-14" width="4" height="9"/>'
                     '<rect x="5" y="-14" width="4" height="9"/>'
                     '<path d="M0 9 v5 c0 5 -8 5 -8 10" stroke="' + color +
                     '" stroke-width="3" fill="none"/>')
        elif kind == "tree":
            g.append('<circle cx="0" cy="-12" r="5.5"/><circle cx="-12" cy="11" r="5"/>'
                     '<circle cx="12" cy="11" r="5"/>'
                     '<path d="M-3 -8 L-10 7 M3 -8 L10 7" stroke="' + color +
                     '" stroke-width="2.6"/>')
        elif kind == "atom":
            for rot in (0, 60, 120):
                g.append(f'<ellipse rx="16" ry="6.5" fill="none" stroke="{color}" '
                         f'stroke-width="2.4" transform="rotate({rot})"/>')
            g.append('<circle r="3.4"/>')
        elif kind == "info":
            g.append('<circle r="15"/>')
            g.append(f'<text x="0" y="8" font-size="22" fill="#14263F" text-anchor="middle" '
                     f'font-weight="bold" font-family="{FONT}">i</text>')
        elif kind == "code":
            g.append(f'<text x="0" y="9" font-size="26" fill="{color}" text-anchor="middle" '
                     f'font-weight="bold" font-family="{MONO}">&lt;/&gt;</text>')
        elif kind == "search":
            g.append('<circle cx="-4" cy="-4" r="9" fill="none" stroke="' + color +
                     '" stroke-width="3.4"/><path d="M3 3 L13 13" stroke="' + color +
                     '" stroke-width="4" stroke-linecap="round"/>')
        elif kind == "question":
            g.append('<circle r="15" fill="none" stroke="' + color + '" stroke-width="3"/>')
            g.append(f'<text x="0" y="8" font-size="22" fill="{color}" text-anchor="middle" '
                     f'font-weight="bold" font-family="{FONT}">?</text>')
        elif kind == "check":
            g.append(f'<path d="M-14 1 L-5 10 L15 -11" stroke="{color}" stroke-width="4.5" '
                     f'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        elif kind == "cross":
            g.append(f'<path d="M-11 -11 L11 11 M11 -11 L-11 11" stroke="{color}" '
                     f'stroke-width="4.5" stroke-linecap="round"/>')
        elif kind == "doc":
            g.append('<path d="M-11 -15 h14 l8 8 v22 h-22 z"/>'
                     '<rect x="-6" y="-8" width="12" height="3" fill="white"/>'
                     '<rect x="-6" y="-1" width="12" height="3" fill="white"/>'
                     '<rect x="-6" y="6" width="8" height="3" fill="white"/>')
        elif kind == "link":
            g.append('<rect x="-15" y="-6" width="14" height="12" rx="4" fill="none" '
                     'stroke="' + color + '" stroke-width="3"/>'
                     '<rect x="1" y="-6" width="14" height="12" rx="4" fill="none" '
                     'stroke="' + color + '" stroke-width="3"/>'
                     '<path d="M-4 0 h8" stroke="' + color + '" stroke-width="3"/>')
        elif kind == "clock":
            g.append('<circle r="14" fill="none" stroke="' + color + '" stroke-width="3"/>'
                     '<path d="M0 -9 V0 L7 5" stroke="' + color +
                     '" stroke-width="3" fill="none" stroke-linecap="round"/>')
        elif kind == "person":
            g.append('<circle cx="0" cy="-8" r="6" fill="none" stroke="' + color +
                     '" stroke-width="3"/>'
                     '<path d="M-13 14 a13,11 0 0 1 26,0" fill="none" stroke="' + color +
                     '" stroke-width="3"/>')
        elif kind == "shield":
            g.append('<path d="M0 -15 L13 -10 V2 C13 11 7 15 0 17 C-7 15 -13 11 -13 2 '
                     'V-10 Z"/><path d="M-6 1 L-2 5 L7 -4" stroke="white" stroke-width="3" '
                     'fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        g.append("</g>")
        self.p.append("".join(g))

    def code_lines(self, x, y, lines, size=13, lh=19, color=INK):
        for ln in lines:
            self.text(x, y, ln, size=size, fill=color, font=MONO)
            y += lh
        return y

    def wrap(self, x, y, s, width_chars, size=13.5, lh=20, fill=INK, weight="normal"):
        words, line = s.split(), ""
        for wd in words:
            if len(line) + len(wd) > width_chars:
                self.text(x, y, line, size=size, fill=fill, weight=weight)
                y += lh
                line = wd + " "
            else:
                line += wd + " "
        if line.strip():
            self.text(x, y, line, size=size, fill=fill, weight=weight)
            y += lh
        return y

    def done(self):
        self.p.append("</svg>")
        return "".join(self.p)


def save(page, path):
    with open(path, "w") as f:
        f.write(page.done())
    print("wrote", path)
