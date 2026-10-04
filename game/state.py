from .board import Board


class StateEncoder:
    """Create independent state snapshots from a Board."""

    def __init__(self, board):
        if not isinstance(board, Board):
            raise TypeError("board must be a Board object.")
        self.board = board

    def encode(self):
        """Return a copy of the board's 9-by-9 cell encoding."""
        return [row[:] for row in self.board.board]

    def encode_flat(self):
        """Return the board snapshot as 81 values in row-major order."""
        return [
            cell
            for row in self.encode()
            for cell in row
        ]
