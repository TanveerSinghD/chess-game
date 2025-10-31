# move.py
class Move:
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_en_passant=False, is_castle=False):
        self.start_row, self.start_col = start_sq
        self.end_row, self.end_col = end_sq
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # Special move flags
        self.is_en_passant = is_en_passant
        if self.is_en_passant:
            self.piece_captured = 'bp' if self.piece_moved == 'wp' else 'wp'

        self.is_pawn_promotion = (self.piece_moved[1] == 'p') and (self.end_row == 0 or self.end_row == 7)
        self.promotion_choice = None  # 'Q','R','B','N'

        self.is_castle = is_castle

        # Equality / hashing
        self.move_id = (self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col)

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, r, c):
        return self.cols_to_files[c] + self.rows_to_ranks[r]

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def __hash__(self):
        return hash(self.move_id)
