"""
game.py — Core game state machine.

States
------
SETUP         : choosing players (not used here, done in main)
ROLL_PHASE    : current player must roll
CHOOSE_PHASE  : player sees valid tokens and picks one
ANIMATE_PHASE : token moving, wait until done
CAPTURE_PHASE : brief pause after capture
NEXT_TURN     : switch to next player
GAME_OVER     : a player has all 4 tokens home
PAUSED        : pause menu open
"""

from __future__ import annotations
import json, time
from typing import TYPE_CHECKING

import pygame

from constants import (
    PLAYER_NAMES, MAIN_PATH, SAFE_SQUARES, HOME_LANES, AI_THINK_DELAY, SAVE_FILE
)
from player import Player
from dice   import Dice
from token  import Token
import ai as ai_module


class GameState:
    ROLL      = "ROLL"
    CHOOSE    = "CHOOSE"
    ANIMATE   = "ANIMATE"
    CAPTURE   = "CAPTURE"
    NEXT_TURN = "NEXT_TURN"
    GAME_OVER = "GAME_OVER"
    PAUSED    = "PAUSED"


class Game:
    """
    Central game controller.

    Parameters
    ----------
    mode : "HvH" | "HvC" | "CvC"
    num_players : 2, 3, or 4
    dark_mode   : toggles colour theme
    """

    def __init__(self, mode: str = "HvH", num_players: int = 4,
                 dark_mode: bool = False):
        self.mode        = mode
        self.num_players = num_players
        self.dark_mode   = dark_mode
        self.dice        = Dice()
        self.players: list[Player] = []
        self.current_idx: int      = 0
        self.state: str            = GameState.ROLL
        self.selected_token: Token | None  = None
        self.movable_tokens: list[Token]   = []
        self.message: str          = ""
        self.winner: Player | None = None
        self.stats: dict           = {"turns": 0, "captures": 0, "sixes": 0}
        self._ai_timer: int        = 0    # ms timestamp for AI delay
        self._prev_state: str      = ""   # for pause/resume
        self._pending_capture: Player | None = None
        self._init_players()

    # ── Initialisation ────────────────────────────────────────────────────────

    def _init_players(self):
        human_flags = {
            "HvH": [True,  True,  True,  True ],
            "HvC": [True,  False, True,  False],
            "CvC": [False, False, False, False],
        }[self.mode]

        self.players = [
            Player(PLAYER_NAMES[i], human_flags[i])
            for i in range(self.num_players)
        ]
        self.current_idx = 0
        self.state       = GameState.ROLL
        self.message     = f"{self.current_player.name}'s turn — Roll the dice!"

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def current_player(self) -> Player:
        return self.players[self.current_idx]

    # ── Update loop ───────────────────────────────────────────────────────────

    def update(self, dt_ms: int):
        """Called every frame. dt_ms = milliseconds since last frame."""
        # Update dice animation
        self.dice.update()

        # Update token animations
        any_moving = False
        for p in self.players:
            for t in p.tokens:
                if t.moving:
                    t.update_animation()
                    if t.moving:
                        any_moving = True

        if self.state == GameState.ANIMATE and not any_moving:
            self._post_animate()

        elif self.state == GameState.CAPTURE and not any_moving:
            self.state   = GameState.NEXT_TURN
            self._next_turn()

        elif self.state == GameState.NEXT_TURN:
            self._next_turn()

        # AI auto-play
        elif self.state in (GameState.ROLL, GameState.CHOOSE):
            if not self.current_player.is_human:
                self._ai_step(dt_ms)

    # ── Player actions ────────────────────────────────────────────────────────

    def handle_roll(self):
        """Human presses Roll button."""
        if self.state != GameState.ROLL: return
        if not self.current_player.is_human: return
        self._do_roll()

    def handle_token_click(self, token: Token):
        """Human clicks a token."""
        if self.state != GameState.CHOOSE: return
        if not self.current_player.is_human: return
        if token not in self.movable_tokens: return
        self._move_token(token)

    def handle_pause(self):
        if self.state == GameState.PAUSED:
            self.state   = self._prev_state
        else:
            self._prev_state = self.state
            self.state       = GameState.PAUSED

    def restart(self, mode: str | None = None, num_players: int | None = None):
        if mode: self.mode = mode
        if num_players: self.num_players = num_players
        self.winner = None
        self.stats  = {"turns": 0, "captures": 0, "sixes": 0}
        self._init_players()

    # ── Internal game flow ────────────────────────────────────────────────────

    def _do_roll(self):
        value = self.dice.roll()
        self.stats["turns"] += 1
        if value == 6:
            self.stats["sixes"] += 1

        movable = self.current_player.movable_tokens(value)
        self.movable_tokens = movable
        self.message = f"{self.current_player.name} rolled a {value}!"

        if not movable:
            self.message += " — No moves available."
            self._schedule_next_turn()
        elif len(movable) == 1 and not self.current_player.is_human:
            self._move_token(movable[0])
        else:
            if self.current_player.is_human:
                self.state   = GameState.CHOOSE
                self.message += " — Select a token to move."
            else:
                self._move_token(movable[0])  # AI will re-pick in _ai_step

    def _move_token(self, token: Token):
        """Execute the move for current_player with self.dice.value."""
        dice   = self.dice.value
        player = self.current_player

        event = player.move_token(token, dice)

        self.state  = GameState.ANIMATE
        self.message = f"{player.name} moves token!"

        if event == "done":
            player.wins += 1
            self.message = f"{player.name} got a token home! 🎉"
        elif event == "entered":
            self.message = f"{player.name} brings a token onto the board!"

        # Check capture (only on main path, non-safe)
        if token.is_active:
            self._check_capture(token, player)

        self.selected_token = None
        self.movable_tokens = []

    def _check_capture(self, token: Token, player: Player):
        """Send opponents home if token shares their cell."""
        idx = token.path_index
        if idx in SAFE_SQUARES: return
        cell = MAIN_PATH[idx]
        for opp in self.players:
            if opp.name == player.name: continue
            for ot in opp.tokens:
                if ot.is_active and MAIN_PATH[ot.path_index] == cell:
                    ot.send_home()
                    player.captures += 1
                    self.stats["captures"] += 1
                    self.message = f"{player.name} captures {opp.name}! Token sent home! 💥"
                    self.state   = GameState.CAPTURE

    def _post_animate(self):
        """Called when all token animations finish."""
        player = self.current_player
        if player.has_won():
            self.winner = player
            self.state  = GameState.GAME_OVER
            self.message = f"🏆 {player.name} wins! Congratulations!"
            return

        if self.dice.value == 6:
            # Extra turn
            self.state   = GameState.ROLL
            self.message = f"{player.name} rolled 6 — Extra turn!"
        else:
            self._next_turn()

    def _schedule_next_turn(self):
        """Skip to next player after brief delay."""
        self.state = GameState.NEXT_TURN

    def _next_turn(self):
        self.current_idx = (self.current_idx + 1) % len(self.players)
        self.state       = GameState.ROLL
        self.message     = f"{self.current_player.name}'s turn — Roll the dice!"
        self._ai_timer   = 0

    # ── AI ────────────────────────────────────────────────────────────────────

    def _ai_step(self, dt_ms: int):
        """Drive AI actions with a think delay for realism."""
        now = pygame.time.get_ticks()
        if self._ai_timer == 0:
            self._ai_timer = now + AI_THINK_DELAY

        if now < self._ai_timer:
            return  # still "thinking"

        if self.state == GameState.ROLL:
            self._do_roll()
            self._ai_timer = 0
        elif self.state == GameState.CHOOSE:
            token = ai_module.choose_token(
                self.current_player, self.players, self.dice.value)
            if token:
                self._move_token(token)
            else:
                self._schedule_next_turn()
            self._ai_timer = 0

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save(self):
        data = {
            "mode":        self.mode,
            "num_players": self.num_players,
            "dark_mode":   self.dark_mode,
            "current_idx": self.current_idx,
            "state":       self.state if self.state != GameState.PAUSED else self._prev_state,
            "dice_value":  self.dice.value,
            "stats":       self.stats,
            "players":     [p.to_dict() for p in self.players],
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        self.message = "Game saved ✓"

    @classmethod
    def load(cls) -> "Game | None":
        try:
            with open(SAVE_FILE) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

        g = cls.__new__(cls)
        g.mode        = data["mode"]
        g.num_players = data["num_players"]
        g.dark_mode   = data.get("dark_mode", False)
        g.dice        = Dice()
        g.dice.value  = data.get("dice_value", 1)
        g.dice._display = g.dice.value
        g.stats       = data.get("stats", {"turns":0,"captures":0,"sixes":0})
        g.players     = [Player.from_dict(pd) for pd in data["players"]]
        g.current_idx = data["current_idx"]
        g.state       = data.get("state", GameState.ROLL)
        g.selected_token   = None
        g.movable_tokens   = []
        g.winner           = None
        g._ai_timer        = 0
        g._prev_state      = ""
        g._pending_capture = None
        g.message     = f"{g.current_player.name}'s turn — (loaded)"
        return g
