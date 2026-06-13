# 🎲 Ludo — Python / Pygame

A complete, production-quality desktop Ludo game built in Python with Pygame.  
Supports 2–4 players, Human vs Human / Human vs AI / AI vs AI modes, animated tokens, save/load, dark mode, and a simple but strategic AI opponent.

---

## Features

| Category | Details |
|---|---|
| **Players** | 2, 3, or 4 players (RED · BLUE · GREEN · YELLOW) |
| **Game Modes** | Human vs Human · Human vs Computer · Computer vs Computer |
| **Rules** | Standard Ludo — roll-6 to exit, captures, safe squares, home lane, exact dice to finish |
| **AI** | Heuristic strategy: capture > finish > safe-lane > closest-to-home > bring out |
| **Animation** | Smooth token glide, dice roll animation, glow on movable tokens |
| **Save / Load** | Full state serialised to `savegame.json` via JSON |
| **Dark Mode** | Full dark palette, toggleable before and during game |
| **Keyboard** | `R` = roll, `P` / `Esc` = pause, `S` = save |

---

## Installation

### Requirements
- Python 3.10 or newer
- pygame 2.x

```bash
pip install -r requirements.txt
```

### Run
```bash
cd ludo_game
python main.py
```

---

## Project Structure

```
ludo_game/
├── main.py        — Entry point: event loop, SetupScreen, GameUI renderer
├── game.py        — State machine (ROLL → CHOOSE → ANIMATE → NEXT_TURN → GAME_OVER)
├── board.py       — Cached board renderer (15×15 grid, home areas, paths, centre)
├── player.py      — Player class — holds 4 tokens, move validation, serialisation
├── token.py       — Token class — state machine (HOME→ACTIVE→LANE→DONE), animation
├── dice.py        — Dice class — random roll, pip renderer, frame animation
├── ai.py          — Heuristic AI — scores each legal move and picks the best
├── constants.py   — All sizes, colours, paths, safe squares, home positions
├── assets/        — Placeholder for sounds / images (game runs without them)
│   ├── dice/
│   └── sounds/
├── savegame.json  — Auto-created on save
└── README.md
```

---

## Architecture & Game Logic

### State Machine (`game.py`)

```
ROLL ──roll──► CHOOSE ──pick token──► ANIMATE ──done──► (check win / extra turn / NEXT_TURN)
  ▲                                        │
  └─────────── NEXT_TURN ◄────────────────┘
              (if captured) CAPTURE ──► NEXT_TURN
```

- **ROLL**: current player must roll the dice.  
- **CHOOSE**: player selects which token to move (only legal tokens are highlighted).  
- **ANIMATE**: tokens glide to their new position; game waits for all animations to finish.  
- **CAPTURE**: brief pause shown after an opponent's token is sent home.  
- **NEXT_TURN**: advance `current_idx` and enter ROLL.  
- **GAME_OVER**: all four tokens of one player are DONE — winner declared.  
- **PAUSED**: pause overlay; state frozen until resumed.

### Token State Machine (`token.py`)

```
HOME ──roll 6──► ACTIVE (main path 0-51) ──enter lane──► LANE (0-5) ──exact dice──► DONE
```

- Tokens are captured only on **ACTIVE** squares that are **not** in `SAFE_SQUARES`.  
- Rolling a **6** grants an extra turn after any move.  
- An **overshoot** (dice > remaining steps) is rejected — the token cannot move.

### AI Strategy (`ai.py`)

Each legal token is scored:

| Priority | Score bonus |
|---|---|
| Token reaches DONE | +10 000 |
| Token captures opponent | +500 |
| Token enters home lane (safe) | +200 |
| Proximity to finish (0–100) | scaled |
| Bring new token onto board (6 rolled) | +80 |
| Landing in danger zone | −30 × threat count |

The AI waits `AI_THINK_DELAY` ms before acting to feel natural.

### Board Layout (`board.py`, `constants.py`)

The board is a 15×15 grid.  
- **Home areas**: 6×6 corners per player.  
- **Main path**: 52 cells traversed clockwise, stored in `MAIN_PATH`.  
- **Home lane**: 6 private cells per player leading to the centre triangle.  
- **Safe squares**: indices `{0, 8, 13, 21, 26, 34, 39, 47}` — star markers, no captures.  
- The board surface is cached and only re-rendered when `dark_mode` changes.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `R` | Roll dice (human turn only) |
| `P` / `Esc` | Pause / Resume |
| `S` | Save game |

---

## Extending the Game

- **Sounds**: drop WAV files into `assets/sounds/` and hook `pygame.mixer` calls in `game.py` on capture/roll/win events.  
- **Board image**: replace `board.py`'s `_render()` with a `pygame.image.load("assets/board.png")` call.  
- **Network play**: replace the human input handler with socket messages carrying `(token_id, dice_value)`.  
- **Difficulty levels**: tune `ai.py` score weights or add lookahead (minimax) for a harder opponent.

---
