class Piece:
    """Represent a colored piece and its board position."""

    MIN_COLOR = 1
    MAX_COLOR = 7

    def __init__(self, x, y, piece_color):
        self._validate_color(piece_color)
        self.x = x
        self.y = y
        self.piece_color = piece_color

    def get_position(self):
        """Return the piece position as an (x, y) tuple."""
        return self.x, self.y

    def set_position(self, x, y):
        """Update the piece position."""
        self.x = x
        self.y = y

    def get_color(self):
        """Return the piece color encoding."""
        return self.piece_color

    @classmethod
    def _validate_color(cls, piece_color):
        if (
            not isinstance(piece_color, int)
            or isinstance(piece_color, bool)
            or not cls.MIN_COLOR <= piece_color <= cls.MAX_COLOR
        ):
            raise ValueError("Piece color must be an integer from 1 through 7.")
