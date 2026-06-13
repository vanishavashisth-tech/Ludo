"""
ai.py — Simple strategic AI for Ludo.

Priority order (highest first):
1. Win a token (enter DONE)
2. Capture an opponent token
3. Move a token that can enter the safe lane
4. Move the token closest to home
5. Bring a new token onto the board (if dice=6)
6. Avoid being 1-5 steps ahead of a dangerous opponent
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from token  import Token

from constants import MAIN_PATH, SAFE_SQUARES, HOME_LANES, START_SQUARES


def choose_token(current_player: "Player", all_players: list["Player"],
                 dice_value: int) -> "Token | None":
    """
    Return the best token for the AI to move, or None if no legal move.
    """
    movable = current_player.movable_tokens(dice_value)
    if not movable:
        return None
    if len(movable) == 1:
        return movable[0]

    scored = [(score(t, current_player, all_players, dice_value), t) for t in movable]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def score(token: "Token", player: "Player", all_players: list["Player"],
          dice_value: int) -> float:
    """Heuristic score for moving this token."""
    from token import Token as T

    s = 0.0

    # 1. Winning move
    if _would_finish(token, dice_value):
        return 10_000.0

    # 2. Capture opportunity
    landing = _landing_main_index(token, player, dice_value)
    if landing is not None:
        if _has_capturable_opponent(landing, player, all_players):
            s += 500.0

    # 3. Entering home lane is safe and good
    if _enters_lane(token, player, dice_value):
        s += 200.0

    # 4. Closer to finish = better (normalised 0..100)
    steps_left = token.steps_to_finish()
    if steps_left > 0:
        s += (56 - min(steps_left, 56)) / 56 * 100

    # 5. Prefer bringing out a new token when a 6 is rolled
    if token.is_home and dice_value == 6:
        s += 80.0

    # 6. Penalise landing in danger zone (opponent within 6 steps behind)
    if landing is not None and landing not in SAFE_SQUARES:
        danger = _danger_level(landing, player, all_players)
        s -= danger * 30

    return s


# ── Helpers ───────────────────────────────────────────────────────────────────

def _would_finish(token: "Token", dice: int) -> bool:
    from token import Token as T
    lane_len = len(HOME_LANES[token.player_name])
    if token.is_in_lane:
        return token.lane_index + dice == lane_len
    if token.is_active:
        start     = START_SQUARES[token.player_name]
        travelled = (token.path_index - start) % len(MAIN_PATH)
        return (len(MAIN_PATH) - travelled) + lane_len == dice + \
               (len(MAIN_PATH) - travelled)
    return False


def _landing_main_index(token: "Token", player: "Player", dice: int) -> int | None:
    """Return the main-path index the token would land on (if still on main path)."""
    from token import Token as T
    if token.is_active:
        start     = START_SQUARES[player.name]
        remaining = len(MAIN_PATH) - (token.path_index - start) % len(MAIN_PATH)
        if dice < remaining:
            return (token.path_index + dice) % len(MAIN_PATH)
    return None


def _enters_lane(token: "Token", player: "Player", dice: int) -> bool:
    from token import Token as T
    if not token.is_active: return False
    start     = START_SQUARES[player.name]
    remaining = len(MAIN_PATH) - (token.path_index - start) % len(MAIN_PATH)
    return dice >= remaining


def _has_capturable_opponent(path_idx: int, player: "Player",
                              all_players: list["Player"]) -> bool:
    if path_idx in SAFE_SQUARES:
        return False
    cell = MAIN_PATH[path_idx]
    for p in all_players:
        if p.name == player.name: continue
        for t in p.tokens:
            if t.is_active and MAIN_PATH[t.path_index] == cell:
                return True
    return False


def _danger_level(path_idx: int, player: "Player",
                  all_players: list["Player"]) -> int:
    """Count opponent tokens that could reach this cell in 1-6 steps."""
    count = 0
    cell  = MAIN_PATH[path_idx]
    for p in all_players:
        if p.name == player.name: continue
        for t in p.tokens:
            if not t.is_active: continue
            for d in range(1, 7):
                landing = (t.path_index + d) % len(MAIN_PATH)
                if MAIN_PATH[landing] == cell:
                    count += 1
    return count
