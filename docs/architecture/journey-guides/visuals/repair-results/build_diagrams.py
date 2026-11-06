#!/usr/bin/env python3
"""Generate the repair-results diagrams.

Fixed visual mapping (same for all four journey guides):
  Card = Optimistic Blue #1871BD, rounded rectangle
  Button (primary action) = Freedom Trail Red #FB4D42, pill shape
  List = teal #0E7C7B, stacked horizontal rows
  Form = light-blue #6FA8F5, rectangle with input lines
  Decision gate = amber #FFD98A diamond
  Screen frame = Charles Blue #091F2F header bar with pale #EDF2F9 body
  State and services = navy #0B1524 with pale #DCE6F4
Symbols are drawn as vector shapes. No typed check or arrow glyphs.
Each diagram: SVG + generator (this file) + PNG at 2x via cairosvg.
"""
import os
import cairosvg

OUT = os.path.expanduser(
    "~/workspace/goals/boston-circular-economy-client-architecture/"
    "files/journey-guides/visuals/repair-results")

CARD = "#1871BD"
BTN = "#FB4D42"
LIST = "#0E7C7B"
FORM = "#6FA8F5"
GATE = "#FFD98A"
FRAME_HDR = "#091F2F"
FRAME_BODY = "#EDF2F9"
STATE = "#0B1524"
STATE_BG = "#DCE6F4"
WHITE = "#FFFFFF"
INK = "#091F2F"
GRAY = "#58585B"
LIGHT = "#F3F3F3"
GOLD_LINE = "#B98A1F"

SANS = "Montserrat, Arial, sans-serif"
SERIF = "Lora, Georgia, serif"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def text(x, y, s, size=18, fill=INK, family=SANS, weight="normal",
         anchor="start", style=""):
    w = f' font-weight="{weight}"' if weight != "normal" else ""
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}"'
            f' fill="{fill}" text-anchor="{anchor}"{w}{st}>{esc(s)}</text>')


def rect(x, y, w, h, fill, rx=0, stroke=None, sw=0, opacity=None):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    o = f' opacity="{opacity}"' if opacity else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"'
            f' fill="{fill}"{s}{o} />')


def diamond(cx, cy, w, h, fill=GATE, stroke=GOLD_LINE, sw=3):
    pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}"'
            f' stroke-width="{sw}" />')


def arrow_h(x1, y, x2, color=INK, sw=3):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2 - 14}" y2="{y}" stroke="{color}"'
            f' stroke-width="{sw}" />'
            f'<polygon points="{x2 - 14},{y - 8} {x2},{y} {x2 - 14},{y + 8}"'
            f' fill="{color}" />')


def arrow_v(x, y1, y2, color=INK, sw=3):
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2 - 14}" stroke="{color}"'
            f' stroke-width="{sw}" />'
            f'<polygon points="{x - 8},{y2 - 14} {x},{y2} {x + 8},{y2 - 14}"'
            f' fill="{color}" />')


def title_block(title, subtitle, w=1600):
    parts = [
        rect(0, 0, w, 118, FRAME_HDR),
        text(48, 38, "CITY OF BOSTON  —  CIRCULAR ECONOMY", 17, "#6FA8F5",
             weight="bold"),
        text(48, 76, title, 34, WHITE, weight="bold"),
        text(48, 106, subtitle, 19, "#DCE6F4", family=SERIF, style="italic"),
    ]
    return "\n".join(parts)


def legend(y, w=1600, compact=False):
    """The fixed mapping, in the legend of every diagram."""
    items = [
        ("card", "Card", CARD, "rr"),
        ("button", "Button", BTN, "pill"),
        ("list", "List", LIST, "rows"),
        ("form", "Form", FORM, "form"),
        ("gate", "Decision gate", GATE, "diamond"),
        ("screen", "Screen frame", FRAME_HDR, "frame"),
        ("state", "State / service", STATE, "state"),
    ]
    x = 48
    gap = 218 if not compact else 200
    out = [text(48, y - 14, "HOW TO READ THIS PICTURE", 15, GRAY, weight="bold")]
    for _key, label, color, kind in items:
        sy = y + 6
        if kind == "rr":
            out.append(rect(x, sy, 34, 22, color, rx=6))
        elif kind == "pill":
            out.append(rect(x, sy, 34, 22, color, rx=11))
        elif kind == "rows":
            out.append(rect(x, sy, 34, 22, color, rx=3))
            out.append(rect(x + 5, sy + 5, 24, 3, WHITE, rx=1))
            out.append(rect(x + 5, sy + 13, 24, 3, WHITE, rx=1))
        elif kind == "form":
            out.append(rect(x, sy, 34, 22, color, rx=3))
            out.append(rect(x + 5, sy + 6, 24, 2, WHITE))
            out.append(rect(x + 5, sy + 13, 24, 2, WHITE))
        elif kind == "diamond":
            out.append(diamond(x + 17, sy + 11, 26, 22))
        elif kind == "frame":
            out.append(rect(x, sy, 34, 22, FRAME_BODY, rx=3,
                            stroke=FRAME_HDR, sw=2))
            out.append(rect(x, sy, 34, 8, FRAME_HDR, rx=3))
        elif kind == "state":
            out.append(rect(x, sy, 34, 22, STATE, rx=3))
            out.append(rect(x + 5, sy + 6, 24, 3, STATE_BG, rx=1))
            out.append(rect(x + 5, sy + 13, 24, 3, STATE_BG, rx=1))
        out.append(text(x + 42, sy + 17, label, 15, INK))
        x += gap
    return "\n".join(out)


