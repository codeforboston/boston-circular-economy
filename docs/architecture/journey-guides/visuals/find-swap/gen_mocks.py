#!/usr/bin/env python3
"""Generate the small phone-width screen mocks for the Find & swap guide.

Each mock is one phone screen (390 wide) in Fleet colors, drawn with the
same fixed mapping as the large diagrams:
  Card     = Optimistic Blue #1871BD, rounded rectangle
  Button   = Freedom Trail Red #FB4D42, pill
  List     = teal #0E7C7B, stacked horizontal rows
  Form     = light blue #6FA8F5, rectangle with input lines
  Screen   = Charles Blue #091F2F header bar with pale #EDF2F9 body
No glyphs are typed; arrows and marks are vector shapes.
"""
import os
import cairosvg

OUT = os.path.expanduser(
    "~/workspace/goals/boston-circular-economy-client-architecture/"
    "files/journey-guides/visuals/find-swap/mocks")
os.makedirs(OUT, exist_ok=True)

CHARLES = "#091F2F"
OPT = "#1871BD"
RED = "#FB4D42"
TEAL = "#0E7C7B"
LIGHTBLUE = "#6FA8F5"
PALE = "#EDF2F9"
BODY = "#58585B"
WHITE = "#FFFFFF"
YELLOW = "#FCB61A"
NAVY = "#0B1524"

MONTS = "Montserrat, Arial, sans-serif"
LORA = "Lora, Georgia, serif"
W = 390
M = 16  # side margin
CW = W - 2 * M  # content width


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def text(x, y, s, size=15, fill=BODY, family=LORA, weight="normal",
         anchor="middle", style=""):
    st = (f' font-style="{style}"' if style else "")
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
            f'{st}>{esc(s)}</text>')


def rrect(x, y, w, h, fill, rx=8, stroke=None, sw=0):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}"{st}/>')


def header(title, right=None):
    s = rrect(0, 0, W, 56, CHARLES, rx=0)
    s += text(20, 35, title, 16, WHITE, MONTS, "bold", anchor="start")
    if right:
        s += text(W - 20, 35, right, 13, WHITE, MONTS, "bold",
                  anchor="end")
    return s


def search_field(y, word="chair", h=64):
    s = rrect(M, y, CW, h, LIGHTBLUE, rx=6)
    s += rrect(M + 10, y + 12, CW - 20, h - 24, WHITE, rx=4)
    s += text(M + 24, y + h / 2 + 6, word, 18, CHARLES, LORA, "normal",
              style="italic", anchor="start")
    return s


def match_row(y, word="chair", bold_len=3):
    s = rrect(M, y, CW, 44, WHITE, rx=6, stroke=OPT, sw=2)
    # yellow highlight behind the matched letters
    s += rrect(M + 14, y + 11, bold_len * 11 + 8, 22, YELLOW, rx=3)
    s += text(M + 18, y + 28, word, 16, CHARLES, MONTS, "bold",
              anchor="start")
    return s


def chips(y, labels, active=None, focus=None, x0=None):
    """One row of chips; wraps to a second row if needed. Returns height."""
    s = ""
    x, yy = (M if x0 is None else x0), y
    for i, lab in enumerate(labels):
        w = len(lab) * 10 + 30
        if x + w > W - M:
            x, yy = M, yy + 52
        fill = OPT if i == active else WHITE
        stroke = OPT if i == active else CHARLES
        tcol = WHITE if i == active else CHARLES
        s += rrect(x, yy, w, 40, fill, rx=20, stroke=stroke, sw=3)
        s += text(x + w / 2, yy + 26, lab, 14, tcol, MONTS, "bold")
        if focus == i:
            s += rrect(x - 5, yy - 5, w + 10, 50, "none", rx=24,
                       stroke=OPT, sw=3)
        x += w + 10
    return s, (yy + 40 - y)


def button(y, label, w=None):
    w = w or (len(label) * 11 + 48)
    x = (W - w) / 2
    s = rrect(x, y, w, 46, RED, rx=23)
    s += text(W / 2, y + 30, label, 15, WHITE, MONTS, "bold")
    return s


def rows(y, labels, h=44, gap=10):
    s = ""
    for i, lab in enumerate(labels):
        yy = y + i * (h + gap)
        s += rrect(M, yy, CW, h, TEAL, rx=6)
        s += text(M + 18, yy + h / 2 + 5, lab, 15, WHITE, MONTS, "bold",
                  anchor="start")
    return s


