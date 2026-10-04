import unittest
from unittest.mock import call, patch

import pygame

from .game import Game
from .piece import Piece
from .renderer import GameRenderer


class GameRendererTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.renderer = GameRenderer(self.game)

    def test_renderer_setup_uses_nine_by_nine_board_dimensions(self):
        expected_side = (
            9 * self.renderer.CELL_SIZE + 2 * self.renderer.BOARD_MARGIN
        )
        expected_height = (
            self.renderer.board_origin[1]
            + 9 * self.renderer.CELL_SIZE
            + self.renderer.BOARD_MARGIN
        )

        self.assertEqual(self.renderer.board_size, 9)
        self.assertEqual(
            self.renderer.window_size,
            (expected_side, expected_height),
        )
        self.assertEqual(len(self.renderer.PIECE_COLORS), 7)
        self.assertEqual(len(set(self.renderer.PIECE_COLORS.values())), 7)

    def test_coordinate_conversion_returns_cell_centers(self):
        self.assertEqual(
            self.renderer.logical_to_screen(0, 0),
            (
                self.renderer.BOARD_MARGIN + self.renderer.CELL_SIZE // 2,
                self.renderer.board_origin[1] + self.renderer.CELL_SIZE // 2,
            ),
        )
        self.assertEqual(
            self.renderer.logical_to_screen(8, 8),
            (
                self.renderer.BOARD_MARGIN
                + 8 * self.renderer.CELL_SIZE
                + self.renderer.CELL_SIZE // 2,
                self.renderer.board_origin[1]
                + 8 * self.renderer.CELL_SIZE
                + self.renderer.CELL_SIZE // 2,
            ),
        )

    def test_coordinate_conversion_rejects_invalid_positions(self):
        for x, y in ((-1, 0), (9, 0), (0, -1), (0, 9)):
            with self.subTest(x=x, y=y):
                with self.assertRaises(IndexError):
                    self.renderer.logical_to_screen(x, y)

    def test_draw_renders_empty_cells_and_piece_without_changing_board(self):
        self.game.board_pieces.add_piece(Piece(2, 3, 1))
        board_before = [row[:] for row in self.game.get_board().board]
        surface = pygame.Surface(self.renderer.window_size)

        self.renderer.draw(surface)

        self.assertEqual(self.game.get_board().board, board_before)
        empty_cell_center = self.renderer.logical_to_screen(0, 0)
        piece_center = self.renderer.logical_to_screen(2, 3)
        self.assertEqual(
            surface.get_at(empty_cell_center)[:3],
            self.renderer.EMPTY_CELL_COLOR,
        )
        self.assertEqual(
            surface.get_at(piece_center)[:3],
            self.renderer.PIECE_COLORS[1],
        )

    def test_draw_accepts_selection_and_path_visual_state(self):
        piece = Piece(2, 3, 1)
        self.game.board_pieces.add_piece(piece)
        path = [(2, 3), (3, 3), (4, 3)]
        surface = pygame.Surface(self.renderer.window_size)

        self.renderer.draw(
            surface,
            selected_position=(2, 3),
            movement_path=path,
            moving_piece_color=1,
            movement_progress=0.5,
        )

        self.assertEqual(self.game.get_board().get_cell(3, 2), 1)
        middle_of_path = (
            self.renderer.logical_to_screen(3, 3)[0] + 20,
            self.renderer.logical_to_screen(3, 3)[1],
        )
        self.assertNotEqual(
            surface.get_at(middle_of_path)[:3],
            self.renderer.EMPTY_CELL_COLOR,
        )

    def test_menu_and_game_over_screens_draw(self):
        surface = pygame.Surface(self.renderer.window_size)

        self.renderer.draw_menu(surface)
        selected_button = self.renderer.menu_button_rect(self.game.difficulty)
        self.assertEqual(
            surface.get_at(
                (selected_button.left + 5, selected_button.top + 5)
            )[:3],
            self.renderer.SELECTED_BUTTON_COLOR,
        )
        self.renderer.draw_game_over(surface)

        self.assertTrue(
            self.renderer.menu_button_rect("Easy").collidepoint(
                self.renderer.menu_button_rect("Easy").center
            )
        )

    def test_game_over_screen_includes_final_and_highest_scores(self):
        self.game.total_score = 24
        self.game.highest_score = 31
        surface = pygame.Surface(self.renderer.window_size)

        with patch.object(self.renderer, "_draw_centered_text") as draw_text:
            self.renderer.draw_game_over(surface)

        self.assertIn(
            call(
                surface,
                "Final Score: 24",
                self.renderer._medium_font,
                self.renderer.TEXT_COLOR,
                300,
            ),
            draw_text.call_args_list,
        )
        self.assertIn(
            call(
                surface,
                "Highest Score: 31",
                self.renderer._medium_font,
                self.renderer.TEXT_COLOR,
                345,
            ),
            draw_text.call_args_list,
        )

    def test_constructor_requires_a_game(self):
        with self.assertRaises(TypeError):
            GameRenderer(object())


if __name__ == "__main__":
    unittest.main()
