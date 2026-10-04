import unittest

from .board import Board
from .board_pieces import BoardPieces
from .movement import PieceMover
from .piece import Piece


class PieceMoverTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.mover = PieceMover(self.board_pieces)

    def add_piece(self, x, y, color=1):
        piece = Piece(x, y, color)
        self.board_pieces.add_piece(piece)
        return piece

    def assert_path_uses_only_orthogonal_steps(self, path):
        for current, following in zip(path, path[1:]):
            distance = abs(current[0] - following[0]) + abs(
                current[1] - following[1]
            )
            self.assertEqual(distance, 1)

    def test_moves_piece_to_adjacent_horizontal_cell(self):
        piece = self.add_piece(2, 3)

        self.assertTrue(self.mover.move_piece(2, 3, 3, 3))
        self.assertIs(self.board_pieces.get_piece(3, 3), piece)

    def test_moves_piece_vertically(self):
        piece = self.add_piece(2, 3)

        self.assertTrue(self.mover.move_piece(2, 3, 2, 4))
        self.assertIs(self.board_pieces.get_piece(2, 4), piece)

    def test_finds_path_around_an_occupied_cell(self):
        self.add_piece(1, 1)
        self.add_piece(2, 1, 2)

        path = self.mover.find_path(1, 1, 3, 1)

        self.assertIsNotNone(path)
        self.assert_path_uses_only_orthogonal_steps(path)
        self.assertGreater(len(path), 3)
        self.assertNotIn((2, 1), path[1:])

    def test_diagonal_destination_requires_orthogonal_steps(self):
        self.add_piece(0, 0)

        path = self.mover.find_path(0, 0, 1, 1)

        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (1, 1))
        self.assertEqual(len(path), 3)
        self.assert_path_uses_only_orthogonal_steps(path)

    def test_occupied_destination_is_rejected(self):
        self.add_piece(1, 1)
        self.add_piece(2, 1, 2)

        self.assertFalse(self.mover.move_piece(1, 1, 2, 1))

    def test_blocked_destination_with_no_path_returns_false(self):
        piece = self.add_piece(0, 0)
        self.add_piece(1, 0, 2)
        self.add_piece(0, 1, 3)
        board_before = [row[:] for row in self.board.board]

        self.assertFalse(self.mover.move_piece(0, 0, 2, 2))

        self.assertEqual(self.board.board, board_before)
        self.assertIs(self.board_pieces.get_piece(0, 0), piece)
        self.assertEqual(piece.get_position(), (0, 0))

    def test_source_without_a_piece_is_rejected(self):
        with self.assertRaises(KeyError):
            self.mover.move_piece(0, 0, 1, 0)

    def test_invalid_coordinates_are_rejected(self):
        for coordinates in (
            (-1, 0, 1, 0),
            (0, 0, 9, 0),
        ):
            with self.subTest(coordinates=coordinates):
                with self.assertRaises(IndexError):
                    self.mover.move_piece(*coordinates)

    def test_successful_move_updates_piece_and_board(self):
        piece = self.add_piece(2, 2, 5)

        self.assertTrue(self.mover.move_piece(2, 2, 4, 2))

        self.assertEqual(piece.get_position(), (4, 2))
        self.assertEqual(self.board.get_cell(2, 2), 0)
        self.assertEqual(self.board.get_cell(2, 4), 5)
        self.assertIs(self.board_pieces.get_piece(4, 2), piece)

    def test_unsuccessful_move_leaves_original_state_unchanged(self):
        piece = self.add_piece(1, 1)
        self.add_piece(2, 1, 2)
        board_before = [row[:] for row in self.board.board]

        self.assertFalse(self.mover.move_piece(1, 1, 2, 1))

        self.assertEqual(self.board.board, board_before)
        self.assertEqual(piece.get_position(), (1, 1))
        self.assertIs(self.board_pieces.get_piece(1, 1), piece)


if __name__ == "__main__":
    unittest.main()
