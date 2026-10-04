import pygame

from .game import Game
from .renderer import GameRenderer


class InputController:
    """Translate mouse clicks into selections and animated move requests."""

    MOVE_SECONDS_PER_STEP = 0.10

    def __init__(self, game, renderer):
        if not isinstance(game, Game):
            raise TypeError("game must be a Game object.")
        if not isinstance(renderer, GameRenderer):
            raise TypeError("renderer must be a GameRenderer object.")
        self.game = game
        self.renderer = renderer
        self.reset()

    def reset(self):
        """Clear selection and any in-progress visual move."""
        self.selected_position = None
        self.movement_path = None
        self.moving_piece_color = None
        self.animation_elapsed = 0.0
        self.last_move_result = None

    @property
    def movement_progress(self):
        if not self.movement_path or len(self.movement_path) < 2:
            return 0.0
        return self.animation_elapsed / self.MOVE_SECONDS_PER_STEP

    def handle_event(self, event):
        """Select a Piece or preview a destination path from a mouse click."""
        if event.type != pygame.MOUSEBUTTONDOWN:
            return False
        if event.button == 3:
            had_selection_or_path = (
                self.selected_position is not None
                or self.movement_path is not None
            )
            self.reset()
            return had_selection_or_path
        if event.button != 1 or self.movement_path is not None:
            return False

        position = self.renderer.screen_to_board(event.pos)
        if position is None:
            return False

        x, y = position
        cell_value = self.game.get_board().get_cell(y, x)
        if self.selected_position is None:
            if cell_value == self.game.get_board().EMPTY:
                return False
            self.selected_position = position
            return True

        if cell_value != self.game.get_board().EMPTY:
            self.selected_position = position
            return True

        source_x, source_y = self.selected_position
        path = self.game.find_path(source_x, source_y, x, y)
        if path is None:
            self.movement_path = None
            self.moving_piece_color = None
            self.animation_elapsed = 0.0
            return False

        self.movement_path = path
        self.moving_piece_color = self.game.get_board().get_cell(
            source_y,
            source_x,
        )
        self.animation_elapsed = 0.0
        self.last_move_result = None
        return True

    def update(self, elapsed_seconds):
        """Advance the visual move and commit it to Game when its animation ends."""
        if self.movement_path is None:
            return None

        self.animation_elapsed += max(0.0, elapsed_seconds)
        movement_duration = max(
            1,
            len(self.movement_path) - 1,
        ) * self.MOVE_SECONDS_PER_STEP
        if self.animation_elapsed < movement_duration:
            return None

        source_x, source_y = self.movement_path[0]
        destination_x, destination_y = self.movement_path[-1]
        move_result = self.game.make_move(
            source_x,
            source_y,
            destination_x,
            destination_y,
        )
        self.reset()
        self.last_move_result = move_result
        return move_result
