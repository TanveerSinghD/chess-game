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

    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_to_move = not self.white_to_move

        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

    def undo_move(self):
        if self.move_log:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move

            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)

    def get_valid_moves(self):
        """
        Generate all legal moves for the current side, filtering out
        any move that would leave the mover’s king in check.
        """
        all_moves = self.get_all_possible_moves()
        valid_moves = []
        original_side = self.white_to_move

        for move in all_moves:
            # 1) Make the move (this flips white_to_move)
            self.make_move(move)

            # 2) Temporarily set back to the side who just moved,
            #    so in_check() checks their king
            self.white_to_move = original_side
            king_in_check = self.in_check()

            # 3) Restore white_to_move to “next-to-move” for undo
            self.white_to_move = not original_side

            # 4) Only keep if your king is not left in check
            if not king_in_check:
                valid_moves.append(move)

            # 5) Undo so the board is back to its original state
            self.undo_move()

        # Update checkmate/stalemate flags
        if not valid_moves:
            # If no legal moves and you’re currently in check → checkmate
            if self.in_check():
                self.checkmate = True
            else:
                # Otherwise it’s stalemate
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
        return any(move.end_row == r and move.end_col == c for move in opponent_moves)

    def get_all_possible_moves(self):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece[0] == ('w' if self.white_to_move else 'b'):
                    self._get_piece_moves(r, c, piece, moves)
        return moves

    def get_all_attacks(self):
        attacks = []
        original_turn = self.white_to_move
        self.white_to_move = not self.white_to_move
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece[0] == ('w' if self.white_to_move else 'b'):
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
            self._get_king_moves(r, c, moves)

    def _get_pawn_moves(self, r, c, moves):
        direction = -1 if self.white_to_move else 1
        start_row = 6 if self.white_to_move else 1
        enemy_color = 'b' if self.white_to_move else 'w'

        if self.board[r + direction][c] == "--":
            moves.append(Move((r, c), (r + direction, c), self.board))
            if r == start_row and self.board[r + 2 * direction][c] == "--":
                moves.append(Move((r, c), (r + 2 * direction, c), self.board))

        for dc in [-1, 1]:
            if 0 <= c + dc < 8:
                end_piece = self.board[r + direction][c + dc]
                if end_piece != "--" and end_piece[0] == enemy_color:
                    moves.append(Move((r, c), (r + direction, c + dc), self.board))

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
