import pygame
import os
from ChessEngine import ChessEngine
from move import Move

WIDTH, HEIGHT = 512, 512
DIMENSION = 8
SQ_SIZE = WIDTH // DIMENSION
MAX_FPS = 15
IMAGES = {}

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK',
              'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    base_path = os.path.join(os.path.dirname(__file__), "pieces")
    for piece in pieces:
        image_path = os.path.join(base_path, f"{piece}.png")
        IMAGES[piece] = pygame.transform.scale(
            pygame.image.load(image_path), (SQ_SIZE, SQ_SIZE)
        )

def draw_board(screen):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            pygame.draw.rect(screen, color, pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlight_squares(screen, game_state, valid_moves, selected_sq):
    if selected_sq:
        r, c = selected_sq
        if game_state.board[r][c][0] == ('w' if game_state.white_to_move else 'b'):
            s = pygame.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(pygame.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            s.fill(pygame.Color('yellow'))
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))

def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], pygame.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def highlight_check(screen, game_state):
    if game_state.in_check():
        king_pos = game_state.white_king_location if game_state.white_to_move else game_state.black_king_location
        s = pygame.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(255)
        s.fill(pygame.Color('red'))
        screen.blit(s, (king_pos[1] * SQ_SIZE, king_pos[0] * SQ_SIZE))

def draw_game_state(screen, game_state, valid_moves, selected_sq):
    draw_board(screen)
    highlight_squares(screen, game_state, valid_moves, selected_sq)
    draw_pieces(screen, game_state.board)
    highlight_check(screen, game_state)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess")
    clock = pygame.time.Clock()
    engine = ChessEngine()
    load_images()

    selected_sq = ()
    player_clicks = []
    valid_moves = engine.get_valid_moves()
    move_made = False
    game_over = False

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and not game_over:
                location = pygame.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if selected_sq == (row, col):
                    selected_sq = ()
                    player_clicks = []
                else:
                    selected_sq = (row, col)
                    player_clicks.append(selected_sq)
                if len(player_clicks) == 2:
                    move = Move(player_clicks[0], player_clicks[1], engine.get_board_state())
                    for valid_move in valid_moves:
                        if move == valid_move:
                            engine.make_move(valid_move)
                            move_made = True
                            selected_sq = ()
                            player_clicks = []
                            break
                    if not move_made:
                        player_clicks = [selected_sq]

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_z:  # Undo
                    engine.undo_move()
                    move_made = True
                    game_over = False
                if e.key == pygame.K_r:  # Restart
                    engine = ChessEngine()
                    selected_sq = ()
                    player_clicks = []
                    valid_moves = engine.get_valid_moves()
                    move_made = False
                    game_over = False

        if move_made:
            valid_moves = engine.get_valid_moves()
            move_made = False

        draw_game_state(screen, engine.get_game_state(), valid_moves, selected_sq)

        if engine.get_game_state().checkmate:
            game_over = True
            font = pygame.font.SysFont("Helvetica", 32, True, False)
            text = "Black wins by checkmate!" if engine.get_game_state().white_to_move else "White wins by checkmate!"
            screen.blit(font.render(text, 1, pygame.Color("Red")), (20, HEIGHT // 2))
        elif engine.get_game_state().stalemate:
            game_over = True
            font = pygame.font.SysFont("Helvetica", 32, True, False)
            screen.blit(font.render("Stalemate!", 1, pygame.Color("Gray")), (20, HEIGHT // 2))

        pygame.display.flip()
        clock.tick(MAX_FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
