Chess Game with AI, Castling, Promotion, and Custom UI
======================================================

Overview
--------
This project is a complete chess game built in Python using the Pygame library. 
It includes both Player vs Player and Player vs Computer modes with a clean, 
interactive graphical interface, supporting all official chess rules.

Features
--------
1. Game Modes
   - Two Player Mode: Two players can play locally on the same device.
   - Vs Computer Mode: Play against a computer opponent powered by a Minimax-based AI.
   - AI Color Option: Choose whether the AI plays as White or Black. The board automatically 
     rotates so the human player always plays from the bottom.

2. Core Chess Mechanics
   - Legal move validation: All moves are validated through rule checks ensuring 
     no illegal moves are possible.
   - Check, Checkmate, and Stalemate detection.
   - Undo and Restart functionality.
   - Key controls: 
       Z → Undo
       R → Restart
       ESC → Return to Main Menu

3. Special Moves
   - Castling:
     Supports both kingside and queenside castling.
     Checks that the king and rook haven’t moved, there are no pieces between them,
     and the king does not pass through or into check.
     Includes a confirmation popup before finalizing the castle.
   
   - En Passant:
     Automatically recognized when a pawn moves two squares forward and an opposing pawn 
     can capture it on the next move.
     The move is available for one turn only.

   - Promotion:
     When a pawn reaches the opposite end of the board, a promotion overlay appears with 
     options to promote to a Queen, Rook, Bishop, or Knight.
     The Options Menu includes an Auto Promotion toggle allowing a default promotion choice.

4. User Interface
   - Main Menu with hover effects:
       Play vs Player
       Play vs Computer
       Options
       Quit
   - Options Menu:
       - Set AI Color (White or Black)
       - Set AI Search Depth (1–10)
       - Enable/Disable Auto Promotion
       - Choose default promotion piece (Q, R, B, N)
   - Top Bar showing current mode, active player, and depth setting.
   - Visual highlights for selected squares and legal moves.
   - Board flips automatically depending on player color.
   - Smooth overlays for promotion and castling confirmation.

5. Artificial Intelligence
   - Uses a basic Minimax algorithm with adjustable search depth (1–10).
   - Evaluates positions based on material balance and move potential.
   - Higher depth values result in stronger but slower decision-making.

File Structure
--------------
chess/
│
├── ChessMain.py       - Handles the main menu, UI rendering, and game loop.
├── ChessEngine.py     - Connects the UI to the board state logic.
├── board.py           - Core chess logic: move generation, validation, and rules.
├── move.py            - Move class defining notation, equality, and flags.
├── ChessAI.py         - Minimax AI logic for computer opponent.
└── pieces/            - Folder containing all chess piece PNG images.

How It Works
------------
1. The Board class manages chess rules, move generation, and legality checks.
2. The ChessEngine acts as a bridge between the Board and GUI.
3. The ChessMain script handles player input, rendering, and in-game logic.
4. The ChessAI module runs Minimax recursion to determine the best move for the computer.
5. Pygame updates the display at each frame with smooth transitions and visual feedback.

Running the Game
----------------
1. Install required dependencies:
   pip install pygame

2. Run the main game:
   python ChessMain.py

3. Select your preferred mode and start playing.

Credits
-------
Developed in Python with Pygame.
Implements all official chess rules with an interactive and user-friendly interface.
