from .board_pieces import BoardPieces
from .movement import PieceMover


class GameOverChecker:
    """Check whether any placed Piece can reach an empty board cell."""

    def __init__(self, board_pieces):
        if not isinstance(board_pieces, BoardPieces):
            raise TypeError("board_pieces must be a BoardPieces object.")
        self.board_pieces = board_pieces
        self.piece_mover = PieceMover(board_pieces)

    def has_legal_move(self):
        """Return whether any Piece has a path to an empty cell."""
        pieces = self.board_pieces.get_pieces()
        if not pieces:
            return False

        board = self.board_pieces.board
        empty_positions = [
            (column, row)
            for row in range(board.SIZE)
            for column in range(board.SIZE)
            if board.is_empty(row, column)
        ]
        if not empty_positions:
            return False

        for piece in pieces:
            start_x, start_y = piece.get_position()
            for destination_x, destination_y in empty_positions:
                if self.piece_mover.find_path(
                    start_x,
                    start_y,
                    destination_x,
                    destination_y,
                ) is not None:
                    return True

        return False

    def is_game_over(self):
        """Return whether the board has no legal move."""
        return not self.has_legal_move()
