from __future__ import annotations

from typing import List

from board import Board

class ChessEngine:
    def __init__(self) -> None:
        self.game_state = Board()

    def get_board_state(self):
        return self.game_state.board

    def get_game_state(self):
        return self.game_state

    def get_valid_moves(self):
        return self.game_state.get_valid_moves()

    def make_move(self, move) -> None:
        self.game_state.make_move(move)

    def undo_move(self) -> None:
        self.game_state.undo_move()
