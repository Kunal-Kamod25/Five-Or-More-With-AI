class ScoreCalculator:
    """Calculate points for a matched line length."""

    MIN_SCORING_LENGTH = 5
    MAX_SCORING_LENGTH = 9
    DEFAULT_LINE_SCORES = {
        5: 10,
        6: 12,
        7: 14,
        8: 16,
        9: 18,
    }

    def __init__(self, line_scores=None):
        if line_scores is not None:
            self.line_scores = {
                int(k): int(v) if float(v).is_integer() else float(v)
                for k, v in line_scores.items()
            }
        else:
            self.line_scores = dict(self.DEFAULT_LINE_SCORES)

    def calculate_score(self, line_length):
        """Return the game score for a line length."""
        if (
            not isinstance(line_length, int)
            or isinstance(line_length, bool)
            or line_length < 0
        ):
            raise ValueError("line_length must be a non-negative integer.")

        return self.line_scores.get(line_length, 0)

