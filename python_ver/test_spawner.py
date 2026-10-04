import unittest

from .board import Board
from .board_pieces import BoardPieces
from .piece import Piece
from .spawner import PieceSpawner


class PieceSpawnerTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.spawner = PieceSpawner(self.board_pieces)

    def test_spawns_one_piece(self):
        pieces = self.spawner.spawn(1)

        self.assertEqual(len(pieces), 1)
        self.assertIsInstance(pieces[0], Piece)
        self.assertEqual(len(self.board_pieces.get_pieces()), 1)

    def test_spawns_multiple_pieces_with_unique_positions(self):
        pieces = self.spawner.spawn(8)
        positions = [piece.get_position() for piece in pieces]

        self.assertEqual(len(pieces), 8)
        self.assertEqual(len(set(positions)), 8)

    def test_spawned_positions_were_empty(self):
        self.board_pieces.add_piece(Piece(0, 0, 1))
        empty_before_spawning = {
            (column, row)
            for row in range(self.board.SIZE)
            for column in range(self.board.SIZE)
            if self.board.is_empty(row, column)
        }

        pieces = self.spawner.spawn(5)

        self.assertTrue(
            all(piece.get_position() in empty_before_spawning for piece in pieces)
        )
        self.assertTrue(
            all(
                self.board.get_cell(y, x) == piece.get_color()
                for piece in pieces
                for x, y in [piece.get_position()]
            )
        )

    def test_spawned_colors_are_between_one_and_seven(self):
        pieces = self.spawner.spawn(30)

        self.assertTrue(all(1 <= piece.get_color() <= 7 for piece in pieces))

    def test_spawns_only_available_empty_cells(self):
        for row in range(self.board.SIZE):
            for column in range(self.board.SIZE):
                if (column, row) not in ((2, 3), (7, 8)):
                    self.board_pieces.add_piece(Piece(column, row, 1))

        pieces = self.spawner.spawn(5)

        self.assertEqual(len(pieces), 2)
        self.assertEqual(
            {piece.get_position() for piece in pieces},
            {(2, 3), (7, 8)},
        )
        self.assertEqual(len(self.board_pieces.get_pieces()), 81)

    def test_spawning_zero_returns_empty_list(self):
        self.assertEqual(self.spawner.spawn(0), [])
        self.assertEqual(self.board_pieces.get_pieces(), ())

    def test_negative_amount_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.spawner.spawn(-1)


if __name__ == "__main__":
    unittest.main()
