import unittest
from unittest.mock import patch

from .board import Board
from .board_pieces import BoardPieces
from .game_over import GameOverChecker
from .piece import Piece


class GameOverCheckerTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.checker = GameOverChecker(self.board_pieces)

    def test_board_with_obvious_legal_move(self):
        self.board_pieces.add_piece(Piece(4, 4, 1))

        self.assertTrue(self.checker.has_legal_move())
        self.assertFalse(self.checker.is_game_over())

    def test_no_pieces_means_no_legal_move(self):
        self.assertFalse(self.checker.has_legal_move())
        self.assertTrue(self.checker.is_game_over())

    def test_completely_full_board_has_no_legal_move(self):
        for row in range(self.board.SIZE):
            for column in range(self.board.SIZE):
                color = (row * self.board.SIZE + column) % 7 + 1
                self.board_pieces.add_piece(Piece(column, row, color))

        self.assertFalse(self.checker.has_legal_move())
        self.assertTrue(self.checker.is_game_over())

    def test_isolated_piece_and_reachable_empty_cells(self):
        self.board_pieces.add_piece(Piece(4, 4, 1))
        for x, y in ((4, 3), (4, 5), (3, 4), (5, 4)):
            self.board_pieces.add_piece(Piece(x, y, 2))

        self.assertIsNone(self.checker.piece_mover.find_path(4, 4, 0, 0))
        self.assertTrue(self.checker.has_legal_move())

    def test_returns_false_when_pathfinder_finds_no_reachable_destination(self):
        self.board_pieces.add_piece(Piece(4, 4, 1))

        with patch.object(self.checker.piece_mover, "find_path", return_value=None):
            self.assertFalse(self.checker.has_legal_move())
            self.assertTrue(self.checker.is_game_over())

    def test_constructor_requires_board_pieces(self):
        with self.assertRaises(TypeError):
            GameOverChecker(object())


if __name__ == "__main__":
    unittest.main()
