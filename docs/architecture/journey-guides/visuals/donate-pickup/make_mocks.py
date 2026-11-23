"""Phone-width screen pictures: one per code block in the guide.

Each picture is a 390-wide phone screen in the fixed visual language,
with the mapping in its legend. Canvas 390 x 800.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 390, 800
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mocks")
os.makedirs(OUT, exist_ok=True)

LEG = [("card", "Card"), ("button", "Primary button"), ("list", "List"),
       ("form", "Form"), ("decision", "Decision gate"), ("frame", "Screen frame"),
       ("state", "State / service")]


def small_swatch(p, kind, x, y):
    if kind == "card":
        rect(p, x, y, 24, 14, OPT, rx=3)
    elif kind == "button":
        rect(p, x, y, 24, 14, RED, rx=7)
    elif kind == "list":
        for i in range(3):
            rect(p, x, y + i * 5, 24, 3, TEAL, rx=1)
    elif kind == "form":
        rect(p, x, y, 24, 14, LIGHTBLUE, rx=1)
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" />' % (x + 3, y + 5, x + 21, y + 5, WHITE))
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" />' % (x + 3, y + 10, x + 17, y + 10, WHITE))
    elif kind == "decision":
        p.append('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="%s" stroke="%s" stroke-width="1" />'
                 % (x + 12, y, x + 24, y + 7, x + 12, y + 14, x, y + 7, GOLD, CHARLES))
    elif kind == "frame":
        rect(p, x, y, 24, 14, PALE, stroke=CHARLES, sw=1)
        rect(p, x, y, 24, 5, CHARLES)
    elif kind == "state":
        rect(p, x, y, 24, 14, NAVY, rx=1)
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" />' % (x + 3, y + 5, x + 21, y + 5, PALEBLUE))
        p.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.5" />' % (x + 3, y + 10, x + 17, y + 10, PALEBLUE))


def base(title):
    p = svg_open(W, H)
    rect(p, 0, 0, W, H, WHITE)
    rect(p, 10, 10, 370, 650, PALE, stroke=CHARLES, sw=2)
    rect(p, 10, 10, 370, 46, CHARLES)
    text(p, 26, 39, title, 16, WHITE, SANS, "bold")
    return p


def legend_strip(p):
    rect(p, 10, 672, 370, 118, WHITE, stroke=BORDER, sw=1)
    text(p, 22, 694, "LEGEND", 11, CHARLES, SANS, "bold", spacing="1")
    for i, (kind, label) in enumerate(LEG):
        cx = 22 + (i % 2) * 185
        cy = 704 + (i // 2) * 21
        small_swatch(p, kind, cx, cy)
        text(p, cx + 32, cy + 11, label, 11, BODY, SANS)


def finish(p, name):
    legend_strip(p)
    p += svg_close()
    render_svg(p, os.path.join(OUT, name + ".png"), W, H)
    print(name, "done")


def radio(p, x, y, label, checked):
    p.append('<circle cx="%.0f" cy="%.0f" r="11" fill="%s" stroke="%s" stroke-width="3" />' % (x + 11, y + 11, WHITE, CHARLES))
    if checked:
        p.append('<circle cx="%.0f" cy="%.0f" r="5" fill="%s" />' % (x + 11, y + 11, OPT))
    text(p, x + 30, y + 16, label, 15, CHARLES, SANS)


def marker_dot(p, cx, cy, n, fill=TEAL):
    p.append('<circle cx="%.0f" cy="%.0f" r="13" fill="%s" stroke="%s" stroke-width="2" />' % (cx, cy, fill, WHITE))
    text(p, cx, cy + 5, str(n), 13, WHITE, SANS, "bold", "middle")


# 01 — first page
p = base("My first page")
text(p, 26, 96, "Hello, Boston", 24, "#000000", SANS, "bold")
para(p, 26, 130, "This is my first webpage.", 16, BODY, 40, SERIF)
rect(p, 26, 150, 110, 40, "#E0E0E0", rx=4)
text(p, 81, 176, "Press me", 15, CHARLES, SANS, "bold", "middle")
finish(p, "mock-01-hello")

# 02 — first page, blue heading
p = base("My first page")
text(p, 26, 96, "Hello, Boston", 24, OPT, SANS, "bold")
para(p, 26, 130, "This is my first webpage.", 16, BODY, 40, SERIF)
rect(p, 26, 150, 110, 40, "#E0E0E0", rx=4)
text(p, 81, 176, "Press me", 15, CHARLES, SANS, "bold", "middle")
finish(p, "mock-02-hello-blue")

# 03 — clean build in the terminal
p = base("Terminal")
rect(p, 26, 72, 338, 170, NAVY, rx=4)
text(p, 42, 108, "$ tsc -b && vite build", 15, PALEBLUE, "Courier New, monospace")
text(p, 42, 140, "Type check passed.", 15, PALEBLUE, "Courier New, monospace")
text(p, 42, 172, "Build done.", 15, PALEBLUE, "Courier New, monospace")
text(p, 42, 204, "Back at the prompt.", 15, PALEBLUE, "Courier New, monospace")
para(p, 26, 280, "No error lines. The app builds.", 16, BODY, 40, SERIF)
finish(p, "mock-03-build-ok")

# 04 — shared shell, skip link shown
p = base("Donate and pickup")
rect(p, 10, 56, 370, 40, CHARLES, stroke=OPT, sw=3)
text(p, 26, 82, "Skip to main content", 15, WHITE, SANS, "bold")
para(p, 26, 140, "Main content starts here.", 16, BODY, 40, SERIF)
para(p, 26, 175, "One Tab press showed the skip link.", 16, BODY, 40, SERIF)
finish(p, "mock-04-shell")

# 05 — loading state
p = base("Donate and pickup")
rect(p, 26, 72, 338, 120, NAVY, rx=4)
text(p, 42, 108, "Loading results…", 16, PALEBLUE, SERIF)
rect(p, 42, 128, 306, 20, WHITE, rx=2)
rect(p, 42, 128, 184, 20, OPT, rx=2)
para(p, 26, 230, "The list appears when the API answers.", 16, BODY, 40, SERIF)
finish(p, "mock-05-loading")

# 06 — checker start
p = base("Donate — will they take it?")
rect(p, 26, 72, 338, 190, LIGHTBLUE, rx=4)
text(p, 42, 104, "WHAT IS YOUR ITEM?", 14, CHARLES, SANS, "bold")
rect(p, 42, 116, 306, 44, WHITE, rx=2)
text(p, 52, 144, "sofa", 16, CHARLES, SERIF)
button_shape(p, 42, 180, 130, 48, "CHECK", size=16)
para(p, 26, 300, "No answer yet.", 16, BODY, 40, SERIF)
finish(p, "mock-06-checker-start")

# 07 — checker yes
p = base("Donate — will they take it?")
rect(p, 26, 72, 338, 150, LIGHTBLUE, rx=4)
text(p, 42, 104, "WHAT IS YOUR ITEM?", 14, CHARLES, SANS, "bold")
rect(p, 42, 116, 306, 44, WHITE, rx=2)
text(p, 52, 144, "sofa", 16, CHARLES, SERIF)
button_shape(p, 42, 172, 130, 44, "CHECK", size=16)
card(p, 26, 244, 338, 96, "Yes", ["The provider takes sofas", "in good shape."], title_size=18, body_size=15, body_chars=34)
finish(p, "mock-07-checker-yes")

# 08 — checker maybe
p = base("Donate — will they take it?")
rect(p, 26, 72, 338, 150, LIGHTBLUE, rx=4)
text(p, 42, 104, "WHAT IS YOUR ITEM?", 14, CHARLES, SANS, "bold")
rect(p, 42, 116, 306, 44, WHITE, rx=2)
text(p, 52, 144, "old chair", 16, CHARLES, SERIF)
button_shape(p, 42, 172, 130, 44, "CHECK", size=16)
rect(p, 26, 244, 338, 96, GOLD, rx=10)
text(p, 44, 278, "Maybe", 18, CHARLES, SANS, "bold")
para(p, 44, 306, "The provider must see the item first.", 15, CHARLES, 34, SERIF)
finish(p, "mock-08-checker-maybe")

# 09 — checker error
p = base("Donate — will they take it?")
rect(p, 26, 72, 338, 190, LIGHTBLUE, rx=4)
text(p, 42, 104, "WHAT IS YOUR ITEM?", 14, CHARLES, SANS, "bold")
rect(p, 42, 116, 306, 44, WHITE, stroke=RED, sw=3, rx=2)
button_shape(p, 42, 180, 130, 48, "CHECK", size=16)
text(p, 26, 300, "Name the item first.", 16, DARKRED, SERIF)
finish(p, "mock-09-checker-error")

# 10 — scheduler size and day
p = base("Donate — book a pickup")
rect(p, 26, 72, 338, 250, LIGHTBLUE, rx=4)
text(p, 42, 104, "ITEM SIZE", 14, CHARLES, SANS, "bold")
radio(p, 42, 118, "Small", False)
radio(p, 140, 118, "Medium", True)
radio(p, 252, 118, "Large", False)
text(p, 42, 176, "DAY", 14, CHARLES, SANS, "bold")
rect(p, 42, 188, 306, 44, WHITE, rx=2)
text(p, 52, 216, "Pick a day", 16, MIDGREY, SERIF)
para(p, 26, 360, "No slots yet. Pick a day first.", 16, BODY, 40, SERIF)
finish(p, "mock-10-scheduler-size")

# 11 — scheduler slots
p = base("Donate — book a pickup")
rect(p, 26, 72, 338, 250, LIGHTBLUE, rx=4)
text(p, 42, 104, "ITEM SIZE", 14, CHARLES, SANS, "bold")
radio(p, 42, 118, "Small", False)
radio(p, 140, 118, "Medium", True)
radio(p, 252, 118, "Large", False)
text(p, 42, 176, "DAY", 14, CHARLES, SANS, "bold")
rect(p, 42, 188, 306, 44, WHITE, rx=2)
text(p, 52, 216, "2026-11-12", 16, CHARLES, SERIF)
rect(p, 26, 344, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=4)
text(p, 76, 372, "10:00 AM", 14, CHARLES, SANS, "bold", "middle")
rect(p, 138, 344, 100, 44, OPT, rx=4)
text(p, 188, 372, "11:00 AM", 14, WHITE, SANS, "bold", "middle")
rect(p, 250, 344, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=4)
text(p, 300, 372, "1:00 PM", 14, CHARLES, SANS, "bold", "middle")
finish(p, "mock-11-scheduler-slots")

# 12 — scheduler summary
p = base("Donate — book a pickup")
rect(p, 26, 72, 338, 250, LIGHTBLUE, rx=4)
text(p, 42, 104, "ITEM SIZE", 14, CHARLES, SANS, "bold")
radio(p, 42, 118, "Small", False)
radio(p, 140, 118, "Medium", True)
radio(p, 252, 118, "Large", False)
text(p, 42, 176, "DAY", 14, CHARLES, SANS, "bold")
rect(p, 42, 188, 306, 44, WHITE, rx=2)
text(p, 52, 216, "2026-11-12", 16, CHARLES, SERIF)
rect(p, 26, 344, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=4)
text(p, 76, 372, "10:00 AM", 14, CHARLES, SANS, "bold", "middle")
rect(p, 138, 344, 100, 44, OPT, rx=4)
text(p, 188, 372, "11:00 AM", 14, WHITE, SANS, "bold", "middle")
rect(p, 250, 344, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=4)
text(p, 300, 372, "1:00 PM", 14, CHARLES, SANS, "bold", "middle")
para(p, 26, 430, "Pickup: medium, 2026-11-12, 11:00 AM.", 16, CHARLES, 38, SERIF)
finish(p, "mock-12-scheduler-summary")

# 13 — locator walking
p = base("Donate — drop-off sites")
rect(p, 26, 72, 110, 44, OPT, rx=22)
text(p, 81, 100, "Walking", 14, WHITE, SANS, "bold", "middle")
rect(p, 146, 72, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 196, 100, "Transit", 14, CHARLES, SANS, "bold", "middle")
rect(p, 256, 72, 80, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 296, 100, "Car", 14, CHARLES, SANS, "bold", "middle")
rect(p, 26, 132, 338, 150, "#BFD9EE", rx=4)
marker_dot(p, 90, 180, 1)
marker_dot(p, 200, 220, 2)
marker_dot(p, 300, 170, 3)
list_rows(p, 26, 300, 338, ["Site A — 0.4 mi on foot", "Site B — 0.8 mi on foot"], row_h=44, size=15)
finish(p, "mock-13-locator-walking")

# 14 — locator selected
p = base("Donate — drop-off sites")
rect(p, 26, 72, 110, 44, OPT, rx=22)
text(p, 81, 100, "Walking", 14, WHITE, SANS, "bold", "middle")
rect(p, 146, 72, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 196, 100, "Transit", 14, CHARLES, SANS, "bold", "middle")
rect(p, 256, 72, 80, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 296, 100, "Car", 14, CHARLES, SANS, "bold", "middle")
rect(p, 26, 132, 338, 150, "#BFD9EE", rx=4)
marker_dot(p, 90, 180, 1, fill=CHARLES)
marker_dot(p, 200, 220, 2)
marker_dot(p, 300, 170, 3)
rect(p, 26, 300, 338, 44, TEAL, rx=6, stroke=CHARLES, sw=3)
text(p, 42, 328, "Site A — 0.4 mi on foot", 15, WHITE, SANS, "bold")
rect(p, 26, 352, 338, 44, TEAL, rx=6)
text(p, 42, 380, "Site B — 0.8 mi on foot", 15, WHITE, SANS, "bold")
finish(p, "mock-14-locator-selected")

# 15 — locator map failed
p = base("Donate — drop-off sites")
rect(p, 26, 72, 110, 44, OPT, rx=22)
text(p, 81, 100, "Walking", 14, WHITE, SANS, "bold", "middle")
rect(p, 146, 72, 100, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 196, 100, "Transit", 14, CHARLES, SANS, "bold", "middle")
rect(p, 256, 72, 80, 44, WHITE, stroke=CHARLES, sw=2, rx=22)
text(p, 296, 100, "Car", 14, CHARLES, SANS, "bold", "middle")
rect(p, 26, 132, 338, 110, WHITE, stroke=BORDER, sw=1, rx=4)
para(p, 42, 168, "The map did not load.", 16, BODY, 34, SERIF)
para(p, 42, 196, "The list below still works.", 16, BODY, 34, SERIF)
list_rows(p, 26, 260, 338, ["Site A — 0.4 mi on foot", "Site B — 0.8 mi on foot", "Site C — list only"], row_h=44, size=15)
finish(p, "mock-15-locator-map-failed")
