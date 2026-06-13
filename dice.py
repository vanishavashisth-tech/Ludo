"""
dice.py — Dice with roll animation (no external images needed).
"""

from __future__ import annotations
import random
import pygame
from constants import DICE_SIZE, DICE_ANIM_FRAMES, COLOR_ACCENT


# Pip layout templates: position offsets (x, y) relative to dice centre
_PIPS: dict[int, list[tuple[float, float]]] = {
    1: [(0, 0)],
    2: [(-0.3, -0.3), (0.3, 0.3)],
    3: [(-0.3, -0.3), (0, 0), (0.3, 0.3)],
    4: [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)],
    5: [(-0.3, -0.3), (0.3, -0.3), (0, 0), (-0.3, 0.3), (0.3, 0.3)],
    6: [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0), (0.3, 0), (-0.3, 0.3), (0.3, 0.3)],
}


class Dice:
    """Animated six-sided die."""

    def __init__(self):
        self.value: int    = 1
        self.rolling: bool = False
        self._frame: int   = 0
        self._display: int = 1   # shown value during animation

    # ── Public API ────────────────────────────────────────────────────────────

    def roll(self) -> int:
        """Start roll animation; returns final value immediately."""
        self.value   = random.randint(1, 6)
        self.rolling = True
        self._frame  = 0
        return self.value

    def update(self):
        """Advance animation one frame."""
        if not self.rolling: return
        self._display = random.randint(1, 6)
        self._frame  += 1
        if self._frame >= DICE_ANIM_FRAMES:
            self.rolling  = False
            self._display = self.value

    def is_settled(self) -> bool:
        return not self.rolling

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, cx: int, cy: int,
             highlight: bool = False, disabled: bool = False):
        """Draw die centred at (cx, cy)."""
        d = DICE_SIZE
        r = 10   # corner radius
        shown = self._display if self.rolling else self.value

        rect = pygame.Rect(cx - d//2, cy - d//2, d, d)

        # Background
        if disabled:
            body_col = (80, 80, 90)
            pip_col  = (50, 50, 60)
            border   = (60, 60, 70)
        elif highlight or self.rolling:
            body_col = (255, 255, 255)
            pip_col  = (30, 30, 40)
            border   = COLOR_ACCENT
        else:
            body_col = (240, 235, 220)
            pip_col  = (30, 30, 40)
            border   = (160, 155, 140)

        # Shadow
        shadow = pygame.Surface((d + 8, d + 8), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 50), shadow.get_rect(), border_radius=r+2)
        surface.blit(shadow, (rect.left - 2, rect.top + 4))

        # Body
        pygame.draw.rect(surface, body_col, rect, border_radius=r)
        pygame.draw.rect(surface, border, rect, width=2, border_radius=r)

        # Rotation wiggle during animation
        if self.rolling:
            import math
            angle = 15 * math.sin(self._frame * 1.2)
            rotsurf = pygame.transform.rotate(surface.subsurface(rect).copy(), angle)
            # just draw pips without rotation for simplicity

        # Pips
        pip_r = max(3, d // 12)
        for (fx, fy) in _PIPS[shown]:
            px = int(cx + fx * d * 0.55)
            py = int(cy + fy * d * 0.55)
            pygame.draw.circle(surface, pip_col, (px, py), pip_r)
