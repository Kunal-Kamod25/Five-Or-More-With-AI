import unittest

from .board import Board
from .state import StateEncoder


class StateEncoderTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.encoder = StateEncoder(self.board)

    def test_encodes_empty_board(self):
        self.assertEqual(
            self.encoder.encode(),
            [[0 for _ in range(9)] for _ in range(9)],
        )

    def test_encodes_known_piece_positions_and_colors(self):
        self.board.set_cell(0, 8, 1)
        self.board.set_cell(4, 2, 5)
        self.board.set_cell(8, 0, 7)

        state = self.encoder.encode()

        self.assertEqual(state[0][8], 1)
        self.assertEqual(state[4][2], 5)
        self.assertEqual(state[8][0], 7)
        self.assertEqual(state[2][4], 0)

    def test_encoded_board_has_nine_rows_and_nine_columns(self):
        state = self.encoder.encode()

        self.assertEqual(len(state), 9)
        self.assertTrue(all(len(row) == 9 for row in state))

    def test_flat_encoding_contains_eighty_one_values_in_row_major_order(self):
        self.board.set_cell(0, 1, 3)
        self.board.set_cell(1, 0, 6)

        flat_state = self.encoder.encode_flat()

        self.assertEqual(len(flat_state), 81)
        self.assertEqual(flat_state[1], 3)
        self.assertEqual(flat_state[9], 6)

    def test_modifying_encoded_data_does_not_modify_board(self):
        self.board.set_cell(2, 3, 4)

        encoded_state = self.encoder.encode()
        encoded_state[2][3] = 0
        encoded_state[0][0] = 7
        flat_state = self.encoder.encode_flat()
        flat_state[2 * 9 + 3] = 1

        self.assertEqual(self.board.get_cell(2, 3), 4)
        self.assertEqual(self.board.get_cell(0, 0), 0)

    def test_constructor_requires_a_board(self):
        with self.assertRaises(TypeError):
            StateEncoder(object())


if __name__ == "__main__":
    unittest.main()
