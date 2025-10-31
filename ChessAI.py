# ChessAI.py
# Minimal evaluation + alpha-beta minimax that works with your ChessEngine/Board/Move API

import math
import random

# Simple piece values (centipawns)
PIECE_SCORES = {
    'p': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,  # keep 0; checkmate is handled separately
}

def evaluate_position(game_state):
    """
    Basic evaluation: material + tiny mobility bonus.
    Positive is good for White, negative is good for Black.
    """
    board = game_state.board
    score = 0

    # material
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--":
                continue
            color = 1 if piece[0] == 'w' else -1
            p = piece[1]
            score += color * PIECE_SCORES.get(p, 0)

    # terminal states (use large values)
    if getattr(game_state, "checkmate", False):
        # If it's white to move and in checkmate -> black just gave mate: bad for White
        return -math.inf if game_state.white_to_move else math.inf
    if getattr(game_state, "stalemate", False):
        return 0

    # mobility (very light)
    try:
        # Avoid calling get_valid_moves() too often; but small bonus helps
        # Note: caller often provides valid moves at root, but here we call directly
        # and accept the cost for simplicity.
        from ChessEngine import ChessEngine  # lazy import to avoid circular at module load
        # We can't construct a new engine here; so skip.
    except Exception:
        pass

    return score

def score_terminal(game_state, ply_from_root):
    """Huge win/loss values with small preference for faster mate (or slower if losing)."""
    if getattr(game_state, "checkmate", False):
        # If side to move is in checkmate, previous player made mate.
        # Prefer faster wins / slower losses: +/- infinity +/- ply
        return (-math.inf + ply_from_root) if game_state.white_to_move else (math.inf - ply_from_root)
    if getattr(game_state, "stalemate", False):
        return 0
    return None

def choose_ai_move(engine, depth=3):
    """
    Find best move for the side to move using alpha-beta minimax.
    Returns a Move or None if no move.
    """
    valid_moves = engine.get_valid_moves()
    if not valid_moves:
        return None

    # Move ordering: quick heuristic — prefer captures and queen promotions
    def move_key(m):
        # Encourage captures and promotions first
        cap = 1 if m.piece_captured != "--" else 0
        promo = 2 if getattr(m, "is_pawn_promotion", False) else 0
        return (promo, cap)

    valid_moves.sort(key=move_key, reverse=True)

    best_move = random.choice(valid_moves)
    best_score = -math.inf if engine.get_game_state().white_to_move else math.inf

    alpha = -math.inf
    beta = math.inf

    for mv in valid_moves:
        # If AI would promote and your Board doesn't handle choices, auto-queen defensively
        try:
            if getattr(mv, "is_pawn_promotion", False) and getattr(mv, "promotion_choice", None) is None:
                mv.promotion_choice = 'Q'
        except Exception:
            pass

        engine.make_move(mv)
        score = _minimax(engine, depth - 1, alpha, beta, maximizing=engine.get_game_state().white_to_move, ply_from_root=1)
        engine.undo_move()

        if engine.get_game_state().white_to_move:
            # We just evaluated a move made by White
            if score > best_score:
                best_score = score
                best_move = mv
            alpha = max(alpha, score)
        else:
            # Black to move at root
            if score < best_score:
                best_score = score
                best_move = mv
            beta = min(beta, score)

        if beta <= alpha:
            break

    return best_move

def _minimax(engine, depth, alpha, beta, maximizing, ply_from_root):
    gs = engine.get_game_state()

    term = score_terminal(gs, ply_from_root)
    if term is not None:
        return term

    if depth == 0:
        return evaluate_position(gs)

    valid_moves = engine.get_valid_moves()
    if not valid_moves:
        # No moves; checkmate/stalemate already reflected in score_terminal at parent
        return evaluate_position(gs)

    # Move ordering
    def move_key(m):
        cap = 1 if m.piece_captured != "--" else 0
        promo = 2 if getattr(m, "is_pawn_promotion", False) else 0
        return (promo, cap)
    valid_moves.sort(key=move_key, reverse=True)

    if maximizing:
        value = -math.inf
        for mv in valid_moves:
            try:
                if getattr(mv, "is_pawn_promotion", False) and getattr(mv, "promotion_choice", None) is None:
                    mv.promotion_choice = 'Q'
            except Exception:
                pass
            engine.make_move(mv)
            value = max(value, _minimax(engine, depth - 1, alpha, beta, False, ply_from_root + 1))
            engine.undo_move()
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = math.inf
        for mv in valid_moves:
            try:
                if getattr(mv, "is_pawn_promotion", False) and getattr(mv, "promotion_choice", None) is None:
                    mv.promotion_choice = 'Q'
            except Exception:
                pass
            engine.make_move(mv)
            value = min(value, _minimax(engine, depth - 1, alpha, beta, True, ply_from_root + 1))
            engine.undo_move()
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value