def footer(y, line, w=1600):
    return text(48, y, line, 15, GRAY, family=SERIF, style="italic")


def save(name, svg, width):
    path_svg = os.path.join(OUT, name + ".svg")
    path_png = os.path.join(OUT, name + ".png")
    with open(path_svg, "w") as f:
        f.write(svg)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=path_png,
                     output_width=width * 2)
    print("wrote", name)


def page(w, h, title, subtitle):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"'
            f' viewBox="0 0 {w} {h}">',
            rect(0, 0, w, h, WHITE), title_block(title, subtitle, w)]


def screen_frame(x, y, w, h, title, body_lines, accent=None):
    """A screen frame: Charles Blue header bar, pale body."""
    out = [rect(x, y, w, h, FRAME_BODY, rx=10, stroke=FRAME_HDR, sw=3),
           rect(x, y, w, 52, FRAME_HDR, rx=10),
           rect(x, y + 40, w, 14, FRAME_HDR),
           text(x + 18, y + 34, title, 19, WHITE, weight="bold")]
    yy = y + 82
    for line in body_lines:
        out.append(text(x + 18, yy, line, 16, INK))
        yy += 28
    return "\n".join(out)


def card_box(x, y, w, h, title, lines):
    out = [rect(x, y, w, h, CARD, rx=12),
           text(x + 18, y + 32, title, 19, WHITE, weight="bold")]
    yy = y + 62
    for line in lines:
        out.append(text(x + 18, yy, line, 16, WHITE))
        yy += 26
    return "\n".join(out)


def state_box(x, y, w, h, title, lines):
    out = [rect(x, y, w, h, STATE, rx=10),
           text(x + 18, y + 32, title, 19, STATE_BG, weight="bold")]
    yy = y + 62
    for line in lines:
        out.append(text(x + 18, yy, line, 16, STATE_BG))
        yy += 26
    return "\n".join(out)


def list_box(x, y, w, h, title, rows):
    out = [rect(x, y, w, h, LIST, rx=10),
           text(x + 18, y + 32, title, 19, WHITE, weight="bold")]
    yy = y + 58
    for r in rows:
        out.append(rect(x + 14, yy, w - 28, 34, WHITE, rx=6, opacity=0.92))
        out.append(text(x + 26, yy + 23, r, 16, INK))
        yy += 44
    return "\n".join(out)


def form_box(x, y, w, h, title, fields):
    out = [rect(x, y, w, h, FORM, rx=10),
           text(x + 18, y + 32, title, 19, INK, weight="bold")]
    yy = y + 58
    for f in fields:
        out.append(text(x + 18, yy, f, 15, INK))
        yy += 22
        out.append(rect(x + 18, yy, w - 36, 26, WHITE, rx=4,
                        stroke=FRAME_HDR, sw=2))
        yy += 40
    return "\n".join(out)


def pill(x, y, w, label, size=17):
    return (rect(x, y, w, 46, BTN, rx=23) +
            text(x + w / 2, y + 30, label, size, WHITE, weight="bold",
                 anchor="middle"))


