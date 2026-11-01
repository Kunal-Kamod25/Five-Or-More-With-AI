import copy
import tempfile
import unittest
from pathlib import Path

import torch
from config.config_loader import load_config
from game.rl.dqn_agent import DQNAgent
from game.rl.evaluate_agent import (
    evaluate_agent,
    evaluate_policy,
    find_latest_checkpoint,
)


class EvaluateAgentTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(load_config())
        self.config["training"]["max_steps_per_episode"] = 4
        self.config["environment"]["difficulty"] = "Easy"

    def test_random_policy_evaluation_is_reproducible(self):
        first = evaluate_policy(None, 3, self.config, seed=821)
        second = evaluate_policy(None, 3, self.config, seed=821)

        self.assertEqual(first, second)
        self.assertEqual(first["policy"], "random_legal")
        self.assertEqual(first["episodes"], 3)
        self.assertEqual(first["truncated_count"], 3)

    def test_invalid_evaluation_episode_count_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_policy(None, 0, self.config)

    def test_checkpoint_config_is_used_for_evaluation(self):
        agent = DQNAgent(self.config, device="cpu")
        checkpoint = {
            "config": self.config,
            "online_state_dict": agent.online_network.state_dict(),
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "model.pth"
            torch.save(checkpoint, path)

            summary = evaluate_agent(
                path,
                episodes=1,
                config=None,
                seed=17,
                verbose=False,
                compare_random=False,
            )

        self.assertEqual(summary["difficulty"], "Easy")
        self.assertEqual(summary["truncated_count"], 1)

    def test_latest_checkpoint_prefers_saved_best_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run = Path(tmpdir) / "run_001"
            run.mkdir()
            latest = run / "model.pth"
            best = run / "best_model.pth"
            latest.touch()
            best.touch()

            self.assertEqual(find_latest_checkpoint(tmpdir), best)


if __name__ == "__main__":
    unittest.main()
