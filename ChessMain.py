# ChessMain.py
import pygame
import os
from ChessEngine import ChessEngine
from move import Move
from ChessAI import choose_ai_move  # supports time_ms for per-move time cap

# --------- Config ---------
AI_MOVE_TIME_MS = 250  # ← AI thinking time per move in milliseconds (tweak here)

# --------- Sizing (1.5× scale) ---------
SCALE = 1.5
BASE_BOARD = 512
BASE_TOPBAR = 80

BOARD_HEIGHT = int(BASE_BOARD * SCALE)   # 768
TOPBAR = int(BASE_TOPBAR * SCALE)        # 120
WIDTH = BOARD_HEIGHT                     # 768
HEIGHT = TOPBAR + BOARD_HEIGHT           # 888
DIMENSION = 8
SQ_SIZE = BOARD_HEIGHT // DIMENSION      # 96
MAX_FPS = 30
IMAGES = {}

# ---------------- Orientation helpers ----------------
def to_display_coords(r, c, flipped: bool):
    """Board (r,c) -> display (row,col) respecting orientation."""
    if flipped:
        return 7 - r, 7 - c
    return r, c

def from_display_coords(dr, dc, flipped: bool):
    """Display (row,col) -> board (r,c) respecting orientation."""
    if flipped:
        return 7 - dr, 7 - dc
    return dr, dc

def screen_to_board(x, y, flipped: bool):
    """Convert pixel to board (r,c) or return None if outside board."""
    if y < TOPBAR or y >= TOPBAR + BOARD_HEIGHT or x < 0 or x >= WIDTH:
        return None
    dc = x // SQ_SIZE
    dr = (y - TOPBAR) // SQ_SIZE
    return from_display_coords(int(dr), int(dc), flipped)

# ---------------- UI Helpers ----------------
class Button:
    def __init__(self, rect, text, on_click, font,
                 bg=(50, 50, 50), fg=(240, 240, 240),
                 hover_bg=(70, 120, 70), radius=12):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.font = font
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.radius = radius

    def draw(self, screen):
        mx, my = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mx, my)
        color = self.hover_bg if is_hover else self.bg
        pygame.draw.rect(screen, color, self.rect, border_radius=self.radius)
        label = self.font.render(self.text, True, self.fg)
        screen.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.on_click()

# ---------------- Assets ----------------
def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK',
              'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    base_path = os.path.join(os.path.dirname(__file__), "pieces")
    for piece in pieces:
        image_path = os.path.join(base_path, f"{piece}.png")
        IMAGES[piece] = pygame.transform.scale(
            pygame.image.load(image_path), (SQ_SIZE, SQ_SIZE)
        )

