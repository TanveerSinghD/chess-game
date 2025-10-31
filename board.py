# board.py
from move import Move

class Board:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.white_to_move = True
        self.move_log = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.checkmate = False
        self.stalemate = False

        # Castling rights
        self.castling_rights = {'wks': True, 'wqs': True, 'bks': True, 'bqs': True}
        self.castling_rights_log = [self.castling_rights.copy()]

        # En passant target square (row, col) jumped over by a double pawn push
        self.en_passant_target = None
        self.en_passant_log = [self.en_passant_target]

    def make_move(self, move):
        # Place piece
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved

        # Update king location
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # En passant capture: remove the pawn behind the end square
        if move.is_en_passant:
            if move.piece_moved == 'wp':
                self.board[move.end_row + 1][move.end_col] = "--"
            else:
                self.board[move.end_row - 1][move.end_col] = "--"

        # Castling rook move
        if move.is_castle:
            if move.piece_moved == "wK":
                if move.end_col == 6:
                    self.board[7][5] = "wR"; self.board[7][7] = "--"
                elif move.end_col == 2:
                    self.board[7][3] = "wR"; self.board[7][0] = "--"
            else:
                if move.end_col == 6:
                    self.board[0][5] = "bR"; self.board[0][7] = "--"
                elif move.end_col == 2:
                    self.board[0][3] = "bR"; self.board[0][0] = "--"

        # Promotion: replace pawn with chosen piece (default Q)
        if move.is_pawn_promotion:
            choice = (move.promotion_choice or 'Q').upper()
            color = move.piece_moved[0]
            self.board[move.end_row][move.end_col] = color + choice

        # Log move
        self.move_log.append(move)

        # Update rights and en passant target
        self._update_castling_rights(move)
        self.castling_rights_log.append(self.castling_rights.copy())
        self._update_en_passant_target(move)

        # Flip turn
        self.white_to_move = not self.white_to_move

    def undo_move(self):
        if not self.move_log:
            return
        move = self.move_log.pop()

        # Unflip turn
        self.white_to_move = not self.white_to_move

        # Restore rights and ep target
        if self.castling_rights_log:
            self.castling_rights_log.pop()
            if self.castling_rights_log:
                self.castling_rights = self.castling_rights_log[-1].copy()
        if self.en_passant_log:
            self.en_passant_log.pop()
            self.en_passant_target = self.en_passant_log[-1] if self.en_passant_log else None

        # Undo promotion
        if move.is_pawn_promotion:
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
        else:
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured

        # Undo EP
        if move.is_en_passant:
            if move.piece_moved == 'wp':
                self.board[move.end_row + 1][move.end_col] = 'bp'
            else:
                self.board[move.end_row - 1][move.end_col] = 'wp'
            self.board[move.end_row][move.end_col] = "--"

        # Undo castling
        if move.is_castle:
            if move.piece_moved == "wK":
                if move.end_col == 6:
                    self.board[7][7] = "wR"; self.board[7][5] = "--"
                elif move.end_col == 2:
                    self.board[7][0] = "wR"; self.board[7][3] = "--"
            else:
                if move.end_col == 6:
                    self.board[0][7] = "bR"; self.board[0][5] = "--"
                elif move.end_col == 2:
                    self.board[0][0] = "bR"; self.board[0][3] = "--"

        # Restore king location
        if move.piece_moved == "wK":
            self.white_king_location = (move.start_row, move.start_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.start_row, move.start_col)

        # Reset flags (re-evaluated later)
        self.checkmate = False
        self.stalemate = False

    def get_valid_moves(self):
        all_moves = self.get_all_possible_moves()
        valid_moves = []
        original_side = self.white_to_move

        for move in all_moves:
            self.make_move(move)
            # check the mover's king safety
            self.white_to_move = original_side
            king_in_check = self.in_check()
            self.white_to_move = not original_side
            if not king_in_check:
                valid_moves.append(move)
            self.undo_move()

        if not valid_moves:
            if self.in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        return valid_moves

    def in_check(self):
        if self.white_to_move:
            return self.square_under_attack(*self.white_king_location)
        else:
            return self.square_under_attack(*self.black_king_location)

    def square_under_attack(self, r, c):
        opponent_moves = self.get_all_attacks()
        return any(m.end_row == r and m.end_col == c for m in opponent_moves)

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != "--" and piece[0] == ('w' if self.white_to_move else 'b'):
                    self._get_piece_moves(r, c, piece, moves)
        return moves

    def get_all_attacks(self):
        attacks = []
        original_turn = self.white_to_move
        self.white_to_move = not self.white_to_move
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != "--" and piece[0] == ('w' if self.white_to_move else 'b'):
                    self._get_attacking_moves(r, c, piece, attacks)
        self.white_to_move = original_turn
        return attacks

    def _get_attacking_moves(self, r, c, piece, moves):
        if piece[1] == 'p':
            direction = -1 if piece[0] == 'w' else 1
            for dc in [-1, 1]:
                end_r, end_c = r + direction, c + dc
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    moves.append(Move((r, c), (end_r, end_c), self.board))
        elif piece[1] == 'R':
            self._get_sliding_moves(r, c, moves, [(-1, 0), (1, 0), (0, -1), (0, 1)])
        elif piece[1] == 'B':
            self._get_sliding_moves(r, c, moves, [(-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif piece[1] == 'Q':
            self._get_sliding_moves(r, c, moves, [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)])
        elif piece[1] == 'N':
            knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2), (2, -1), (1, -2), (2, 1), (1, 2)]
            for dr, dc in knight_moves:
                end_r, end_c = r + dr, c + dc
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    moves.append(Move((r, c), (end_r, end_c), self.board))
        elif piece[1] == 'K':
            king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in king_moves:
                end_r, end_c = r + dr, c + dc
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

    def _get_piece_moves(self, r, c, piece, moves):
        if piece[1] == 'p':
            self._get_pawn_moves(r, c, moves)
        elif piece[1] == 'R':
            self._get_rook_moves(r, c, moves)
        elif piece[1] == 'N':
            self._get_knight_moves(r, c, moves)
        elif piece[1] == 'B':
            self._get_bishop_moves(r, c, moves)
        elif piece[1] == 'Q':
            self._get_queen_moves(r, c, moves)
        elif piece[1] == 'K':
            self._get_king_moves(r, c, moves)  # includes castling add-on

    def _get_pawn_moves(self, r, c, moves):
        direction = -1 if self.white_to_move else 1
        start_row = 6 if self.white_to_move else 1
        enemy_color = 'b' if self.white_to_move else 'w'

        # forward one
        fr = r + direction
        if 0 <= fr < 8 and self.board[fr][c] == "--":
            moves.append(Move((r, c), (fr, c), self.board))
            # forward two from start
            fr2 = r + 2 * direction
            if r == start_row and self.board[fr2][c] == "--":
                moves.append(Move((r, c), (fr2, c), self.board))

        # normal captures
        for dc in [-1, 1]:
            ec = c + dc
            er = r + direction
            if 0 <= er < 8 and 0 <= ec < 8:
                end_piece = self.board[er][ec]
                if end_piece != "--" and end_piece[0] == enemy_color:
                    moves.append(Move((r, c), (er, ec), self.board))

        # en passant captures
        if self.en_passant_target is not None:
            target_r, target_c = self.en_passant_target
            if r + direction == target_r and abs(c - target_c) == 1:
                moves.append(Move((r, c), (target_r, target_c), self.board, is_en_passant=True))

    def _get_rook_moves(self, r, c, moves):
        self._get_sliding_moves(r, c, moves, [(-1, 0), (1, 0), (0, -1), (0, 1)])

    def _get_bishop_moves(self, r, c, moves):
        self._get_sliding_moves(r, c, moves, [(-1, -1), (-1, 1), (1, -1), (1, 1)])

    def _get_queen_moves(self, r, c, moves):
        self._get_sliding_moves(r, c, moves, [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)])

    def _get_sliding_moves(self, r, c, moves, directions):
        enemy_color = 'b' if self.white_to_move else 'w'
        for dr, dc in directions:
            for i in range(1, 8):
                end_r, end_c = r + dr * i, c + dc * i
                if 0 <= end_r < 8 and 0 <= end_c < 8:
                    end_piece = self.board[end_r][end_c]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_r, end_c), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((r, c), (end_r, end_c), self.board))
                        break
                    else:
                        break
                else:
                    break

    def _get_knight_moves(self, r, c, moves):
        knight_moves = [(-2, -1), (-1, -2), (-2, 1), (-1, 2), (2, -1), (1, -2), (2, 1), (1, 2)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in knight_moves:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece == "--" or end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_r, end_c), self.board))

    def _get_king_moves(self, r, c, moves):
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        ally_color = 'w' if self.white_to_move else 'b'
        for dr, dc in king_moves:
            end_r, end_c = r + dr, c + dc
            if 0 <= end_r < 8 and 0 <= end_c < 8:
                end_piece = self.board[end_r][end_c]
                if end_piece == "--" or end_piece[0] != ally_color:
                    # ensure not moving into check
                    original_king_pos = self.white_king_location if self.white_to_move else self.black_king_location
                    if self.white_to_move:
                        self.white_king_location = (end_r, end_c)
                    else:
                        self.black_king_location = (end_r, end_c)

                    temp = self.board[end_r][end_c]
                    self.board[r][c] = "--"
                    self.board[end_r][end_c] = "wK" if self.white_to_move else "bK"
                    in_check = self.in_check()
                    self.board[r][c] = "wK" if self.white_to_move else "bK"
                    self.board[end_r][end_c] = temp

                    if self.white_to_move:
                        self.white_king_location = original_king_pos
                    else:
                        self.black_king_location = original_king_pos

                    if not in_check:
                        moves.append(Move((r, c), (end_r, end_c), self.board))

        # Add castling moves
        self._add_castle_moves(r, c, moves)

    # ---- Castling helpers ----
    def _add_castle_moves(self, r, c, moves):
        if self.in_check():
            return  # cannot castle out of check

        if self.white_to_move and self.board[r][c] == "wK" and (r, c) == (7, 4):
            if self.castling_rights['wks']:
                if self.board[7][5] == "--" and self.board[7][6] == "--":
                    if not self.square_under_attack(7, 5) and not self.square_under_attack(7, 6):
                        moves.append(Move((7, 4), (7, 6), self.board, is_castle=True))
            if self.castling_rights['wqs']:
                if self.board[7][1] == "--" and self.board[7][2] == "--" and self.board[7][3] == "--":
                    if not self.square_under_attack(7, 3) and not self.square_under_attack(7, 2):
                        moves.append(Move((7, 4), (7, 2), self.board, is_castle=True))

        elif (not self.white_to_move) and self.board[r][c] == "bK" and (r, c) == (0, 4):
            if self.castling_rights['bks']:
                if self.board[0][5] == "--" and self.board[0][6] == "--":
                    if not self.square_under_attack(0, 5) and not self.square_under_attack(0, 6):
                        moves.append(Move((0, 4), (0, 6), self.board, is_castle=True))
            if self.castling_rights['bqs']:
                if self.board[0][1] == "--" and self.board[0][2] == "--" and self.board[0][3] == "--":
                    if not self.square_under_attack(0, 3) and not self.square_under_attack(0, 2):
                        moves.append(Move((0, 4), (0, 2), self.board, is_castle=True))

    def _update_castling_rights(self, move):
        cr = self.castling_rights.copy()
        # If a king moves, lose both rights
        if move.piece_moved == "wK":
            cr['wks'] = False; cr['wqs'] = False
        elif move.piece_moved == "bK":
            cr['bks'] = False; cr['bqs'] = False

        # If a rook moves from its starting square, lose that side
        if move.piece_moved == "wR":
            if (move.start_row, move.start_col) == (7, 0): cr['wqs'] = False
            if (move.start_row, move.start_col) == (7, 7): cr['wks'] = False
        elif move.piece_moved == "bR":
            if (move.start_row, move.start_col) == (0, 0): cr['bqs'] = False
            if (move.start_row, move.start_col) == (0, 7): cr['bks'] = False

        # If a rook is captured on its starting square, lose that side
        if move.piece_captured == "wR":
            if (move.end_row, move.end_col) == (7, 0): cr['wqs'] = False
            if (move.end_row, move.end_col) == (7, 7): cr['wks'] = False
        elif move.piece_captured == "bR":
            if (move.end_row, move.end_col) == (0, 0): cr['bqs'] = False
            if (move.end_row, move.end_col) == (0, 7): cr['bks'] = False

        self.castling_rights = cr

    def _update_en_passant_target(self, move):
        """Set/clear the en passant target square based on the last move."""
        target = None
        if move.piece_moved[1] == 'p':
            if move.start_row == 6 and move.end_row == 4:  # white double
                target = (5, move.start_col)
            elif move.start_row == 1 and move.end_row == 3:  # black double
                target = (2, move.start_col)
        self.en_passant_target = target
        self.en_passant_log.append(self.en_passant_target)
