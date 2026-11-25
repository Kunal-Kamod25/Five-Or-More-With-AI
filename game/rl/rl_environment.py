"""Headless reinforcement-learning interface for Five-or-More.

Actions are integers in [0, 6560]. Each action packs a row-major source
cell index and destination cell index: action = source_index * 81 +
destination_index. A cell index is y * 9 + x. ``step`` returns
``(state, reward, done, info)`` and rejects illegal actions without changing
the game.
"""

from collections import deque
from numbers import Integral

from ..core.game import Game
from ..core.scoring import ScoreCalculator
from ..core.state import StateEncoder


class FiveOrMoreEnv:
    """Wrap the existing headless Game logic with an RL-friendly API."""

    ACTION_COUNT = 81 * 81
    INVALID_ACTION_REWARD = -1.0
    REWARD_PER_SCORE_POINT = 1.0
    STEP_PENALTY = 0.001
    GAME_OVER_PENALTY = 1.0
    SAME_COLOR_CONNECTION_REWARD = 0.1
    SAME_COLOR_DISCONNECTION_PENALTY = 0.1

    def __init__(
        self,
        difficulty="Medium",
        invalid_action_reward=INVALID_ACTION_REWARD,
        score_per_point=REWARD_PER_SCORE_POINT,
        step_penalty=STEP_PENALTY,
        game_over_penalty=GAME_OVER_PENALTY,
        line_rewards=None,
        same_color_connection_reward=SAME_COLOR_CONNECTION_REWARD,
        same_color_disconnection_penalty=SAME_COLOR_DISCONNECTION_PENALTY,
    ):
        if difficulty not in Game.DIFFICULTY_SPAWN_AMOUNTS:
            raise ValueError("difficulty must be Easy, Medium, or Hard.")
        self.difficulty = difficulty
        self.invalid_action_reward = float(invalid_action_reward)
        self.score_per_point = float(score_per_point)
        self.step_penalty = float(step_penalty)
        self.game_over_penalty = float(game_over_penalty)
        self.line_rewards = line_rewards
        self.same_color_connection_reward = float(same_color_connection_reward)
        self.same_color_disconnection_penalty = float(
            same_color_disconnection_penalty
        )
        self.game = None
        self.state_encoder = None

    def reset(self):
        """Start a fresh game and return its 9-by-9 integer state snapshot."""
        score_calc = (
            ScoreCalculator(self.line_rewards)
            if self.line_rewards is not None
            else None
        )
        self.game = Game(
            difficulty=self.difficulty,
            score_calculator=score_calc,
        )
        self.game.start_game()
        self.state_encoder = StateEncoder(self.game.get_board())
        return self.get_state()

    def get_state(self):
        """Return the current board as a copied 9-by-9 list of integer values."""
        self._require_reset()
        return self.state_encoder.encode()

    def get_valid_actions(self):
        """Return legal move actions using one flood fill per source piece."""
        self._require_reset()
        valid_actions = []

        for piece in self.game.get_pieces():
            source_x, source_y = piece.get_position()
            source_index = self._cell_to_index(source_x, source_y)
            for destination_y, destination_x in self._reachable_empty_cells(
                source_x,
                source_y,
            ):
                destination_index = self._cell_to_index(
                    destination_x,
                    destination_y,
                )
                valid_actions.append(source_index * 81 + destination_index)

        return valid_actions

    def step(self, action):
        """Apply one encoded legal move and return state, reward, done, info.

        Invalid actions receive ``INVALID_ACTION_REWARD`` and leave the game
        unchanged. Valid moves receive score-based reward less a small step
        penalty; terminal states also apply ``GAME_OVER_PENALTY``.
        """
        self._require_reset()
        if not isinstance(action, Integral) or isinstance(action, bool):
            return self._invalid_action("action must be an integer action index.")

        action = int(action)
        if not 0 <= action < self.ACTION_COUNT:
            return self._invalid_action("action index is outside the action space.")

        coordinates = self._decode_and_validate_action(action)
        if coordinates is None:
            return self._invalid_action("action is not a legal move.")
        source_x, source_y, destination_x, destination_y = coordinates

        previous_group_potential = self._same_color_group_potential(
            self.get_state()
        )
        previous_score = self.game.get_score()
        moved = self.game.make_move(
            source_x,
            source_y,
            destination_x,
            destination_y,
        )
        if not moved:
            return self._invalid_action("game rejected the requested move.")

        score_delta = self.game.get_score() - previous_score
        group_potential_delta = (
            self._same_color_group_potential(self.get_state())
            - previous_group_potential
        )
        connection_reward = 0.0
        disconnection_penalty = 0.0
        if score_delta == 0:
            connection_reward = (
                max(group_potential_delta, 0)
                * self.same_color_connection_reward
            )
            disconnection_penalty = (
                max(-group_potential_delta, 0)
                * self.same_color_disconnection_penalty
            )
        done = self.game.is_game_over()
        reward = (
            score_delta * self.score_per_point
            + connection_reward
            - disconnection_penalty
            - self.step_penalty
        )
        if done:
            reward -= self.game_over_penalty

        info = {
            "invalid_action": False,
            "score_delta": score_delta,
            "same_color_group_potential_delta": group_potential_delta,
            "connection_reward": connection_reward,
            "disconnection_penalty": disconnection_penalty,
            "difficulty": self.game.difficulty,
        }
        return self.get_state(), reward, done, info

    @staticmethod
    def _same_color_group_potential(state):
        """Score same-color components quadratically by their size."""
        board_size = len(state)
        visited = set()
        potential = 0
        directions = tuple(
            (delta_x, delta_y)
            for delta_y in (-1, 0, 1)
            for delta_x in (-1, 0, 1)
            if delta_x or delta_y
        )

        for y in range(board_size):
            for x in range(board_size):
                color = state[y][x]
                if color == 0 or (x, y) in visited:
                    continue

                component = [(x, y)]
                visited.add((x, y))
                for current_x, current_y in component:
                    for delta_x, delta_y in directions:
                        neighbor_x = current_x + delta_x
                        neighbor_y = current_y + delta_y
                        neighbor = (neighbor_x, neighbor_y)
                        if (
                            0 <= neighbor_x < board_size
                            and 0 <= neighbor_y < board_size
                            and neighbor not in visited
                            and state[neighbor_y][neighbor_x] == color
                        ):
                            visited.add(neighbor)
                            component.append(neighbor)

                if len(component) > 1:
                    potential += (len(component) - 1) ** 2

        return potential

    def _reachable_empty_cells(self, source_x, source_y):
        """Return empty cells connected orthogonally to a source piece."""
        board = self.game.get_board()
        start = (source_x, source_y)
        frontier = deque([start])
        visited = {start}
        reachable = []
        directions = self.game.piece_mover.DIRECTIONS

        while frontier:
            x, y = frontier.popleft()
            for delta_x, delta_y in directions:
                neighbor_x = x + delta_x
                neighbor_y = y + delta_y
                neighbor = (neighbor_x, neighbor_y)
                if neighbor in visited:
                    continue
                if not board.is_inside(neighbor_y, neighbor_x):
                    continue
                if not board.is_empty(neighbor_y, neighbor_x):
                    continue

                visited.add(neighbor)
                reachable.append((neighbor_y, neighbor_x))
                frontier.append(neighbor)

        return reachable

    def _decode_and_validate_action(self, action):
        """Validate action encoding and endpoint occupancy for one move.

        Reachability is checked by the existing ``Game.make_move`` path before
        it mutates the board. This avoids performing a separate path search.
        """
        if not isinstance(action, Integral) or isinstance(action, bool):
            return None
        action = int(action)
        if not 0 <= action < self.ACTION_COUNT:
            return None

        source_index, destination_index = divmod(action, 81)
        source_x, source_y = self._index_to_cell(source_index)
        destination_x, destination_y = self._index_to_cell(destination_index)
        board = self.game.get_board()
        if self.game.game_over:
            return None
        if self.game.board_pieces.get_piece(source_x, source_y) is None:
            return None
        if not board.is_empty(destination_y, destination_x):
            return None
        return source_x, source_y, destination_x, destination_y

    @staticmethod
    def encode_action(source_x, source_y, destination_x, destination_y):
        """Pack source and destination (x, y) cells into one integer action."""
        source_index = FiveOrMoreEnv._cell_to_index(source_x, source_y)
        destination_index = FiveOrMoreEnv._cell_to_index(
            destination_x,
            destination_y,
        )
        return source_index * 81 + destination_index

    @staticmethod
    def decode_action(action):
        """Unpack an integer action as (source_x, source_y, dest_x, dest_y)."""
        if (
            not isinstance(action, Integral)
            or isinstance(action, bool)
            or not 0 <= action < FiveOrMoreEnv.ACTION_COUNT
        ):
            raise ValueError("action must be an integer from 0 through 6560.")
        source_index, destination_index = divmod(int(action), 81)
        source_x, source_y = FiveOrMoreEnv._index_to_cell(source_index)
        destination_x, destination_y = FiveOrMoreEnv._index_to_cell(
            destination_index
        )
        return source_x, source_y, destination_x, destination_y

    def _invalid_action(self, reason):
        return (
            self.get_state(),
            self.invalid_action_reward,
            self.game.is_game_over(),
            {
                "invalid_action": True,
                "reason": reason,
            },
        )

    def _require_reset(self):
        if self.game is None or self.state_encoder is None:
            raise RuntimeError("Call reset() before using the environment.")

    @staticmethod
    def _cell_to_index(x, y):
        if (
            not isinstance(x, Integral)
            or isinstance(x, bool)
            or not isinstance(y, Integral)
            or isinstance(y, bool)
            or not 0 <= x < 9
            or not 0 <= y < 9
        ):
            raise ValueError("Cell coordinates must be integers from 0 through 8.")
        return int(y) * 9 + int(x)

    @staticmethod
    def _index_to_cell(index):
        y, x = divmod(index, 9)
        return x, y
