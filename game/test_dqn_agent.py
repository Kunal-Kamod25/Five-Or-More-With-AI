import copy
import random
import unittest
from unittest.mock import patch

import torch

from config.config_loader import load_config
from .dqn_agent import DQNAgent
from .q_network import LegalActionQNetwork
from .replay_buffer import ExperienceReplayBuffer
from .target_network import TargetNetwork


class FixedRandom:
    def __init__(self, value=0.0, choice_index=0):
        self.value = value
        self.choice_index = choice_index

    def random(self):
        return self.value

    def choice(self, choices):
        return choices[self.choice_index]


class DQNAgentTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(load_config())
        self.config["dqn"]["batch_size"] = 2
        self.config["dqn"]["replay_buffer_size"] = 8

    @staticmethod
    def make_transition(action=10, reward=1.0, done=False, next_actions=None):
        state = [[0 for _ in range(9)] for _ in range(9)]
        state[1][2] = 3
        next_state = [[0 for _ in range(9)] for _ in range(9)]
        next_state[4][5] = 2
        return {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "next_legal_actions": [5, 9] if next_actions is None else next_actions,
        }

    def test_initialization_connects_existing_components_on_cpu(self):
        agent = DQNAgent(self.config)

        self.assertIsInstance(agent.online_network, LegalActionQNetwork)
        self.assertIsInstance(agent.target_network, TargetNetwork)
        self.assertIsInstance(agent.replay_buffer, ExperienceReplayBuffer)
        self.assertEqual(agent.device.type, "cpu")
        self.assertTrue(
            all(parameter.requires_grad for parameter in agent.online_network.parameters())
        )
        self.assertTrue(
            all(not parameter.requires_grad for parameter in agent.target_network.model.parameters())
        )
        optimizer_parameter_ids = {
            id(parameter)
            for group in agent.optimizer.param_groups
            for parameter in group["params"]
        }
        self.assertEqual(
            optimizer_parameter_ids,
            {id(parameter) for parameter in agent.online_network.parameters()},
        )
        self.assertTrue(
            optimizer_parameter_ids.isdisjoint(
                {id(parameter) for parameter in agent.target_network.model.parameters()}
            )
        )

    def test_greedy_selection_returns_highest_scoring_legal_action(self):
        agent = DQNAgent(self.config, rng=FixedRandom(value=0.9))
        legal_actions = [17, 28, 39]
        scores = torch.tensor([[1.0], [3.0], [2.0]])

        with patch.object(agent.online_network, "score_actions", return_value=scores):
            action = agent.select_action([[0] * 9 for _ in range(9)], legal_actions, epsilon=0.0)

        self.assertEqual(action, 28)
        self.assertIn(action, legal_actions)

    def test_exploratory_selection_chooses_only_a_supplied_legal_action(self):
        agent = DQNAgent(self.config, rng=FixedRandom(value=0.1, choice_index=1))
        legal_actions = [17, 28, 39]

        action = agent.select_action([[0] * 9 for _ in range(9)], legal_actions, epsilon=1.0)

        self.assertEqual(action, 28)
        self.assertIn(action, legal_actions)

    def test_empty_legal_action_list_returns_none(self):
        agent = DQNAgent(self.config)
        self.assertIsNone(agent.select_action([], []))

    def test_store_transition_uses_replay_buffer_and_preserves_values(self):
        agent = DQNAgent(self.config)
        transition = self.make_transition()
        agent.store_transition(**transition)

        stored = agent.replay_buffer.sample(1)[0]
        for field, value in transition.items():
            self.assertEqual(stored[field], value)

    def test_learning_skips_when_buffer_is_smaller_than_batch_size(self):
        agent = DQNAgent(self.config)
        agent.store_transition(**self.make_transition())

        result = agent.learn_step()

        self.assertEqual(result, {"loss": None, "updated": False})

    def test_sampled_batch_produces_finite_loss_and_updates_online_parameters(self):
        agent = DQNAgent(self.config)
        agent.store_transition(**self.make_transition(action=100, reward=3.0))
        agent.store_transition(**self.make_transition(action=200, reward=2.0))
        before = [parameter.detach().clone() for parameter in agent.online_network.parameters()]

        result = agent.learn_step()

        self.assertTrue(result["updated"])
        self.assertTrue(torch.isfinite(torch.tensor(result["loss"])))
        self.assertTrue(
            any(
                not torch.equal(previous, current)
                for previous, current in zip(before, agent.online_network.parameters())
            )
        )
        self.assertTrue(
            all(parameter.grad is None for parameter in agent.target_network.model.parameters())
        )

    def test_terminal_transition_uses_reward_only_target(self):
        agent = DQNAgent(self.config)
        transition = self.make_transition(reward=2.5, done=True, next_actions=[1, 2])
        with patch.object(
            agent.target_network.model,
            "score_actions",
            side_effect=AssertionError("terminal target must not score next actions"),
        ):
            target = agent._target_value(transition)

        self.assertEqual(target.item(), 2.5)

    def test_empty_next_action_list_uses_reward_only_target(self):
        agent = DQNAgent(self.config)
        transition = self.make_transition(reward=-0.75, done=False, next_actions=[])
        with patch.object(
            agent.target_network.model,
            "score_actions",
            side_effect=AssertionError("empty candidate list must not be scored"),
        ):
            target = agent._target_value(transition)

        self.assertEqual(target.item(), -0.75)

    def test_nonterminal_target_uses_maximum_target_q_over_legal_actions(self):
        agent = DQNAgent(self.config)
        agent.gamma = 0.5
        transition = self.make_transition(reward=2.0, done=False, next_actions=[5, 9])
        target_scores = torch.tensor([[1.0], [4.0]])

        with patch.object(
            agent.target_network.model,
            "score_actions",
            return_value=target_scores,
        ) as score_actions:
            target = agent._target_value(transition)

        self.assertEqual(target.item(), 4.0)
        score_actions.assert_called_once_with(transition["next_state"], [5, 9])

    def test_target_synchronization_copies_online_parameters(self):
        agent = DQNAgent(self.config)
        with torch.no_grad():
            agent.online_network.conv1.weight.add_(1.0)

        agent.synchronize_target_network()

        self.assertTrue(
            torch.equal(
                agent.online_network.conv1.weight,
                agent.target_network.model.conv1.weight,
            )
        )
        self.assertTrue(
            all(not parameter.requires_grad for parameter in agent.target_network.model.parameters())
        )

    def test_agent_accepts_supplied_network_and_replay_buffer(self):
        online = LegalActionQNetwork(self.config)
        memory = ExperienceReplayBuffer(capacity=4, seed=3)
        agent = DQNAgent(
            self.config,
            online_network=online,
            replay_buffer=memory,
            rng=random.Random(3),
        )

        self.assertIs(agent.online_network, online)
        self.assertIs(agent.replay_buffer, memory)


if __name__ == "__main__":
    unittest.main()
