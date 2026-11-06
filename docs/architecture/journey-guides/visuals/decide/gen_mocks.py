"""Phone-width screen mocks for the Decide journey guide.

One small SVG per build step, showing what the code just made.
Each mock uses the fixed mapping in fleet_draw.py and carries its
legend strip at the bottom.
"""

import os
from fleet_draw import *

HERE = os.path.dirname(os.path.abspath(__file__))
W = 420
FX, FW = 15, 390
IX = FX + 16          # inner content x
IW = FW - 32          # inner content width


def radio(x, y, r, checked):
    p = [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{WHITE}" '
         f'stroke="{CHARLES}" stroke-width="3"/>']
    if checked:
        p.append(f'<circle cx="{x}" cy="{y}" r="{r - 7}" '
                 f'fill="{OPTIMISTIC}"/>')
        p.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{WHITE}"/>')
    return "".join(p)


def progress(x, y, w, frac):
    return (rect(x, y, w, 20, WHITE, stroke=CHARLES, sw=3)
            + rect(x, y, int(w * frac), 20, OPTIMISTIC))


def grey_line(x, y, w):
    return rect(x, y, w, 9, DIVIDER_GRAY, rx=4)


def mock(name, header, frame_h, content):
    """content(ix, iy) returns SVG for the frame body at top iy."""
    lh = 4 * 30
    total = 15 + frame_h + 16 + lh + 12
    p = [screen_frame(FX, 15, FW, frame_h, header, 20)]
    p.append(content(IX, 15 + 46))
    p.append(line(FX, 15 + frame_h + 8, FX + FW, 15 + frame_h + 8,
                  DIVIDER_GRAY, 1))
    p.append(legend_block(FX, 15 + frame_h + 16, FW, 13))
    svg = doc(W, total, "".join(p))
    s, pg = write_pair(svg, os.path.join(HERE, name), W)
    print("wrote", s, pg)


def c_hello(ix, iy):
    p = [text(ix, iy + 52, "Hello, Boston", 32, OPTIMISTIC, "bold"),
         text(ix, iy + 92, "This is my first webpage.", 19, BODY_GRAY),
         button_pill(ix, iy + 120, 150, 48, "Press me", 20)]
    return "".join(p)


def c_shell(ix, iy):
    p = [rect(ix, iy + 16, IW, 44, WHITE, stroke=OPTIMISTIC, sw=2),
         text(ix + 14, iy + 45, "Skip to main content", 19, OPTIMISTIC,
              "bold"),
         text(ix, iy + 96, "Main content", 19, CHARLES, "bold"),
         grey_line(ix, iy + 116, IW),
         grey_line(ix, iy + 138, int(IW * 0.7)),
         grey_line(ix, iy + 160, int(IW * 0.85))]
    return "".join(p)


def c_hero(ix, iy):
    p = [rect(ix, iy + 16, IW, 150, CHARLES, rx=6),
         text(ix + 18, iy + 66, "GIVE YOUR THINGS", 26, WHITE, "bold"),
         text(ix + 18, iy + 100, "A NEXT LIFE", 26, WHITE, "bold"),
         text(ix + 18, iy + 138, "Repair it, share it, or pass it on.",
              18, WHITE, "normal"),
         grey_line(ix, iy + 186, IW),
         grey_line(ix, iy + 208, int(IW * 0.6))]
    return "".join(p)


def c_search(ix, iy):
    p = [text(ix, iy + 40, "What is your item?", 20, CHARLES, "bold"),
         form_box(ix, iy + 56, IW, 92),
         text(ix, iy + 190, "Matches", 18, CHARLES, "bold")]
    p.append(list_rows(ix, iy + 204, IW, 40, 2, gap=8,
                       labels=["TV", "Jacket"], size=19))
    return "".join(p)


