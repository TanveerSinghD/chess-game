from __future__ import annotations

import time
import math
import random
from collections import defaultdict
from typing import List, Optional, Tuple

from openings import get_book_reply
from move import Move

# ------------------ Tunables (safe defaults) ------------------
INFINITY = 10_000_000
MATE = 9_000_000
DRAW = 0

# Time control
DEFAULT_TIME_MS = 250          # soft time cap per move (you can pass a custom time_ms)
ABORT_CHECK_INTERVAL = 1024    # nodes between time checks (more responsive to time caps)

# Quiescence
QDEPTH_MAX = 6                 # max extra plies in quiescence
DELTA_MARGIN = 150             # delta pruning margin (centipawns)

# Pruning/Reductions
NULL_MOVE_R = 2                # base null-move reduction
LMR_BASE = 1                   # base late move reduction
FUTILITY_MARGIN = 90           # static futility margin at depth=1 (scaled with depth)
RAZOR_MARGIN = 200             # razoring margin at depth=1

# Heuristics
HISTORY_BONUS = 32
KILLER_SLOTS = 2               # two killer moves per ply

# Piece values (centipawns)
PVAL = {'p': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}

# Evaluation tweaks
BISHOP_PAIR_BONUS = 40
DOUBLED_PAWN_PENALTY = 12
ISOLATED_PAWN_PENALTY = 15
PASSED_PAWN_BASE = 20
PASSED_PAWN_SCALE = 8
ROOK_OPEN_FILE_BONUS = 20
ROOK_SEMI_OPEN_FILE_BONUS = 12
MOBILITY_WEIGHT = 2
ROOK_ON_7TH_BONUS = 35
ROOK_BEHIND_PASSED_BONUS = 25
KING_CENTER_END_WEIGHT = 12
PASSED_END_SCALER = 0.6
KING_SHIELD_BONUS = 12
KING_OPEN_FILE_PENALTY = 16
KING_SEMI_OPEN_FILE_PENALTY = 8
BACKWARD_PAWN_PENALTY = 10
CONNECTED_PASSED_BONUS = 25
SPACE_CENTER_BONUS = 3
MOBILITY_WEIGHTS = {'N': 4, 'B': 5, 'R': 3, 'Q': 2}
SEE_DROP_MARGIN = -50
LMP_DEPTH = 3
LMP_MOVE_THRESHOLD = 14

# Game phase (midgame → endgame blend)
PHASE_WEIGHTS = {'N': 1, 'B': 1, 'R': 2, 'Q': 4}
PHASE_MAX = 24  # 4N, 4B, 4R, 2Q across both sides

# Simple piece-square tables (midgame-ish), white POV; mirrored for black
PST_P = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 50, 50, 50, 50, 50, 50, 50, 50],
    [ 10, 10, 20, 30, 30, 20, 10, 10],
    [  5,  5, 10, 25, 25, 10,  5,  5],
    [  0,  0,  0, 20, 20,  0,  0,  0],
    [  5, -5,-10,  0,  0,-10, -5,  5],
    [  5, 10, 10,-20,-20, 10, 10,  5],
    [  0,  0,  0,  0,  0,  0,  0,  0],
]
PST_N = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50],
]
PST_B = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20],
]
PST_R = [
    [  0,  0,  5, 10, 10,  5,  0,  0],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [ -5,  0,  0,  0,  0,  0,  0, -5],
    [  5, 10, 10, 10, 10, 10, 10,  5],
    [  0,  0,  5, 15, 15,  5,  0,  0],
]
PST_Q = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-10,  5,  5,  5,  5,  5,  5,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  5,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20],
]
PST_K = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-30,-30,-40,-40,-30,-30,-30],
    [-20,-20,-20,-20,-20,-20,-20,-20],
    [-10,-10,-10,-10,-10,-10,-10,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 30, 30, 10,  0,  0, 10, 30, 30],
    [ 30, 40, 20,  0,  0, 20, 40, 30],
]
PST_K_END = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 10, 20, 20, 10,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 10, 20, 20, 10,-10,-30],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-50,-40,-30,-20,-20,-30,-40,-50],
]
PST = {'p': PST_P, 'N': PST_N, 'B': PST_B, 'R': PST_R, 'Q': PST_Q, 'K': PST_K}

# ----------------- Global search state -----------------
TT = {}  # key -> (depth, score, flag, best_move_id)
HISTORY = defaultdict(int)
KILLERS = defaultdict(lambda: [None, None])  # ply -> [m1, m2]
NODE_COUNT = 0
TIME_LIMIT = 0.0
TIME_START = 0.0
STOP = False

