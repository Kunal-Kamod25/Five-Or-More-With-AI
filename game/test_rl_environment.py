import random
import subprocess
import sys
import unittest
from unittest.mock import patch

from .piece import Piece
from .rl_environment import FiveOrMoreEnv


class FiveOrMoreEnvTests(unittest.TestCase):
    def setUp(self):
        self.env = FiveOrMoreEnv()
        self.env.reset()

    def clear_pieces(self):
        for piece in self.env.game.get_pieces():
            x, y = piece.get_position()
            self.env.game.board_pieces.remove_piece(x, y)

    def add_piece(self, x, y, color=1):
        piece = Piece(x, y, color)
        self.env.game.board_pieces.add_piece(piece)
        return piece

    def replace_pieces(self, positions):
        self.clear_pieces()
        for x, y, color in positions:
            self.add_piece(x, y, color)

    def reference_valid_actions(self):
        """Original per-source/destination A* enumeration used as an oracle."""
        board = self.env.game.get_board()
        actions = set()
        for source_y in range(board.SIZE):
            for source_x in range(board.SIZE):
                if board.is_empty(source_y, source_x):
                    continue
                source_index = source_y * board.SIZE + source_x
                for destination_y in range(board.SIZE):
                    for destination_x in range(board.SIZE):
                        if not board.is_empty(destination_y, destination_x):
                            continue
                        if self.env.game.find_path(
                            source_x,
                            source_y,
                            destination_x,
                            destination_y,
                        ) is not None:
                            destination_index = (
                                destination_y * board.SIZE + destination_x
                            )
                            actions.add(source_index * 81 + destination_index)
        return actions

    def test_reset_returns_valid_nine_by_nine_encoded_state(self):
        state = self.env.reset()

        self.assertEqual(len(state), 9)
        self.assertTrue(all(len(row) == 9 for row in state))
        self.assertTrue(all(0 <= value <= 7 for row in state for value in row))
        self.assertEqual(sum(value != 0 for row in state for value in row), 5)

    def test_state_is_a_snapshot(self):
        state = self.env.get_state()
        state[0][0] = 7

        self.assertNotEqual(self.env.game.get_board().get_cell(0, 0), 7)

    def test_action_encoding_and_decoding_round_trip(self):
        action = self.env.encode_action(2, 3, 7, 8)

        self.assertEqual(action, (3 * 9 + 2) * 81 + (8 * 9 + 7))
        self.assertEqual(
            self.env.decode_action(action),
            (2, 3, 7, 8),
        )

    def test_valid_actions_are_legal_source_destination_pairs(self):
        self.clear_pieces()
        self.add_piece(4, 4)

        actions = self.env.get_valid_actions()
        decoded_actions = [self.env.decode_action(action) for action in actions]

        self.assertEqual(len(actions), 80)
        self.assertTrue(
            all(
                (source_x, source_y) == (4, 4)
                and self.env.game.get_board().is_empty(destination_y, destination_x)
                and self.env.game.find_path(
                    source_x,
                    source_y,
                    destination_x,
                    destination_y,
                )
                is not None
                for source_x, source_y, destination_x, destination_y
                in decoded_actions
            )
        )

    def test_flood_fill_matches_reference_on_varied_board_configurations(self):
        scenarios = {
            "empty": [],
            "single_center": [(4, 4, 1)],
            "single_corner": [(0, 0, 1)],
            "single_edge": [(0, 4, 1)],
            "multiple_pieces": [
                (0, 0, 1),
                (4, 4, 2),
                (8, 8, 3),
                (0, 8, 4),
            ],
            "blocked_center": [
                (4, 4, 1),
                (3, 4, 2),
                (5, 4, 3),
                (4, 3, 4),
                (4, 5, 5),
                (0, 0, 6),
            ],
            "dense": [
                (x, y, (x + y) % 7 + 1)
                for y in range(9)
                for x in range(9)
                if (x, y) not in ((0, 0), (8, 8), (4, 4), (2, 6))
            ],
            "full": [
                (x, y, (x + y) % 7 + 1)
                for y in range(9)
                for x in range(9)
            ],
        }
        rng = random.Random(8421)
        cells = [(x, y) for y in range(9) for x in range(9)]
        for board_number in range(12):
            occupied_count = rng.randint(1, 72)
            occupied_cells = rng.sample(cells, occupied_count)
            scenarios[f"random_{board_number}"] = [
                (x, y, rng.randint(1, 7)) for x, y in occupied_cells
            ]

        for scenario_name, positions in scenarios.items():
            with self.subTest(scenario=scenario_name):
                self.replace_pieces(positions)
                self.assertEqual(
                    set(self.env.get_valid_actions()),
                    self.reference_valid_actions(),
                )

    def test_flood_fill_handles_corner_edge_and_blocked_piece(self):
        self.replace_pieces([(0, 0, 1)])
        corner_actions = self.env.get_valid_actions()
        self.assertEqual(len(corner_actions), 80)

        self.replace_pieces([(0, 4, 1)])
        edge_actions = self.env.get_valid_actions()
        self.assertEqual(len(edge_actions), 80)

        self.replace_pieces(
            [
                (4, 4, 1),
                (3, 4, 2),
                (5, 4, 3),
                (4, 3, 4),
                (4, 5, 5),
                (0, 0, 6),
            ]
        )
        blocked_actions = {
            self.env.decode_action(action)
            for action in self.env.get_valid_actions()
        }
        self.assertFalse(
            any(
                source_x == 4 and source_y == 4
                for source_x, source_y, _, _ in blocked_actions
            )
        )

    def test_valid_step_does_not_enumerate_all_valid_actions(self):
        self.replace_pieces([(4, 4, 3)])
        action = self.env.encode_action(4, 4, 4, 5)

        with patch.object(
            self.env,
            "get_valid_actions",
            side_effect=AssertionError("step must not enumerate all moves"),
        ) as get_valid_actions:
            _, _, done, info = self.env.step(action)

        get_valid_actions.assert_not_called()
        self.assertFalse(info["invalid_action"])
        self.assertIsInstance(done, bool)

    def test_unreachable_move_is_rejected_without_changing_the_board(self):
        self.replace_pieces(
            [
                (4, 4, 1),
                (3, 4, 2),
                (5, 4, 3),
                (4, 3, 4),
                (4, 5, 5),
                (0, 0, 6),
            ]
        )
        state_before = self.env.get_state()
        action = self.env.encode_action(4, 4, 8, 8)

        next_state, reward, done, info = self.env.step(action)

        self.assertEqual(next_state, state_before)
        self.assertEqual(reward, self.env.INVALID_ACTION_REWARD)
        self.assertTrue(info["invalid_action"])
        self.assertIsInstance(done, bool)

    def test_legal_action_updates_board_and_returns_reward_and_done(self):
        self.clear_pieces()
        self.add_piece(1, 1, color=3)
        action = self.env.encode_action(1, 1, 2, 1)

        next_state, reward, done, info = self.env.step(action)

        self.assertEqual(next_state[1][1], 0)
        self.assertEqual(next_state[1][2], 3)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertFalse(info["invalid_action"])
        self.assertEqual(info["score_delta"], 0)

    def test_invalid_action_does_not_crash_or_change_state(self):
        state_before = self.env.get_state()

        next_state, reward, done, info = self.env.step(-1)

        self.assertEqual(next_state, state_before)
        self.assertEqual(reward, self.env.INVALID_ACTION_REWARD)
        self.assertIsInstance(done, bool)
        self.assertTrue(info["invalid_action"])
        self.assertIn("reason", info)

    def test_invalid_action_types_are_handled(self):
        state_before = self.env.get_state()

        next_state, reward, done, info = self.env.step((0, 1))

        self.assertEqual(next_state, state_before)
        self.assertEqual(reward, self.env.INVALID_ACTION_REWARD)
        self.assertTrue(info["invalid_action"])
        self.assertIsInstance(done, bool)

    def test_clearing_a_line_produces_positive_reward(self):
        self.clear_pieces()
        for x in range(4):
            self.add_piece(x, 0, color=2)
        self.add_piece(4, 1, color=2)
        self.add_piece(8, 8, color=7)
        action = self.env.encode_action(4, 1, 4, 0)

        _, reward, done, info = self.env.step(action)

        self.assertGreater(reward, 0)
        self.assertEqual(info["score_delta"], 10)
        self.assertTrue(all(value == 0 for value in self.env.get_state()[0][:5]))
        self.assertIsInstance(done, bool)

    def test_game_over_is_reported_after_board_fills(self):
        self.clear_pieces()
        for y in range(9):
            for x in range(9):
                if (x, y) not in ((0, 0), (1, 0)):
                    self.add_piece(x, y, color=(x + 2 * y) % 7 + 1)
        self.add_piece(0, 0, color=1)
        self.env.game.game_over = False
        action = self.env.encode_action(0, 0, 1, 0)

        with patch.object(
            self.env.game.match_resolver,
            "resolve_matches",
            return_value=(0, []),
        ):
            _, reward, done, info = self.env.step(action)

        self.assertTrue(done)
        self.assertLess(reward, 0)
        self.assertFalse(info["invalid_action"])
        self.assertEqual(len(self.env.get_valid_actions()), 0)

    def test_environment_import_does_not_load_pygame(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; import game.rl_environment; "
                    "assert 'pygame' not in sys.modules"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_using_environment_before_reset_is_reported(self):
        env = FiveOrMoreEnv()

        with self.assertRaises(RuntimeError):
            env.get_state()


if __name__ == "__main__":
    unittest.main()
