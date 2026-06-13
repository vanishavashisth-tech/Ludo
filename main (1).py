"""
main.py — Ludo Game entry point.

Run:  python main.py
"""

from __future__ import annotations
import sys, math
import pygame

from constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BOARD_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    CELL_SIZE, FPS, PLAYER_COLORS, PLAYER_NAMES,
    COLOR_BG, COLOR_PANEL_BG, COLOR_PANEL_EDGE, COLOR_TEXT_LIGHT,
    COLOR_TEXT_DIM, COLOR_ACCENT, COLOR_BTN_NORM, COLOR_BTN_HOVER,
    COLOR_BTN_PRESS, DARK_COLOR_BG, MAIN_PATH, HOME_LANES,
    HOME_TOKEN_POSITIONS, DICE_SIZE,
)
from board  import Board
from game   import Game, GameState
from token  import Token


# ── UI helpers ────────────────────────────────────────────────────────────────

def load_fonts():
    fonts = {}
    for name, size, bold in [
        ("title",   28, True ),
        ("header",  20, True ),
        ("body",    15, False),
        ("small",   12, False),
        ("large",   36, True ),
    ]:
        fonts[name] = pygame.font.SysFont("segoeui,arial,sans", size, bold=bold)
    return fonts


def draw_text(surf, font, text, color, cx, cy, align="center"):
    img = font.render(text, True, color)
    r   = img.get_rect()
    if align == "center": r.center  = (cx, cy)
    elif align == "left": r.midleft = (cx, cy)
    elif align == "right":r.midright= (cx, cy)
    surf.blit(img, r)


def draw_rounded_rect(surf, color, rect, radius=8, border=0, border_color=None):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, rect, width=border, border_radius=radius)


def pill_button(surf, fonts, label, rect, hover, pressed, disabled=False,
                color_bg=None, color_hover=None):
    """Draw a pill-style button; return True if currently hovered."""
    bg    = color_bg    or COLOR_BTN_NORM
    bgh   = color_hover or COLOR_BTN_HOVER
    if disabled:
        bg = (50, 50, 60)
        col_txt = (80, 80, 90)
    else:
        bg = COLOR_BTN_PRESS if pressed else (bgh if hover else bg)
        col_txt = COLOR_TEXT_LIGHT

    draw_rounded_rect(surf, bg, rect, radius=rect.height//2,
                      border=1, border_color=COLOR_PANEL_EDGE)
    draw_text(surf, fonts["body"], label, col_txt, rect.centerx, rect.centery)


# ── Setup screen ──────────────────────────────────────────────────────────────

