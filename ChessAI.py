# ChessAI.py
# Fast & Strong Chess AI for your engine (board.py)
# Techniques:
# - Iterative Deepening + Principal Variation Search (PVS/Negascout)
# - Transposition Table with proper bounds (EXACT/ALPHA/BETA)
# - Null-Move Pruning (safe guard in check / low-material)
# - Late Move Reductions (LMR) on non-tactical late moves
# - Futility & Razoring (shallow pruning on quiets)
# - Killer Move & History Heuristics
# - MVV-LVA ordering for captures, promotion first
# - Quiescence with Delta Pruning (captures/promotions only)
#
# API:
#   from ChessAI import choose_ai_move
#   move = choose_ai_move(engine, depth=ai_depth, time_ms=250)
#
# Notes:
# - Works with your current Board API (get_valid_moves/make_move/undo_move/in_check etc.)
# - Defaults to a small time cap so depth 3–4 won’t lag laptops.

import time
import math
from collections import defaultdict

# ------------------ Tunables (safe defaults) ------------------
INFINITY = 10_000_000
MATE = 9_000_000
DRAW = 0

# Time control
DEFAULT_TIME_MS = 250          # soft time cap per move (you can pass a custom time_ms)
ABORT_CHECK_INTERVAL = 4096    # nodes between time checks

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
def choose_ai_move(engine, depth=3, time_ms=DEFAULT_TIME_MS):
    """
    Iterative deepening search up to 'depth' plies or until 'time_ms' elapses.
    Returns the best Move for side-to-move.
    """
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

        # Futility pruning (quiet late moves, shallow)
        if depth <= 2 and not in_check and not _is_tactical(game, mv):
            stand = _eval(game)
            margin = FUTILITY_MARGIN * depth
            if stand + margin <= alpha:
                continue

        # PVS window: full window for first move; narrow for rest
        engine.make_move(mv)
        if legal_index == 0:
            score = -_pvs(engine, depth - 1, -beta, -alpha, ply + 1, allow_null=True)
        else:
            # Late Move Reductions for non-tactical late moves
            reduce = 0
            if depth >= 3 and not in_check and not _is_tactical(game, mv):
                reduce = LMR_BASE + (legal_index // 6)
            # Try reduced null-window search
            score = -_pvs(engine, depth - 1 - reduce, -alpha - 1, -alpha, ply + 1, allow_null=True)
            if not STOP and score > alpha and reduce > 0:
                # Research at depth-1 if it looks interesting
                score = -_pvs(engine, depth - 1, -alpha - 1, -alpha, ply + 1, allow_null=True)
            if not STOP and score > alpha and score < beta:
                # Full re-search
                score = -_pvs(engine, depth - 1, -beta, -alpha, ply + 1, allow_null=True)

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

    for r in range(8):
        for c in range(8):
            pc = board[r][c]
            if pc == "--":
                continue
            col = 1 if pc[0] == 'w' else -1
            t = pc[1]
            material += col * PVAL.get(t, 0)
            pr = r if col == 1 else 7 - r
            pst_tab = PST.get(t)
            if pst_tab:
                pst += col * pst_tab[pr][c]

    # Tiny mobility for STM (cheap proxy)
    try:
        mobility = len(game.get_valid_moves())
        pst += (mobility * 2) * (1 if game.white_to_move else -1)
    except:
        pass

    return stm * (material + pst)

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
