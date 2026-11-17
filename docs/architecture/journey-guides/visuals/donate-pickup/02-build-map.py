"""Build map: shell, service, and the three parts in build order, each with its closing check."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viz_common import *

W, H = 1600, 1000
p = svg_open(W, H)
rect(p, 0, 0, W, H, WHITE)
title_block(p, W, "CODE FOR BOSTON  —  CIRCULAR ECONOMY",
            "Donate and pickup: the build order",
            "Build the shell first, then the service, then the three parts in the order Jason sees them.")

frames = [
    (60, "1. Shared shell", ["__root.tsx", "Skip link", "Live region"]),
    (350, "2. Search query", ["search.ts", "searchQueryOptions", "One API call"]),
    (640, "3. Checker", ["AcceptanceChecker.tsx", "W-10", "Yes, No, Maybe"]),
    (930, "4. Scheduler", ["PickupScheduler.tsx", "W-03", "Size, day, slot"]),
    (1220, "5. Locator", ["DropOffLocator.tsx", "W-13", "Walking, transit, car"]),
]
y = 180
for x, header, body in frames:
    frame_box(p, x, y, 260, 260, header, body, body_size=15, body_chars=24)
for x in (320, 610, 900, 1190):
    arrow(p, x, y + 130, x + 30, y + 130)

checks = [
    (190, ["Check:", "skip link works"]),
    (480, ["Check:", "loading", "words show"]),
    (770, ["Check:", "answer in words"]),
    (1060, ["Check:", "slot from server"]),
    (1350, ["Check:", "list works,", "map failed"]),
]
for cx, lines in checks:
    arrow(p, cx, y + 260, cx, 505)
    diamond(p, cx, 560, 100, 56, lines, size=14)

state_box(p, 60, 660, 1480, 120, "The same eight steps on every part",
          ["1 Page model   2 Widgets   3 Fleet classes   4 Page tree   5 Wire state   6 States   7 Access   8 Verify"],
          body_size=18, body_chars=110)

legend(p, W, 850)
p += svg_close()
render_svg(p, os.path.join(os.path.dirname(os.path.abspath(__file__)), "02-build-map.png"), W, H)
print("02-build-map done")