def card(y, title, lines, h=None):
    h = h or (64 + len(lines) * 24)
    s = rrect(M, y, CW, h, OPT, rx=10)
    s += text(M + 18, y + 32, title, 17, WHITE, MONTS, "bold",
              anchor="start")
    for i, ln in enumerate(lines):
        s += text(M + 18, y + 60 + i * 24, ln, 14, WHITE, LORA, "normal",
                  anchor="start")
    return s, h


def progress(y, label="Loading results…"):
    s = rrect(M, y, CW, 20, WHITE, rx=4, stroke=CHARLES, sw=3)
    s += rrect(M + 3, y + 3, int(CW * 0.6), 14, OPT, rx=2)
    s += text(W / 2, y + 48, label, 15, BODY, LORA, "normal")
    return s


def mini_card(x, y, w, title, sub):
    s = rrect(x, y, w, 64, OPT, rx=8)
    s += text(x + 10, y + 26, title, 14, WHITE, MONTS, "bold",
              anchor="start")
    s += text(x + 10, y + 48, sub, 12, WHITE, LORA, "normal",
              anchor="start")
    return s


def columns(y, wanted_n=2, offered_n=2, offered_empty=False):
    col_w = (CW - 12) / 2
    s = ""
    s += text(M, y, "WANTED", 14, CHARLES, MONTS, "bold", anchor="start")
    s += text(M + col_w + 12, y, "OFFERED", 14, CHARLES, MONTS, "bold",
              anchor="start")
    for col, n, empty in ((0, wanted_n, False),
                          (1, offered_n, offered_empty)):
        x = M + col * (col_w + 12)
        s += rrect(x, y + 12, col_w, 12 + n * 74, TEAL, rx=8)
        if empty:
            s += rrect(x, y + 12, col_w, 64, TEAL, rx=8)
            s += text(x + col_w / 2, y + 52, "No offered", 13, WHITE,
                      LORA, "normal")
            s += text(x + col_w / 2, y + 70, "items yet.", 13, WHITE,
                      LORA, "normal")
        else:
            for i in range(n):
                s += mini_card(x + 6, y + 24 + i * 74, col_w - 12,
                               f"Listing {i + 1}", "Free · 1 mi")
    return s


def pagination(y):
    items = ["Prev", "1", "2", "3", "Next"]
    widths = [64, 40, 40, 40, 64]
    total = sum(widths) + 4 * 8
    x = (W - total) / 2
    s = ""
    for i, (lab, w) in enumerate(zip(items, widths)):
        active = (lab == "1")
        fill = OPT if active else WHITE
        tcol = WHITE if active else CHARLES
        s += rrect(x, y, w, 42, fill, rx=6, stroke=CHARLES, sw=2)
        s += text(x + w / 2, y + 27, lab, 14, tcol, MONTS, "bold")
        x += w + 8
    return s


def render(name, H, body):
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
           f'height="{H}" viewBox="0 0 {W} {H}">']
    svg.append(f'<rect width="{W}" height="{H}" fill="{PALE}"/>')
    svg.extend(body)
    svg.append("</svg>")
    path = os.path.join(OUT, name + ".svg")
    with open(path, "w") as f:
        f.write("\n".join(svg))
    cairosvg.svg2png(url=path, write_to=os.path.join(OUT, name + ".png"),
                     output_width=W * 2)
    print("wrote", name)


# ------------------------------------------------------------------ the mocks
def m_shell():
    b = [header("FIND AND SWAP")]
    b.append(text(W / 2, 300, "Main content goes here.", 16, BODY, LORA,
                  "normal"))
    render("shell", 560, b)


def m_service():
    b = [header("FIND AND SWAP")]
    b.append(rows(80, ["Location 1", "Location 2", "Location 3"]))
    b.append(text(W / 2, 300, "Answers from the API.", 15, BODY, LORA,
                  "normal", style="italic"))
    render("service", 560, b)


def m_hook():
    b = [header("FIND AND SWAP")]
    b.append(progress(100))
    render("hook", 560, b)


def m_data_state():
    b = [header("FIND AND SWAP")]
    b.append(progress(100))
    b.append(text(W / 2, 200, "The list appears when the API answers.",
                  15, BODY, LORA, "normal", style="italic"))
    render("data-state", 560, b)


def m_page_model():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(text(W / 2, 300, "Page model written.", 16, BODY, LORA,
                  "normal"))
    b.append(text(W / 2, 328, "No component yet.", 16, BODY, LORA,
                  "normal"))
    render("page-model", 560, b)


