"""Wiring diagram: the acceptance checker."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 1600, 1000
p = svg_open(W, H)
rect(p, 0, 0, W, H, WHITE)
title_block(p, W, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
            "Wiring: the acceptance checker",
            "The form takes the item. The rules answer. The answer is derived, never stored.")

y = 200
rect(p, 60, y, 300, 220, LIGHTBLUE, rx=4)
text(p, 76, y + 30, "Item form", 17, CHARLES, SANS, "bold")
text(p, 76, y + 58, "What is your item?", 14, CHARLES, SANS, "bold")
rect(p, 76, y + 66, 268, 30, WHITE, rx=2)
button_shape(p, 76, y + 116, 130, 44, "CHECK", size=16)
arrow(p, 360, y + 110, 420, y + 110)
state_box(p, 420, y, 250, 220, "Form state", ["item: the text", "Jason typed", "One owner only"], body_chars=22)
arrow(p, 670, y + 110, 730, y + 110)
diamond(p, 840, y + 110, 115, 100, ["Rule", "answers?"])
arrow(p, 955, y + 110, 1015, y + 110)
card(p, 1015, y, 525, 64, "Yes — the reason", [], title_size=18)
card(p, 1015, y + 76, 525, 64, "No — the reason", [], title_size=18)
card(p, 1015, y + 152, 525, 64, "Maybe — the reason", [], title_size=18)

para(p, 1250, 452, "First rule that answers wins.", 17, BODY, 34, SERIF, anchor="middle")

state_box(p, 60, 500, 520, 200, "Answer: derived, never stored",
          ["Computed from the rules.", "A maybe stays a maybe", "until a human answers."], body_chars=40)
state_box(p, 640, 500, 420, 200, "Provider rules — props",
          ["One function per provider.", "The page shows the answer.", "A rule change needs", "no page change."], body_chars=34)
arrow(p, 850, 500, 840, 420)
frame_box(p, 1100, 500, 440, 200, "Live region",
          ["Announces the answer", "in words.", "Screen reader hears it."], body_size=16, body_chars=34)

para(p, 800, 790, "Strategy: one function per provider rule. The checker picks the rules for that provider.",
     18, BODY, 95, SERIF, anchor="middle")

legend(p, W, 850)
p += svg_close()
render_svg(p, os.path.join(os.path.dirname(os.path.abspath(__file__)), "03-wiring-acceptance-checker.png"), W, H)
print("03-wiring-acceptance-checker done")
