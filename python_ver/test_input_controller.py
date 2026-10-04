import unittest
from unittest.mock import patch

import pygame

from .game import Game
from .input_controller import InputController
from .piece import Piece
from .renderer import GameRenderer


class InputControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.game = Game()
        self.game.start_game()
        for piece in self.game.get_pieces():
            x, y = piece.get_position()
            self.game.board_pieces.remove_piece(x, y)
        self.game.board_pieces.add_piece(Piece(2, 2, 1))
        self.game.board_pieces.add_piece(Piece(5, 5, 2))
        self.renderer = GameRenderer(self.game)
        self.controller = InputController(self.game, self.renderer)

    def click_cell(self, x, y):
        return self.controller.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                {"pos": self.renderer.logical_to_screen(x, y), "button": 1},
            )
        )

    def test_first_click_selects_a_piece(self):
        self.assertTrue(self.click_cell(2, 2))

        self.assertEqual(self.controller.selected_position, (2, 2))

    def test_empty_cell_does_not_become_a_source_selection(self):
        self.assertFalse(self.click_cell(0, 0))

        self.assertIsNone(self.controller.selected_position)

    def test_second_click_requests_move_with_source_and_destination(self):
        self.click_cell(2, 2)

        with patch.object(self.game, "make_move", return_value=True) as make_move:
            self.assertTrue(self.click_cell(3, 2))
            self.assertEqual(
                self.controller.movement_path,
                [(2, 2), (3, 2)],
            )
            self.controller.update(self.controller.MOVE_SECONDS_PER_STEP)

        make_move.assert_called_once_with(2, 2, 3, 2)

    def test_unreachable_destination_preserves_selection_and_board(self):
        self.click_cell(2, 2)
        board_before = [row[:] for row in self.game.board.board]

        with patch.object(self.game, "find_path", return_value=None) as find_path:
            self.assertFalse(self.click_cell(0, 0))

        find_path.assert_called_once_with(2, 2, 0, 0)
        self.assertEqual(self.controller.selected_position, (2, 2))
        self.assertIsNone(self.controller.movement_path)
        self.assertEqual(self.game.board.board, board_before)

    def test_successful_move_resets_selection(self):
        self.click_cell(2, 2)
        self.click_cell(3, 2)

        self.assertIsNotNone(self.controller.movement_path)
        self.controller.update(self.controller.MOVE_SECONDS_PER_STEP)

        self.assertIsNone(self.controller.selected_position)
        self.assertEqual(self.game.board.get_cell(2, 3), 1)

    def test_clicking_another_piece_replaces_selection(self):
        self.click_cell(2, 2)

        self.assertTrue(self.click_cell(5, 5))

        self.assertEqual(self.controller.selected_position, (5, 5))
        self.assertIsNone(self.controller.movement_path)

    def test_right_click_cancels_selection_and_path(self):
        self.click_cell(2, 2)
        self.click_cell(3, 2)

        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": self.renderer.logical_to_screen(3, 2), "button": 3},
        )

        self.assertTrue(self.controller.handle_event(event))
        self.assertIsNone(self.controller.selected_position)
        self.assertIsNone(self.controller.movement_path)

    def test_reset_clears_selection_and_animation_state(self):
        self.click_cell(2, 2)
        self.click_cell(3, 2)

        self.controller.reset()

        self.assertIsNone(self.controller.selected_position)
        self.assertIsNone(self.controller.movement_path)
        self.assertIsNone(self.controller.moving_piece_color)

    def test_non_left_click_does_not_change_selection(self):
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": self.renderer.logical_to_screen(2, 2), "button": 3},
        )

        self.assertFalse(self.controller.handle_event(event))
        self.assertIsNone(self.controller.selected_position)


if __name__ == "__main__":
    unittest.main()
