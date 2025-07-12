A fully‑featured chess game built in Python, using a custom chess engine and a Pygame-based GUI. Supports all standard chess rules: legal move generation, pawn promotion, en passant, castling, check/checkmate detection, and move highlighting.

🚀 Features

Custom Chess Engine: generates all possible moves, filters illegal ones (no moving into check), handles special moves.

Pygame GUI: interactive board with drag & click controls, highlights for selected squares, valid moves, and checks.

Undo/Redo: press Z to undo the last move.

Algebraic Notation: moves are recorded and can be exported in standard format.

🐞 Challenges & Solutions

1. Legal King Moves & Checks

Problem: The king was initially allowed to move into squares where it would be in check, and could also capture defended enemy pieces—even if doing so exposed it to attack.

Solution: Implemented a move simulation inside get_valid_moves():

Make the move on a copy of the board.

Temporarily flip back the side to move so that in_check() tests the mover’s king.

Only accept moves that leave the king out of check.

Undo the move cleanly.

Outcome: After this fix, the king can no longer move into attacked squares, and capturing defended pieces is correctly blocked when it would expose the king. All legal checks and checkmates now register properly.

2. Check Highlighting

Problem: Checks on the enemy king (e.g., queen delivering check on h7) were not highlighted, and moves that gave check were filtered out.

Solution: Adjusted the logic that filtered valid moves so it no longer excluded moves that put the opponent in check. Now in_check() always refers to the side whose legality is being tested.

Outcome: Check moves are now visible, and a red highlight shows the king in check.


🎓 Skills & Techniques Learned

Backtracking & Move Simulation: Using make/undo paired calls and side-flipping to test move legality without side effects.

State Logging: Implemented logs (moveLog, enPassantLog, castleRightsLog) to fully restore game state on undo.

Deep Copy vs. Shallow: Learned when to use copy.deepcopy() (for nested rights), and when simple assignment suffices.

Pygame Basics: Board rendering, image loading, event handling, and surface highlighting.

Algebraic Notation: Converting coordinate moves into standard chess notation (including O-O/O-O-O, promotions, captures).

👀 Future Improvements

AI opponent with minimax and alpha-beta pruning.

PGN import/export.

Online multiplayer.

Mobile/touchscreen controls.

This project has been a great exercise in algorithm design, object‑oriented programming, and real‑time graphical interfaces—combining rigorous rule enforcement with interactive visuals.

