"""Wiring diagram: the drop-off locator."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 1600, 1000
p = svg_open(W, H)
rect(p, 0, 0, W, H, WHITE)
title_block(p, W, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
            "Wiring: the drop-off locator",
            "Travel chips pick one mode. One function per mode filters the sites. The page links the list and the map.")

text(p, 60, 210, "Travel mode — one chip at a time", 17, CHARLES, SANS, "bold")
rect(p, 60, 230, 150, 54, OPT, rx=27)
text(p, 135, 264, "Walking", 17, WHITE, SANS, "bold", "middle")
rect(p, 225, 230, 150, 54, WHITE, stroke=CHARLES, sw=2, rx=27)
text(p, 300, 264, "Transit", 17, CHARLES, SANS, "bold", "middle")
rect(p, 390, 230, 130, 54, WHITE, stroke=CHARLES, sw=2, rx=27)
text(p, 455, 264, "Car", 17, CHARLES, SANS, "bold", "middle")
arrow(p, 520, 257, 580, 257)
state_box(p, 580, 190, 330, 170, "Strategy filter", ["byTravelMode(mode)", "One function per mode", "Smaller list out"], body_chars=28)
arrow(p, 910, 257, 970, 257)
frame_box(p, 970, 190, 570, 170, "Page mediates",
          ["selectedId: string | null", "One owner of the choice"], body_size=16, body_chars=44)

frame_box(p, 60, 420, 700, 230, "SearchMap — reused",
          ["One marker per site.", "Markers are buttons.", "Centre [42.36, -71.06]."], body_size=16, body_chars=52)
text(p, 820, 448, "List — same sites, same order", 17, CHARLES, SANS, "bold")
list_rows(p, 820, 470, 720, ["Site A — 0.4 mi on foot", "Site B — 0.8 mi on foot", "Site C — list only, no map spot"])
arrow(p, 760, 520, 820, 520)
arrow(p, 820, 560, 760, 560)
para(p, 800, 700, "A selection on one side updates both sides. The page passes selectedId down to both.",
     18, BODY, 95, SERIF, anchor="middle")

diamond(p, 350, 780, 120, 52, ["Site has", "coordinates?"], size=15)
arrow(p, 470, 780, 540, 780)
text(p, 560, 772, "Yes — plot the marker", 17, TEAL, SANS, "bold")
text(p, 560, 806, "No — list only, never a false spot", 17, DARKRED, SANS, "bold")

legend(p, W, 850)
p += svg_close()
render_svg(p, os.path.join(os.path.dirname(os.path.abspath(__file__)), "05-wiring-drop-off-locator.png"), W, H)
print("05-wiring-drop-off-locator done")