# ---------------- Drawing ----------------
def draw_board(screen, flipped: bool):
    colors = [pygame.Color(238, 238, 210), pygame.Color(118, 150, 86)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            dr, dc = to_display_coords(r, c, flipped)
            color = colors[(r + c) % 2]
            pygame.draw.rect(
                screen, color,
                pygame.Rect(dc * SQ_SIZE, dr * SQ_SIZE + TOPBAR, SQ_SIZE, SQ_SIZE)
            )

def highlight_squares(screen, game_state, valid_moves, selected_sq, flipped: bool):
    if selected_sq:
        r, c = selected_sq
        if (
            0 <= r < 8
            and 0 <= c < 8
            and game_state.board[r][c] != "--"
            and game_state.board[r][c][0] == ('w' if game_state.white_to_move else 'b')
        ):
            s = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(90)
            s.fill(pygame.Color(66, 135, 245))
            dr, dc = to_display_coords(r, c, flipped)
            screen.blit(s, (dc * SQ_SIZE, dr * SQ_SIZE + TOPBAR))
            s.fill(pygame.Color(246, 190, 0))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    mdr, mdc = to_display_coords(move.end_row, move.end_col, flipped)
                    screen.blit(s, (mdc * SQ_SIZE, mdr * SQ_SIZE + TOPBAR))

def draw_pieces(screen, board, flipped: bool):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                dr, dc = to_display_coords(r, c, flipped)
                screen.blit(IMAGES[piece], pygame.Rect(dc * SQ_SIZE, dr * SQ_SIZE + TOPBAR, SQ_SIZE, SQ_SIZE))

def highlight_check(screen, game_state, flipped: bool):
    if hasattr(game_state, "in_check") and game_state.in_check():
        king_pos = game_state.white_king_location if game_state.white_to_move else game_state.black_king_location
        dr, dc = to_display_coords(king_pos[0], king_pos[1], flipped)
        s = pygame.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(120)
        s.fill(pygame.Color('red'))
        screen.blit(s, (dc * SQ_SIZE, dr * SQ_SIZE + TOPBAR))

def draw_topbar(screen, font, mode_text, player_to_move_text):
    # background
    pygame.draw.rect(screen, (30, 30, 30), pygame.Rect(0, 0, WIDTH, TOPBAR))

    # render both labels
    left_surf = font.render(mode_text, True, (235, 235, 235))
    right_surf = font.render(player_to_move_text, True, (200, 200, 200))

    # base positions on same row
    left_pos = (16, 24)
    right_rect = right_surf.get_rect()
    right_rect.midright = (WIDTH - 16, 24)

    # prevent overlap — push right text to next line if needed
    if left_pos[0] + left_surf.get_width() + 20 > right_rect.left:
        right_rect.midright = (WIDTH - 16, 24 + left_surf.get_height() + 8)

    # draw
    screen.blit(left_surf, left_pos)
    screen.blit(right_surf, right_rect)

def draw_game_state(screen, game_state, valid_moves, selected_sq, mode_text, font, flipped: bool):
    player = "White" if game_state.white_to_move else "Black"
    draw_topbar(screen, font, mode_text, f"Player to move: {player}")
    draw_board(screen, flipped)
    highlight_squares(screen, game_state, valid_moves, selected_sq, flipped)
    draw_pieces(screen, game_state.board, flipped)
    highlight_check(screen, game_state, flipped)

# ---------------- Overlays ----------------
def draw_promotion_overlay(screen, move, images, alpha):
    """
    Dim background + centered promotion panel.
    Returns rects [Q, R, B, N] for click detection.
    """
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, alpha))
    screen.blit(dim, (0, 0))

    panel_w = SQ_SIZE * 4
    panel_h = SQ_SIZE + 20
    panel_x = (WIDTH - panel_w) // 2
    panel_y = (HEIGHT - panel_h) // 2

    panel = pygame.Surface((panel_w, panel_h))
    panel.fill((40, 40, 40))
    pygame.draw.rect(panel, (80, 80, 80), panel.get_rect(), width=2, border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    color = move.piece_moved[0]
    order = ['Q', 'R', 'B', 'N']
    rects = []
    for i, p in enumerate(order):
        piece_key = color + p
        piece_img = images[piece_key]
        small = pygame.transform.smoothscale(piece_img, (SQ_SIZE, SQ_SIZE))
        px = panel_x + i * SQ_SIZE
        py = panel_y + 10

        mx, my = pygame.mouse.get_pos()
        piece_rect = pygame.Rect(px, py, SQ_SIZE, SQ_SIZE)
        if piece_rect.collidepoint(mx, my):
            pygame.draw.rect(screen, (180, 180, 0), piece_rect, 3, border_radius=6)

        screen.blit(small, (px, py))
        rects.append(piece_rect)

    return rects

def draw_castle_overlay(screen, alpha):
    """Centered Yes/No popup for castling. Returns (yes_rect, no_rect)."""
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, alpha))
    screen.blit(dim, (0, 0))

    panel_w = int(SQ_SIZE * 4.5)
    panel_h = int(SQ_SIZE * 1.5)
    panel_x = (WIDTH - panel_w) // 2
    panel_y = (HEIGHT - panel_h) // 2

    panel = pygame.Surface((panel_w, panel_h))
    panel.fill((40, 40, 40))
    pygame.draw.rect(panel, (80, 80, 80), panel.get_rect(), width=2, border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    font = pygame.font.SysFont("Helvetica", int(20 * SCALE), True)
    msg = "Castle with this rook?"
    label = font.render(msg, True, (230, 230, 230))
    screen.blit(label, label.get_rect(center=(WIDTH // 2, panel_y + int(0.4 * panel_h))))

    btn_w = int(100 * SCALE)
    btn_h = int(40 * SCALE)
    gap = int(20 * SCALE)
    yes_rect = pygame.Rect(WIDTH // 2 - btn_w - gap // 2, panel_y + int(0.8 * panel_h), btn_w, btn_h)
    no_rect  = pygame.Rect(WIDTH // 2 + gap // 2,       panel_y + int(0.8 * panel_h), btn_w, btn_h)

    def draw_btn(rect, text):
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        bg = (70, 120, 70) if text == "Yes" else (120, 70, 70)
        base = (50, 50, 50)
        color = bg if hover else base
        pygame.draw.rect(screen, color, rect, border_radius=10)
        t = font.render(text, True, (240, 240, 240))
        screen.blit(t, t.get_rect(center=rect.center))

    draw_btn(yes_rect, "Yes")
    draw_btn(no_rect,  "No")
    return yes_rect, no_rect

# ---------------- Scenes ----------------
SCENE_MENU = "menu"
SCENE_OPTIONS = "options"
SCENE_GAME = "game"

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()
    load_images()

    # Fonts
    title_font = pygame.font.SysFont("Helvetica", int(48 * SCALE), True)
    btn_font = pygame.font.SysFont("Helvetica", int(26 * SCALE), True)
    bar_font = pygame.font.SysFont("Helvetica", int(24 * SCALE), True)
    small_font = pygame.font.SysFont("Helvetica", int(18 * SCALE), False)

    # State
    scene = SCENE_MENU
    vs_computer = False
    ai_plays_white = False
    ai_depth = 3

    # Auto-promotion settings
    auto_promotion_on = False
    auto_promotion_piece = 'Q'  # 'Q','R','B','N'

    # Game session vars
    engine = None
    selected_sq = ()
    player_clicks = []
    valid_moves = []
    move_made = False
    game_over = False

    # Promotion UI state
    show_promotion = False
    pending_move = None
    promotion_rects = []
    promotion_alpha = 0  # 0..180

    # Castle UI state
    show_castle_confirm = False
    pending_castle_move = None
    castle_alpha = 0
    castle_yes_rect = None
    castle_no_rect = None

    # --- Menu handlers ---
    def go_vs_player():
        nonlocal vs_computer
        vs_computer = False
        start_new_game()

    def go_vs_computer():
        nonlocal vs_computer
        vs_computer = True
        start_new_game()

    def go_options():
        nonlocal scene
        scene = SCENE_OPTIONS

    def quit_game():
        pygame.quit()
        raise SystemExit

    def build_menu_buttons():
        btns = []
        btn_w, btn_h, gap = int(280 * SCALE), int(56 * SCALE), int(16 * SCALE)
        start_y = int(200 * SCALE)
        x = WIDTH // 2 - btn_w // 2
        btns.append(Button((x, start_y, btn_w, btn_h), "Play vs Player", go_vs_player, btn_font))
        btns.append(Button((x, start_y + (btn_h + gap), btn_w, btn_h), "Play vs Computer", go_vs_computer, btn_font))
        btns.append(Button((x, start_y + 2 * (btn_h + gap), btn_w, btn_h), "Options", go_options, btn_font))
        btns.append(Button((x, start_y + 3 * (btn_h + gap), btn_w, btn_h), "Quit", quit_game, btn_font))
        return btns

    # --- Options handlers ---
    def toggle_ai_colour():
        nonlocal ai_plays_white
        ai_plays_white = not ai_plays_white

    def dec_depth():
        nonlocal ai_depth
        ai_depth = max(1, ai_depth - 1)

    def inc_depth():
        nonlocal ai_depth
        ai_depth = min(10, ai_depth + 1)  # up to 10

    def toggle_auto_promo():
        nonlocal auto_promotion_on
        auto_promotion_on = not auto_promotion_on

    def back_to_menu():
        nonlocal scene
        scene = SCENE_MENU

    def build_options_buttons():
        btns = []
        btn_w, btn_h, gap = int(260 * SCALE), int(50 * SCALE), int(16 * SCALE)
        start_y = int(220 * SCALE)
        x = WIDTH // 2 - btn_w // 2

        colour_text = f"AI Colour: {'White' if ai_plays_white else 'Black'}"
        btns.append(Button((x, start_y, btn_w, btn_h), colour_text, toggle_ai_colour, btn_font))

        # depth row
        btns.append(Button((x, start_y + (btn_h + gap), btn_w // 2 - 8, btn_h), "- Depth", dec_depth, btn_font))
        btns.append(Button((x + btn_w // 2 + 8, start_y + (btn_h + gap), btn_w // 2 - 8, btn_h), "+ Depth", inc_depth, btn_font))

        # auto-promotion toggle
        auto_text = f"Auto Promotion: {'ON' if auto_promotion_on else 'OFF'}"
        btns.append(Button((x, start_y + 2 * (btn_h + gap), btn_w, btn_h), auto_text, toggle_auto_promo, btn_font))

        # radio row for piece selection if ON
        if auto_promotion_on:
            small_w = int(50 * SCALE)
            row_y = start_y + 3 * (btn_h + gap)
            gap_x = int(10 * SCALE)
            start_x = WIDTH // 2 - (4 * small_w + 3 * gap_x) // 2

            def make_piece_setter(piece_code):
                def _set():
                    nonlocal auto_promotion_piece
                    auto_promotion_piece = piece_code
                return _set

            for i, piece_code in enumerate(['Q', 'R', 'B', 'N']):
                is_selected = (piece_code == auto_promotion_piece)
                bg = (60, 110, 60) if is_selected else (50, 50, 50)
                btns.append(
                    Button(
                        (start_x + i * (small_w + gap_x), row_y, small_w, btn_h),
                        piece_code,
                        make_piece_setter(piece_code),
                        btn_font,
                        bg=bg
                    )
                )

        # back button
        btns.append(Button((x, HEIGHT - int(100 * SCALE), btn_w, btn_h), "Back", back_to_menu, btn_font))
        return btns

    def start_new_game():
        nonlocal scene, engine, selected_sq, player_clicks, valid_moves, move_made, game_over
        nonlocal show_promotion, pending_move, promotion_rects, promotion_alpha
        nonlocal show_castle_confirm, pending_castle_move, castle_alpha, castle_yes_rect, castle_no_rect
        engine = ChessEngine()
        selected_sq = ()
        player_clicks = []
        valid_moves = engine.get_valid_moves()
        move_made = False
        game_over = False
        # reset overlays
        show_promotion = False
        pending_move = None
        promotion_rects = []
        promotion_alpha = 0
        show_castle_confirm = False
        pending_castle_move = None
        castle_alpha = 0
        castle_yes_rect = None
        castle_no_rect = None
        scene = SCENE_GAME

    # ------------ Main Loop ------------
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            # ===== MENU EVENTS =====
            if scene == SCENE_MENU:
                for b in build_menu_buttons():
                    b.handle_event(e)

            # ===== OPTIONS EVENTS =====
            elif scene == SCENE_OPTIONS:
                for b in build_options_buttons():
                    b.handle_event(e)

            # ===== GAME EVENTS =====
            elif scene == SCENE_GAME and engine is not None:
                # Orientation: if AI is white, flip so human (black) is at the bottom
                flipped = (vs_computer and ai_plays_white)

                # AI turn only in vs_computer mode
                is_ai_turn = (
                    vs_computer and (
                        (engine.get_game_state().white_to_move and ai_plays_white) or
                        (not engine.get_game_state().white_to_move and not ai_plays_white)
                    )
                )

                # Promotion overlay blocks all other inputs
                if show_promotion:
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        mx, my = e.pos
                        for idx, rect in enumerate(promotion_rects):
                            if rect.collidepoint(mx, my):
                                choice_map = ['Q', 'R', 'B', 'N']
                                chosen = choice_map[idx]
                                pending_move.promotion_choice = chosen
                                engine.make_move(pending_move)
                                move_made = True
                                show_promotion = False
                                pending_move = None
                                promotion_rects = []
                                promotion_alpha = 0
                                selected_sq = ()
                                player_clicks = []
                                break
                    continue  # block rest

                # Castle confirmation blocks all other inputs
                if show_castle_confirm:
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        mx, my = e.pos
                        if castle_yes_rect and castle_yes_rect.collidepoint(mx, my):
                            engine.make_move(pending_castle_move)
                            move_made = True
                            show_castle_confirm = False
                            pending_castle_move = None
                            castle_alpha = 0
                        elif castle_no_rect and castle_no_rect.collidepoint(mx, my):
                            show_castle_confirm = False
                            pending_castle_move = None
                            castle_alpha = 0
                    continue  # block rest

                # Normal game controls
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        scene = SCENE_MENU
                    if e.key == pygame.K_z:
                        engine.undo_move()
                        move_made = True
                        game_over = False
                        selected_sq = ()
                        player_clicks = []
                    if e.key == pygame.K_r:
                        start_new_game()

                # Human move input (PvP both sides, VsAI only when not AI turn)
                if e.type == pygame.MOUSEBUTTONDOWN and not game_over and (not is_ai_turn):
                    pos = screen_to_board(*e.pos, flipped)
                    if pos is not None:
                        row, col = pos
                        if selected_sq == (row, col):
                            selected_sq = ()
                            player_clicks = []
                        else:
                            selected_sq = (row, col)
                            player_clicks.append(selected_sq)
                        if len(player_clicks) == 2:
                            move = Move(player_clicks[0], player_clicks[1], engine.get_board_state())
                            move_found = False
                            for valid_move in valid_moves:
                                if move == valid_move:
                                    # Handle PROMOTION for human
                                    if getattr(valid_move, "is_pawn_promotion", False):
                                        if auto_promotion_on:
                                            valid_move.promotion_choice = auto_promotion_piece
                                            engine.make_move(valid_move)
                                            move_made = True
                                        else:
                                            show_promotion = True
                                            pending_move = valid_move
                                            promotion_alpha = 0
                                        selected_sq = ()
                                        player_clicks = []
                                        move_found = True
                                        break

                                    # Handle CASTLING for human
                                    if getattr(valid_move, "is_castle", False):
                                        show_castle_confirm = True
                                        pending_castle_move = valid_move
                                        castle_alpha = 0
                                        selected_sq = ()
                                        player_clicks = []
                                        move_found = True
                                        break

                                    # Normal move
                                    engine.make_move(valid_move)
                                    move_made = True
                                    selected_sq = ()
                                    player_clicks = []
                                    move_found = True
                                    break
                            if not move_found:
                                player_clicks = [selected_sq]

        # ===== DRAW / UPDATE =====
        screen.fill((18, 18, 18))
        if scene == SCENE_MENU:
            title = title_font.render("Chess", True, (235, 235, 235))
            screen.blit(title, title.get_rect(center=(WIDTH // 2, int(120 * SCALE))))

            # (Subtitle removed)

            for b in build_menu_buttons():
                b.draw(screen)

        elif scene == SCENE_OPTIONS:
            title = title_font.render("Options", True, (235, 235, 235))
            screen.blit(title, title.get_rect(center=(WIDTH // 2, int(120 * SCALE))))

            summary = f"AI: {'White' if ai_plays_white else 'Black'}   |   Depth: {ai_depth} (1–10)"
            screen.blit(
                small_font.render(summary, True, (200, 200, 200)),
                small_font.render(summary, True, (200, 200, 200)).get_rect(center=(WIDTH // 2, int(170 * SCALE)))
            )

            for b in build_options_buttons():
                b.draw(screen)

        elif scene == SCENE_GAME and engine is not None:
            # Orientation for drawing this frame
            flipped = (vs_computer and ai_plays_white)

            # If vs computer, let AI move on its turn (no popups)
            is_ai_turn = (
                vs_computer and (
                    (engine.get_game_state().white_to_move and ai_plays_white) or
                    (not engine.get_game_state().white_to_move and not ai_plays_white)
                )
            )
            if is_ai_turn and not game_over and not (show_promotion or show_castle_confirm):
                # ← NOW USING TIME CAP
                ai_move = choose_ai_move(engine, depth=ai_depth, time_ms=AI_MOVE_TIME_MS)
                if ai_move:
                    if getattr(ai_move, "is_pawn_promotion", False):
                        ai_move.promotion_choice = 'Q' if not auto_promotion_on else auto_promotion_piece
                    engine.make_move(ai_move)
                    move_made = True

            if move_made:
                valid_moves = engine.get_valid_moves()
                move_made = False

            mode_text = (
                f"Vs Computer  |  AI: {'White' if ai_plays_white else 'Black'}  |  Depth: {ai_depth}"
                if vs_computer else
                "Two Player Mode"
            )
            draw_game_state(screen, engine.get_game_state(), valid_moves, selected_sq, mode_text, bar_font, flipped)

            gs = engine.get_game_state()
            if getattr(gs, "checkmate", False):
                game_over = True
                end_font = pygame.font.SysFont("Helvetica", int(32 * SCALE), True, False)
                text = "Black wins by checkmate!" if gs.white_to_move else "White wins by checkmate!"
                screen.blit(end_font.render(text, True, pygame.Color("Red")), (20, BOARD_HEIGHT // 2 + 40))
            elif getattr(gs, "stalemate", False):
                game_over = True
                end_font = pygame.font.SysFont("Helvetica", int(32 * SCALE), True, False)
                screen.blit(end_font.render("Stalemate!", True, pygame.Color("Gray")), (20, BOARD_HEIGHT // 2 + 40))

            # Promotion overlay (fade)
            if show_promotion and pending_move:
                promotion_alpha = min(180, promotion_alpha + 10)
                promotion_rects = draw_promotion_overlay(screen, pending_move, IMAGES, promotion_alpha)

            # Castle confirmation overlay (fade)
            if show_castle_confirm and pending_castle_move:
                castle_alpha = min(180, castle_alpha + 10)
                castle_yes_rect, castle_no_rect = draw_castle_overlay(screen, castle_alpha)

        pygame.display.flip()
        clock.tick(MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
