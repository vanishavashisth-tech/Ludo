"""
board.py — Renders the 15×15 Ludo board onto a pygame surface.
"""

from __future__ import annotations
import pygame
import math
from constants import (
    BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, CELL_SIZE,
    PLAYER_COLORS, PLAYER_NAMES, HOME_AREAS, HOME_LANES, MAIN_PATH,
    SAFE_SQUARES, COLOR_BOARD_BG, COLOR_GRID_LINE, COLOR_SAFE_ZONE,
    COLOR_HOME_PATH, COLOR_CENTER, DARK_COLOR_BOARD_BG, DARK_COLOR_GRID_LINE,
    HOME_TOKEN_POSITIONS, START_SQUARES,
)


def _cell_rect(col: int, row: int) -> pygame.Rect:
    """Pixel rect for grid cell (col, row)."""
    x = BOARD_OFFSET_X + col * CELL_SIZE
    y = BOARD_OFFSET_Y + row * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def _cell_centre(col: int, row: int) -> tuple[int, int]:
    r = _cell_rect(col, row)
    return r.centerx, r.centery


class Board:
    """Handles all board-drawing logic."""

    def __init__(self, dark_mode: bool = False):
        self.dark_mode = dark_mode
        self._surface: pygame.Surface | None = None   # cached board (no tokens)
        self._dirty   = True

    def mark_dirty(self):
        self._dirty = True

    def draw(self, screen: pygame.Surface):
        """Draw cached board surface; re-render only when dirty."""
        if self._dirty or self._surface is None:
            self._surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
            self._render(self._surface)
            self._dirty = False
        screen.blit(self._surface, (BOARD_OFFSET_X, BOARD_OFFSET_Y))

    # ── Internal render ───────────────────────────────────────────────────────

    def _render(self, surf: pygame.Surface):
        bg = DARK_COLOR_BOARD_BG if self.dark_mode else COLOR_BOARD_BG
        surf.fill(bg)

        self._draw_home_areas(surf)
        self._draw_path_cells(surf)
        self._draw_home_lanes(surf)
        self._draw_center_triangle(surf)
        self._draw_grid_lines(surf)
        self._draw_safe_markers(surf)
        self._draw_start_arrows(surf)

    def _draw_home_areas(self, surf: pygame.Surface):
        """Coloured squares (6×6) in each corner for token storage."""
        for pname in PLAYER_NAMES:
            c0, r0, cw, rh = HOME_AREAS[pname]
            color_light = PLAYER_COLORS[pname]["light"]
            color_dark  = PLAYER_COLORS[pname]["dark"]
            # Fill whole area
            rect = pygame.Rect(c0 * CELL_SIZE, r0 * CELL_SIZE, cw * CELL_SIZE, rh * CELL_SIZE)
            pygame.draw.rect(surf, color_light, rect)
            pygame.draw.rect(surf, color_dark,  rect, 2)

            # Inner yard (inner 4×4 = 2 cells padding)
            inner = pygame.Rect(
                (c0 + 1) * CELL_SIZE, (r0 + 1) * CELL_SIZE,
                (cw - 2) * CELL_SIZE, (rh - 2) * CELL_SIZE
            )
            pygame.draw.rect(surf, (255, 255, 255, 180), inner)
            pygame.draw.rect(surf, color_dark, inner, 1)

    def _draw_path_cells(self, surf: pygame.Surface):
        """Main 52-cell path."""
        for idx, (col, row) in enumerate(MAIN_PATH):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if idx in SAFE_SQUARES:
                pygame.draw.rect(surf, COLOR_SAFE_ZONE, rect)
            else:
                pygame.draw.rect(surf, (255, 255, 255), rect)

            # Colour the first square of each player's path
            for pname, si in START_SQUARES.items():
                if idx == si:
                    c = PLAYER_COLORS[pname]["light"]
                    pygame.draw.rect(surf, c, rect)

    def _draw_home_lanes(self, surf: pygame.Surface):
        """Coloured lanes leading to the centre."""
        for pname in PLAYER_NAMES:
            c = COLOR_HOME_PATH[pname]
            for col, row in HOME_LANES[pname]:
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surf, c, rect)

    def _draw_center_triangle(self, surf: pygame.Surface):
        """Draw the 3×3 centre with four coloured triangles."""
        cx = 6 * CELL_SIZE   # top-left of centre 3×3
        cy = 6 * CELL_SIZE
        w  = 3 * CELL_SIZE
        # Background
        pygame.draw.rect(surf, COLOR_CENTER, (cx, cy, w, w))

        centre = (cx + w//2, cy + w//2)
        corners = [(cx, cy), (cx+w, cy), (cx+w, cy+w), (cx, cy+w)]
        colors  = [
            PLAYER_COLORS["BLUE"]["primary"],
            PLAYER_COLORS["GREEN"]["primary"],
            PLAYER_COLORS["YELLOW"]["primary"],
            PLAYER_COLORS["RED"]["primary"],
        ]
        for i in range(4):
            pts = [centre, corners[i], corners[(i+1) % 4]]
            pygame.draw.polygon(surf, colors[i], pts)

        # Star overlay
        self._draw_star(surf, centre[0], centre[1], w // 2 - 4, (255,255,255,200))

    def _draw_star(self, surf, cx, cy, r, color):
        points = []
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            radius = r if i % 2 == 0 else r * 0.4
            points.append((cx + radius * math.cos(angle),
                            cy - radius * math.sin(angle)))
        pygame.draw.polygon(surf, color[:3], points)

    def _draw_grid_lines(self, surf: pygame.Surface):
        col = DARK_COLOR_GRID_LINE if self.dark_mode else COLOR_GRID_LINE
        for i in range(16):
            x = i * CELL_SIZE
            pygame.draw.line(surf, col, (x, 0), (x, BOARD_SIZE))
            pygame.draw.line(surf, col, (0, x), (BOARD_SIZE, x))

    def _draw_safe_markers(self, surf: pygame.Surface):
        """Draw small stars on safe squares."""
        for idx in SAFE_SQUARES:
            col, row = MAIN_PATH[idx]
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = row * CELL_SIZE + CELL_SIZE // 2
            self._draw_star(surf, cx, cy, CELL_SIZE // 3, (255, 200, 0, 200))

    def _draw_start_arrows(self, surf: pygame.Surface):
        """Arrow on each player's starting square."""
        arrow_dirs = {
            "RED":    (0, -1),
            "BLUE":   (1,  0),
            "GREEN":  (0,  1),
            "YELLOW": (-1, 0),
        }
        font = pygame.font.SysFont("arial", int(CELL_SIZE * 0.5), bold=True)
        arrows = {(0,-1):"↑", (1,0):"→", (0,1):"↓", (-1,0):"←"}
        for pname, si in START_SQUARES.items():
            col, row = MAIN_PATH[si]
            cx = col * CELL_SIZE + CELL_SIZE // 2
            cy = row * CELL_SIZE + CELL_SIZE // 2
            d  = arrow_dirs[pname]
            txt = font.render(arrows[d], True, PLAYER_COLORS[pname]["dark"])
            surf.blit(txt, txt.get_rect(center=(cx, cy)))

    # ── Public helpers ────────────────────────────────────────────────────────

    @staticmethod
    def cell_rect(col: int, row: int) -> pygame.Rect:
        return _cell_rect(col, row)

    @staticmethod
    def cell_centre(col: int, row: int) -> tuple[int, int]:
        return _cell_centre(col, row)
