from .board import Board
from .piece import Piece


class BoardPieces:
    """Manage Piece objects placed on an existing Board."""

    def __init__(self, board):
        if not isinstance(board, Board):
            raise TypeError("board must be a Board object.")
        self.board = board
        self._pieces = {}

    def add_piece(self, piece):
        """Place a Piece on an empty board cell."""
        if not isinstance(piece, Piece):
            raise TypeError("piece must be a Piece object.")

        x, y = piece.get_position()
        if not self.board.is_inside(y, x):
            raise IndexError("Piece position must be inside the board.")
        if not self.board.is_empty(y, x):
            raise ValueError("Cannot add a piece to an occupied cell.")

        self.board.set_cell(y, x, piece.get_color())
        self._pieces[(x, y)] = piece

    def remove_piece(self, x, y):
        """Remove and return the Piece at the given position."""
        if not self.board.is_inside(y, x):
            raise IndexError("Piece position must be inside the board.")
        if (x, y) not in self._pieces:
            raise KeyError("No piece exists at the given position.")

        piece = self._pieces.pop((x, y))
        self.board.set_cell(y, x, self.board.EMPTY)
        return piece

    def get_piece(self, x, y):
        """Return the Piece at a position, or None when there is no Piece."""
        if not self.board.is_inside(y, x):
            return None
        return self._pieces.get((x, y))

    def get_pieces(self):
        """Return a tuple snapshot of the currently stored Piece objects."""
        return tuple(self._pieces.values())
