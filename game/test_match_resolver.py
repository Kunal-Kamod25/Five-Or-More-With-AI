import unittest

from .board import Board
from .board_pieces import BoardPieces
from .line_detector import LineDetector
from .match_resolver import MatchResolver
from .piece import Piece
from .scoring import ScoreCalculator


class MatchResolverTests(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.line_detector = LineDetector(self.board_pieces)
        self.score_calculator = ScoreCalculator()
        self.resolver = MatchResolver(
            self.board_pieces,
            self.line_detector,
            self.score_calculator,
        )

    def add_positions(self, positions, color=1):
        pieces = []
        for x, y in positions:
            piece = Piece(x, y, color)
            self.board_pieces.add_piece(piece)
            pieces.append(piece)
        return pieces

    def assert_resolved_line(self, positions, expected_score):
        original_pieces = self.add_positions(positions)

        score, removed_pieces = self.resolver.resolve_matches()

        self.assertEqual(score, expected_score)
        self.assertEqual(len(removed_pieces), len(positions))
        self.assertEqual(set(removed_pieces), set(original_pieces))
        self.assertTrue(
            all(self.board.get_cell(y, x) == 0 for x, y in positions)
        )

    def test_no_matching_line_returns_zero_and_removes_nothing(self):
        pieces = self.add_positions([(0, 0), (1, 0), (2, 0), (3, 0)])
        board_before = [row[:] for row in self.board.board]

        score, removed_pieces = self.resolver.resolve_matches()

        self.assertEqual(score, 0)
        self.assertEqual(removed_pieces, [])
        self.assertEqual(self.board.board, board_before)
        self.assertEqual(set(self.board_pieces.get_pieces()), set(pieces))

    def test_exactly_five_horizontal_pieces_score_and_are_removed(self):
        self.assert_resolved_line({(x, 2) for x in range(5)}, 10)

    def test_exactly_five_vertical_pieces_score_and_are_removed(self):
        self.assert_resolved_line({(3, y) for y in range(5)}, 10)

    def test_exactly_five_diagonal_down_right_pieces_score_and_are_removed(self):
        self.assert_resolved_line({(index, index) for index in range(5)}, 10)

    def test_exactly_five_diagonal_up_right_pieces_score_and_are_removed(self):
        self.assert_resolved_line({(index, 8 - index) for index in range(5)}, 10)

    def test_lines_of_six_through_nine_score_correctly(self):
        for line_length, expected_score in (
            (6, 12),
            (7, 14),
            (8, 16),
            (9, 18),
        ):
            with self.subTest(line_length=line_length):
                self.setUp()
                self.assert_resolved_line(
                    {(x, 4) for x in range(line_length)},
                    expected_score,
                )

    def test_multiple_separate_matching_lines_sum_their_scores(self):
        horizontal = {(x, 1) for x in range(5)}
        vertical = {(7, y) for y in range(4, 9)}
        positions = horizontal | vertical
        self.add_positions(sorted(positions))

        score, removed_pieces = self.resolver.resolve_matches()

        self.assertEqual(score, 20)
        self.assertEqual(len(removed_pieces), 10)
        self.assertTrue(all(self.board.get_cell(y, x) == 0 for x, y in positions))

    def test_overlapping_lines_score_individually_but_remove_shared_piece_once(self):
        horizontal = {(x, 4) for x in range(5)}
        vertical = {(4, y) for y in range(5)}
        positions = horizontal | vertical
        self.add_positions(sorted(positions))

        score, removed_pieces = self.resolver.resolve_matches()

        self.assertEqual(score, 20)
        self.assertEqual(len(removed_pieces), 9)
        self.assertEqual(len({piece.get_position() for piece in removed_pieces}), 9)
        self.assertTrue(all(self.board.get_cell(y, x) == 0 for x, y in positions))

    def test_unrelated_pieces_remain_unchanged(self):
        matching_positions = {(x, 2) for x in range(5)}
        unrelated = self.add_positions([(8, 8)], color=2)[0]
        self.add_positions(sorted(matching_positions))

        score, removed_pieces = self.resolver.resolve_matches()

        self.assertEqual(score, 10)
        self.assertEqual(len(removed_pieces), 5)
        self.assertEqual(unrelated.get_position(), (8, 8))
        self.assertIs(self.board_pieces.get_piece(8, 8), unrelated)
        self.assertEqual(self.board.get_cell(8, 8), 2)

    def test_constructor_validates_argument_types(self):
        with self.assertRaises(TypeError):
            MatchResolver(object(), self.line_detector, self.score_calculator)
        with self.assertRaises(TypeError):
            MatchResolver(self.board_pieces, object(), self.score_calculator)
        with self.assertRaises(TypeError):
            MatchResolver(self.board_pieces, self.line_detector, object())


if __name__ == "__main__":
    unittest.main()
