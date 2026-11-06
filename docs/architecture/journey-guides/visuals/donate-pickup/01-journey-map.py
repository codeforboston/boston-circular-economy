"""Journey map: Jason moves out, checks an item, books a pickup, finds a drop-off site."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 1600, 1000
p = svg_open(W, H)
rect(p, 0, 0, W, H, WHITE)
title_block(p, W, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
            "Donate and pickup: the journey Jason takes",
            "Jason moves out. He checks an item, books a pickup, and finds a drop-off site on foot or by transit.")

y, h = 190, 210
card(p, 60, y, 215, h, "1. Jason moves out", ["Bulky items", "to give away", "No car"])
arrow(p, 275, y + 105, 305, y + 105)
card(p, 305, y, 215, h, "2. Checker", ["Names an item", "Answer in words", "Yes, No, Maybe"])
arrow(p, 520, y + 105, 530, y + 105)
diamond(p, 640, y + 105, 112, 96, ["Will they", "take it?"])
arrow(p, 752, y + 105, 775, y + 105)
card(p, 775, y, 215, h, "3. Scheduler", ["Size, day, slot", "Summary", "in words"])
arrow(p, 990, y + 105, 1020, y + 105)
card(p, 1020, y, 215, h, "4. Locator", ["Walking, transit", "or car", "Map and list", "in sync"])
arrow(p, 1235, y + 105, 1265, y + 105)
state_box(p, 1265, y, 275, h, "Done", ["Item leaves", "the home"])

para(p, 640, 452, "Yes, No, or Maybe, in words, with the reason.", 17, BODY, 46, SERIF, anchor="middle")

state_box(p, 60, 490, 1480, 110, "No-car access is the point",
          ["Six of nine residents move bulky items without a car.",
           "Walking and transit filters sit on the locator, not after it."], body_chars=95)
frame_box(p, 60, 630, 1480, 130, "Persona: Jason, move-out journey",
          ["Trigger: bulky items are hard to give away. Plan: donate items people want.",
           "Worry: penalties for poor-condition items."], body_size=17, body_chars=95)

legend(p, W, 850)
p += svg_close()
render_svg(p, os.path.join(os.path.dirname(os.path.abspath(__file__)), "01-journey-map.png"), W, H)
print("01-journey-map done")
