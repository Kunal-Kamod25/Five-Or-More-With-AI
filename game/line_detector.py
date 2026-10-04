from .board_pieces import BoardPieces


class LineDetector:
    """Find all board positions that belong to lines of five or more."""

    MIN_MATCH_LENGTH = 5
    DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))

    def __init__(self, board_pieces):
        if not isinstance(board_pieces, BoardPieces):
            raise TypeError("board_pieces must be a BoardPieces object.")
        self.board_pieces = board_pieces

    def find_matches(self):
        """Return the set of positions in every contiguous matching line."""
        board = self.board_pieces.board
        matches = set()

        for y in range(board.SIZE):
            for x in range(board.SIZE):
                color = board.get_cell(y, x)
                if color == board.EMPTY:
                    continue

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
                        matches.update(line)

        return matches