def c_cards(ix, iy):
    p = []
    labels = ["Repair", "Reuse", "Recycle", "Join"]
    for i, label in enumerate(labels):
        x = ix + (i % 2) * (IW // 2 + 8)
        y = iy + 16 + (i // 2) * 128
        p.append(card(x, y, IW // 2 - 4, 112, label, 22))
    return "".join(p)


def c_icons(ix, iy):
    p = []
    labels = ["Donate", "Recycle", "Request Pickup", "Swap"]
    for i, label in enumerate(labels):
        x = ix + (i % 2) * (IW // 2 + 8)
        y = iy + 16 + (i // 2) * 128
        p.append(rect(x, y, IW // 2 - 4, 112, WHITE, stroke=CHARLES, sw=2,
                      rx=6))
        p.append(f'<circle cx="{x + (IW // 2 - 4) // 2}" cy="{y + 38}" '
                 f'r="24" fill="{WHITE}" stroke="{OPTIMISTIC}" '
                 f'stroke-width="3"/>')
        p.append(text(x + (IW // 2 - 4) // 2, y + 92, label, 16, CHARLES,
                      "bold", "middle"))
    return "".join(p)


def c_faq(ix, iy):
    p = [rect(ix, iy + 16, IW, 48, CHARLES),
         text(ix + 14, iy + 47, "How does repair work?", 19, WHITE,
              "bold"),
         text(ix + IW - 14, iy + 47, "hide", 17, WHITE, "normal", "end"),
         rect(ix, iy + 64, IW, 84, WHITE, stroke=BORDER_GRAY, sw=1),
         grey_line(ix + 14, iy + 88, IW - 28),
         grey_line(ix + 14, iy + 112, int((IW - 28) * 0.7)),
         rect(ix, iy + 164, IW, 48, BG_GRAY),
         text(ix + 14, iy + 195, "Where is the next clinic?", 19,
              CHARLES, "bold"),
         rect(ix, iy + 228, IW, 48, BG_GRAY),
         text(ix + 14, iy + 259, "What does it cost?", 19, CHARLES,
              "bold")]
    return "".join(p)


def c_landing_done(ix, iy):
    p = [rect(ix, iy + 16, IW, 84, CHARLES, rx=6),
         text(ix + 16, iy + 52, "GIVE YOUR THINGS", 22, WHITE, "bold"),
         text(ix + 16, iy + 80, "A NEXT LIFE", 22, WHITE, "bold"),
         form_box(ix, iy + 116, IW, 84, "What is your item?", 17)]
    p.append(card(ix, iy + 216, (IW - 8) // 2, 72, "Repair", 20))
    p.append(card(ix + (IW - 8) // 2 + 8, iy + 216, (IW - 8) // 2, 72,
                  "Reuse", 20))
    p.append(button_pill(ix, iy + 304, IW, 56, "NEXT", 22))
    return "".join(p)


def wizard_head(ix, iy, step, frac):
    p = [text(ix, iy + 34, f"Step {step} of 3", 20, CHARLES, "bold"),
         progress(ix, iy + 48, IW, frac)]
    return p


def c_wizard(ix, iy):
    p = wizard_head(ix, iy, 1, 1 / 3)
    p.append(form_box(ix, iy + 92, IW, 170, "Question group", 18))
    p.append(radio(ix + 22, iy + 196, 14, False))
    p.append(radio(ix + 22, iy + 232, 14, False))
    return "".join(p)


def c_condition(ix, iy):
    p = wizard_head(ix, iy, 1, 1 / 3)
    p.append(text(ix, iy + 116, "What is the condition?", 21, CHARLES,
                  "bold"))
    p.append(radio(ix + 22, iy + 156, 14, True))
    p.append(text(ix + 48, iy + 163, "Broken zip", 19, CHARLES))
    p.append(radio(ix + 22, iy + 200, 14, False))
    p.append(text(ix + 48, iy + 207, "Hole or tear", 19, CHARLES))
    p.append(button_pill(ix, iy + 236, 150, 52, "NEXT", 20))
    return "".join(p)


def c_intent(ix, iy):
    p = wizard_head(ix, iy, 2, 2 / 3)
    p.append(text(ix, iy + 116, "What do you want to do?", 21, CHARLES,
                  "bold"))
    p.append(radio(ix + 22, iy + 156, 14, False))
    p.append(grey_line(ix + 48, iy + 152, 180))
    p.append(radio(ix + 22, iy + 200, 14, False))
    p.append(grey_line(ix + 48, iy + 196, 140))
    p.append(text(ix, iy + 252,
                  "Option words come from the decision matrix.",
                  15, BODY_GRAY))
    p.append(button_pill(ix, iy + 272, 150, 52, "NEXT", 20))
    return "".join(p)


def c_location(ix, iy):
    p = wizard_head(ix, iy, 3, 1.0)
    p.append(form_box(ix, iy + 92, IW, 120, "Where are you?", 18))
    p.append(button_pill(ix, iy + 240, 150, 52, "NEXT", 20))
    return "".join(p)


def c_result(ix, iy):
    p = [rect(ix, iy + 16, IW, 130, OPTIMISTIC, rx=10),
         text(ix + IW // 2, iy + 66, "Your path is", 22, WHITE, "normal",
              "middle"),
         text(ix + IW // 2, iy + 106, "Repair.", 30, WHITE, "bold",
              "middle"),
         button_pill(ix, iy + 170, IW, 56, "Continue", 22)]
    return "".join(p)


def c_terminal(ix, iy):
    # A terminal window is drawn as a navy box, not a screen frame.
    return ""


if __name__ == "__main__":
    mock("mock-hello", "My first page", 260, c_hello)
    mock("mock-shell", "Circular Economy", 260, c_shell)
    mock("mock-hero", "Circular Economy", 300, c_hero)
    mock("mock-search", "Circular Economy", 350, c_search)
    mock("mock-cards", "Circular Economy", 320, c_cards)
    mock("mock-icons", "Circular Economy", 320, c_icons)
    mock("mock-faq", "Circular Economy", 340, c_faq)
    mock("mock-landing-done", "Circular Economy", 420, c_landing_done)
    mock("mock-wizard", "Decide", 320, c_wizard)
    mock("mock-condition", "Decide", 340, c_condition)
    mock("mock-intent", "Decide", 380, c_intent)
    mock("mock-location", "Decide", 340, c_location)
    mock("mock-result", "Decide", 300, c_result)

    # Terminal mock: navy box with pale text, plus a drawn check.
    W2 = 420
    lh = 4 * 30
    th = 220
    total = 15 + th + 16 + lh + 12
    p = [rect(15, 15, 390, th, NAVY, rx=6),
         text(31, 52, "$ tsc -b && vite build", 19, WHITE, "normal"),
         text(31, 92, "Checking types...", 18, PALE),
         text(31, 122, "Building pages...", 18, PALE),
         '<polyline points="31,152 39,160 53,144" fill="none" '
         f'stroke="{TEAL}" stroke-width="4" stroke-linecap="round" '
         'stroke-linejoin="round"/>',
         text(64, 160, "Build passed. No errors.", 19, WHITE, "bold"),
         line(15, 15 + th + 8, 405, 15 + th + 8, DIVIDER_GRAY, 1),
         legend_block(15, 15 + th + 16, 390, 13)]
    svg = doc(W2, total, "".join(p))
    s, pg = write_pair(svg, os.path.join(HERE, "mock-terminal"), W2)
    print("wrote", s, pg)
