class ScoreCalculator:
    """Calculate points for a matched line length."""

    MIN_SCORING_LENGTH = 5
    MAX_SCORING_LENGTH = 9

    def calculate_score(self, line_length):
        """Return the original game score for a line length."""
        if (
            not isinstance(line_length, int)
            or isinstance(line_length, bool)
            or line_length < 0
        ):
            raise ValueError("line_length must be a non-negative integer.")

        if self.MIN_SCORING_LENGTH <= line_length <= self.MAX_SCORING_LENGTH:
            return line_length * 2
        return 0
