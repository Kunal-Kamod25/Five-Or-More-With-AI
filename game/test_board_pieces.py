import unittest

from .board import Board
from .board_pieces import BoardPieces
from .piece import Piece


class BoardPiecesTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.piece = Piece(3, 5, 4)

    def test_adding_piece_updates_board(self):
        self.board_pieces.add_piece(self.piece)

        self.assertEqual(self.board.get_cell(5, 3), 4)

    def test_piece_can_be_retrieved_by_position(self):
        self.board_pieces.add_piece(self.piece)

        self.assertIs(self.board_pieces.get_piece(3, 5), self.piece)

    def test_get_pieces_contains_added_piece(self):
        self.board_pieces.add_piece(self.piece)

        self.assertIn(self.piece, self.board_pieces.get_pieces())

    def test_get_pieces_does_not_expose_internal_collection(self):
        self.board_pieces.add_piece(self.piece)
        pieces = self.board_pieces.get_pieces()

        with self.assertRaises(AttributeError):
            pieces.clear()

    def test_removing_piece_clears_board_and_collection(self):
        self.board_pieces.add_piece(self.piece)

        removed_piece = self.board_pieces.remove_piece(3, 5)

        self.assertIs(removed_piece, self.piece)
        self.assertEqual(self.board.get_cell(5, 3), 0)
        self.assertIsNone(self.board_pieces.get_piece(3, 5))

    def test_adding_piece_to_occupied_cell_fails(self):
        self.board_pieces.add_piece(self.piece)
        another_piece = Piece(3, 5, 2)

        with self.assertRaises(ValueError):
            self.board_pieces.add_piece(another_piece)

    def test_invalid_board_positions_fail(self):
        for x, y in ((-1, 0), (9, 0), (0, -1), (0, 9)):
            with self.subTest(x=x, y=y):
                with self.assertRaises(IndexError):
                    self.board_pieces.add_piece(Piece(x, y, 1))
                with self.assertRaises(IndexError):
                    self.board_pieces.remove_piece(x, y)

    def test_removing_nonexistent_piece_fails(self):
        with self.assertRaises(KeyError):
            self.board_pieces.remove_piece(3, 5)


if __name__ == "__main__":
    unittest.main()
