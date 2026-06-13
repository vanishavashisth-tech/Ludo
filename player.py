"""
player.py — Player (human or AI) holding 4 tokens.
"""

from __future__ import annotations
from token import Token
from constants import START_SQUARES, MAIN_PATH, SAFE_SQUARES, HOME_LANES


class Player:
    """
    Represents one Ludo player (human or AI).

    Attributes
    ----------
    name       : colour identifier e.g. "RED"
    is_human   : True = user controls; False = AI controls
    tokens     : list of 4 Token objects
    extra_turn : True when player earned an extra roll (rolled 6)
    """

    def __init__(self, name: str, is_human: bool = True):
        self.name      = name
        self.is_human  = is_human
        self.tokens    = [Token(name, i) for i in range(4)]
        self.extra_turn = False
        self.wins      = 0     # tokens that have finished this game
        self.captures  = 0     # opponent tokens sent home

    # ── Queries ───────────────────────────────────────────────────────────────

    def has_won(self) -> bool:
        return all(t.is_done for t in self.tokens)

    def movable_tokens(self, dice_value: int) -> list[Token]:
        """Return tokens that can legally move given the dice roll."""
        movable = []
        for t in self.tokens:
            if t.is_done:
                continue
            if t.is_home:
                if dice_value == 6:
                    movable.append(t)
                continue
            # Simulate move to see if it's valid
            result = self._simulate_advance(t, dice_value)
            if result != "overshoot":
                movable.append(t)
        return movable

    def active_tokens(self) -> list[Token]:
        return [t for t in self.tokens if t.is_active]

    def home_tokens(self) -> list[Token]:
        return [t for t in self.tokens if t.is_home]

    def lane_tokens(self) -> list[Token]:
        return [t for t in self.tokens if t.is_in_lane]

    # ── Mutations ─────────────────────────────────────────────────────────────

    def move_token(self, token: Token, dice_value: int) -> str:
        """
        Move token by dice_value steps.
        Returns event: 'ok' | 'lane' | 'done' | 'entered' | 'overshoot'
        """
        if token.is_home and dice_value == 6:
            token.enter_board(START_SQUARES[self.name])
            return "entered"
        return token.advance(dice_value)

    # ── Static helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _simulate_advance(token: Token, steps: int) -> str:
        """Non-mutating: check if token can advance by steps."""
        from token import Token as T
        if token.state == T.ACTIVE:
            start     = START_SQUARES[token.player_name]
            travelled = (token.path_index - start) % len(MAIN_PATH)
            remaining = len(MAIN_PATH) - travelled
            lane_len  = len(HOME_LANES[token.player_name])
            total     = remaining + lane_len
            if steps > total:
                return "overshoot"
            return "ok"
        elif token.state == T.LANE:
            lane_len  = len(HOME_LANES[token.player_name])
            new_lane  = token.lane_index + steps
            if new_lane > lane_len:
                return "overshoot"
            return "ok"
        return "overshoot"

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "name":     self.name,
            "is_human": self.is_human,
            "captures": self.captures,
            "tokens":   [
                {
                    "state":      t.state,
                    "path_index": t.path_index,
                    "lane_index": t.lane_index,
                }
                for t in self.tokens
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        p = cls(data["name"], data["is_human"])
        p.captures = data.get("captures", 0)
        for i, td in enumerate(data["tokens"]):
            t = p.tokens[i]
            t.state      = td["state"]
            t.path_index = td["path_index"]
            t.lane_index = td["lane_index"]
            t._sync_target()
            t.pixel_x = t.target_x
            t.pixel_y = t.target_y
        return p

    def __repr__(self):
        done = sum(1 for t in self.tokens if t.is_done)
        return f"<Player {self.name} {'H' if self.is_human else 'AI'} done={done}/4>"