FLAG_EXACT, FLAG_ALPHA, FLAG_BETA = 0, 1, 2

# ----------------- Public entrypoint -------------------
def choose_ai_move(engine, depth: int = 3, time_ms: int = DEFAULT_TIME_MS) -> Optional[Move]:
    """
    Iterative deepening search up to 'depth' plies or until 'time_ms' elapses.
    Returns the best Move for side-to-move.
    """
    # For very low depths, intentionally add noise to make the play weaker
    if depth <= 2:
        noise = 300 if depth == 1 else 150
        return _weak_move_with_noise(engine, noise)

    # Quick opening-book lookup (does not consume search time)
    book_move = _book_move(engine)
    if book_move:
        return book_move

    global TT, HISTORY, KILLERS, NODE_COUNT, TIME_LIMIT, TIME_START, STOP
    NODE_COUNT = 0
    STOP = False
    TIME_START = time.perf_counter()
    TIME_LIMIT = TIME_START + (max(50, time_ms) / 1000.0)  # never below 50ms

    # Iterative deepening with aspiration windows
    best_move = None
    alpha, beta = -INFINITY, INFINITY
    last_score = 0

    for d in range(1, max(1, depth) + 1):
        if STOP:
            break
        # Tight aspiration window around last score
        window = 50 + 10 * (d - 1)
        a, b = last_score - window, last_score + window
        score, move = _pvs_root(engine, d, a, b)
        if STOP:
            break
        # If fail-low/high, re-search with full window
        if score <= a or score >= b:
            score, move = _pvs_root(engine, d, -INFINITY, INFINITY)
            if STOP: break
        if move:
            best_move = move
            last_score = score

    return best_move

# ----------------- Root search -----------------
def _pvs_root(engine, depth, alpha, beta):
    global NODE_COUNT
    game = engine.get_game_state()
    moves = engine.get_valid_moves()
    if not moves:
        return (_mate_or_draw(game), None)

    # seed TT move
    tt_move = _probe_tt_best(game)
    _order_moves(game, moves, tt_move, ply=0)

    best = -INFINITY
    best_move = None

    for i, mv in enumerate(moves):
        _maybe_set_default_promo(mv)
        engine.make_move(mv)
        score = -_pvs(engine, depth - 1, -beta, -alpha, 1, allow_null=True)
        engine.undo_move()

        if STOP: break

        if score > best:
            best = score
            best_move = mv
            if score > alpha:
                alpha = score
        if alpha >= beta:
            _store_tt(game, depth, best, FLAG_BETA, mv)
            return best, best_move

    _store_tt(game, depth, best, FLAG_EXACT, best_move)
    return best, best_move

