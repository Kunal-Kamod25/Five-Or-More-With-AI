import heapq

from .board_pieces import BoardPieces


class PieceMover:
    """Find paths and move Pieces on an existing Board."""

    DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))

    def __init__(self, board_pieces):
        if not isinstance(board_pieces, BoardPieces):
            raise TypeError("board_pieces must be a BoardPieces object.")
        self.board_pieces = board_pieces

    def find_path(self, start_x, start_y, destination_x, destination_y):
        """Find an A* path as a list of (x, y) positions, or return None."""
        board = self.board_pieces.board
        start = (start_x, start_y)
        destination = (destination_x, destination_y)

        if not board.is_inside(start_y, start_x):
            return None
        if not board.is_inside(destination_y, destination_x):
            return None
        if self.board_pieces.get_piece(start_x, start_y) is None:
            return None
        if not board.is_empty(destination_y, destination_x):
            return None

        open_positions = []
        heapq.heappush(
            open_positions,
            (self._heuristic(start, destination), 0, start),
        )
        came_from = {}
        path_costs = {start: 0}
        visited = set()
        sequence = 1

        while open_positions:
            _, current_cost, current = heapq.heappop(open_positions)
            if current in visited:
                continue
            if current == destination:
                return self._build_path(came_from, destination)
            visited.add(current)

            for delta_x, delta_y in self.DIRECTIONS:
                neighbor = (current[0] + delta_x, current[1] + delta_y)
                neighbor_x, neighbor_y = neighbor

                if not board.is_inside(neighbor_y, neighbor_x):
                    continue
                if not board.is_empty(neighbor_y, neighbor_x):
                    continue

                new_cost = current_cost + 1
                if new_cost >= path_costs.get(neighbor, float("inf")):
                    continue

                came_from[neighbor] = current
                path_costs[neighbor] = new_cost
                priority = new_cost + self._heuristic(neighbor, destination)
                heapq.heappush(
                    open_positions,
                    (priority, sequence, neighbor),
                )
                sequence += 1

        return None

    def move_piece(self, start_x, start_y, destination_x, destination_y):
        """Move a Piece logically, returning False for an invalid destination."""
        board = self.board_pieces.board
        coordinates = (
            (start_x, start_y),
            (destination_x, destination_y),
        )
        if any(not board.is_inside(y, x) for x, y in coordinates):
            raise IndexError("Piece positions must be inside the board.")

        piece = self.board_pieces.get_piece(start_x, start_y)
        if piece is None:
            raise KeyError("No piece exists at the source position.")
        if not board.is_empty(destination_y, destination_x):
            return False
        if (
            self.find_path(start_x, start_y, destination_x, destination_y)
            is None
        ):
            return False

        self.board_pieces.remove_piece(start_x, start_y)
        piece.set_position(destination_x, destination_y)
        self.board_pieces.add_piece(piece)
        return True

    @staticmethod
    def _heuristic(position, destination):
        return abs(position[0] - destination[0]) + abs(position[1] - destination[1])

    @staticmethod
    def _build_path(came_from, destination):
        path = [destination]
        while path[-1] in came_from:
            path.append(came_from[path[-1]])
        path.reverse()
        return path
