#!/usr/bin/env python3
"""Big-picture layout page, pack style. Top-down: journey, client, API, data.

Read down the bands = layer by layer. Read across a band = component by component.
Content grounded in the repo as of 2026-10-29 (main + PR #88 branch for the client).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pack_kit import *  # noqa

OUT = str(Path(__file__).resolve().parent)

pg = Page()
pg.header("Boston Circular Economy — Big-Picture Layout",
          "Top-down: how the app is built — read down by layer, across by component", "L0")

# ---- Visitor journey strip ----
pg.text(36, 128, "VISITOR JOURNEY — how a visitor moves, left to right",
        size=13, fill=MUTED, weight="bold")
stages = [
    ("Zero Waste Boston", "entry page", None),
    ("/decide", "answers questions", None),
    ("/search?…", "zip · radius", "category · service-type"),
    ("Results list", "first 10 shown", None),
    ("Clinic visit", "repair done", None),
]
for i, (t, sub, sub2) in enumerate(stages):
    x = 36 + i * 307
    pg.rect(x, 142, 260, 70, "white", NAVY, 2, rx=10)
    pg.num_badge(x + 26, 177, i + 1, r=15)
    pg.text(x + 50, 168, t, size=14, weight="bold")
    pg.text(x + 50, 188, sub, size=12.5, fill=MUTED)
    if sub2:
        pg.text(x + 50, 206, sub2, size=12.5, fill=MUTED)
    if i < 4:
        pg.arrow(x + 264, 177, x + 303, 177, color=NAVY, sw=2.5)

# ---- Layer 1: Client ----
pg.panel(36, 230, 1488, 232, "LAYER 1 · CLIENT — the web app (TanStack)", stroke=CLIENT[0])
boxes = [
    ("Pages — routes", "screen", [
        "/decide — questions",
        "/decide/service-type",
        "/decide/repair",
        "/search — results",
        "/dev/* — prototypes",
    ]),
    ("Components", "tree", [
        "ui/ — reusable parts",
        "domain parts (map, …)",
        "page holds parts, one tree",
        "parts take props, never fetch",
    ]),
    ("Services — only API callers", "plug", [
        "typed api client (openapi)",
        "query hook per endpoint",
        "no page writes its own fetch",
    ]),
    ("Platform", "gear", [
        "TanStack Router — URL state",
        "TanStack Query — cache",
        "Vite build + dev proxy",
    ]),
]
for j, (title, kind, lines) in enumerate(boxes):
    x = 56 + j * 364
    y = 292
    top = pg.panel_plain(x, y, 340, 138, CLIENT, title)
    pg.icon(kind, x + 316, y + 15, CLIENT[0], s=0.85)
    for k, ln in enumerate(lines):
        pg.text(x + 16, top + 22 + k * 20, ln, size=13)
pg.text(56, 450, "Rule: Screens never call the API. Screens ask Services. Services call the API.",
        size=13.5, fill=CLIENT[0], weight="bold")

pg.down_arrow(954, 462, 498, color=CLIENT[0], sw=2.5)
pg.label(1010, 480, "HTTP")

# ---- Layer 2: API ----
pg.panel(36, 506, 1488, 190, "LAYER 2 · API — the only door from browser to data", stroke=API[0])
top = pg.panel_plain(56, 568, 440, 112, API, "Public API — live")
pg.icon("server", 56 + 416, 568 + 15, API[0], s=0.85)
for k, ln in enumerate(["GET /ping", "GET /search — all locations", "POST /feedback — 501 yet"]):
    pg.text(72, top + 22 + k * 20, ln, size=13)
top = pg.panel_plain(520, 568, 480, 112, CONTRACT, "Contracts — shared types")
pg.icon("doc", 520 + 456, 568 + 15, CONTRACT[0], s=0.85)
for k, ln in enumerate(["SearchResult — page view", "NormalizedLocation — shared", "ItemCategory · Activity"]):
    pg.text(536, top + 22 + k * 20, ln, size=13)
pg.rect(1024, 568, 460, 112, API[1], API[0], 2, rx=10, dash=True)
pg.text(1040, 596, "Internal API — PLANNED, stubs (#47)", size=15, fill=API[0], weight="bold")
pg.icon("server", 1024 + 436, 568 + 15, API[0], s=0.85)
for k, ln in enumerate(["snapshot writes", "merged-location writes"]):
    pg.text(1040, 618 + k * 20, ln, size=13)

pg.down_arrow(1284, 696, 734, color=API[0], sw=2.5)
pg.label(1180, 715, "API reads")

# ---- Layer 3: Data + ETL ----
pg.panel(36, 742, 1488, 176, "LAYER 3 · DATA + ETL — where locations come from", stroke=DATA[0])
top = pg.panel_plain(56, 804, 400, 98, DATA, "Sources")
pg.icon("funnel", 56 + 376, 804 + 15, DATA[0], s=0.85)
for k, ln in enumerate(["Google Places", "OpenStreetMap"]):
    pg.text(72, top + 22 + k * 20, ln, size=13)
top = pg.panel_plain(480, 804, 560, 98, DATA, "ETL jobs")
pg.icon("gear", 480 + 536, 804 + 15, DATA[0], s=0.85)
for k, ln in enumerate(["scrape_to_local: fetch → normalize → snapshot",
                        "merge: match (150 m, 90) → merge → output"]):
    pg.text(496, top + 22 + k * 20, ln, size=13)
top = pg.panel_plain(1064, 804, 440, 98, DATA, "Store")
pg.icon("db", 1064 + 416, 804 + 15, DATA[0], s=0.85)
for k, ln in enumerate(["LocalDataStore — files today", "DB store later, same parent"]):
    pg.text(1080, top + 22 + k * 20, ln, size=13)
pg.arrow(460, 853, 476, 853, color=DATA[0], sw=2.5)
pg.arrow(1044, 853, 1060, 853, color=DATA[0], sw=2.5)

# ---- Rule strip ----
pg.rule_strip(934,
              "Read it two ways: down the bands = layer by layer; across a band = component by component.",
              "Detail follows: class diagram · component diagram · sequence diagram · page component view · page model · server page components.")

# ---- Custom legend ----
pg.text(40, 1056, "LEGEND", size=12.5, fill=MUTED, weight="bold")
for lx, sch, lab in [(130, CLIENT, "Client"), (250, API, "API"),
                     (350, CONTRACT, "Contracts"), (500, DATA, "Data + ETL")]:
    pg.rect(lx, 1041, 18, 18, sch[1], sch[0], 1.6, rx=4)
    pg.text(lx + 26, 1056, lab, size=12.5, fill=MUTED)
pg.rect(680, 1041, 18, 18, "white", NAVY, 1.6, rx=4, dash=True)
pg.text(706, 1056, "Planned", size=12.5, fill=MUTED)
pg.text(1520, 1056, "Big-picture layout · pack edition", size=12.5, fill=MUTED, anchor="end")

save(pg, OUT + "/big-picture-layout.svg")
print("wrote", OUT + "/big-picture-layout.svg")
