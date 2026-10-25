import subprocess
import sys
import unittest
from unittest.mock import patch

from . import random_agent
from .rl_environment import FiveOrMoreEnv


class RandomAgentTests(unittest.TestCase):
    def test_one_real_random_game_reaches_termination(self):
        env = FiveOrMoreEnv(difficulty="Easy")
        observed_states = []
        original_step = env.step

        def step_and_check_state(action):
            result = original_step(action)
            observed_states.append(result[0])
            return result

        with patch.object(env, "step", side_effect=step_and_check_state):
            result = random_agent.play_random_game(env=env)

        self.assertTrue(result["game_over"] or result["no_valid_actions"])
        self.assertGreater(result["steps"], 0)
        self.assertEqual(len(observed_states), result["steps"])
        for state in observed_states:
            self.assertEqual(len(state), 9)
            self.assertTrue(all(len(row) == 9 for row in state))
            self.assertTrue(
                all(0 <= cell <= 7 for row in state for cell in row)
            )

    def test_multiple_random_games_run_and_report_aggregate_statistics(self):
        with patch.object(
            random_agent,
            "play_random_game",
            side_effect=[
                {
                    "score": 10,
                    "steps": 5,
                    "total_reward": 0.5,
                    "game_over": True,
                    "no_valid_actions": False,
                },
                {
                    "score": 20,
                    "steps": 7,
                    "total_reward": 1.2,
                    "game_over": False,
                    "no_valid_actions": True,
                },
            ],
        ) as play_game:
            with patch("builtins.print"):
                summary = random_agent.run_random_games(
                    num_games=2,
                    verbose=False,
                )

        self.assertEqual(play_game.call_count, 2)
        self.assertEqual(summary["games"], 2)
        self.assertEqual(summary["average_score"], 15)
        self.assertEqual(summary["maximum_score"], 20)
        self.assertEqual(summary["minimum_score"], 10)
        self.assertEqual(summary["average_steps"], 6)
        self.assertAlmostEqual(summary["average_total_reward"], 0.85)
        self.assertEqual(summary["game_over_count"], 1)
        self.assertEqual(summary["no_valid_actions_count"], 1)

    def test_chosen_action_is_selected_from_current_valid_actions(self):
        class RecordingEnvironment:
            def __init__(self):
                self.game = type("GameScore", (), {"get_score": lambda _: 0})()
                self.valid_actions = [3, 7, 11]
                self.selected = []
                self.calls = 0

            def reset(self):
                return [[0] * 9 for _ in range(9)]

            def get_valid_actions(self):
                return self.valid_actions

            def step(self, action):
                self.selected.append(action)
                self.calls += 1
                return (
                    [[0] * 9 for _ in range(9)],
                    0.0,
                    self.calls == 1,
                    {},
                )

        class RecordingRandom:
            def choice(self, actions):
                self.received_actions = list(actions)
                return actions[-1]

        env = RecordingEnvironment()
        rng = RecordingRandom()

        result = random_agent.play_random_game(env=env, rng=rng)

        self.assertEqual(rng.received_actions, env.valid_actions)
        self.assertTrue(all(action in env.valid_actions for action in env.selected))
        self.assertTrue(result["game_over"])

    def test_no_valid_actions_stops_without_calling_step(self):
        class EmptyActionEnvironment:
            game = type("GameScore", (), {"get_score": lambda _: 0})()

            def reset(self):
                return [[0] * 9 for _ in range(9)]

            def get_valid_actions(self):
                return []

            def step(self, action):
                raise AssertionError("step must not run without a valid action")

        result = random_agent.play_random_game(env=EmptyActionEnvironment())

        self.assertEqual(result["steps"], 0)
        self.assertFalse(result["game_over"])
        self.assertTrue(result["no_valid_actions"])

    def test_random_simulation_import_does_not_load_pygame(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; import game.random_agent; "
                    "assert 'pygame' not in sys.modules"
                ),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_run_random_games_rejects_nonpositive_counts(self):
        for invalid_count in (0, -1, True, 2.5):
            with self.subTest(num_games=invalid_count):
                with self.assertRaises(ValueError):
                    random_agent.run_random_games(
                        num_games=invalid_count,
                        verbose=False,
                    )


if __name__ == "__main__":
    unittest.main()
