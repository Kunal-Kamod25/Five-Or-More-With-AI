import unittest

from .board import Board


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_new_board_is_nine_by_nine_and_empty(self):
        self.assertEqual(len(self.board.board), 9)
        self.assertTrue(all(len(row) == 9 for row in self.board.board))
        self.assertEqual(
            sum(cell == 0 for row in self.board.board for cell in row),
            81,
        )

    def test_read_and_change_cell(self):
        self.assertEqual(self.board.get_cell(2, 3), 0)
        self.board.set_cell(2, 3, 4)
        self.assertEqual(self.board.get_cell(2, 3), 4)
        self.assertFalse(self.board.is_empty(2, 3))
        self.assertTrue(self.board.is_empty(0, 0))

    def test_reset_clears_all_cells(self):
        self.board.set_cell(8, 8, 7)
        self.board.reset()
        self.assertTrue(all(cell == 0 for row in self.board.board for cell in row))

    def test_out_of_bounds_coordinates_are_rejected(self):
        for row, column in ((-1, 0), (9, 0), (0, -1), (0, 9)):
            with self.subTest(row=row, column=column):
                self.assertFalse(self.board.is_inside(row, column))
                with self.assertRaises(IndexError):
                    self.board.get_cell(row, column)
                with self.assertRaises(IndexError):
                    self.board.set_cell(row, column, 1)

    def test_non_integer_coordinates_are_rejected(self):
        for row, column in ((1.5, 0), (0, "1"), (True, 0)):
            with self.subTest(row=row, column=column):
                self.assertFalse(self.board.is_inside(row, column))

    def test_cell_values_must_use_the_defined_encoding(self):
        for invalid_value in (-1, 8, 1.5, True):
            with self.subTest(cell_value=invalid_value):
                with self.assertRaises(ValueError):
                    self.board.set_cell(0, 0, invalid_value)


if __name__ == "__main__":
    unittest.main()
