import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

from config.config_loader import load_config
from experiment_manager import ExperimentManager
import game.rl.train_dqn as train_module
from game.rl.train_dqn import epsilon_after_steps, train_dqn


class FakeGame:
    def __init__(self):
        self.score = 0

    def get_score(self):
        return self.score


class FakeEnvironment:
    def __init__(self, episode_scripts):
        self.episode_scripts = episode_scripts
        self.reset_count = 0
        self.game = FakeGame()
        self.actions_taken = []
        self.script = None
        self.step_index = 0

    def reset(self):
        self.script = self.episode_scripts[self.reset_count]
        self.reset_count += 1
        self.step_index = 0
        self.game.score = 0
        return [[self.reset_count] * 9 for _ in range(9)]

    def get_valid_actions(self):
        return self.script["actions"][self.step_index]

    def step(self, action):
        legal_actions = self.get_valid_actions()
        if action not in legal_actions:
            raise AssertionError("runner executed an action outside legal actions")
        self.actions_taken.append(action)
        transition = self.script["transitions"][self.step_index]
        self.step_index += 1
        self.game.score = transition["score"]
        return (
            [[self.reset_count + self.step_index] * 9 for _ in range(9)],
            transition["reward"],
            transition["done"],
            {},
        )


class FakeNetwork:
    def __init__(self):
        self.training = True

    def state_dict(self):
        return {"weight": torch.tensor([1.0])}

    def eval(self):
        self.training = False

    def train(self, training):
        self.training = training


class FakeOptimizer:
    def state_dict(self):
        return {}


class FakeAgent:
    def __init__(self, update_results=None):
        self.online_network = FakeNetwork()
        self.optimizer = FakeOptimizer()
        self.update_results = list(update_results or [])
        self.actions_selected = []
        self.transitions = []
        self.learn_calls = 0
        self.sync_calls = 0

    def select_action(self, state, legal_actions, epsilon):
        self.actions_selected.append((list(legal_actions), epsilon))
        return legal_actions[-1]

    def store_transition(self, **transition):
        self.transitions.append(transition)

    def learn_step(self):
        self.learn_calls += 1
        if self.update_results:
            return self.update_results.pop(0)
        return {"loss": None, "updated": False}

    def synchronize_target_network(self):
        self.sync_calls += 1


class TrainDQNTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(load_config())
        self.config["training"]["episodes"] = 2
        self.config["training"]["max_steps_per_episode"] = 5
        self.config["dqn"]["target_update_frequency"] = 2
        self.config["exploration"]["epsilon_start"] = 1.0
        self.config["exploration"]["epsilon_min"] = 0.1
        self.config["exploration"]["epsilon_decay"] = 0.5
        self.config["training"]["evaluation_interval"] = 0

    @staticmethod
    def normal_script(reward, score):
        return {
            "actions": [[10], [20]],
            "transitions": [
                {"reward": reward, "done": False, "score": score},
                {"reward": reward, "done": True, "score": score},
            ],
        }

    def test_runner_executes_configured_episodes_and_resets_each_time(self):
        env = FakeEnvironment([self.normal_script(1.0, 7), self.normal_script(2.0, 9)])
        agent = FakeAgent()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(self.config, base_dir=tmpdir)
            summary = train_dqn(
                self.config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(env.reset_count, 2)
        self.assertEqual(summary["episodes"], 2)
        self.assertEqual(summary["environment_steps"], 4)
        self.assertEqual(agent.learn_calls, 4)

    def test_actions_and_transitions_use_current_legal_lists(self):
        env = FakeEnvironment([self.normal_script(0.5, 4)])
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(env.actions_taken, [10, 20])
        self.assertEqual(agent.transitions[0]["action"], 10)
        self.assertEqual(agent.transitions[0]["next_legal_actions"], [20])
        self.assertTrue(agent.transitions[1]["done"])
        self.assertEqual(agent.transitions[1]["next_legal_actions"], [])

    def test_no_legal_actions_stops_and_preserves_actual_done_flag(self):
        env = FakeEnvironment(
            [
                {
                    "actions": [[]],
                    "transitions": [],
                }
            ]
        )
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(summary["episode_stop_reasons"], ["no_legal_actions"])
        self.assertEqual(summary["environment_steps"], 0)
        self.assertEqual(agent.transitions, [])
        self.assertEqual(manager.results["episodes"], 1)

    def test_empty_next_actions_preserve_false_environment_done_flag(self):
        env = FakeEnvironment(
            [
                {
                    "actions": [[12], []],
                    "transitions": [
                        {"reward": 0.25, "done": False, "score": 3},
                    ],
                }
            ]
        )
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(summary["episode_stop_reasons"], ["no_legal_actions"])
        self.assertFalse(agent.transitions[0]["done"])
        self.assertEqual(agent.transitions[0]["next_legal_actions"], [])

    def test_epsilon_starts_and_decays_per_environment_step(self):
        self.assertEqual(epsilon_after_steps(1.0, 0.1, 0.5, 0), 1.0)
        self.assertEqual(epsilon_after_steps(1.0, 0.1, 0.5, 2), 0.25)
        self.assertEqual(epsilon_after_steps(1.0, 0.1, 0.5, 10), 0.1)

        env = FakeEnvironment([self.normal_script(0.0, 0)])
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            train_dqn(config, env=env, agent=agent, experiment_manager=manager)

        self.assertEqual([item[1] for item in agent.actions_selected], [1.0, 0.5])

    def test_only_successful_updates_count_and_trigger_target_sync(self):
        env = FakeEnvironment([self.normal_script(0.0, 1)])
        agent = FakeAgent(
            [
                {"loss": None, "updated": False},
                {"loss": 0.5, "updated": True},
            ]
        )
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(summary["optimizer_updates"], 1)
        self.assertEqual(agent.sync_calls, 0)
        self.assertEqual(manager.results["average_loss"], 0.5)

    def test_target_sync_interval_counts_successful_updates(self):
        env = FakeEnvironment([self.normal_script(0.0, 1), self.normal_script(0.0, 1)])
        agent = FakeAgent([{"loss": 0.25, "updated": True}] * 4)
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(self.config, base_dir=tmpdir)
            summary = train_dqn(
                self.config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(summary["optimizer_updates"], 4)
        self.assertEqual(agent.sync_calls, 2)

    def test_metrics_distinguish_game_score_from_reward_and_allow_missing_loss(self):
        env = FakeEnvironment([self.normal_script(0.25, 13)])
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["episodes"] = 1
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )
            with open(manager.metrics_path, encoding="utf-8", newline="") as metrics_file:
                metrics = metrics_file.readlines()
            checkpoint = torch.load(manager.model_path, map_location="cpu", weights_only=False)
            results = json.loads(Path(manager.results_path).read_text(encoding="utf-8"))

        self.assertEqual(summary["final_score"], 13.0)
        self.assertEqual(summary["average_reward"], 0.5)
        self.assertEqual(manager.results["final_score"], 13.0)
        self.assertEqual(manager.results["average_loss"], None)
        self.assertIn(",13.0,0.5,2,True,1.0,,13.0,0.5", metrics[1])
        self.assertEqual(checkpoint["run_id"], manager.run_id)
        self.assertEqual(checkpoint["environment_steps"], 2)
        self.assertEqual(checkpoint["online_state_dict"]["weight"].item(), 1.0)
        self.assertEqual(results["status"], "completed")

    def test_invalid_configuration_is_rejected_before_experiment_creation(self):
        config = copy.deepcopy(self.config)
        config["dqn"]["gamma"] = 2.0
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                train_dqn(config, experiment_dir=tmpdir)
    def test_train_frequency_limits_learning_updates(self):
        env = FakeEnvironment([self.normal_script(1.0, 7), self.normal_script(2.0, 9)])
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"]["train_frequency"] = 2
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )

        self.assertEqual(summary["environment_steps"], 4)
        # With train_frequency = 2 across 4 steps, learn_step is called 2 times
        self.assertEqual(agent.learn_calls, 2)

    def test_parallel_step_limit_resets_worker_without_marking_terminal(self):
        class FakeParallelEnvironment:
            instance = None

            def __init__(self, num_workers, **kwargs):
                self.num_workers = num_workers
                self.current_states = [[[0] * 9 for _ in range(9)] for _ in range(2)]
                self.current_legal_actions = [[10], [20]]
                self.reset_calls = []
                FakeParallelEnvironment.instance = self

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return None

            def reset(self):
                return self.current_states, self.current_legal_actions

            def step(self, actions):
                return [
                    {
                        "worker_id": worker,
                        "state": self.current_states[worker],
                        "action": actions[worker],
                        "reward": 0.25,
                        "next_state": [[worker + 1] * 9 for _ in range(9)],
                        "done": False,
                        "next_legal_actions": [30],
                        "score": 5.0,
                    }
                    for worker in range(2)
                ]

            def reset_workers(self, worker_ids):
                self.reset_calls.append(list(worker_ids))
                for worker_id in worker_ids:
                    self.current_states[worker_id] = [[9] * 9 for _ in range(9)]
                    self.current_legal_actions[worker_id] = [40]

        config = copy.deepcopy(self.config)
        config["training"].update(episodes=1, max_steps_per_episode=1, num_workers=2)
        agent = FakeAgent()
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            with patch.object(train_module, "ParallelEnvManager", FakeParallelEnvironment):
                summary = train_dqn(
                    config,
                    agent=agent,
                    experiment_manager=manager,
                )
            metrics_text = manager.metrics_path.read_text(encoding="utf-8")

        parallel_env = FakeParallelEnvironment.instance
        self.assertEqual(parallel_env.reset_calls, [[0]])
        self.assertFalse(agent.transitions[0]["done"])
        self.assertEqual(agent.transitions[0]["next_legal_actions"], [30])
        self.assertEqual(summary["episode_stop_reasons"], ["max_steps"])
        self.assertIn(",False,1.0,,5.0,0.25,True,max_steps", metrics_text)

    def test_best_checkpoint_and_comparison_evaluation_are_saved(self):
        env = FakeEnvironment([self.normal_script(0.0, 7)])
        agent = FakeAgent()
        config = copy.deepcopy(self.config)
        config["training"].update(
            episodes=1,
            max_steps_per_episode=2,
            evaluation_interval=1,
            evaluation_episodes=1,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ExperimentManager(config, base_dir=tmpdir)
            summary = train_dqn(
                config,
                env=env,
                agent=agent,
                experiment_manager=manager,
            )
            evaluation_rows = manager.evaluations_path.read_text(encoding="utf-8").splitlines()

            self.assertTrue(manager.best_model_path.is_file())
            self.assertEqual(len(evaluation_rows), 1)

        self.assertIn("best_evaluation", summary)
        self.assertIn("random_baseline", summary)
        self.assertEqual(agent.online_network.training, True)

    def test_short_parallel_training_records_evaluations_and_best_model(self):
        config = copy.deepcopy(self.config)
        config["training"].update(
            episodes=2,
            max_steps_per_episode=2,
            num_workers=2,
            torch_threads=1,
            evaluation_interval=1,
            evaluation_episodes=1,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = train_dqn(config, experiment_dir=tmpdir)
            manager_dir = Path(tmpdir) / "run_001"

            evaluations = manager_dir / "evaluations.jsonl"
            records = [json.loads(line) for line in evaluations.read_text(encoding="utf-8").splitlines()]
            results = json.loads((manager_dir / "results.json").read_text(encoding="utf-8"))

            self.assertTrue((manager_dir / "best_model.pth").is_file())
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["episode"], 2)
            self.assertEqual(results["config_hash"], records[0]["config_hash"])
            self.assertEqual(summary["episodes"], 2)
            self.assertEqual(summary["episode_stop_reasons"], ["max_steps", "max_steps"])

    def test_cli_parser_and_overrides(self):
        parser = train_module.build_parser()
        args = parser.parse_args([
            "--episodes", "50",
            "--lr", "0.0005",
            "--gamma", "0.95",
            "--batch-size", "128",
            "--train-freq", "4",
            "--workers", "4",
            "--target-update", "2000",
            "--step-penalty", "0.005",
            "--score-per-point", "2.0",
            "--difficulty", "Hard",
            "--surveillance-interval", "25",
            "--eval-interval", "10",
            "--eval-episodes", "5",
            "--epsilon-decay", "0.9999",
        ])
        config = copy.deepcopy(self.config)
        modified = train_module.apply_cli_overrides(config, args)

        self.assertEqual(modified["training"]["episodes"], 50)
        self.assertEqual(modified["dqn"]["learning_rate"], 0.0005)
        self.assertEqual(modified["dqn"]["gamma"], 0.95)
        self.assertEqual(modified["dqn"]["batch_size"], 128)
        self.assertEqual(modified["training"]["train_frequency"], 4)
        self.assertEqual(modified["training"]["num_workers"], 4)
        self.assertEqual(modified["dqn"]["target_update_frequency"], 2000)
        self.assertEqual(modified["reward"]["step_penalty"], 0.005)
        self.assertEqual(modified["reward"]["score_per_point"], 2.0)
        self.assertEqual(modified["environment"]["difficulty"], "Hard")
        self.assertEqual(modified["training"]["surveillance_interval"], 25)
        self.assertEqual(modified["training"]["evaluation_interval"], 10)
        self.assertEqual(modified["training"]["evaluation_episodes"], 5)
        self.assertEqual(modified["exploration"]["epsilon_decay"], 0.9999)


if __name__ == "__main__":
    unittest.main()