class SetupScreen:
    """Initial mode/player count selection screen."""

    def __init__(self, fonts):
        self.fonts      = fonts
        self.mode       = "HvH"
        self.num_players= 4
        self.dark_mode  = False
        self.done       = False
        self.load_saved = False
        self._hover     = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Mode buttons
            for i, m in enumerate(["HvH","HvC","CvC"]):
                r = self._mode_rect(i)
                if r.collidepoint(mx, my): self.mode = m
            # Player count
            for n in [2, 3, 4]:
                r = self._players_rect(n)
                if r.collidepoint(mx, my): self.num_players = n
            # Dark mode
            if self._dark_rect().collidepoint(mx, my):
                self.dark_mode = not self.dark_mode
            # Start
            if self._start_rect().collidepoint(mx, my):
                self.done = True
            # Load
            import os
            from constants import SAVE_FILE
            if os.path.exists(SAVE_FILE) and self._load_rect().collidepoint(mx, my):
                self.load_saved = True
                self.done       = True

    def update(self):
        mx, my = pygame.mouse.get_pos()
        self._hover = None
        for i, m in enumerate(["HvH","HvC","CvC"]):
            if self._mode_rect(i).collidepoint(mx, my): self._hover = f"mode{i}"
        for n in [2,3,4]:
            if self._players_rect(n).collidepoint(mx, my): self._hover = f"np{n}"
        if self._dark_rect().collidepoint(mx, my): self._hover = "dark"
        if self._start_rect().collidepoint(mx, my): self._hover = "start"

    def draw(self, surf):
        bg = DARK_COLOR_BG if self.dark_mode else (235, 228, 210)
        surf.fill(bg)

        cx = WINDOW_WIDTH // 2
        fonts = self.fonts

        # Title
        draw_text(surf, fonts["large"], "♟  LUDO", COLOR_ACCENT, cx, 80)
        draw_text(surf, fonts["small"], "Classic Board Game", COLOR_TEXT_DIM, cx, 118)

        # ── Mode ──
        draw_text(surf, fonts["header"], "Game Mode", COLOR_TEXT_LIGHT if self.dark_mode else (40,40,50), cx, 165)
        labels = {"HvH":"👥 Human vs Human","HvC":"🤖 Human vs Computer","CvC":"🤖 Computer vs Computer"}
        for i, m in enumerate(["HvH","HvC","CvC"]):
            r      = self._mode_rect(i)
            active = self.mode == m
            hover  = self._hover == f"mode{i}"
            bg_c   = COLOR_ACCENT if active else (COLOR_BTN_HOVER if hover else COLOR_BTN_NORM)
            txt_c  = (30,30,40) if active else COLOR_TEXT_LIGHT
            draw_rounded_rect(surf, bg_c, r, radius=8)
            draw_text(surf, fonts["body"], labels[m], txt_c, r.centerx, r.centery)

        # ── Players ──
        draw_text(surf, fonts["header"], "Number of Players", COLOR_TEXT_LIGHT if self.dark_mode else (40,40,50), cx, 310)
        for n in [2, 3, 4]:
            r      = self._players_rect(n)
            active = self.num_players == n
            hover  = self._hover == f"np{n}"
            bg_c   = COLOR_ACCENT if active else (COLOR_BTN_HOVER if hover else COLOR_BTN_NORM)
            txt_c  = (30,30,40) if active else COLOR_TEXT_LIGHT
            draw_rounded_rect(surf, bg_c, r, radius=8)
            draw_text(surf, fonts["body"], str(n), txt_c, r.centerx, r.centery)

        # ── Dark mode ──
        dr   = self._dark_rect()
        dh   = self._hover == "dark"
        bg_c = COLOR_ACCENT if self.dark_mode else (COLOR_BTN_HOVER if dh else COLOR_BTN_NORM)
        txt_c= (30,30,40) if self.dark_mode else COLOR_TEXT_LIGHT
        draw_rounded_rect(surf, bg_c, dr, radius=8)
        draw_text(surf, fonts["body"], "🌙 Dark Mode", txt_c, dr.centerx, dr.centery)

        # ── Start ──
        sr   = self._start_rect()
        sh   = self._hover == "start"
        draw_rounded_rect(surf, COLOR_ACCENT if sh else (200,160,30), sr, radius=sr.height//2)
        draw_text(surf, fonts["header"], "▶  Start Game", (30,30,40), sr.centerx, sr.centery)

        # ── Load ──
        import os
        from constants import SAVE_FILE
        if os.path.exists(SAVE_FILE):
            lr = self._load_rect()
            draw_rounded_rect(surf, COLOR_BTN_HOVER, lr, radius=lr.height//2)
            draw_text(surf, fonts["body"], "📂 Load Saved Game", COLOR_TEXT_LIGHT, lr.centerx, lr.centery)

    # rect helpers
    def _mode_rect(self, i):
        w, h = 260, 40
        x = WINDOW_WIDTH//2 - w//2
        y = 185 + i * 50
        return pygame.Rect(x, y, w, h)

    def _players_rect(self, n):
        w, h = 70, 40
        total = 3*w + 2*20
        x = WINDOW_WIDTH//2 - total//2 + (n-2)*(w+20)
        y = 330
        return pygame.Rect(x, y, w, h)

    def _dark_rect(self):
        w, h = 180, 38
        return pygame.Rect(WINDOW_WIDTH//2 - w//2, 400, w, h)

    def _start_rect(self):
        w, h = 220, 50
        return pygame.Rect(WINDOW_WIDTH//2 - w//2, 460, w, h)

    def _load_rect(self):
        w, h = 220, 42
        return pygame.Rect(WINDOW_WIDTH//2 - w//2, 528, w, h)


# ── Main game UI ──────────────────────────────────────────────────────────────

class GameUI:
    """
    Renders the running game: board, tokens, panel, dice, messages.
    """

    PANEL_X = BOARD_OFFSET_X + BOARD_SIZE + 10
    PANEL_W = WINDOW_WIDTH - PANEL_X - 10

    def __init__(self, game: Game, fonts):
        self.game      = game
        self.fonts     = fonts
        self.board_gfx = Board(game.dark_mode)
        self._hover    = None
        self._press    = None

    # ── Event handling ────────────────────────────────────────────────────────

    def handle_event(self, event):
        g = self.game
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            self._press = self._button_at(mx, my)

            # Token click
            if g.state == GameState.CHOOSE and g.current_player.is_human:
                t = self._token_at(mx, my)
                if t and t in g.movable_tokens:
                    g.handle_token_click(t)

            # Roll button
            if self._press == "roll" and g.state == GameState.ROLL:
                g.handle_roll()

            # Pause
            if self._press == "pause":
                g.handle_pause()

            # Restart
            if self._press == "restart":
                return "setup"   # signal main loop

            # Save
            if self._press == "save" and g.state not in (GameState.ANIMATE, GameState.GAME_OVER):
                g.save()

            # Dark mode toggle
            if self._press == "dark":
                g.dark_mode = not g.dark_mode
                self.board_gfx.dark_mode = g.dark_mode
                self.board_gfx.mark_dirty()

        if event.type == pygame.MOUSEBUTTONUP:
            self._press = None

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self._hover = self._button_at(mx, my)

        return None

    def _button_at(self, mx, my):
        for name, r in self._button_rects().items():
            if r.collidepoint(mx, my): return name
        return None

    def _token_at(self, mx, my) -> Token | None:
        for p in self.game.players:
            for t in p.tokens:
                dist = math.hypot(t.pixel_x - mx, t.pixel_y - my)
                if dist < 18:
                    return t
        return None

    # ── Draw ─────────────────────────────────────────────────────────────────

    def draw(self, surf):
        g = self.game
        bg = DARK_COLOR_BG if g.dark_mode else COLOR_BG
        surf.fill(bg)

        # Board
        self.board_gfx.draw(surf)

        # Tokens
        self._draw_tokens(surf)

        # Side panel
        self._draw_panel(surf)

        # Overlays
        if g.state == GameState.PAUSED:
            self._draw_pause_overlay(surf)
        if g.state == GameState.GAME_OVER:
            self._draw_win_overlay(surf)

    def _draw_tokens(self, surf):
        g = self.game
        # Count tokens per cell to offset stacked ones
        cell_count: dict[tuple, int] = {}

        for p in g.players:
            for t in p.tokens:
                key = (t.pixel_x, t.pixel_y)
                cell_count[key] = cell_count.get(key, 0) + 1

        cell_drawn: dict[tuple, int] = {}
        for p in g.players:
            for t in p.tokens:
                is_movable  = (t in g.movable_tokens)
                is_selected = (t is g.selected_token)
                key = (t.pixel_x, t.pixel_y)
                idx = cell_drawn.get(key, 0)
                cell_drawn[key] = idx + 1
                count = cell_count[key]
                offset = 0
                if count > 1:
                    offset = (idx - count//2) * 8
                t.draw(surf, is_selected, is_movable, offset)

    def _draw_panel(self, surf):
        g     = self.game
        fonts = self.fonts
        PX    = self.PANEL_X
        PW    = self.PANEL_W
        PY    = BOARD_OFFSET_Y
        PH    = BOARD_SIZE

        # Panel background
        panel_rect = pygame.Rect(PX - 4, PY, PW + 4, PH)
        draw_rounded_rect(surf, COLOR_PANEL_BG, panel_rect, radius=12,
                          border=1, border_color=COLOR_PANEL_EDGE)

        cy = PY + 18
        cx = PX + PW // 2

        # Title
        draw_text(surf, fonts["header"], "LUDO", COLOR_ACCENT, cx, cy)
        cy += 30

        # Mode
        mode_label = {"HvH":"Human vs Human","HvC":"Human vs AI","CvC":"AI vs AI"}[g.mode]
        draw_text(surf, fonts["small"], mode_label, COLOR_TEXT_DIM, cx, cy)
        cy += 25

        # Divider
        pygame.draw.line(surf, COLOR_PANEL_EDGE, (PX, cy), (PX+PW, cy))
        cy += 12

        # Player scorecard
        for p in g.players:
            is_current = (p is g.current_player) and g.state not in (GameState.GAME_OVER, GameState.PAUSED)
            pc = PLAYER_COLORS[p.name]
            row_h = 46

            row_rect = pygame.Rect(PX + 2, cy, PW - 4, row_h)
            if is_current:
                draw_rounded_rect(surf, pc["dark"], row_rect, radius=6)
            else:
                draw_rounded_rect(surf, (40, 40, 55), row_rect, radius=6)

            # Colour swatch
            swatch = pygame.Rect(PX + 8, cy + 8, 10, row_h - 16)
            draw_rounded_rect(surf, pc["primary"], swatch, radius=4)

            # Name
            label = p.name + (" (You)" if p.is_human else " (AI)")
            draw_text(surf, fonts["body"], label, pc["light"], PX + 26, cy + 14, align="left")

            # Tokens done
            done = sum(1 for t in p.tokens if t.is_done)
            for di in range(4):
                tx = PX + 26 + di * 14
                ty = cy + 30
                col = pc["primary"] if di < done else (60, 60, 75)
                pygame.draw.circle(surf, col, (tx, ty), 5)

            # Captures badge
            if p.captures:
                draw_text(surf, fonts["small"], f"⚔ {p.captures}", COLOR_TEXT_DIM,
                          PX + PW - 10, cy + row_h//2, align="right")

            cy += row_h + 4

        cy += 8
        pygame.draw.line(surf, COLOR_PANEL_EDGE, (PX, cy), (PX+PW, cy))
        cy += 14

        # Dice
        dice_cx = PX + PW // 2
        disabled = (g.state != GameState.ROLL or not g.current_player.is_human)
        g.dice.draw(surf, dice_cx, cy + DICE_SIZE//2,
                    highlight=(g.state == GameState.ROLL and g.current_player.is_human),
                    disabled=disabled)
        cy += DICE_SIZE + 8

        # Roll button
        brs  = self._button_rects()
        roll_r = brs["roll"]
        hovR = self._hover == "roll"
        presR = self._press == "roll"
        roll_disabled = disabled
        pill_button(surf, fonts, "🎲  Roll Dice", roll_r, hovR, presR, roll_disabled,
                    color_bg=(80, 150, 80), color_hover=(100, 180, 100))
        cy = roll_r.bottom + 10

        # Message box
        msg_rect = pygame.Rect(PX + 4, cy, PW - 8, 50)
        draw_rounded_rect(surf, (35, 35, 50), msg_rect, radius=8)
        # Wrap long messages
        msg = g.message[:80]
        draw_text(surf, fonts["small"], msg, COLOR_TEXT_LIGHT, msg_rect.centerx, msg_rect.centery)
        cy = msg_rect.bottom + 10

        # Stats
        s = g.stats
        draw_text(surf, fonts["small"],
                  f"Turns:{s['turns']}  Sixes:{s['sixes']}  Captures:{s['captures']}",
                  COLOR_TEXT_DIM, cx, cy)
        cy += 20

        # Bottom buttons
        for key, label in [("save","💾 Save"), ("pause","⏸ Pause"),
                            ("dark","🌙"), ("restart","↩ Menu")]:
            r = brs[key]
            hov = self._hover == key
            prs = self._press == key
            pill_button(surf, fonts, label, r, hov, prs)

    def _button_rects(self) -> dict[str, pygame.Rect]:
        PX = self.PANEL_X
        PW = self.PANEL_W
        PH = BOARD_SIZE
        PY = BOARD_OFFSET_Y
        # Fixed positions from bottom of panel
        bottom = PY + PH - 8

        rects = {}
        rects["restart"] = pygame.Rect(PX + 4,  bottom - 38, PW//2 - 6, 34)
        rects["pause"]   = pygame.Rect(PX + PW//2 + 2, bottom - 38, PW//2 - 6, 34)
        rects["save"]    = pygame.Rect(PX + 4,  bottom - 78, PW//2 - 6, 34)
        rects["dark"]    = pygame.Rect(PX + PW//2 + 2, bottom - 78, PW//2 - 6, 34)

        # Roll button just below dice
        player_rows = len(self.game.players)
        panel_top   = PY + 18 + 30 + 25 + 12 + player_rows * 50 + 8 + 14
        dice_bottom = panel_top + DICE_SIZE + 8
        rects["roll"] = pygame.Rect(PX + 10, dice_bottom, PW - 20, 38)
        return rects

    def _draw_pause_overlay(self, surf):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0,0))
        cx = WINDOW_WIDTH//2
        cy = WINDOW_HEIGHT//2
        box = pygame.Rect(cx-120, cy-80, 240, 160)
        draw_rounded_rect(surf, COLOR_PANEL_BG, box, radius=14,
                          border=2, border_color=COLOR_ACCENT)
        draw_text(surf, self.fonts["large"], "PAUSED", COLOR_ACCENT, cx, cy-40)
        draw_text(surf, self.fonts["body"], "Press P or ⏸ to resume", COLOR_TEXT_DIM, cx, cy+10)

    def _draw_win_overlay(self, surf):
        g = self.game
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        cx = WINDOW_WIDTH//2
        cy = WINDOW_HEIGHT//2

        pc = PLAYER_COLORS[g.winner.name]
        box = pygame.Rect(cx-170, cy-120, 340, 240)
        draw_rounded_rect(surf, pc["dark"], box, radius=18,
                          border=3, border_color=COLOR_ACCENT)

        draw_text(surf, self.fonts["large"], "🏆  WINNER!", COLOR_ACCENT, cx, cy-80)
        draw_text(surf, self.fonts["header"], g.winner.name, pc["light"], cx, cy-35)
        draw_text(surf, self.fonts["body"],
                  f"Captures: {g.winner.captures}  |  Turns: {g.stats['turns']}",
                  COLOR_TEXT_DIM, cx, cy+5)
        draw_text(surf, self.fonts["body"], "Press  ↩  for menu", COLOR_TEXT_LIGHT, cx, cy+60)


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_caption("Ludo")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock  = pygame.time.Clock()
    fonts  = load_fonts()

    # ── Setup screen ──
    setup = SetupScreen(fonts)
    while not setup.done:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            setup.handle_event(event)
        setup.update()
        setup.draw(screen)
        pygame.display.flip()

    # ── Load or new game ──
    if setup.load_saved:
        game = Game.load()
        if game is None:
            game = Game(setup.mode, setup.num_players, setup.dark_mode)
    else:
        game = Game(setup.mode, setup.num_players, setup.dark_mode)

    ui = GameUI(game, fonts)

    # ── Game loop ──
    while True:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.handle_pause()
                if event.key == pygame.K_p:
                    game.handle_pause()
                if event.key == pygame.K_r and game.state == GameState.ROLL:
                    game.handle_roll()
                if event.key == pygame.K_s:
                    game.save()

            signal = ui.handle_event(event)
            if signal == "setup":
                # Return to setup
                setup2 = SetupScreen(fonts)
                setup2.done = False
                while not setup2.done:
                    dt2 = clock.tick(FPS)
                    for ev2 in pygame.event.get():
                        if ev2.type == pygame.QUIT: pygame.quit(); sys.exit()
                        setup2.handle_event(ev2)
                    setup2.update()
                    setup2.draw(screen)
                    pygame.display.flip()
                if setup2.load_saved:
                    game = Game.load() or Game(setup2.mode, setup2.num_players, setup2.dark_mode)
                else:
                    game = Game(setup2.mode, setup2.num_players, setup2.dark_mode)
                ui = GameUI(game, fonts)

        game.update(dt)
        ui.draw(screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
