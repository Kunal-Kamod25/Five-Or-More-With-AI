from .board_pieces import BoardPieces
from .line_detector import LineDetector
from .scoring import ScoreCalculator


class MatchResolver:
    """Score detected lines and remove their Pieces from the board."""

    DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))
    MIN_MATCH_LENGTH = 5

    def __init__(self, board_pieces, line_detector, score_calculator):
        if not isinstance(board_pieces, BoardPieces):
            raise TypeError("board_pieces must be a BoardPieces object.")
        if not isinstance(line_detector, LineDetector):
            raise TypeError("line_detector must be a LineDetector object.")
        if not isinstance(score_calculator, ScoreCalculator):
            raise TypeError("score_calculator must be a ScoreCalculator object.")

        self.board_pieces = board_pieces
        self.line_detector = line_detector
        self.score_calculator = score_calculator

    def resolve_matches(self):
        """Score every distinct matching line, then remove its Pieces once."""
        matched_positions = self.line_detector.find_matches()
        if not matched_positions:
            return 0, []

        board = self.board_pieces.board
        matching_lines = set()

        for x, y in matched_positions:
            color = board.get_cell(y, x)
            for delta_x, delta_y in self.DIRECTIONS:
                previous_x = x - delta_x
                previous_y = y - delta_y
                if (
                    board.is_inside(previous_y, previous_x)
                    and board.get_cell(previous_y, previous_x) == color
                ):
                    continue

                line = []
                current_x = x
                current_y = y
                while (
                    board.is_inside(current_y, current_x)
                    and board.get_cell(current_y, current_x) == color
                ):
                    line.append((current_x, current_y))
                    current_x += delta_x
                    current_y += delta_y

                if len(line) >= self.MIN_MATCH_LENGTH:
                    matching_lines.add(tuple(line))

        total_score = sum(
            self.score_calculator.calculate_score(len(line))
            for line in matching_lines
        )

        removed_pieces = [
            self.board_pieces.remove_piece(x, y)
            for x, y in matched_positions
        ]
        return total_score, removed_pieces