def m_search_input():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(search_field(80))
    b.append(match_row(160))
    b.append(text(W / 2, 250, "Matched letters show in bold.", 15, BODY,
                  LORA, "normal", style="italic"))
    render("search-input", 560, b)


def m_filter_bar():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(search_field(80, h=56))
    s, _ = chips(152, ["Category", "Nearby", "Pickup", "Language"],
                 active=0)
    b.append(s)
    b.append(button(290, "Clear all"))
    render("filter-bar", 560, b)


def m_language():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(rrect(M, 80, 200, 96, OPT, rx=8))
    b.append(text(M + 16, 112, "English", 15, WHITE, MONTS, "bold",
                  anchor="start"))
    b.append(text(M + 16, 152, "Español", 15, WHITE, MONTS, "bold",
                  anchor="start"))
    b.append(text(W / 2, 230, "Pick a language. The page changes.",
                  15, BODY, LORA, "normal", style="italic"))
    render("language", 560, b)


def m_wired_search():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(search_field(80, h=56))
    s, _ = chips(152, ["Category", "Nearby", "Pickup"], active=0)
    b.append(s)
    b.append(rows(260, ["Listing 1", "Listing 2", "Listing 3"]))
    render("wired-search", 560, b)


def m_search_a11y():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(search_field(80, h=56))
    s, _ = chips(152, ["Category", "Nearby", "Pickup"], active=0, focus=0)
    b.append(s)
    b.append(text(W / 2, 250, "The focus ring sits on Category.", 15,
                  BODY, LORA, "normal", style="italic"))
    render("search-a11y", 560, b)


def m_listing_card():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    s, _ = card(80, "Wooden chair",
                ["Cost: Free", "Distance: 1 mi",
                 "Instructions: Ring the bell."])
    b.append(s)
    render("listing-card", 560, b)


def m_board():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(columns(90))
    render("board", 560, b)


def m_board_filter():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    s, _ = chips(80, ["Wanted", "Offered", "All"], active=2)
    b.append(s)
    b.append(columns(150, wanted_n=1, offered_n=1))
    render("board-filter", 560, b)


def m_board_empty():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(columns(90, wanted_n=1, offered_n=0, offered_empty=True))
    render("board-empty", 560, b)


def m_results_list():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(rows(76, [f"Result {i}" for i in range(1, 11)], h=36,
                  gap=8))
    render("results-list", 560, b)


def m_count():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(text(M, 96, "Displaying 1 – 10 of 22 results.", 16, CHARLES,
                  MONTS, "bold", anchor="start"))
    b.append(rows(120, ["Result 1", "Result 2", "Result 3"]))
    render("count", 560, b)


def m_pagination():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(text(M, 96, "Displaying 1 – 10 of 22 results.", 16, CHARLES,
                  MONTS, "bold", anchor="start"))
    b.append(rows(120, ["Result 1", "Result 2", "Result 3"]))
    b.append(pagination(300))
    render("pagination", 560, b)


def m_dialog():
    b = [header("FIND AND SWAP", "ESPAÑOL")]
    b.append(search_field(80, h=56))
    s, _ = chips(152, ["Category", "Nearby", "Pickup"], active=0)
    b.append(s)
    # dimmed layer over the body
    b.append(f'<rect x="0" y="56" width="{W}" height="504" '
             f'fill="#1871BD" fill-opacity="0.75"/>')
    # dialog
    b.append(rrect(24, 130, W - 48, 260, WHITE, rx=10))
    b.append(text(48, 168, "Filters", 17, CHARLES, MONTS, "bold",
                  anchor="start"))
    b.append(rrect(W - 76, 140, 36, 36, RED, rx=6))
    b.append(text(W - 58, 165, "X", 16, WHITE, MONTS, "bold"))
    s, _ = chips(200, ["Category", "Nearby", "Pickup"], active=1, x0=40)
    b.append(s)
    b.append(button(320, "Show results"))
    render("dialog", 560, b)


if __name__ == "__main__":
    m_shell()
    m_service()
    m_hook()
    m_data_state()
    m_page_model()
    m_search_input()
    m_filter_bar()
    m_language()
    m_wired_search()
    m_search_a11y()
    m_listing_card()
    m_board()
    m_board_filter()
    m_board_empty()
    m_results_list()
    m_count()
    m_pagination()
    m_dialog()
