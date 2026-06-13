"""
constants.py - All game constants, colors, paths, and configuration.
"""

import os

# ── Window & Board ────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 900
WINDOW_HEIGHT = 750
BOARD_SIZE    = 700          # square board pixel size
BOARD_OFFSET_X = 10
BOARD_OFFSET_Y = 25
CELL_SIZE     = BOARD_SIZE // 15   # 15×15 grid → ~46 px per cell
FPS           = 60

# ── Player colours (name, primary, light, dark) ───────────────────────────────
PLAYER_COLORS = {
    "RED":    {"primary": (220,  50,  50), "light": (255, 180, 180), "dark": (150,  20,  20)},
    "BLUE":   {"primary": (50,  100, 220), "light": (180, 200, 255), "dark": ( 20,  50, 150)},
    "GREEN":  {"primary": (40,  170,  60), "light": (180, 240, 190), "dark": ( 20, 100,  30)},
    "YELLOW": {"primary": (220, 190,  30), "light": (255, 240, 160), "dark": (160, 130,  10)},
}
PLAYER_NAMES = ["RED", "BLUE", "GREEN", "YELLOW"]

# ── Board Palette ─────────────────────────────────────────────────────────────
COLOR_BG         = (245, 240, 230)   # warm cream
COLOR_BOARD_BG   = (255, 255, 255)
COLOR_GRID_LINE  = (200, 195, 185)
COLOR_SAFE_ZONE  = (200, 230, 200)
COLOR_HOME_PATH  = {
    "RED":    (255, 200, 200),
    "BLUE":   (200, 215, 255),
    "GREEN":  (200, 240, 210),
    "YELLOW": (255, 245, 180),
}
COLOR_CENTER     = (240, 240, 240)
COLOR_STAR_FILL  = (255, 215, 0)

# ── UI Palette ────────────────────────────────────────────────────────────────
COLOR_PANEL_BG   = (30,  30,  40)
COLOR_PANEL_EDGE = (60,  60,  80)
COLOR_TEXT_LIGHT = (240, 235, 225)
COLOR_TEXT_DIM   = (150, 145, 135)
COLOR_ACCENT     = (255, 200,  60)
COLOR_BTN_NORM   = (55,  55,  75)
COLOR_BTN_HOVER  = (80,  80, 110)
COLOR_BTN_PRESS  = (35,  35,  55)
COLOR_SHADOW     = (0,   0,   0,  80)

# Dark-mode overrides (applied when dark_mode=True)
DARK_COLOR_BG        = (18,  18,  24)
DARK_COLOR_BOARD_BG  = (30,  30,  40)
DARK_COLOR_GRID_LINE = (50,  50,  65)

# ── Standard Ludo Path (15×15 grid coordinates) ───────────────────────────────
# Each player's token travels 56 squares on the main path then 5 home-lane
# squares. Coordinates are (col, row) in the 15×15 grid.
#
# Main path starting positions (first square OUTSIDE home area, going CW):
START_SQUARES = {
    "RED":    1,   # index into MAIN_PATH
    "BLUE":   14,
    "GREEN":  27,
    "YELLOW": 40,
}

# 52-square clockwise main path
MAIN_PATH = [
    # Bottom of RED home (col, row)
    (6,13),(6,12),(6,11),(6,10),(6,9),(6,8),  # 0-5  going up left col
    (5,8),(4,8),(3,8),(2,8),(1,8),             # 6-10 going left top row
    (0,8),(0,7),(0,6),                         # 11-13
    (1,6),(2,6),(3,6),(4,6),(5,6),             # 14-18 BLUE entry zone
    (6,5),(6,4),(6,3),(6,2),(6,1),(6,0),       # 19-24 going up
    (7,0),(8,0),                               # 25-26
    (8,1),(8,2),(8,3),(8,4),(8,5),             # 27-31 GREEN entry zone
    (9,6),(10,6),(11,6),(12,6),(13,6),(14,6),  # 32-37 going right
    (14,7),(14,8),                             # 38-39
    (13,8),(12,8),(11,8),(10,8),(9,8),         # 40-44 YELLOW entry zone
    (8,9),(8,10),(8,11),(8,12),(8,13),(8,14),  # 45-50 going down
    (7,14),(7,13),                             # 51, 0→wrap
]

# Home lane cells (col, row) leading to center — per player
HOME_LANES = {
    "RED":    [(7,13),(7,12),(7,11),(7,10),(7,9),(7,8)],
    "BLUE":   [(1,7),(2,7),(3,7),(4,7),(5,7),(6,7)],
    "GREEN":  [(7,1),(7,2),(7,3),(7,4),(7,5),(7,6)],
    "YELLOW": [(13,7),(12,7),(11,7),(10,7),(9,7),(8,7)],
}

# Safe squares (star squares) — indices in MAIN_PATH
SAFE_SQUARES = {8, 13, 21, 26, 34, 39, 47, 0}

# Home area bounding boxes (col_start, row_start, cols, rows) in grid units
HOME_AREAS = {
    "RED":    (0,  9, 6, 6),
    "BLUE":   (0,  0, 6, 6),
    "GREEN":  (9,  0, 6, 6),
    "YELLOW": (9,  9, 6, 6),
}

# Token start positions INSIDE the home yard (grid coords for 4 tokens)
HOME_TOKEN_POSITIONS = {
    "RED":    [(1,10),(3,10),(1,12),(3,12)],
    "BLUE":   [(1,1), (3,1), (1,3), (3,3)],
    "GREEN":  [(10,1),(12,1),(10,3),(12,3)],
    "YELLOW": [(10,10),(12,10),(10,12),(12,12)],
}

# ── Dice ──────────────────────────────────────────────────────────────────────
DICE_SIZE     = 70
DICE_ANIM_FRAMES = 12   # frames of spinning before settling

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVE_FILE  = os.path.join(BASE_DIR, "savegame.json")

# ── AI ────────────────────────────────────────────────────────────────────────
AI_THINK_DELAY = 800   # ms before AI acts

# ── Animation ─────────────────────────────────────────────────────────────────
TOKEN_MOVE_SPEED = 6   # pixels per frame during animation
TOKEN_RADIUS     = int(CELL_SIZE * 0.38)
