import unittest

from .piece import Piece


class PieceTests(unittest.TestCase):
    def test_creates_piece_with_position_and_color(self):
        piece = Piece(2, 5, 4)

        self.assertEqual(piece.x, 2)
        self.assertEqual(piece.y, 5)
        self.assertEqual(piece.piece_color, 4)

    def test_get_position(self):
        piece = Piece(2, 5, 4)

        self.assertEqual(piece.get_position(), (2, 5))

    def test_set_position(self):
        piece = Piece(2, 5, 4)
        piece.set_position(7, 1)

        self.assertEqual(piece.get_position(), (7, 1))

    def test_get_color(self):
        piece = Piece(2, 5, 6)

        self.assertEqual(piece.get_color(), 6)

    def test_rejects_invalid_colors(self):
        for invalid_color in (0, -1, 8, 1.5, True):
            with self.subTest(piece_color=invalid_color):
                with self.assertRaises(ValueError):
                    Piece(0, 0, invalid_color)


if __name__ == "__main__":
    unittest.main()