# ---------------------------------------------------------------- journey map
def journey_map():
    w, h = 1600, 1010
    p = page(w, h, "Repair results — the journey Denise walks",
             "Six screens, in the order Denise sees them. One real journey, built in order.")
    p.append(text(48, 168, "DENISE  —  SENIOR RESIDENT  —  TV AND JACKET  —  SAVES MONEY  —  DORCHESTER, 4 MILES",
                  17, CARD, weight="bold"))
    frames = [
        ("1", "/repair", ["Repair form", "Estimator", "SEARCH"]),
        ("2", "/repair/results", ["FREE and PAID", "Map and list", "Pick a provider"]),
        ("3", "/repair/form", ["Step 1: TV", "Step 2: jacket", "Step 3: name, email"]),
        ("4", "/repair/events", ["Fixit Clinic", "Date, time, place", "Event cards"]),
        ("5", "/providers/:id", ["Hours, services", "Price in words", "Register by email"]),
        ("6", "Confirmation", ["Share card", "Feedback vote", "Thank you"]),
    ]
    x, y = 48, 210
    fw, fh = 470, 250
    for i, (num, route, lines) in enumerate(frames):
        cx = x + (i % 3) * (fw + 46)
        cy = y + (i // 3) * (fh + 90)
        p.append(screen_frame(cx, cy, fw, fh, f"STEP {num}  {route}", lines))
        if i % 3 < 2:
            p.append(arrow_h(cx + fw + 4, cy + fh / 2, cx + fw + 42, CARD, 4))
        elif i == 2:
            p.append(arrow_v(cx + fw / 2, cy + fh + 4, cy + fh + 86, CARD, 4))
    # decision gate between results and form
    p.append(text(48, 838, "Denise starts on /repair, picks a provider on /repair/results, registers on /repair/form,",
                  18, INK))
    p.append(text(48, 866, "checks the clinic event, opens the provider page, and ends with feedback.",
                  18, INK))
    p.append(legend(916, w))
    p.append(footer(985, "Derived from the Developer Guide worked example and the Repair journey digest.", w))
    return "\n".join(p) + "\n</svg>"


# ------------------------------------------------------------------ build map
def build_map():
    w, h = 1600, 1080
    p = page(w, h, "Repair results — the build map",
             "Build screen by screen, in layer order. One component per step. Check each screen before the next.")
    p.append(text(48, 168, "LAYER ORDER — FOLLOW IT ON EVERY SCREEN", 17, CARD, weight="bold"))
    layers = ["1  Journey and", "2  Shell", "3  Widgets", "4  State wiring", "5  Services", "6  States, access,"]
    layers2 = ["page model", "", "", "", "", "and mobile"]
    lx = 48
    for i, (a, b) in enumerate(zip(layers, layers2)):
        p.append(rect(lx, 186, 240, 78, STATE_BG, rx=10, stroke=STATE, sw=2))
        p.append(text(lx + 16, 216, a, 16, STATE, weight="bold"))
        if b:
            p.append(text(lx + 16, 242, b, 16, STATE))
        if i < 5:
            p.append(arrow_h(lx + 244, 225, lx + 256, CARD, 3))
        lx += 258
    screens = [
        ("1  /repair", ["W-01 Estimator", "W-06 Search input", "W-08 Validation"]),
        ("2  /repair/results", ["W-05 Results list", "W-07 Filter bar", "W-09 Map  W-12 Card"]),
        ("3  /repair/form", ["W-02 Registration", "W-08 Validation", "W-16 Stepper"]),
        ("4  /repair/events", ["W-11 Event finder", "W-26 States", "Event cards"]),
        ("5  /providers/:id", ["W-12 Provider card", "Details list", "Referral box"]),
        ("6  Confirmation", ["Share card", "W-14 Feedback", "POST /feedback"]),
    ]
    x, y = 48, 300
    fw, fh = 470, 200
    for i, (title, lines) in enumerate(screens):
        cx = x + (i % 3) * (fw + 46)
        cy = y + (i // 3) * (fh + 70)
        p.append(screen_frame(cx, cy, fw, fh, title, lines))
        if i % 3 < 2:
            p.append(arrow_h(cx + fw + 4, cy + fh / 2, cx + fw + 42, CARD, 4))
        elif i == 2:
            p.append(arrow_v(cx + fw / 2, cy + fh + 4, cy + fh + 66, CARD, 4))
    p.append(text(48, 852, "Each screen ends with a check: what you should see in the browser, in Fleet colors.",
                  18, INK))
    p.append(text(48, 880, "Run the check before you move on to the next screen.",
                  18, INK))
    p.append(legend(950, w))
    p.append(footer(1025, "Derived from the Developer Guide eight-step page-design sequence and the wiring layers.", w))
    return "\n".join(p) + "\n</svg>"


# ------------------------------------------------------------- wiring diagrams
def wiring_base(title, subtitle, h=1080):
    return page(1600, h, title, subtitle)


def wiring_footer(p, w=1600, y=1010):
    p.append(legend(y, w))
    p.append(footer(y + 75, "Derived from the Developer Guide page models, stubs, and the Repair journey digest.", w))
    return "\n".join(p) + "\n</svg>"


def wiring_repair():
    p = wiring_base("Wiring — /repair — repair form and estimator",
                    "Form state feeds the estimator. SEARCH moves the form to the URL.")
    p.append(state_box(48, 170, 420, 300, "FORM STATE (page)",
                       ["items: TV, jacket", "mode: self", "priority: money",
                        "getting-there, zip", "distance: 4 miles"]))
    p.append(state_box(48, 500, 420, 170, "DERIVED — NO STATE",
                       ["estimated impact", "from items and mode"]))
    p.append(state_box(48, 700, 420, 170, "SERVICE",
                       ["client/src/lib/estimate.ts",
                        "one rule function"]))
    p.append(arrow_h(472, 320, 520, CARD, 4))
    p.append(arrow_h(472, 585, 520, CARD, 4))
    p.append(arrow_h(472, 785, 520, CARD, 4))
    p.append(form_box(520, 170, 430, 420, "REPAIR FORM",
                      ["Item 1", "Item 2", "Repair mode", "Priority"]))
    p.append(card_box(520, 620, 430, 250, "ESTIMATOR  .est",
                      ["Estimated impact", "Savings $500",
                       "Reduced waste 43 lbs"]))
    p.append(arrow_h(954, 380, 1002, CARD, 4))
    p.append(diamond(1120, 380, 190, 130))
    p.append(text(1120, 374, "Form passes", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 398, "validation?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 470, "No: error text", 15, GRAY, anchor="middle"))
    p.append(text(1120, 492, "under the field", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 380, 1266, CARD, 4))
    p.append(pill(1270, 357, 180, "SEARCH"))
    p.append(text(1360, 440, "Yes: SEARCH writes", 15, INK, anchor="middle"))
    p.append(text(1360, 462, "the URL", 15, INK, anchor="middle"))
    p.append(screen_frame(1000, 620, 550, 250, "/repair/results — next screen",
                          ["URL holds the search:", "item=tv, item=jacket, mode=self",
                           "priority=money, zip=02122, distance=4"]))
    return wiring_footer(p, y=920)


def wiring_results():
    p = wiring_base("Wiring — /repair/results — results, map, and selection",
                    "The URL owns the search. The query client owns the results. The page owns the selection.")
    p.append(state_box(48, 170, 420, 230, "URL STATE",
                       ["item=tv, item=jacket", "mode=self, priority=money",
                        "zip=02122, distance=4", "page=1"]))
    p.append(state_box(48, 430, 420, 200, "QUERY CLIENT",
                       ["results, cached", "key: search"]))
    p.append(state_box(48, 660, 420, 170, "PAGE STATE",
                       ["selectedId: string | null"]))
    p.append(arrow_h(472, 285, 520, CARD, 4))
    p.append(arrow_h(472, 530, 520, CARD, 4))
    p.append(arrow_h(472, 745, 520, CARD, 4))
    p.append(list_box(520, 170, 430, 330, "RESULTS LIST  .sr-list",
                      ["Fixit Clinic — Free", "Paid card 1", "Paid card 2"]))
    p.append(card_box(520, 530, 430, 300, "MAP  .mp  +  FILTER BAR  .fl",
                      ["One marker per provider", "Markers are buttons",
                       "Filter bar holds the values"]))
    p.append(arrow_h(954, 330, 1002, CARD, 4))
    p.append(diamond(1120, 330, 190, 130))
    p.append(text(1120, 324, "priority =", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 348, "money?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 420, "Yes: FREE / PAID", 15, GRAY, anchor="middle"))
    p.append(text(1120, 442, "No: This week", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 330, 1266, CARD, 4))
    p.append(card_box(1270, 200, 282, 260, "PROVIDER CARD  .pv",
                      ["Name", "Services", "Price, distance, stars"]))
    p.append(state_box(1000, 530, 552, 300, "SEARCH QUERY",
                       ["client/src/api/search.ts",
                        "searchQueryOptions",
                        "GET /api/v1/search",
                        "Every location, first 10 shown"]))
    return wiring_footer(p, y=920)


def wiring_form():
    p = wiring_base("Wiring — /repair/form — three-step registration",
                    "The step is the state. BACK moves back, NEXT moves forward, SUBMIT ends it.")
    p.append(state_box(48, 170, 420, 200, "COMPONENT STATE",
                       ["step: 1, 2, or 3"]))
    p.append(state_box(48, 400, 420, 230, "FORM STATE",
                       ["item fields per item", "name, email",
                        "waiver agreed: false"]))
    p.append(state_box(48, 660, 420, 170, "SERVER",
                       ["submitted state", "on SUBMIT"]))
    p.append(arrow_h(472, 270, 520, CARD, 4))
    p.append(arrow_h(472, 515, 520, CARD, 4))
    p.append(form_box(520, 170, 430, 460, "REGISTRATION FORM  .rg",
                      ["Step 1: item 1 (TV)", "Step 2: item 2 (jacket)",
                       "Step 3: name, email"]))
    p.append(card_box(520, 660, 430, 170, "WAIVER  .rg-waiver",
                      ["Liability waiver", "Media release", "Agreement checkbox"]))
    p.append(arrow_h(954, 400, 1002, CARD, 4))
    p.append(diamond(1120, 400, 190, 130))
    p.append(text(1120, 394, "Step passes", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 418, "its check?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 490, "No: stay, show error", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 400, 1266, CARD, 4))
    p.append(pill(1270, 377, 180, "NEXT"))
    p.append(text(1360, 460, "Step 3: SUBMIT", 15, INK, anchor="middle"))
    p.append(state_box(1000, 660, 552, 170, "VALIDATION  .fld-err",
                       ["client/src/lib/validate.ts",
                        "one function per form"]))
    return wiring_footer(p, y=920)


def wiring_events():
    p = wiring_base("Wiring — /repair/events — event finder",
                    "Events come from the API. The page holds no event data itself.")
    p.append(state_box(48, 170, 420, 230, "QUERY CLIENT",
                       ["events, cached", "from the API"]))
    p.append(state_box(48, 430, 420, 200, "SEARCH QUERY",
                       ["searchQueryOptions", "GET /api/v1/search"]))
    p.append(arrow_h(472, 285, 520, CARD, 4))
    p.append(arrow_h(472, 530, 520, CARD, 4))
    p.append(list_box(520, 170, 430, 330, "EVENT LIST  .ef",
                      ["Fixit Clinic — Sat 10am", "Fixit Clinic — Sat 2pm",
                       "Clinic — date to be set"]))
    p.append(card_box(520, 530, 430, 300, "EVENT CARD  .evt",
                      ["Date flag, yellow", "Time and place",
                       "Links to provider page"]))
    p.append(arrow_h(954, 330, 1002, CARD, 4))
    p.append(diamond(1120, 330, 190, 130))
    p.append(text(1120, 324, "Date", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 348, "set?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 420, "No: Date to be set", 15, GRAY, anchor="middle"))
    p.append(text(1120, 442, "Never a blank card", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 330, 1266, CARD, 4))
    p.append(screen_frame(1270, 200, 282, 260, "/providers/:id",
                          ["Event card links", "to the provider", "page"]))
    p.append(text(1000, 620, "Each event links to its provider page. A card with no date shows", 17, INK))
    p.append(text(1000, 648, "\"Date to be set\", never a blank card.", 17, INK))
    p.append(text(1000, 700, "File: client/src/pages/repair/events.tsx", 17, CARD, weight="bold"))
    p.append(text(1000, 728, "Card: client/src/components/repair/EventCard.tsx", 17, CARD, weight="bold"))
    return wiring_footer(p, y=920)


def wiring_provider():
    p = wiring_base("Wiring — /providers/:id — provider page",
                    "The URL names the provider. The query client holds the record.")
    p.append(state_box(48, 170, 420, 200, "URL PATH",
                       ["provider id", "/providers/:id"]))
    p.append(state_box(48, 400, 420, 200, "QUERY CLIENT",
                       ["provider record", "shared link opens",
                        "the same provider"]))
    p.append(state_box(48, 630, 420, 200, "FORM STATE",
                       ["registration email", "until SUBMIT"]))
    p.append(arrow_h(472, 270, 520, CARD, 4))
    p.append(arrow_h(472, 500, 520, CARD, 4))
    p.append(arrow_h(472, 730, 520, CARD, 4))
    p.append(card_box(520, 170, 430, 330, "PROVIDER DETAILS  .pv  .dl",
                      ["Name, services", "Hours, price", "Distance, stars"]))
    p.append(card_box(520, 530, 430, 300, "REFERRAL BOX  .refbox",
                      ["Referral link in full", "text, and the count",
                       "Tracking is server-side"]))
    p.append(arrow_h(954, 330, 1002, CARD, 4))
    p.append(diamond(1120, 330, 190, 130))
    p.append(text(1120, 324, "Hours say", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 348, "open?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 420, "Derived from record", 15, GRAY, anchor="middle"))
    p.append(text(1120, 442, "Open / closed in words", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 330, 1266, CARD, 4))
    p.append(pill(1270, 307, 180, "REGISTER"))
    p.append(text(1360, 390, "Sends the", 15, INK, anchor="middle"))
    p.append(text(1360, 412, "registration email", 15, INK, anchor="middle"))
    p.append(screen_frame(1000, 530, 552, 300, "Provider page — what Denise sees",
                          ["Provider name and details", "Open or Closed, in words",
                           "Referral box with the full link"]))
    return wiring_footer(p, y=920)


def wiring_confirmation():
    p = wiring_base("Wiring — confirmation and feedback",
                    "The share card is derived. The feedback widget has three states: vote, message, sent.")
    p.append(state_box(48, 170, 420, 200, "REGISTRATION ID",
                       ["URL / email link"]))
    p.append(state_box(48, 400, 420, 200, "DERIVED — NO STATE",
                       ["impact values", "share card"]))
    p.append(state_box(48, 630, 420, 200, "COMPONENT STATE",
                       ["vote, message, sent"]))
    p.append(arrow_h(472, 270, 520, CARD, 4))
    p.append(arrow_h(472, 500, 520, CARD, 4))
    p.append(arrow_h(472, 730, 520, CARD, 4))
    p.append(card_box(520, 170, 430, 330, "SHARE CARD  .sh",
                      ["Estimated impact", "Facebook / Instagram links",
                       "QR code note in text"]))
    p.append(form_box(520, 530, 430, 300, "FEEDBACK  .fb",
                      ["Like or dislike", "Message"]))
    p.append(arrow_h(954, 330, 1002, CARD, 4))
    p.append(diamond(1120, 330, 190, 130))
    p.append(text(1120, 324, "Vote", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 348, "given?", 17, INK, weight="bold", anchor="middle"))
    p.append(text(1120, 420, "No: stay on vote", 15, GRAY, anchor="middle"))
    p.append(arrow_h(1218, 330, 1266, CARD, 4))
    p.append(pill(1270, 307, 180, "SUBMIT"))
    p.append(text(1360, 390, "POST /feedback", 15, INK, anchor="middle"))
    p.append(text(1360, 412, "Sends once only", 15, INK, anchor="middle"))
    p.append(card_box(1000, 530, 552, 300, "SENT STATE  .nt",
                      ["Thank you. Your feedback was sent.",
                       "The widget does not send twice.",
                       "File: client/src/components/feedback/FeedbackWidget.tsx"]))
    return wiring_footer(p, y=920)


# ------------------------------------------------------------------- phone mocks
def mock_base(title):
    w, h = 390, 800
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"'
             f' viewBox="0 0 {w} {h}">',
             rect(0, 0, w, h, WHITE),
             rect(0, 0, w, 56, FRAME_HDR),
             text(18, 36, title, 19, WHITE, weight="bold"),
             rect(0, 56, w, h - 56, FRAME_BODY)]
    return parts, w, h


def mock_legend(p, y=742):
    items = [("Card", CARD, "rr"), ("Button", BTN, "pill"),
             ("List", LIST, "rows"), ("Form", FORM, "form"),
             ("Gate", GATE, "diamond")]
    x = 14
    for label, color, kind in items:
        sy = y
        if kind == "rr":
            p.append(rect(x, sy, 18, 12, color, rx=3))
        elif kind == "pill":
            p.append(rect(x, sy, 18, 12, color, rx=6))
        elif kind == "rows":
            p.append(rect(x, sy, 18, 12, color, rx=2))
            p.append(rect(x + 3, sy + 3, 12, 2, WHITE))
            p.append(rect(x + 3, sy + 7, 12, 2, WHITE))
        elif kind == "form":
            p.append(rect(x, sy, 18, 12, color, rx=2))
            p.append(rect(x + 3, sy + 3, 12, 1, WHITE))
            p.append(rect(x + 3, sy + 7, 12, 1, WHITE))
        elif kind == "diamond":
            p.append(diamond(x + 9, sy + 6, 14, 12))
        p.append(text(x + 22, sy + 11, label, 11, INK))
        x += 74
    p.append(text(14, y + 34, "Screen frame: Charles Blue header, pale body.  State: navy.",
                  11, GRAY))
    p.append(text(14, y + 50, "Full mapping: see the journey map legend.", 11, GRAY))
    return p


def mock_save(name, parts):
    svg = "\n".join(parts) + "\n</svg>"
    save(name, svg, 390)


def mock_repair_form():
    p, w, h = mock_base("Repair")
    p.append(form_box(16, 76, 358, 240, "YOUR ITEMS",
                      ["Item 1", "Item 2"]))
    # remove the extra empty input the helper adds per field is fine; add mode radios
    p.append(text(32, 362, "Repair mode:  Self   Drop off", 15, INK))
    p.append(text(32, 392, "Priority:  Save money", 15, INK))
    p.append(text(32, 432, "Zip: 02122   Distance: 4 miles", 15, INK))
    p.append(pill(16, 466, 358, "SEARCH"))
    p.append(text(16, 556, "What you should see: two item fields,", 15, INK))
    p.append(text(16, 580, "mode and priority radios, zip and", 15, INK))
    p.append(text(16, 604, "distance, and a red SEARCH button.", 15, INK))
    mock_legend(p)
    mock_save("mock-01-repair-form", p)


def mock_estimator():
    p, w, h = mock_base("Repair")
    p.append(card_box(16, 76, 358, 220, "ESTIMATED IMPACT",
                      ["Savings $500", "Reduced waste 43 lbs",
                       "TV and jacket"]))
    p.append(form_box(16, 320, 358, 180, "YOUR ITEMS", ["Item 1"]))
    p.append(pill(16, 540, 358, "SEARCH"))
    p.append(text(16, 630, "What you should see: the blue card", 15, INK))
    p.append(text(16, 654, "shows $500 saved and 43 lbs kept out.", 15, INK))
    mock_legend(p)
    mock_save("mock-02-estimator", p)


def mock_results():
    p, w, h = mock_base("Search results")
    p.append(text(16, 96, "Displaying 1 - 10 of 22", 16, INK, weight="bold"))
    p.append(list_box(16, 116, 358, 150, "FREE",
                      ["Fixit Clinic — Free"]))
    p.append(list_box(16, 286, 358, 200, "PAID",
                      ["Paid card 1", "Paid card 2"]))
    p.append(text(16, 530, "What you should see: the count, then", 15, INK))
    p.append(text(16, 554, "a FREE section and a PAID section.", 15, INK))
    mock_legend(p)
    mock_save("mock-03-results", p)


def mock_selected():
    p, w, h = mock_base("Search results")
    p.append(rect(16, 76, 358, 150, "#BFD9EC", rx=10, stroke=CARD, sw=2))
    p.append(text(32, 110, "MAP — markers are buttons", 15, INK, weight="bold"))
    p.append(rect(60, 140, 26, 26, CARD, rx=13))
    p.append(rect(200, 160, 26, 26, CARD, rx=13))
    p.append(text(32, 210, "Tap a marker to select a provider.", 14, INK))
    p.append(list_box(16, 246, 358, 200, "FREE",
                      ["Fixit Clinic — Free — selected"]))
    p.append(text(16, 500, "Fixit Clinic selected", 16, CARD, weight="bold"))
    p.append(text(16, 530, "The live region speaks the selection.", 15, INK))
    p.append(text(16, 560, "Focus moves to the list entry.", 15, INK))
    p.append(pill(16, 600, 358, "EDIT SEARCH"))
    mock_legend(p)
    mock_save("mock-04-results-selected", p)


def mock_dialog():
    p, w, h = mock_base("Search results")
    p.append(rect(16, 76, 358, 300, WHITE, rx=10, stroke=GRAY, sw=2))
    p.append(text(32, 112, "Results list, dimmed", 15, GRAY))
    p.append(rect(40, 420, 310, 250, WHITE, rx=10, stroke=FRAME_HDR, sw=3))
    p.append(rect(40, 420, 310, 48, FRAME_HDR, rx=10))
    p.append(text(58, 451, "FILTER", 17, WHITE, weight="bold"))
    p.append(text(58, 510, "Category: Any", 15, INK))
    p.append(text(58, 544, "Pickup: Any", 15, INK))
    p.append(text(58, 578, "Language: Any", 15, INK))
    p.append(text(58, 612, "Escape closes. Focus returns", 14, INK))
    p.append(text(58, 636, "to the FILTER button.", 14, INK))
    mock_legend(p)
    mock_save("mock-05-dialog", p)


def mock_form_step1():
    p, w, h = mock_base("Register your item")
    p.append(text(16, 96, "Step 1 of 3", 16, INK, weight="bold"))
    p.append(rect(16, 112, 358, 20, LIGHT, rx=10))
    p.append(rect(16, 112, 119, 20, CARD, rx=10))
    p.append(form_box(16, 156, 358, 300, "ITEM 1 — TV",
                      ["What is wrong?", "Brand / make"]))
    p.append(pill(16, 500, 358, "NEXT"))
    p.append(text(16, 580, "What you should see: step 1 of 3,", 15, INK))
    p.append(text(16, 604, "item fields for the TV, and NEXT.", 15, INK))
    mock_legend(p)
    mock_save("mock-06-form-step1", p)


def mock_form_step3():
    p, w, h = mock_base("Register your item")
    p.append(text(16, 96, "Step 3 of 3", 16, INK, weight="bold"))
    p.append(rect(16, 112, 358, 20, LIGHT, rx=10))
    p.append(rect(16, 112, 358, 20, CARD, rx=10))
    p.append(form_box(16, 156, 358, 300, "YOUR DETAILS",
                      ["First and last name", "Email"]))
    p.append(text(32, 500, "Agreement checkbox: I agree to", 15, INK))
    p.append(text(32, 524, "the waiver and media release.", 15, INK))
    p.append(pill(16, 556, 358, "SUBMIT"))
    p.append(text(16, 640, "SUBMIT sends the form. A step with", 15, INK))
    p.append(text(16, 664, "no answer blocks NEXT.", 15, INK))
    mock_legend(p)
    mock_save("mock-07-form-step3", p)


def mock_events():
    p, w, h = mock_base("Repair events")
    p.append(list_box(16, 76, 358, 240, "FIXIT CLINIC EVENTS",
                      ["Sat 10am — Dorchester", "Sat 2pm — Roxbury"]))
    p.append(card_box(16, 336, 358, 200, "EVENT CARD  .evt",
                      ["Date flag, yellow", "Time and place",
                       "Links to provider page"]))
    p.append(text(16, 580, "A card with no date shows", 15, INK))
    p.append(text(16, 604, "\"Date to be set\", never blank.", 15, INK))
    mock_legend(p)
    mock_save("mock-08-events", p)


def mock_provider():
    p, w, h = mock_base("Fixit Clinic")
    p.append(card_box(16, 76, 358, 220, "PROVIDER DETAILS",
                      ["Open — in words", "Repairs TVs, jackets",
                       "Free  |  2 mi  |  4 stars"]))
    p.append(card_box(16, 316, 358, 150, "REFERRAL BOX  .refbox",
                      ["Referral link in full text", "and the count"]))
    p.append(pill(16, 500, 358, "REGISTER"))
    p.append(text(16, 580, "What you should see: details, open", 15, INK))
    p.append(text(16, 604, "in words, the referral box, REGISTER.", 15, INK))
    mock_legend(p)
    mock_save("mock-09-provider", p)


def mock_confirmation():
    p, w, h = mock_base("Thank you")
    p.append(card_box(16, 76, 358, 200, "SHARE CARD  .sh",
                      ["Estimated impact: $500 saved",
                       "Facebook / Instagram links", "QR code note"]))
    p.append(form_box(16, 296, 358, 180, "PROVIDE YOUR FEEDBACK",
                      ["Your message"]))
    p.append(pill(16, 516, 358, "SUBMIT"))
    p.append(text(16, 600, "Like or dislike, then a message,", 15, INK))
    p.append(text(16, 624, "then SUBMIT sends it once.", 15, INK))
    mock_legend(p)
    mock_save("mock-10-confirmation", p)


def mock_feedback_sent():
    p, w, h = mock_base("Thank you")
    p.append(card_box(16, 76, 358, 200, "SHARE CARD  .sh",
                      ["Estimated impact: $500 saved",
                       "Facebook / Instagram links", "QR code note"]))
    p.append(rect(16, 296, 358, 120, "#EAF4E4", rx=10, stroke=LIST, sw=3))
    p.append(text(32, 336, "Thank you. Your feedback", 17, INK, weight="bold"))
    p.append(text(32, 362, "was sent.", 17, INK, weight="bold"))
    p.append(text(32, 394, "The widget does not send twice.", 15, INK))
    p.append(text(16, 470, "What you should see: the sent state", 15, INK))
    p.append(text(16, 494, "in words, and no second SUBMIT.", 15, INK))
    mock_legend(p)
    mock_save("mock-11-feedback-sent", p)


def mock_empty():
    p, w, h = mock_base("Search results")
    p.append(text(16, 96, "Displaying 0 of 0", 16, INK, weight="bold"))
    p.append(rect(16, 116, 358, 130, WHITE, rx=10, stroke=GRAY, sw=2))
    p.append(text(32, 152, "No results match", 17, INK, weight="bold"))
    p.append(text(32, 180, "'lamp repair' near 02131.", 17, INK, weight="bold"))
    p.append(text(32, 212, "Try a wider distance.", 15, INK))
    p.append(pill(16, 280, 358, "EDIT SEARCH"))
    p.append(text(16, 360, "What you should see: a plain-word", 15, INK))
    p.append(text(16, 384, "sentence, never a blank area.", 15, INK))
    mock_legend(p)
    mock_save("mock-12-empty", p)


def main():
    os.makedirs(OUT, exist_ok=True)
    save("01-journey-map", journey_map(), 1600)
    save("02-build-map", build_map(), 1600)
    save("03-wiring-repair", wiring_repair(), 1600)
    save("04-wiring-results", wiring_results(), 1600)
    save("05-wiring-form", wiring_form(), 1600)
    save("06-wiring-events", wiring_events(), 1600)
    save("07-wiring-provider", wiring_provider(), 1600)
    save("08-wiring-confirmation", wiring_confirmation(), 1600)
    mock_repair_form()
    mock_estimator()
    mock_results()
    mock_selected()
    mock_dialog()
    mock_form_step1()
    mock_form_step3()
    mock_events()
    mock_provider()
    mock_confirmation()
    mock_feedback_sent()
    mock_empty()


if __name__ == "__main__":
    main()
