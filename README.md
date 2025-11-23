# Chess

A lightweight Python chess game with a built‑in engine and optional computer opponent. It uses `pygame` for the UI and a custom searcher with an opening book. You can play PvP or against the AI, pick AI color, adjust depth/difficulty, and enable auto‑promotion.

## Requirements
- Python 3.9+ (tested with the bundled `.venv`; any modern 3.x should work)
- `pygame` (install via `pip install pygame` if not using the provided venv)

## Project layout
- `chess/ChessMain.py` — game UI and main loop.
- `chess/ChessAI.py` — searcher (PVS + heuristics) with adjustable depth and low‑depth “weaker” mode.
- `chess/openings.py` — small opening book with varied replies.
- `chess/board.py`, `chess/move.py`, `chess/ChessEngine.py` — game state and move logic.
- `chess/pieces/` — piece images.

## Running the game
From the project root:
```bash
# Option A: use the existing virtualenv
source .venv/bin/activate
python chess/ChessMain.py

# Option B: system Python
python3 -m venv .venv
source .venv/bin/activate
pip install pygame
python chess/ChessMain.py
```
Make sure you run it from a terminal with GUI access (not a headless shell), since `pygame` needs a display.

## Controls & options
- Menus: choose PvP or vs. computer; set AI color; tweak depth (1–10) and see an approximate Elo; toggle auto‑promotion and piece choice.
- In‑game: click squares to move; `Z` to undo last move; `R` to restart; `Esc` to return to menu.
- Promotions show a popup unless auto‑promotion is enabled.
- Castling asks for confirmation before executing.

## AI notes
- Depth 1–2 use a noisy, weaker selector for easier play; higher depths use the full search.
- An opening book supplies varied replies early on; if no book move is available, the searcher plays normally.

## Packaging for GitHub
If you don’t want to commit the virtualenv, remove `.venv/` before pushing, and consider adding it to `.gitignore`. Keep the `pieces/` images alongside the code.
