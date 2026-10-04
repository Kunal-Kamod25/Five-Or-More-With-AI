import math

import pygame

from .game import Game


class GameRenderer:
    """Draw the board, game status, menus, and visual movement feedback."""

    CELL_SIZE = 64
    BOARD_MARGIN = 24
    HEADER_HEIGHT = 92
    GRID_LINE_WIDTH = 2
    PIECE_RADIUS = 22

    BACKGROUND_COLOR = (28, 31, 38)
    EMPTY_CELL_COLOR = (54, 60, 70)
    GRID_LINE_COLOR = (25, 28, 34)
    TEXT_COLOR = (245, 245, 245)
    MUTED_TEXT_COLOR = (185, 192, 202)
    BUTTON_COLOR = (63, 73, 88)
    BUTTON_HOVER_COLOR = (81, 96, 117)
    SELECTED_BUTTON_COLOR = (54, 125, 101)
    PATH_COLOR = (255, 255, 255, 115)
    PIECE_COLORS = {
        1: (220, 55, 55),
        2: (55, 180, 85),
        3: (65, 115, 230),
        4: (245, 210, 55),
        5: (160, 85, 200),
        6: (55, 200, 205),
        7: (240, 140, 45),
    }

    def __init__(self, game):
        if not isinstance(game, Game):
            raise TypeError("game must be a Game object.")
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.board_size = game.get_board().SIZE
        board_pixels = self.board_size * self.CELL_SIZE
        self.board_origin = (
            self.BOARD_MARGIN,
            self.HEADER_HEIGHT + self.BOARD_MARGIN,
        )
        self.window_size = (
            board_pixels + 2 * self.BOARD_MARGIN,
            self.board_origin[1] + board_pixels + self.BOARD_MARGIN,
        )
        self._title_font = pygame.font.Font(None, 58)
        self._large_font = pygame.font.Font(None, 44)
        self._medium_font = pygame.font.Font(None, 30)
        self._small_font = pygame.font.Font(None, 24)

    def logical_to_screen(self, x, y):
        """Return the pixel center of a logical (x, y) board cell."""
        if not self.game.get_board().is_inside(y, x):
            raise IndexError("Board coordinates must be between 0 and 8.")
        origin_x, origin_y = self.board_origin
        return (
            origin_x + x * self.CELL_SIZE + self.CELL_SIZE // 2,
            origin_y + y * self.CELL_SIZE + self.CELL_SIZE // 2,
        )

    def screen_to_board(self, screen_position):
        """Return a board (x, y) position or None when outside the grid."""
        screen_x, screen_y = screen_position
        origin_x, origin_y = self.board_origin
        board_x = screen_x - origin_x
        board_y = screen_y - origin_y
        board_pixels = self.board_size * self.CELL_SIZE
        if not (0 <= board_x < board_pixels and 0 <= board_y < board_pixels):
            return None
        return board_x // self.CELL_SIZE, board_y // self.CELL_SIZE

    def gameplay_button_rect(self, button_name):
        """Return the screen rectangle for a gameplay control."""
        right = self.window_size[0] - self.BOARD_MARGIN
        if button_name == "quit":
            return pygame.Rect(right - 78, 22, 78, 36)
        if button_name == "restart":
            return pygame.Rect(right - 172, 22, 84, 36)
        raise ValueError("Unknown gameplay button.")

    def menu_button_rect(self, button_name):
        """Return the screen rectangle for a menu button."""
        center_x = self.window_size[0] // 2
        if button_name in self.game.DIFFICULTY_SPAWN_AMOUNTS:
            index = tuple(self.game.DIFFICULTY_SPAWN_AMOUNTS).index(button_name)
            width = 112
            gap = 12
            total_width = 3 * width + 2 * gap
            left = center_x - total_width // 2
            return pygame.Rect(left + index * (width + gap), 330, width, 46)
        if button_name == "start":
            return pygame.Rect(center_x - 105, 405, 210, 52)
        if button_name == "quit":
            return pygame.Rect(center_x - 105, 475, 210, 48)
        raise ValueError("Unknown menu button.")

    def game_over_button_rect(self, button_name):
        """Return the screen rectangle for a game-over action."""
        center_x = self.window_size[0] // 2
        if button_name == "restart":
            return pygame.Rect(center_x - 112, 420, 224, 48)
        if button_name == "quit":
            return pygame.Rect(center_x - 112, 482, 224, 48)
        raise ValueError("Unknown game-over button.")

    def draw(
        self,
        surface,
        selected_position=None,
        movement_path=None,
        moving_piece_color=None,
        movement_progress=0.0,
    ):
        """Draw current gameplay state and optional path/selection animation."""
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_scoreboard(surface)
        origin_x, origin_y = self.board_origin

        for y in range(self.board_size):
            for x in range(self.board_size):
                cell_rect = pygame.Rect(
                    origin_x + x * self.CELL_SIZE,
                    origin_y + y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                pygame.draw.rect(surface, self.EMPTY_CELL_COLOR, cell_rect)
                pygame.draw.rect(
                    surface,
                    self.GRID_LINE_COLOR,
                    cell_rect,
                    self.GRID_LINE_WIDTH,
                )

        if movement_path:
            self._draw_movement_path(surface, movement_path)

        moving_source = movement_path[0] if movement_path and moving_piece_color else None
        for piece in self.game.get_pieces():
            x, y = piece.get_position()
            if moving_source == (x, y):
                continue
            center = self.logical_to_screen(x, y)
            self._draw_piece(surface, piece.get_color(), center)

        if selected_position is not None and moving_source is None:
            self._draw_selection(surface, selected_position)

        if movement_path and moving_piece_color is not None:
            moving_center = self._path_position(movement_path, movement_progress)
            self._draw_piece(surface, moving_piece_color, moving_center)

    def draw_menu(self, surface):
        """Draw the start menu and currently selected difficulty."""
        surface.fill(self.BACKGROUND_COLOR)
        self._draw_centered_text(
            surface,
            "Five-or-More",
            self._title_font,
            self.TEXT_COLOR,
            215,
        )
        self._draw_centered_text(
            surface,
            "Choose difficulty",
            self._medium_font,
            self.MUTED_TEXT_COLOR,
            285,
        )

        for difficulty in self.game.DIFFICULTY_SPAWN_AMOUNTS:
            self._draw_button(
                surface,
                self.menu_button_rect(difficulty),
                difficulty,
                selected=difficulty == self.game.difficulty,
            )
        self._draw_button(surface, self.menu_button_rect("start"), "Start Game")
        self._draw_button(surface, self.menu_button_rect("quit"), "Quit")

    def draw_game_over(self, surface):
        """Draw a game-over overlay with final and highest scores."""
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))
        panel = pygame.Rect(self.window_size[0] // 2 - 190, 160, 380, 390)
        pygame.draw.rect(surface, (39, 44, 53), panel, border_radius=12)
        self._draw_centered_text(
            surface,
            "Game Over",
            self._large_font,
            self.TEXT_COLOR,
            225,
        )
        self._draw_centered_text(
            surface,
            f"Final Score: {self.game.get_score()}",
            self._medium_font,
            self.TEXT_COLOR,
            300,
        )
        self._draw_centered_text(
            surface,
            f"Highest Score: {self.game.get_highest_score()}",
            self._medium_font,
            self.TEXT_COLOR,
            345,
        )
        self._draw_button(
            surface,
            self.game_over_button_rect("restart"),
            "Restart",
        )
        self._draw_button(
            surface,
            self.game_over_button_rect("quit"),
            "Quit",
        )

    def _draw_scoreboard(self, surface):
        score_surface = self._small_font.render(
            f"Score: {self.game.get_score()}",
            True,
            self.TEXT_COLOR,
        )
        highest_surface = self._small_font.render(
            f"Highest Score: {self.game.get_highest_score()}",
            True,
            self.MUTED_TEXT_COLOR,
        )
        surface.blit(score_surface, (self.BOARD_MARGIN, 17))
        surface.blit(highest_surface, (self.BOARD_MARGIN, 49))
        self._draw_button(
            surface,
            self.gameplay_button_rect("restart"),
            "Restart",
            small=True,
        )
        self._draw_button(
            surface,
            self.gameplay_button_rect("quit"),
            "Quit",
            small=True,
        )

    def _draw_piece(self, surface, color_code, center):
        pygame.draw.circle(
            surface,
            self.PIECE_COLORS[color_code],
            center,
            self.PIECE_RADIUS,
        )
        pygame.draw.circle(
            surface,
            (255, 255, 255),
            center,
            self.PIECE_RADIUS,
            2,
        )

    def _draw_selection(self, surface, position):
        center = self.logical_to_screen(*position)
        pulse = (math.sin(pygame.time.get_ticks() / 130.0) + 1) / 2
        radius = self.PIECE_RADIUS + 5 + round(pulse * 5)
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 3)
        pygame.draw.circle(surface, (255, 220, 90), center, radius + 4, 1)

    def _draw_movement_path(self, surface, path):
        centers = [self.logical_to_screen(x, y) for x, y in path]
        path_layer = pygame.Surface(self.window_size, pygame.SRCALPHA)
        if len(centers) > 1:
            pygame.draw.lines(path_layer, self.PATH_COLOR, False, centers, 7)
        for index, center in enumerate(centers):
            radius = 12 if index in (0, len(centers) - 1) else 7
            pygame.draw.circle(path_layer, self.PATH_COLOR, center, radius)
        surface.blit(path_layer, (0, 0))

    def _path_position(self, path, progress):
        if len(path) == 1:
            return self.logical_to_screen(*path[0])

        step = min(max(progress, 0.0), len(path) - 1)
        segment = min(int(step), len(path) - 2)
        fraction = step - segment
        start_x, start_y = self.logical_to_screen(*path[segment])
        end_x, end_y = self.logical_to_screen(*path[segment + 1])
        return (
            round(start_x + (end_x - start_x) * fraction),
            round(start_y + (end_y - start_y) * fraction),
        )

    def _draw_centered_text(self, surface, text, font, color, y):
        text_surface = font.render(text, True, color)
        rect = text_surface.get_rect(center=(self.window_size[0] // 2, y))
        surface.blit(text_surface, rect)

    def _draw_button(self, surface, rect, label, selected=False, small=False):
        color = self.SELECTED_BUTTON_COLOR if selected else self.BUTTON_COLOR
        pygame.draw.rect(surface, color, rect, border_radius=7)
        pygame.draw.rect(surface, self.GRID_LINE_COLOR, rect, 2, border_radius=7)
        font = self._small_font if small else self._medium_font
        text_surface = font.render(label, True, self.TEXT_COLOR)
        surface.blit(text_surface, text_surface.get_rect(center=rect.center))
