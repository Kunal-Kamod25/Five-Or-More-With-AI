import random

from .board_pieces import BoardPieces
from .piece import Piece


class PieceSpawner:
    """Spawn randomly colored pieces into empty cells."""

    def __init__(self, board_pieces):
        if not isinstance(board_pieces, BoardPieces):
            raise TypeError("board_pieces must be a BoardPieces object.")
        self.board_pieces = board_pieces

    def spawn(self, amount):
        """Create up to amount pieces in randomly selected empty cells."""
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise ValueError("amount must be a non-negative integer.")

        board = self.board_pieces.board
        empty_positions = [
            (column, row)
            for row in range(board.SIZE)
            for column in range(board.SIZE)
            if board.is_empty(row, column)
        ]
        selected_positions = random.sample(
            empty_positions,
            min(amount, len(empty_positions)),
        )

        pieces = []
        for x, y in selected_positions:
            piece = Piece(x, y, random.randint(1, 7))
            self.board_pieces.add_piece(piece)
            pieces.append(piece)

        return pieces
