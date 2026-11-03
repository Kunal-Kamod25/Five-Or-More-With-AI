"""Unit tests for automated hyperparameter tuning and leaderboard generation."""

import json
import tempfile
import unittest
from pathlib import Path

from config.config_loader import load_config
from game.rl.tune_hyperparameters import (
    _get_nested,
    _set_nested,
    build_tuning_parser,
    generate_configurations,
    run_tuning_sweep,
)


class HyperparameterTuningTests(unittest.TestCase):
    def setUp(self):
        self.base_config = load_config()

    def test_nested_helpers(self):
        data = {}
        _set_nested(data, "a.b.c", 42)
        self.assertEqual(data["a"]["b"]["c"], 42)
        self.assertEqual(_get_nested(data, "a.b.c"), 42)
        self.assertIsNone(_get_nested(data, "a.nonexistent"))

    def test_generate_configurations_grid(self):
        space = {
            "dqn.learning_rate": [0.001, 0.002],
            "dqn.gamma": [0.95, 0.99],
        }
        configs = generate_configurations(
            self.base_config,
            space,
            strategy="grid",
            max_trials=4,
        )
        self.assertEqual(len(configs), 4)
        lrs = {c["dqn"]["learning_rate"] for c in configs}
        gammas = {c["dqn"]["gamma"] for c in configs}
        self.assertEqual(lrs, {0.001, 0.002})
        self.assertEqual(gammas, {0.95, 0.99})

    def test_generate_configurations_random(self):
        space = {
            "dqn.learning_rate": [0.0001, 0.0002, 0.0003, 0.0004],
            "dqn.gamma": [0.9, 0.95, 0.99],
        }
        configs = generate_configurations(
            self.base_config,
            space,
            strategy="random",
            max_trials=3,
            seed=123,
        )
        self.assertEqual(len(configs), 3)

    def test_cli_parser(self):
        parser = build_tuning_parser()
        args = parser.parse_args([
            "--episodes-per-trial", "100",
            "--max-trials", "3",
            "--strategy", "grid",
            "--lr", "0.0001", "0.0005",
            "--train-freq", "2", "4",
            "--workers", "2",
        ])
        self.assertEqual(args.episodes_per_trial, 100)
        self.assertEqual(args.max_trials, 3)
        self.assertEqual(args.strategy, "grid")
        self.assertEqual(args.lr, [0.0001, 0.0005])
        self.assertEqual(args.train_freq, [2, 4])
        self.assertEqual(args.workers, 2)

    def test_run_tuning_sweep_creates_leaderboard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_space = {
                "dqn.learning_rate": [0.0001, 0.0005],
            }
            config = load_config()
            config["training"]["max_steps_per_episode"] = 2
            config["training"]["num_workers"] = 1
            config["training"]["evaluation_episodes"] = 1

            results = run_tuning_sweep(
                base_config=config,
                search_space=test_space,
                episodes_per_trial=1,
                max_trials=2,
                strategy="grid",
                output_dir=tmpdir,
                verbose=False,
            )

            self.assertEqual(results["status"], "completed")
            self.assertEqual(results["trials_evaluated"], 2)
            self.assertIsNotNone(results["winner"])

            leaderboard_csv = Path(results["leaderboard_csv"])
            leaderboard_json = Path(results["leaderboard_json"])
            self.assertTrue(leaderboard_csv.is_file())
            self.assertTrue(leaderboard_json.is_file())

            parsed_json = json.loads(leaderboard_json.read_text(encoding="utf-8"))
            self.assertEqual(len(parsed_json["leaderboard"]), 2)
            self.assertEqual(parsed_json["leaderboard"][0]["rank"], 1)
            self.assertEqual(parsed_json["leaderboard"][1]["rank"], 2)

    def test_multi_node_partitioning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_space = {
                "dqn.learning_rate": [0.0001, 0.0002, 0.0003, 0.0004],
            }
            config = load_config()
            config["training"]["max_steps_per_episode"] = 2
            config["training"]["num_workers"] = 1
            config["training"]["evaluation_episodes"] = 1

            # Node 0 of 2 should evaluate trials 1 and 3
            results_node0 = run_tuning_sweep(
                base_config=config,
                search_space=test_space,
                episodes_per_trial=1,
                max_trials=4,
                strategy="grid",
                output_dir=Path(tmpdir) / "node0",
                num_nodes=2,
                node_rank=0,
                verbose=False,
            )
            self.assertEqual(results_node0["trials_evaluated"], 2)
            evaluated_trials_0 = [r["trial"] for r in results_node0["ranked_results"]]
            self.assertEqual(sorted(evaluated_trials_0), [1, 3])

            # Node 1 of 2 should evaluate trials 2 and 4
            results_node1 = run_tuning_sweep(
                base_config=config,
                search_space=test_space,
                episodes_per_trial=1,
                max_trials=4,
                strategy="grid",
                output_dir=Path(tmpdir) / "node1",
                num_nodes=2,
                node_rank=1,
                verbose=False,
            )
            self.assertEqual(results_node1["trials_evaluated"], 2)
            evaluated_trials_1 = [r["trial"] for r in results_node1["ranked_results"]]
            self.assertEqual(sorted(evaluated_trials_1), [2, 4])

    def test_multi_node_validation_errors(self):
        config = load_config()
        with self.assertRaises(ValueError):
            run_tuning_sweep(base_config=config, num_nodes=0, node_rank=0)
        with self.assertRaises(ValueError):
            run_tuning_sweep(base_config=config, num_nodes=2, node_rank=2)


if __name__ == "__main__":
    unittest.main()
