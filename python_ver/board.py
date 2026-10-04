class Board:
    """Store the actual Five-or-More board as a 9-by-9 grid of integers."""

    SIZE = 9
    EMPTY = 0
    MIN_CELL_VALUE = 0
    MAX_CELL_VALUE = 7

    def __init__(self):
        self.reset()

    def reset(self):
        """Replace the board contents with 81 empty cells."""
        self.board = [
            [self.EMPTY for _ in range(self.SIZE)]
            for _ in range(self.SIZE)
        ]

    def is_inside(self, row, column):
        """Return whether the given row and column are on the board."""
        return (
            isinstance(row, int)
            and not isinstance(row, bool)
            and isinstance(column, int)
            and not isinstance(column, bool)
            and 0 <= row < self.SIZE
            and 0 <= column < self.SIZE
        )

    def get_cell(self, row, column):
        """Return a cell value, raising IndexError for an invalid coordinate."""
        if not self.is_inside(row, column):
            raise IndexError("Board coordinates must be between 0 and 8.")
        return self.board[row][column]

    def set_cell(self, row, column, cell_value):
        """Set a cell to an encoding from 0 (empty) through 7 (orange)."""
        if not self.is_inside(row, column):
            raise IndexError("Board coordinates must be between 0 and 8.")
        if (
            not isinstance(cell_value, int)
            or isinstance(cell_value, bool)
            or not self.MIN_CELL_VALUE <= cell_value <= self.MAX_CELL_VALUE
        ):
            raise ValueError("Cell values must be integers from 0 through 7.")
        self.board[row][column] = cell_value

    def is_empty(self, row, column):
        """Return whether a cell is empty, raising IndexError if out of bounds."""
        return self.get_cell(row, column) == self.EMPTY
