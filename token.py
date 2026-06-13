"""
token.py — Represents a single Ludo token (piece) belonging to a player.
"""

from __future__ import annotations
from constants import (
    MAIN_PATH, HOME_LANES, HOME_TOKEN_POSITIONS, HOME_AREAS,
    CELL_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y, TOKEN_RADIUS, PLAYER_COLORS
)
import pygame


class Token:
    """
    A single game token.

    State machine
    -------------
    - HOME   : token is in the starting yard (not yet on board)
    - ACTIVE : token is on the main path (path_index 0-51)
    - LANE   : token is in its player's home lane (lane_index 0-5)
    - DONE   : token has reached the center (finished)
    """

    HOME   = "HOME"
    ACTIVE = "ACTIVE"
    LANE   = "LANE"
    DONE   = "DONE"

    def __init__(self, player_name: str, token_id: int):
        self.player_name = player_name
        self.token_id    = token_id
        self.state       = Token.HOME

        # position on path / lane
        self.path_index  = -1   # 0-51 on MAIN_PATH
        self.lane_index  = -1   # 0-5 in HOME_LANES

        # pixel position for drawing (centre of token)
        start_pos = HOME_TOKEN_POSITIONS[player_name][token_id]
        self.pixel_x = BOARD_OFFSET_X + start_pos[0] * CELL_SIZE + CELL_SIZE // 2
        self.pixel_y = BOARD_OFFSET_Y + start_pos[1] * CELL_SIZE + CELL_SIZE // 2

        # animation target
        self.target_x = self.pixel_x
        self.target_y = self.pixel_y
        self.moving   = False

    # ── Queries ───────────────────────────────────────────────────────────────

    @property
    def is_home(self)  -> bool: return self.state == Token.HOME
    @property
    def is_active(self)-> bool: return self.state == Token.ACTIVE
    @property
    def is_in_lane(self)->bool: return self.state == Token.LANE
    @property
    def is_done(self)  -> bool: return self.state == Token.DONE

    def grid_pos(self):
        """Return current (col, row) in the 15×15 grid."""
        if self.state == Token.ACTIVE:
            return MAIN_PATH[self.path_index]
        if self.state == Token.LANE:
            return HOME_LANES[self.player_name][self.lane_index]
        if self.state == Token.HOME:
            return HOME_TOKEN_POSITIONS[self.player_name][self.token_id]
        return (7, 7)   # center

    def steps_to_finish(self) -> int:
        """Total steps remaining to reach DONE (-1 if not applicable)."""
        if self.is_done: return 0
        if self.is_home: return -1
        lane_len = len(HOME_LANES[self.player_name])
        if self.is_in_lane:
            return lane_len - self.lane_index
        # active: steps to exit main path + home-lane length
        from constants import START_SQUARES
        start = START_SQUARES[self.player_name]
        pos   = (self.path_index - start) % len(MAIN_PATH)
        return (len(MAIN_PATH) - pos) + lane_len

    # ── Mutations ─────────────────────────────────────────────────────────────

    def send_home(self):
        """Reset token to home yard after being captured."""
        self.state      = Token.HOME
        self.path_index = -1
        self.lane_index = -1
        start_pos = HOME_TOKEN_POSITIONS[self.player_name][self.token_id]
        self.target_x = BOARD_OFFSET_X + start_pos[0] * CELL_SIZE + CELL_SIZE // 2
        self.target_y = BOARD_OFFSET_Y + start_pos[1] * CELL_SIZE + CELL_SIZE // 2
        self.moving = True

    def enter_board(self, start_index: int):
        """Move from HOME to ACTIVE at the player's starting path index."""
        self.state      = Token.ACTIVE
        self.path_index = start_index
        self._sync_target()
        self.moving = True

    def advance(self, steps: int) -> str:
        """
        Advance token by `steps`.  Returns event string:
        'ok', 'lane', 'done', 'overshoot'
        """
        from constants import START_SQUARES
        lane_len = len(HOME_LANES[self.player_name])

        if self.state == Token.ACTIVE:
            start     = START_SQUARES[self.player_name]
            travelled = (self.path_index - start) % len(MAIN_PATH)
            remaining = len(MAIN_PATH) - travelled  # steps to reach lane entry

            if steps < remaining:
                self.path_index = (self.path_index + steps) % len(MAIN_PATH)
                self._sync_target(); self.moving = True
                return "ok"
            elif steps == remaining:
                # Enter lane at index 0
                self.state      = Token.LANE
                self.lane_index = 0
                self._sync_target(); self.moving = True
                return "lane"
            else:
                # How many into the lane?
                lane_steps = steps - remaining
                if lane_steps < lane_len:
                    self.state      = Token.LANE
                    self.lane_index = lane_steps
                    self._sync_target(); self.moving = True
                    return "lane"
                elif lane_steps == lane_len:
                    self.state      = Token.DONE
                    self._sync_target(); self.moving = True
                    return "done"
                else:
                    return "overshoot"

        elif self.state == Token.LANE:
            new_lane = self.lane_index + steps
            if new_lane < lane_len:
                self.lane_index = new_lane
                self._sync_target(); self.moving = True
                return "lane"
            elif new_lane == lane_len:
                self.state = Token.DONE
                self._sync_target(); self.moving = True
                return "done"
            else:
                return "overshoot"

        return "overshoot"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _sync_target(self):
        """Compute pixel target from logical position."""
        col, row = self.grid_pos()
        self.target_x = BOARD_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
        self.target_y = BOARD_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2

    # ── Drawing ───────────────────────────────────────────────────────────────

    def update_animation(self, speed: int = 6):
        """Slide pixel position toward target. Returns True while still moving."""
        dx = self.target_x - self.pixel_x
        dy = self.target_y - self.pixel_y
        dist = (dx**2 + dy**2) ** 0.5
        if dist < speed:
            self.pixel_x = self.target_x
            self.pixel_y = self.target_y
            self.moving  = False
        else:
            self.pixel_x += int(dx / dist * speed)
            self.pixel_y += int(dy / dist * speed)
        return self.moving

    def draw(self, surface: pygame.Surface, is_selected: bool = False,
             is_movable: bool = False, offset: int = 0):
        """Render the token on the given surface."""
        x = self.pixel_x + offset
        y = self.pixel_y

        colors = PLAYER_COLORS[self.player_name]
        primary = colors["primary"]
        light   = colors["light"]
        dark    = colors["dark"]

        r = TOKEN_RADIUS

        # Glow when movable
        if is_movable:
            for glow_r in range(r + 9, r - 1, -3):
                alpha = max(0, 80 - (glow_r - r) * 12)
                glow_surf = pygame.Surface((glow_r*2+2, glow_r*2+2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*primary, alpha), (glow_r+1, glow_r+1), glow_r)
                surface.blit(glow_surf, (x - glow_r - 1, y - glow_r - 1))

        # Shadow
        shadow_surf = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0,0,0,60), (r+2+2, r+2+4), r)
        surface.blit(shadow_surf, (x - r - 2, y - r - 2))

        # Outer ring
        pygame.draw.circle(surface, dark, (x, y), r)

        # Main body
        pygame.draw.circle(surface, primary, (x, y), r - 2)

        # Inner highlight
        pygame.draw.circle(surface, light, (x - r//4, y - r//4), r // 3)

        # Selection ring
        if is_selected:
            pygame.draw.circle(surface, (255, 255, 100), (x, y), r + 3, 3)

    def __repr__(self):
        return f"<Token {self.player_name}#{self.token_id} {self.state} path={self.path_index} lane={self.lane_index}>"
