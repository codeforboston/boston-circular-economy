"""Wiring diagram: the pickup scheduler."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 1600, 1000
p = svg_open(W, H)
rect(p, 0, 0, W, H, WHITE)
title_block(p, W, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
            "Wiring: the pickup scheduler",
            "Size and day go in. The server returns the open slots. The summary reads the booking back in words.")


def elbow(p, pts, color=CHARLES):
    s = " ".join("%.0f,%.0f" % (x, y) for x, y in pts)
    p.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="3" />' % (s, color))
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    if x2 > x1:
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />' % (x2, y2, x2 - 14, y2 - 7, x2 - 14, y2 + 7, color))
    elif y2 > y1:
        p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" fill="%s" />' % (x2, y2, x2 - 7, y2 - 14, x2 + 7, y2 - 14, color))


y = 190
rect(p, 60, y, 300, 210, LIGHTBLUE, rx=4)
text(p, 76, y + 30, "Size and day", 17, CHARLES, SANS, "bold")
text(p, 76, y + 60, "Item size radios", 14, CHARLES, SANS, "bold")
for i, cx in enumerate((88, 168, 248)):
    p.append('<circle cx="%d" cy="%d" r="11" fill="%s" stroke="%s" stroke-width="3" />' % (cx, y + 84, WHITE, CHARLES))
    if i == 1:
        p.append('<circle cx="%d" cy="%d" r="5" fill="%s" />' % (cx, y + 84, OPT))
text(p, 76, y + 124, "Day field", 14, CHARLES, SANS, "bold")
rect(p, 76, y + 132, 268, 30, WHITE, rx=2)
arrow(p, 360, y + 105, 410, y + 105)
state_box(p, 410, y, 250, 210, "Form state", ["size", "day", "slot"], body_chars=22)
arrow(p, 660, y + 105, 710, y + 105)
state_box(p, 710, y, 300, 210, "Hook and server", ["usePickupSlots(size, day)", "Server returns", "the open slots"], body_chars=26)
arrow(p, 1010, y + 105, 1040, y + 105)
diamond(p, 1160, y + 105, 120, 95, ["Slots open", "that day?"])

text(p, 60, 500, "YES — slots show", 17, TEAL, SANS, "bold")
list_rows(p, 60, 520, 500, ["10:00 AM", "11:00 AM", "1:00 PM"])
card(p, 60, 700, 500, 76, "Pickup: size, day, slot.", [], title_size=18)
text(p, 1000, 500, "NO — no slots", 17, DARKRED, SANS, "bold")
state_box(p, 1000, 520, 540, 150, "No open slots", ["No open slots that day.", "Pick another day.", "Never a blank area."], body_chars=44)

elbow(p, [(1160, 390), (1160, 470), (310, 470), (310, 500)])
elbow(p, [(1160, 390), (1160, 470), (1270, 470), (1270, 500)])

para(p, 800, 810, "The page never invents a slot. The summary is derived, never stored.",
     18, BODY, 80, SERIF, anchor="middle")

legend(p, W, 850)
p += svg_close()
render_svg(p, os.path.join(os.path.dirname(os.path.abspath(__file__)), "04-wiring-pickup-scheduler.png"), W, H)
print("04-wiring-pickup-scheduler done")