# ----------------- Principal Variation Search -----------------
def _pvs(engine, depth, alpha, beta, ply, allow_null):
    global NODE_COUNT, STOP
    NODE_COUNT += 1
    if NODE_COUNT % ABORT_CHECK_INTERVAL == 0 and time.perf_counter() >= TIME_LIMIT:
        STOP = True
        return 0

    game = engine.get_game_state()

    # Terminal / depth
    if depth <= 0:
        return _quiescence(engine, alpha, beta, ply, 0)

    # TT lookup
    tt = _probe_tt(game)
    if tt and tt['depth'] >= depth:
        if tt['flag'] == FLAG_EXACT:
            return tt['score']
        elif tt['flag'] == FLAG_ALPHA:
            alpha = max(alpha, tt['score'])
        elif tt['flag'] == FLAG_BETA:
            beta = min(beta, tt['score'])
        if alpha >= beta:
            return tt['score']

    in_check = game.in_check()

    # Null-move pruning (skip if in check; also avoid in low material positions)
    if allow_null and depth >= 3 and not in_check:
        # Make a null move by just toggling side-to-move using a lightweight hack:
        # (We can’t null-move via engine; emulate by trusting pruning on quiet positions.)
        # Use a stand-pat eval to decide if pruning is plausible.
        eval0 = _eval(game)
        if eval0 - 50 > beta:  # only try null if already quite good
            R = NULL_MOVE_R + depth // 4
            score = -_pvs(engine, depth - 1 - R, -beta, -beta + 1, ply + 1, allow_null=False)
            if STOP: return 0
            if score >= beta:
                return beta

    # Razoring (shallow depth, quiet node)
    if not in_check and depth == 1:
        stand = _eval(game)
        if stand + RAZOR_MARGIN <= alpha:
            return _quiescence(engine, alpha, beta, ply, 0)

    # Generate moves
    moves = engine.get_valid_moves()
    if not moves:
        return _mate_or_draw(game)

    # Move ordering
    tt_move = tt['best'] if tt else None
    _order_moves(game, moves, tt_move, ply)

    best = -INFINITY
    best_move = None
    legal_index = 0

    for mv in moves:
        _maybe_set_default_promo(mv)
        tactical = _is_tactical(game, mv)

        # Late move pruning for quiet moves at shallow depth
        if depth <= LMP_DEPTH and not in_check and not tactical and legal_index >= LMP_MOVE_THRESHOLD:
            legal_index += 1
            continue

        # Futility pruning (quiet late moves, shallow) + SEE guard
        if depth <= 2 and not in_check and not tactical:
            stand = _eval(game)
            margin = FUTILITY_MARGIN * depth
            if stand + margin <= alpha:
                legal_index += 1
                continue
            if _see(game.board, mv) < SEE_DROP_MARGIN:
                legal_index += 1
                continue

        # PVS window: full window for first move; narrow for rest
        engine.make_move(mv)
        gave_check = game.in_check()

        # Extend for giving check or a passed pawn reaching 7th
        ext = 1 if gave_check else 0
        mover_color = mv.piece_moved[0]
        if mv.piece_moved[1] == 'p':
            if (mover_color == 'w' and mv.end_row == 1) or (mover_color == 'b' and mv.end_row == 6):
                if _is_passed_pawn(game.board, mover_color, mv.end_row, mv.end_col):
                    ext = max(ext, 1)

        search_depth = depth - 1 + ext

        if legal_index == 0:
            score = -_pvs(engine, search_depth, -beta, -alpha, ply + 1, allow_null=True)
        else:
            # Late Move Reductions for non-tactical late moves
            reduce = 0
            if search_depth >= 2 and not in_check and not tactical and not gave_check:
                reduce = LMR_BASE + (legal_index // 4) + (depth // 5)
                reduce = min(reduce, search_depth - 1)
            # Try reduced null-window search
            score = -_pvs(engine, search_depth - reduce, -alpha - 1, -alpha, ply + 1, allow_null=True)
            if not STOP and score > alpha and reduce > 0:
                # Research at full search_depth if it looks interesting
                score = -_pvs(engine, search_depth, -alpha - 1, -alpha, ply + 1, allow_null=True)
            if not STOP and score > alpha and score < beta:
                # Full re-search
                score = -_pvs(engine, search_depth, -beta, -alpha, ply + 1, allow_null=True)

        engine.undo_move()
        if STOP: return 0

        if score > best:
            best = score
            best_move = mv
            if score > alpha:
                alpha = score
                _bump_history(mv, depth)
                _set_killer(mv, ply)

        legal_index += 1
        if alpha >= beta:
            # Beta cutoff
            _bump_history(mv, depth)
            _set_killer(mv, ply)
            break

    # Store TT
    if best <= alpha:   # after loop, alpha is final; re-derive flag via compare with original window
        # We don't have original alpha; safest: set exact if best_move found, else ALPHA.
        flag = FLAG_EXACT if best_move else FLAG_ALPHA
    else:
        # If cutoff never happened and we improved alpha, it's exact;
        # if we broke on cutoff, we returned earlier. So here: exact.
        flag = FLAG_EXACT

    _store_tt(game, depth, best, flag, best_move)
    return best

# ----------------- Quiescence (captures/promotions only) -----------------
def _quiescence(engine, alpha, beta, ply, depth_q):
    global NODE_COUNT, STOP
    NODE_COUNT += 1
    if NODE_COUNT % ABORT_CHECK_INTERVAL == 0 and time.perf_counter() >= TIME_LIMIT:
        STOP = True
        return 0

    game = engine.get_game_state()
    stand = _eval(game)

    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    if depth_q >= QDEPTH_MAX:
        return alpha

    # Generate tactical moves only
    moves = engine.get_valid_moves()
    tacts = [m for m in moves if _is_tactical(game, m)]

    # Delta pruning: if even a max capture can’t reach alpha, prune
    if tacts:
        max_gain = max(_capture_gain(game, m) for m in tacts)
        if stand + max_gain + DELTA_MARGIN < alpha:
            return alpha

    # MVV-LVA order
    tacts.sort(key=lambda m: _mvv_lva(game, m), reverse=True)

    for mv in tacts:
        _maybe_set_default_promo(mv)
        if _see(game.board, mv) < SEE_DROP_MARGIN:
            continue
        engine.make_move(mv)
        score = -_quiescence(engine, -beta, -alpha, ply + 1, depth_q + 1)
        engine.undo_move()
        if STOP: return 0

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

# ----------------- Helpers: ordering, heuristics, TT -----------------
def _probe_tt(game):
    key = _pos_key(game)
    return TT.get(key)

def _probe_tt_best(game):
    tt = _probe_tt(game)
    return tt['best'] if tt else None

def _store_tt(game, depth, score, flag, best_move):
    key = _pos_key(game)
    best_id = _move_id(best_move) if best_move else None
    entry = TT.get(key)
    # Prefer keeping deeper info; replace shallower entries
    if entry is None or depth >= entry['depth']:
        TT[key] = {'depth': depth, 'score': score, 'flag': flag, 'best': best_id}

def _order_moves(game, moves, tt_move_id, ply):
    def score(m):
        s = 0
        mid = _move_id(m)
        if tt_move_id and mid == tt_move_id:
            s += 50_000
        if getattr(m, "is_pawn_promotion", False):
            s += 10_000
        if _is_capture(game, m) or getattr(m, "is_en_passant", False):
            s += 5_000 + _mvv_lva(game, m)
            see = _see(game.board, m)
            s += max(-1500, min(1500, see * 4))
        # Killer moves
        killers = KILLERS[ply]
        if killers[0] and _same_move(mid, killers[0]):
            s += 3_000
        elif killers[1] and _same_move(mid, killers[1]):
            s += 2_000
        # History
        s += HISTORY[(m.start_row, m.start_col, m.end_row, m.end_col)]
        return s
    moves.sort(key=score, reverse=True)

def _bump_history(m, depth):
    HISTORY[(m.start_row, m.start_col, m.end_row, m.end_col)] += HISTORY_BONUS * depth * depth

def _set_killer(m, ply):
    mid = _move_id(m)
    k = KILLERS[ply]
    if not k[0] or not _same_move(mid, k[0]):
        k[1] = k[0]
        k[0] = mid

def _move_id(m):
    if m is None:
        return None
    # Use your existing move_id (compatible with equality)
    return getattr(m, "move_id", (m.start_row * 1000 + m.start_col * 100 + m.end_row * 10 + m.end_col))

def _same_move(a, b):
    return a == b

# ----------------- Static board helpers -----------------
_KNIGHT_DELTAS = [(-2, -1), (-1, -2), (-2, 1), (-1, 2), (2, -1), (1, -2), (2, 1), (1, 2)]
_KING_DELTAS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
_BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
_ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _piece_attacks(board, pr, pc, tr, tc):
    """Return True if piece at (pr, pc) attacks (tr, tc) ignoring pins."""
    pcv = board[pr][pc]
    if pcv == "--":
        return False
    color, t = pcv[0], pcv[1]
    dr, dc = tr - pr, tc - pc

    if t == 'p':
        step = -1 if color == 'w' else 1
        return dr == step and abs(dc) == 1
    if t == 'N':
        return (dr, dc) in _KNIGHT_DELTAS
    if t == 'K':
        return abs(dr) <= 1 and abs(dc) <= 1 and (dr != 0 or dc != 0)
    if t == 'B' or t == 'Q':
        if abs(dr) == abs(dc) and dr != 0:
            sr, sc = (1 if dr > 0 else -1), (1 if dc > 0 else -1)
            r, c = pr + sr, pc + sc
            while _in_bounds(r, c):
                if (r, c) == (tr, tc):
                    return True
                if board[r][c] != "--":
                    break
                r += sr; c += sc
    if t == 'R' or t == 'Q':
        if (dr == 0 or dc == 0) and not (dr == 0 and dc == 0):
            sr = 0 if dr == 0 else (1 if dr > 0 else -1)
            sc = 0 if dc == 0 else (1 if dc > 0 else -1)
            r, c = pr + sr, pc + sc
            while _in_bounds(r, c):
                if (r, c) == (tr, tc):
                    return True
                if board[r][c] != "--":
                    break
                r += sr; c += sc
    return False

def _attackers_to(board, tr, tc, color):
    """List attackers of square (tr, tc) belonging to 'color'."""
    attackers = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece != "--" and piece[0] == color:
                if _piece_attacks(board, r, c, tr, tc):
                    attackers.append((PVAL.get(piece[1], 0), r, c, piece))
    attackers.sort(key=lambda x: x[0])  # least valuable first
    return attackers

def _attacked_squares(board, color):
    """Return set of squares attacked by 'color' (ignores pins/check)."""
    attacks = set()
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--" or piece[0] != color:
                continue
            t = piece[1]
            if t == 'p':
                step = -1 if color == 'w' else 1
                for dc in (-1, 1):
                    rr, cc = r + step, c + dc
                    if _in_bounds(rr, cc):
                        attacks.add((rr, cc))
            elif t == 'N':
                for dr, dc in _KNIGHT_DELTAS:
                    rr, cc = r + dr, c + dc
                    if _in_bounds(rr, cc):
                        attacks.add((rr, cc))
            elif t == 'K':
                for dr, dc in _KING_DELTAS:
                    rr, cc = r + dr, c + dc
                    if _in_bounds(rr, cc):
                        attacks.add((rr, cc))
            elif t == 'B' or t == 'Q':
                for dr, dc in _BISHOP_DIRS:
                    rr, cc = r + dr, c + dc
                    while _in_bounds(rr, cc):
                        attacks.add((rr, cc))
                        if board[rr][cc] != "--":
                            break
                        rr += dr; cc += dc
            if t == 'R' or t == 'Q':
                for dr, dc in _ROOK_DIRS:
                    rr, cc = r + dr, c + dc
                    while _in_bounds(rr, cc):
                        attacks.add((rr, cc))
                        if board[rr][cc] != "--":
                            break
                        rr += dr; cc += dc
    return attacks

def _pseudo_mobility(board, color):
    """Cheap pseudo-legal mobility counts per piece type."""
    mob = {'N': 0, 'B': 0, 'R': 0, 'Q': 0}
    friendly = color
    enemy = 'b' if color == 'w' else 'w'
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "--" or piece[0] != friendly:
                continue
            t = piece[1]
            if t == 'N':
                for dr, dc in _KNIGHT_DELTAS:
                    rr, cc = r + dr, c + dc
                    if _in_bounds(rr, cc) and (board[rr][cc] == "--" or board[rr][cc][0] == enemy):
                        mob['N'] += 1
            elif t == 'B' or t == 'Q':
                for dr, dc in _BISHOP_DIRS:
                    rr, cc = r + dr, c + dc
                    while _in_bounds(rr, cc):
                        if board[rr][cc] == "--":
                            mob['B' if t == 'B' else 'Q'] += 1
                        else:
                            if board[rr][cc][0] == enemy:
                                mob['B' if t == 'B' else 'Q'] += 1
                            break
                        rr += dr; cc += dc
            if t == 'R' or t == 'Q':
                for dr, dc in _ROOK_DIRS:
                    rr, cc = r + dr, c + dc
                    while _in_bounds(rr, cc):
                        if board[rr][cc] == "--":
                            mob['R' if t == 'R' else 'Q'] += 1
                        else:
                            if board[rr][cc][0] == enemy:
                                mob['R' if t == 'R' else 'Q'] += 1
                            break
                        rr += dr; cc += dc
    return mob

def _center_control(board, attacks_w, attacks_b):
    central = [(3, 3), (3, 4), (4, 3), (4, 4)]
    extended = [(2, 2), (2, 3), (2, 4), (2, 5),
                (3, 2), (3, 5),
                (4, 2), (4, 5),
                (5, 2), (5, 3), (5, 4), (5, 5)]
    score = 0
    for sq in central:
        if sq in attacks_w: score += 2
        if sq in attacks_b: score -= 2
    for sq in extended:
        if sq in attacks_w: score += 1
        if sq in attacks_b: score -= 1
    return score

def _king_safety(board, color, king_pos, pawn_files, attacks_enemy):
    if not king_pos:
        return 0
    sign = 1 if color == 'w' else -1
    r, c = king_pos
    direction = -1 if color == 'w' else 1

    # Pawn shield in front of king (up to two ranks)
    shield = 0
    for dc in (-1, 0, 1):
        for step in (1, 2):
            rr, cc = r + direction * step, c + dc
            if _in_bounds(rr, cc) and board[rr][cc] == color + 'p':
                shield += 1
                break
    safety = shield * KING_SHIELD_BONUS

    # Open/semi-open files near king (king file +/-1)
    for dc in (-1, 0, 1):
        cc = c + dc
        if 0 <= cc < 8:
            friendly_pawns = pawn_files[color][cc]
            enemy_pawns = pawn_files['b' if color == 'w' else 'w'][cc]
            if friendly_pawns == 0 and enemy_pawns == 0:
                safety -= KING_OPEN_FILE_PENALTY
            elif friendly_pawns == 0 and enemy_pawns > 0:
                safety -= KING_SEMI_OPEN_FILE_PENALTY

    # Enemy attacks in king ring
    ring = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if _in_bounds(rr, cc) and (rr, cc) in attacks_enemy:
                ring += 1
    safety -= ring * 4

    return sign * safety

def _is_backward_pawn(board, color, r, c, pawn_files):
    direction = -1 if color == 'w' else 1
    # If blocked by enemy pawn ahead and no friendly pawn on adjacent files ahead
    has_support = False
    for dc in (-1, 1):
        cc = c + dc
        if 0 <= cc < 8:
            if color == 'w':
                ahead = [rr for rr in range(r - 1, -1, -1)]
            else:
                ahead = [rr for rr in range(r + 1, 8)]
            for rr in ahead:
                if board[rr][cc] == color + 'p':
                    has_support = True
                    break
            if has_support:
                break
    if has_support:
        return False
    forward_r = r + direction
    if not _in_bounds(forward_r, c):
        return False
    # Backward if square in front is controlled by enemy pawn or occupied by enemy pawn chain
    enemy = 'b' if color == 'w' else 'w'
    enemy_control = False
    if color == 'w':
        for dc in (-1, 1):
            cc = c + dc
            if _in_bounds(forward_r + 1, cc) and board[forward_r + 1][cc] == enemy + 'p':
                enemy_control = True
                break
    else:
        for dc in (-1, 1):
            cc = c + dc
            if _in_bounds(forward_r - 1, cc) and board[forward_r - 1][cc] == enemy + 'p':
                enemy_control = True
                break
    if enemy_control:
        return True
    # Also consider if enemy pawn blocks on same file ahead and no friendly pawn ahead
    if color == 'w':
        blockers = [rr for rr in range(forward_r, -1, -1)]
    else:
        blockers = [rr for rr in range(forward_r, 8)]
    for rr in blockers:
        if board[rr][c] == color + 'p':
            return False
        if board[rr][c] == enemy + 'p':
            return True
    return False

def _connected_passed_bonus(passed_pawns):
    bonus = {'w': 0, 'b': 0}
    for color, pawns in passed_pawns.items():
        for r, c in pawns:
            for dc in (-1, 1):
                cc = c + dc
                if 0 <= cc < 8:
                    for rr in (r - 1, r, r + 1):
                        if 0 <= rr < 8 and (rr, cc) in pawns:
                            bonus[color] += CONNECTED_PASSED_BONUS
                            break
    return bonus

def _see(board, move):
    """Static exchange evaluation: approximate net gain of a capture."""
    if not getattr(move, "is_en_passant", False) and board[move.end_row][move.end_col] == "--":
        return 0
    b = [row[:] for row in board]
    tr, tc = move.end_row, move.end_col
    color_to_move = 0 if move.piece_moved[0] == 'w' else 1  # 0 white, 1 black

    def val(piece):
        if piece == "--":
            return 0
        return PVAL.get(piece[1], 0)

    # Apply initial capture
    captured_value = val(move.piece_captured if not move.is_en_passant else ('bp' if move.piece_moved[0] == 'w' else 'wp'))
    gain = [captured_value]
    b[move.start_row][move.start_col] = "--"
    b[tr][tc] = move.piece_moved
    if move.is_en_passant:
        cap_r = tr + 1 if move.piece_moved[0] == 'w' else tr - 1
        b[cap_r][tc] = "--"

    attackers = [set(), set()]

    def refresh_attackers():
        attackers[0].clear(); attackers[1].clear()
        for r in range(8):
            for c in range(8):
                pc = b[r][c]
                if pc == "--":
                    continue
                idx = 0 if pc[0] == 'w' else 1
                if _piece_attacks(b, r, c, tr, tc):
                    attackers[idx].add((PVAL.get(pc[1], 0), r, c, pc))

    refresh_attackers()

    occupied_value = val(move.piece_moved)
    side = 1 - color_to_move  # opponent to move after initial capture

    while True:
        att = sorted(list(attackers[side]))
        if not att:
            break
        _, ar, ac, apiece = att[0]
        gain.append(occupied_value - gain[-1])
        # make capture
        b[ar][ac] = "--"
        b[tr][tc] = apiece
        occupied_value = val(apiece)
        refresh_attackers()
        side = 1 - side

    for i in range(len(gain) - 2, -1, -1):
        gain[i] = max(gain[i], -gain[i + 1])
    return gain[0]

# ----------------- Tactical helpers -----------------
def _is_tactical(game, m):
    return _is_capture(game, m) or getattr(m, "is_pawn_promotion", False) or getattr(m, "is_castle", False)

def _is_capture(game, m):
    if getattr(m, "is_en_passant", False):
        return True
    return game.board[m.end_row][m.end_col] != "--"

def _mvv_lva(game, m):
    # Most Valuable Victim - Least Valuable Attacker
    cap = None
    if getattr(m, "is_en_passant", False):
        cap = 'bp' if game.board[m.start_row][m.start_col] == 'wp' else 'wp'
    else:
        cap = game.board[m.end_row][m.end_col]
    if cap == "--":
        return 0
    victim = PVAL.get(cap[1], 0)
    attacker = PVAL.get(m.piece_moved[1], 0)
    return victim * 10 - attacker

def _capture_gain(game, m):
    # optimistic material swing for delta pruning in quiescence
    if getattr(m, "is_pawn_promotion", False):
        return PVAL.get('Q', 900) - PVAL.get('p', 100)
    if getattr(m, "is_en_passant", False):
        return 100  # pawn capture
    cap = game.board[m.end_row][m.end_col]
    if cap == "--":
        return 0
    return PVAL.get(cap[1], 0)

def _maybe_set_default_promo(m):
    if getattr(m, "is_pawn_promotion", False) and not getattr(m, "promotion_choice", None):
        m.promotion_choice = 'Q'  # engine GUI may override for humans; AI defaults to queen

# ----------------- Evaluation -----------------
def _eval(game):
    # Positive for side-to-move
    board = game.board
    stm = 1 if game.white_to_move else -1

    material = 0
    pst = 0
    struct = 0

    pieces = []
    pawn_files = {'w': [0] * 8, 'b': [0] * 8}
    pawn_pos = {'w': [], 'b': []}
    bishops = {'w': 0, 'b': 0}
    rooks = {'w': [], 'b': []}
    passed_pawns = {'w': [], 'b': []}

    phase_score = 0
    attacks_w = _attacked_squares(board, 'w')
    attacks_b = _attacked_squares(board, 'b')
    mob_w = _pseudo_mobility(board, 'w')
    mob_b = _pseudo_mobility(board, 'b')

    # Pass 1: collect features and phase info
    for r in range(8):
        for c in range(8):
            pc = board[r][c]
            if pc == "--":
                continue
            color = pc[0]
            t = pc[1]
            pieces.append((r, c, color, t))
            phase_score += PHASE_WEIGHTS.get(t, 0)
            if t == 'p':
                pawn_files[color][c] += 1
                pawn_pos[color].append((r, c))
            elif t == 'B':
                bishops[color] += 1
            elif t == 'R':
                rooks[color].append((r, c))

    phase = min(1.0, phase_score / PHASE_MAX)
    end_factor = 1.0 - phase
    mid_factor = phase

    # Pass 2: material and piece-square terms (king blended mid/end)
    for r, c, color, t in pieces:
        sign = 1 if color == 'w' else -1
        material += sign * PVAL.get(t, 0)
        pr = r if color == 'w' else 7 - r
        if t == 'K':
            mid = PST_K[pr][c]
            end = PST_K_END[pr][c]
            pst += sign * int(mid * phase + end * end_factor)
        else:
            pst_tab = PST.get(t)
            if pst_tab:
                pst += sign * pst_tab[pr][c]

    # Bishop pair bonus
    if bishops['w'] >= 2:
        struct += BISHOP_PAIR_BONUS
    if bishops['b'] >= 2:
        struct -= BISHOP_PAIR_BONUS

    # Pawn structure: doubled / isolated / passed
    for color in ('w', 'b'):
        sign = 1 if color == 'w' else -1
        files = pawn_files[color]
        for f, count in enumerate(files):
            if count > 1:
                struct += sign * (-DOUBLED_PAWN_PENALTY * (count - 1))
            if count > 0:
                left = files[f - 1] if f > 0 else 0
                right = files[f + 1] if f < 7 else 0
                if left == 0 and right == 0:
                    struct += sign * (-ISOLATED_PAWN_PENALTY)
        for r, c in pawn_pos[color]:
            if _is_passed_pawn(board, color, r, c):
                passed_pawns[color].append((r, c))
                advance = (7 - r) if color == 'w' else r
                scale = 1.0 + end_factor * PASSED_END_SCALER
                struct += sign * int((PASSED_PAWN_BASE + advance * PASSED_PAWN_SCALE) * scale)

    # Rooks on (semi-)open files
    for color in ('w', 'b'):
        sign = 1 if color == 'w' else -1
        foe = 'b' if color == 'w' else 'w'
        for _, c in rooks[color]:
            friendly_pawns = pawn_files[color][c]
            enemy_pawns = pawn_files[foe][c]
            if friendly_pawns == 0:
                if enemy_pawns == 0:
                    struct += sign * ROOK_OPEN_FILE_BONUS
                else:
                    struct += sign * ROOK_SEMI_OPEN_FILE_BONUS

    # Rooks on 7th rank and behind passed pawns (endgame leaning)
    for color in ('w', 'b'):
        sign = 1 if color == 'w' else -1
        target_rank = 1 if color == 'w' else 6
        for rr, cc in rooks[color]:
            if rr == target_rank:
                struct += sign * int(ROOK_ON_7TH_BONUS * (0.5 + 0.5 * end_factor))
            for pr, pc in passed_pawns[color]:
                if pc == cc:
                    if (color == 'w' and rr > pr) or (color == 'b' and rr < pr):
                        struct += sign * int(ROOK_BEHIND_PASSED_BONUS * (0.5 + 0.5 * end_factor))
                        break

    # Backward pawn penalties
    for color in ('w', 'b'):
        sign = 1 if color == 'w' else -1
        for r, c in pawn_pos[color]:
            if _is_backward_pawn(board, color, r, c, pawn_files):
                struct += sign * (-BACKWARD_PAWN_PENALTY)

    # Connected passed pawn bonuses
    conn = _connected_passed_bonus(passed_pawns)
    struct += conn['w'] - conn['b']

    # King safety (midgame-weighted)
    safety_mid_scale = mid_factor
    struct += int(_king_safety(board, 'w', getattr(game, "white_king_location", None), pawn_files, attacks_b) * safety_mid_scale)
    struct += int(_king_safety(board, 'b', getattr(game, "black_king_location", None), pawn_files, attacks_w) * safety_mid_scale)

    # Center control (midgame-weighted)
    center_score = _center_control(board, attacks_w, attacks_b)
    struct += int(center_score * SPACE_CENTER_BONUS * mid_factor)

    # Mobility split by piece type (midgame-weighted)
    mob_score = 0
    for t, w in MOBILITY_WEIGHTS.items():
        mob_score += (mob_w.get(t, 0) - mob_b.get(t, 0)) * w
    struct += int(mob_score * mid_factor * 0.5)

    # Tiny mobility for STM (cheap proxy)
    try:
        mobility = len(game.get_all_possible_moves())
        struct += (mobility * MOBILITY_WEIGHT) * (1 if game.white_to_move else -1)
    except Exception:
        pass

    # King activity in endings: encourage centralization when pieces are off
    try:
        wk = getattr(game, "white_king_location", None)
        bk = getattr(game, "black_king_location", None)
        def center_score(pos):
            if not pos:
                return 0.0
            dist = abs(pos[0] - 3.5) + abs(pos[1] - 3.5)
            return max(0.0, 6.0 - dist)
        king_activity = center_score(wk) - center_score(bk)
        struct += int(KING_CENTER_END_WEIGHT * end_factor * king_activity)
    except Exception:
        pass

    return stm * (material + pst + struct)

def _mate_or_draw(game):
    if getattr(game, "checkmate", False):
        return -MATE
    return DRAW

# ----------------- Position key (compact & deterministic) -----------------
def _pos_key(game):
    # Compact tuple-hash based on board, side, castling, ep
    b = game.board
    parts = []
    for r in range(8):
        for c in range(8):
            parts.append(b[r][c])
    parts.append('w' if game.white_to_move else 'b')
    cr = getattr(game, "castling_rights", None)
    if cr:
        parts.append(1 if cr.get('wks') else 0)
        parts.append(1 if cr.get('wqs') else 0)
        parts.append(1 if cr.get('bks') else 0)
        parts.append(1 if cr.get('bqs') else 0)
    ep = getattr(game, "en_passant_target", None)
    if ep:
        parts.append(('ep', ep[0], ep[1]))
    else:
        parts.append(('ep', -1, -1))
    return hash(tuple(parts))

# ----------------- Opening book -----------------
def _book_move(engine) -> Optional[Move]:
    game = engine.get_game_state()
    history = [m.get_chess_notation() for m in game.move_log]
    reply = get_book_reply(history)
    if not reply:
        return None
    for mv in engine.get_valid_moves():
        if mv.get_chess_notation() == reply:
            return mv
    return None

# ----------------- Pawn helper -----------------
def _is_passed_pawn(board, color, r, c):
    enemy = 'b' if color == 'w' else 'w'
    if color == 'w':
        rows = range(r - 1, -1, -1)
    else:
        rows = range(r + 1, 8)
    for rr in rows:
        for dc in (c - 1, c, c + 1):
            if 0 <= dc < 8 and board[rr][dc] == enemy + 'p':
                return False
    return True

# ----------------- Weak-play helper -----------------
def _weak_move_with_noise(engine, noise: int) -> Optional[Move]:
    moves = engine.get_valid_moves()
    if not moves:
        return None
    game = engine.get_game_state()
    best = None
    best_score = -INFINITY
    for mv in moves:
        engine.make_move(mv)
        # Opponent to move after making mv; negate eval to score for mover
        score = -_eval(game) + random.gauss(0, noise)
        engine.undo_move()
        if score > best_score:
            best_score = score
            best = mv
    return best
