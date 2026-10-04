from .board import Board
from .board_pieces import BoardPieces
from .game_over import GameOverChecker
from .line_detector import LineDetector
from .match_resolver import MatchResolver
from .movement import PieceMover
from .scoring import ScoreCalculator
from .spawner import PieceSpawner


class Game:
    """Coordinate the core Five-or-More game components."""

    INITIAL_PIECE_COUNT = 5
    DIFFICULTY_SPAWN_AMOUNTS = {
        "Easy": 1,
        "Medium": 2,
        "Hard": 3,
    }

    def __init__(self, difficulty="Medium"):
        self.board = Board()
        self.board_pieces = BoardPieces(self.board)
        self.spawner = PieceSpawner(self.board_pieces)
        self.piece_mover = PieceMover(self.board_pieces)
        self.line_detector = LineDetector(self.board_pieces)
        self.score_calculator = ScoreCalculator()
        self.match_resolver = MatchResolver(
            self.board_pieces,
            self.line_detector,
            self.score_calculator,
        )
        self.game_over_checker = GameOverChecker(self.board_pieces)
        self.total_score = 0
        self.highest_score = 0
        self.game_started = False
        self.game_over = False
        self.set_difficulty(difficulty)

    def set_difficulty(self, difficulty):
        """Set the spawn amount used after a non-matching move."""
        if (
            not isinstance(difficulty, str)
            or difficulty not in self.DIFFICULTY_SPAWN_AMOUNTS
        ):
            raise ValueError("difficulty must be Easy, Medium, or Hard.")
        self.difficulty = difficulty

    def get_highest_score(self):
        """Return the highest score achieved in this application session."""
        return self.highest_score

    def find_path(self, start_x, start_y, destination_x, destination_y):
        """Return a movement path without changing the board."""
        return self.piece_mover.find_path(
            start_x,
            start_y,
            destination_x,
            destination_y,
        )

    def start_game(self):
        """Reset the board and begin a new game with five pieces."""
        for piece in self.board_pieces.get_pieces():
            x, y = piece.get_position()
            self.board_pieces.remove_piece(x, y)

        self.board.reset()
        self.total_score = 0
        self.game_over = False
        self.spawner.spawn(self.INITIAL_PIECE_COUNT)
        self.game_started = True
        score, _ = self.match_resolver.resolve_matches()
        self._add_score(score)
        self.game_over = self.game_over_checker.is_game_over()

    def restart_game(self):
        """Start a new game while preserving difficulty and highest score."""
        self.start_game()

    def make_move(self, start_x, start_y, destination_x, destination_y):
        """Move a piece, resolve matches, and spawn once after a non-match."""
        if not self.game_started or self.game_over:
            return False

        try:
            moved = self.piece_mover.move_piece(
                start_x,
                start_y,
                destination_x,
                destination_y,
            )
        except (IndexError, KeyError):
            return False

        if not moved:
            return False

        score, removed_pieces = self.match_resolver.resolve_matches()
        self._add_score(score)
        if not removed_pieces:
            spawn_amount = self.DIFFICULTY_SPAWN_AMOUNTS[self.difficulty]
            self.spawner.spawn(spawn_amount)
            score, _ = self.match_resolver.resolve_matches()
            self._add_score(score)

        self.game_over = self.game_over_checker.is_game_over()
        return True

    def get_score(self):
        """Return the current total score."""
        return self.total_score

    def get_board(self):
        """Return the game's Board."""
        return self.board

    def get_pieces(self):
        """Return a snapshot of the pieces currently in play."""
        return self.board_pieces.get_pieces()

    def is_game_over(self):
        """Return whether the game has ended."""
        return self.game_over

    def _add_score(self, score):
        self.total_score += score
        self.highest_score = max(self.highest_score, self.total_score)
