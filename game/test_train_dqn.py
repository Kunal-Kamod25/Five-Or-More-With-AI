import copy
import json
import tempfile
import unittest
from pathlib import Path

import torch

from config.config_loader import load_config
from experiment_manager import ExperimentManager
from .train_dqn import epsilon_after_steps, train_dqn


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
    def state_dict(self):
        return {"weight": torch.tensor([1.0])}


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
            self.assertEqual(list(Path(tmpdir).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
