import unittest

from .board import Board
from .board_pieces import BoardPieces
from .line_detector import LineDetector
from .piece import Piece


class LineDetectorTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.detector = LineDetector(self.board_pieces)

    def add_positions(self, positions, color=1):
        for x, y in positions:
            self.board_pieces.add_piece(Piece(x, y, color))

    def test_no_matches(self):
        self.add_positions([(0, 0), (1, 0), (2, 0), (3, 0)])

        self.assertEqual(self.detector.find_matches(), set())

    def test_exactly_five_horizontal_pieces_match(self):
        positions = {(x, 2) for x in range(5)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), positions)

    def test_exactly_five_vertical_pieces_match(self):
        positions = {(3, y) for y in range(5)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), positions)

    def test_exactly_five_diagonal_down_right_pieces_match(self):
        positions = {(index, index) for index in range(5)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), positions)

    def test_exactly_five_diagonal_up_right_pieces_match(self):
        positions = {(index, 8 - index) for index in range(5)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), positions)

    def test_fewer_than_five_contiguous_pieces_do_not_match(self):
        positions = {(x, 4) for x in range(4)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), set())

    def test_line_longer_than_five_matches_all_pieces(self):
        positions = {(x, 5) for x in range(7)}
        self.add_positions(sorted(positions))

        self.assertEqual(self.detector.find_matches(), positions)

    def test_different_color_interrupts_a_line(self):
        red_positions = {(x, 3) for x in (0, 1, 2, 3, 5, 6, 7, 8)}
        self.add_positions(sorted(red_positions), color=1)
        self.add_positions([(4, 3)], color=2)

        self.assertEqual(self.detector.find_matches(), set())

    def test_separate_matching_lines_are_all_detected(self):
        horizontal = {(x, 1) for x in range(5)}
        vertical = {(7, y) for y in range(4, 9)}
        self.add_positions(sorted(horizontal | vertical))

        self.assertEqual(self.detector.find_matches(), horizontal | vertical)

    def test_crossing_lines_are_detected_without_duplicate_positions(self):
        horizontal = {(x, 4) for x in range(9)}
        vertical = {(4, y) for y in range(9)}
        expected = horizontal | vertical
        self.add_positions(sorted(expected))

        matches = self.detector.find_matches()

        self.assertEqual(matches, expected)
        self.assertEqual(len(matches), 17)

    def test_lines_at_board_edges_and_corners_are_detected(self):
        top_edge = {(x, 0) for x in range(4, 9)}
        down_right_from_corner = {(index, index) for index in range(5)}
        up_right_from_corner = {(index, 8 - index) for index in range(5)}
        expected = (
            top_edge | down_right_from_corner | up_right_from_corner
        )
        self.add_positions(sorted(expected))

        self.assertEqual(self.detector.find_matches(), expected)


if __name__ == "__main__":
    unittest.main()
