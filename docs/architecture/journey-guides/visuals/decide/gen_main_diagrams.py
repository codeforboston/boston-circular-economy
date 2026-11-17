"""Main diagrams for the Decide journey guide.

Four diagrams: journey map, build map, landing wiring, wizard wiring.
All use the fixed mapping in fleet_draw.py and carry its legend.
"""

import os
from fleet_draw import *

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1600


def footer(y, s):
    return text(48, y, s, 18, MID_GRAY)


def journey_map():
    h = 980
    p = []
    p.append(title_block(
        W, "CODE FOR BOSTON  |  CIRCULAR ECONOMY",
        "Decide journey map",
        "Landing, then three wizard steps, then one routing rule sends the resident on."))
    y0 = 210
    # Row of four screen frames, then the decision diamond.
    frames = [
        ("Landing  /", "Type the item", "Pick a card", "Press NEXT"),
        ("Step 1", "Condition", "Broken zip", "Hole or tear"),
        ("Step 2", "Intent", "One question", "One answer"),
        ("Step 3", "Location", "Where are you?", "Type the place"),
    ]
    fx, fw, fh, gap = 48, 240, 260, 20
    for i, (head, l1, l2, l3) in enumerate(frames):
        x = fx + i * (fw + gap)
        p.append(screen_frame(x, y0, fw, fh, head, 20))
        p.append(text(x + 16, y0 + 84, l1, 22, CHARLES, "bold"))
        p.append(text(x + 16, y0 + 122, l2, 19, BODY_GRAY))
        p.append(text(x + 16, y0 + 152, l3, 19, BODY_GRAY))
        if i < 3:
            p.append(arrow(x + fw + 2, y0 + fh // 2, x + fw + gap - 2,
                           y0 + fh // 2))
    # Arrow into the diamond.
    dx = fx + 4 * (fw + gap)
    p.append(arrow(dx - 2, y0 + fh // 2, dx + 26, y0 + fh // 2))
    # Decision diamond.
    p.append(diamond(dx + 26, y0 + 10, 220, 240,
                     ["Route by", "answers"], 22))
    # Four route cards stacked at the right.
    rx = dx + 264
    routes = ["Repair", "Reuse", "Recycle", "Maintain"]
    for i, r in enumerate(routes):
        ry = y0 + i * 68
        p.append(card(rx, ry, 200, 52, r, 22))
        p.append(arrow(dx + 246, y0 + 130, rx - 6, ry + 26))
    # Second row: what each part is, in mapping shapes.
    y1 = 540
    p.append(text(48, y1, "What each shape means on this map", 22,
                  CHARLES, "bold"))
    p.append(rect(48, y1 + 24, 300, 64, PALE_BODY, stroke=CHARLES, sw=2))
    p.append(rect(48, y1 + 24, 300, 22, CHARLES))
    p.append(text(48, y1 + 128, "Each screen is one frame.", 18, BODY_GRAY))
    p.append(text(48, y1 + 156, "Read it top to bottom.", 18, BODY_GRAY))
    p.append(diamond(420, y1 + 24, 180, 64, ["One rule"], 20))
    p.append(text(420, y1 + 128, "The diamond is the rule.", 18,
                  BODY_GRAY))
    p.append(text(420, y1 + 156, "It reads the answers.", 18, BODY_GRAY))
    p.append(form_box(680, y1 + 24, 300, 64))
    p.append(text(680, y1 + 128, "Each step asks one question.", 18,
                  BODY_GRAY))
    p.append(text(680, y1 + 156, "One group, one answer.", 18, BODY_GRAY))
    p.append(button_pill(1060, y1 + 24, 300, 64, "NEXT", 22))
    p.append(text(1060, y1 + 128, "NEXT is the primary action.", 18,
                  BODY_GRAY))
    p.append(text(1060, y1 + 156, "It moves the resident on.", 18,
                  BODY_GRAY))
    # Legend.
    p.append(line(48, 760, W - 48, 760, DIVIDER_GRAY, 2))
    p.append(text(48, 800, "Legend", 20, CHARLES, "bold"))
    p.append(legend_row(48, 824, W - 96, 17))
    p.append(footer(950, "Decide journey: landing, wizard, routing result."))
    return doc(W, h, "".join(p))


def build_map():
    h = 940
    p = []
    p.append(title_block(
        W, "CODE FOR BOSTON  |  CIRCULAR ECONOMY",
        "Build map: Decide, screen by screen",
        "One real journey, built in order. Each step ends with a check."))
    # Row 1: four stages.
    stages1 = [
        ("1", "Set up", "Tools, first file,", "first style"),
        ("2", "Shared shell", "Skip link, main,", "live region"),
        ("3", "Landing", "Hero, search, cards,", "FAQ, NEXT"),
        ("4", "Wizard", "Three steps,", "BACK and NEXT"),
    ]
    y0 = 210
    fw, fh, gap = 330, 220, 40
    for i, (num, head, l1, l2) in enumerate(stages1):
        x = 48 + i * (fw + gap)
        p.append(screen_frame(x, y0, fw, fh, "Stage " + num + "  |  " + head,
                              20))
        p.append(text(x + 16, y0 + 92, l1, 20, BODY_GRAY))
        p.append(text(x + 16, y0 + 126, l2, 20, BODY_GRAY))
        p.append(text(x + 16, y0 + 180, "Check before you move on.", 19,
                      OPTIMISTIC, "bold"))
        if i < 3:
            p.append(arrow(x + fw + 2, y0 + fh // 2, x + fw + gap - 2,
                           y0 + fh // 2))
    # Down arrow to row 2.
    p.append(arrow(48 + 3 * (fw + gap) + fw // 2, y0 + fh + 2,
                   48 + 3 * (fw + gap) + fw // 2, y0 + fh + 58))
    # Row 2: three stages, right to left flow continues under row 1.
    stages2 = [
        ("5", "Routing result", "One function,", "four routes"),
        ("6", "Final check", "Keyboard, screen reader,", "zoom, phone width"),
        ("7", "Working journey", "Landing to route,", "end to end"),
    ]
    y1 = y0 + fh + 60
    for i, (num, head, l1, l2) in enumerate(stages2):
        x = 48 + (2 - i) * (fw + gap)
        p.append(screen_frame(x, y1, fw, fh, "Stage " + num + "  |  " + head,
                              20))
        p.append(text(x + 16, y1 + 92, l1, 20, BODY_GRAY))
        p.append(text(x + 16, y1 + 126, l2, 20, BODY_GRAY))
        if i == 0:
            p.append(text(x + 16, y1 + 180, "The route word updates.", 19,
                          OPTIMISTIC, "bold"))
        elif i == 1:
            p.append(text(x + 16, y1 + 180, "Every walk passes.", 19,
                          OPTIMISTIC, "bold"))
        else:
            p.append(text(x + 16, y1 + 180, "The journey works.", 19,
                          OPTIMISTIC, "bold"))
        if i < 2:
            p.append(arrow(x - 2, y1 + fh // 2, x - gap + 2, y1 + fh // 2))
    # Legend.
    p.append(line(48, 780, W - 48, 780, DIVIDER_GRAY, 2))
    p.append(text(48, 820, "Legend", 20, CHARLES, "bold"))
    p.append(legend_row(48, 844, W - 96, 17))
    p.append(footer(910, "Build order: setup, shell, landing, wizard, "
                         "routing result, final check."))
    return doc(W, h, "".join(p))


def wiring_landing():
    h = 1040
    p = []
    p.append(title_block(
        W, "CODE FOR BOSTON  |  CIRCULAR ECONOMY",
        "Wiring: the landing page",
        "Components, state, and services on the landing page."))
    # Screen frame on the left.
    sx, sy, sw, sh = 48, 210, 860, 600
    p.append(screen_frame(sx, sy, sw, sh, "Landing  /", 22))
    inner = sx + 24
    # Hero band inside the frame.
    p.append(rect(inner, sy + 66, sw - 48, 74, CHARLES, rx=6))
    p.append(text(inner + 18, sy + 114, "HERO  .hro", 22, WHITE, "bold"))
    # Search form.
    p.append(form_box(inner, sy + 160, sw - 48, 96, "What is your item?"))
    # Service cards row.
    cy = sy + 276
    for i, label in enumerate(["Repair", "Reuse", "Recycle", "Join"]):
        p.append(card(inner + i * 205, cy, 185, 64, label, 20))
    # Icon cards row as a teal list.
    p.append(list_rows(inner, cy + 84, sw - 48, 30, 2, gap=6,
                       labels=["Donate  |  Recycle",
                               "Request Pickup  |  Swap"], size=18))
    # FAQ card.
    p.append(card(inner, cy + 170, sw - 48, 52, "FAQ  .ht-tab", 20))
    # NEXT pill.
    p.append(button_pill(inner, sy + sh - 84, sw - 48, 56, "NEXT  .btn", 22))
    # State and services panel on the right.
    bx = 960
    p.append(state_box(bx, sy, 592, 240, "STATE  —  component state",
                       ["item: text the resident types",
                        "FAQ open: one section at a time",
                        "service type: picked card"], 19))
    p.append(state_box(bx, sy + 270, 592, 250, "STATE  —  URL and services",
                       ["URL owns the item after NEXT:",
                        "  /decide?item=<item>",
                        "Service client: no call on this screen",
                        "Query client: nothing cached here"], 19))
    # Arrows from the frame to the state boxes.
    p.append(arrow(sx + sw + 2, sy + 210, bx - 4, sy + 120))
    p.append(arrow(sx + sw + 2, sy + 450, bx - 4, sy + 400))
    p.append(text(48, 860, "NEXT moves the item from component state to "
                  "the URL. The next page reads it from the link.", 20,
                  BODY_GRAY))
    p.append(line(48, 900, W - 48, 900, DIVIDER_GRAY, 2))
    p.append(text(48, 940, "Legend", 20, CHARLES, "bold"))
    p.append(legend_row(48, 964, W - 96, 17))
    p.append(footer(1010, "Landing wiring: presentational parts, "
                          "component state, URL state."))
    return doc(W, h, "".join(p))


def wiring_decide():
    h = 1060
    p = []
    p.append(title_block(
        W, "CODE FOR BOSTON  |  CIRCULAR ECONOMY",
        "Wiring: the Decide wizard",
        "Steps, state, and the routing rule on the wizard page."))
    # Wizard frame on the left.
    sx, sy, sw, sh = 48, 210, 700, 470
    p.append(screen_frame(sx, sy, sw, sh, "Decide  /decide", 22))
    inner = sx + 24
    # Progress bar.
    p.append(text(inner, sy + 84, "STEP 1 OF 3", 20, CHARLES, "bold"))
    p.append(rect(inner, sy + 96, sw - 48, 20, WHITE, stroke=CHARLES, sw=3))
    p.append(rect(inner, sy + 96, int((sw - 48) / 3), 20, OPTIMISTIC))
    # Question group as a form box.
    p.append(form_box(inner, sy + 140, sw - 48, 150,
                      "Question group"))
    # BACK and NEXT.
    p.append(rect(inner, sy + 320, 180, 52, WHITE, stroke=CHARLES, sw=3,
                  rx=26))
    p.append(text(inner + 90, sy + 354, "BACK", 20, OPTIMISTIC, "bold",
                  "middle"))
    p.append(button_pill(inner + sw - 48 - 180, sy + 320, 180, 52, "NEXT",
                         20))
    # Diamond in the middle.
    dx = 800
    p.append(arrow(sx + sw + 2, sy + 235, dx - 4, sy + 235))
    p.append(diamond(dx, sy + 115, 250, 240, ["Route by", "answers"], 22))
    # Route cards on the right.
    rx = 1100
    for i, r in enumerate(["Repair", "Reuse", "Recycle", "Maintain"]):
        ry = sy + 40 + i * 110
        p.append(card(rx, ry, 240, 72, r, 22))
        p.append(arrow(dx + 250, sy + 235, rx - 6, ry + 36))
    # State strip along the bottom.
    by = 730
    p.append(state_box(48, by, 480, 110, "STEP  —  component state",
                       ["step: 1, 2, or 3"], 19))
    p.append(state_box(560, by, 480, 110, "ANSWERS  —  form state",
                       ["condition, intent, location"], 19))
    p.append(state_box(1072, by, 480, 110, "ROUTE  —  derived",
                       ["routeByAnswers(answers)"], 19))
    p.append(text(48, 890, "The next step is a function of the answers so "
                  "far. The route is derived, never stored.", 20, BODY_GRAY))
    p.append(line(48, 920, W - 48, 920, DIVIDER_GRAY, 2))
    p.append(text(48, 960, "Legend", 20, CHARLES, "bold"))
    p.append(legend_row(48, 984, W - 96, 16))
    p.append(footer(1045, "Wizard wiring: step state, form state, "
                          "derived route."))
    return doc(W, h, "".join(p))


if __name__ == "__main__":
    jobs = [
        ("journey-map", journey_map()),
        ("build-map", build_map()),
        ("wiring-landing", wiring_landing()),
        ("wiring-decide", wiring_decide()),
    ]
    for name, svg in jobs:
        s, pg = write_pair(svg, os.path.join(HERE, name), W)
        print("wrote", s, pg)
