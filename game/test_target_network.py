import unittest

import torch

from .q_network import LegalActionQNetwork
from .target_network import TargetNetwork


class TargetNetworkTests(unittest.TestCase):
    def setUp(self):
        self.online = LegalActionQNetwork()
        self.target = TargetNetwork(self.online)

    def test_target_starts_with_same_parameter_values(self):
        for online_param, target_param in zip(
            self.online.parameters(),
            self.target.model.parameters(),
        ):
            self.assertTrue(torch.equal(online_param, target_param))

    def test_target_and_online_are_independent_objects(self):
        self.online.conv1.weight.data.fill_(0.0)
        self.assertFalse(torch.equal(self.online.conv1.weight, self.target.model.conv1.weight))

    def test_target_parameters_require_no_grad(self):
        for parameter in self.target.model.parameters():
            self.assertFalse(parameter.requires_grad)

    def test_online_updates_do_not_change_target_until_hard_update(self):
        online_value = self.online.conv1.weight.clone()
        self.online.conv1.weight.data.add_(1.0)
        self.assertFalse(torch.equal(self.online.conv1.weight, self.target.model.conv1.weight))

        self.target.hard_update()
        self.assertTrue(torch.equal(self.online.conv1.weight, self.target.model.conv1.weight))

    def test_target_remains_frozen_after_hard_update(self):
        self.target.hard_update()
        for parameter in self.target.model.parameters():
            self.assertFalse(parameter.requires_grad)

    def test_component_works_on_cpu(self):
        state = [[0 for _ in range(9)] for _ in range(9)]
        state[0][0] = 1
        state[4][4] = 2
        actions = [0, 5, 7]
        scores = self.target.model.score_actions(state, actions)
        self.assertEqual(scores.shape, (3, 1))

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is not available")
    def test_cuda_target_uses_same_device(self):
        online = LegalActionQNetwork().to("cuda")
        target = TargetNetwork(online)
        self.assertEqual(str(target.model.conv1.weight.device), "cuda:0")
        self.assertEqual(str(online.conv1.weight.device), "cuda:0")

    def test_target_preserves_legal_action_scoring_interface(self):
        state = [[0 for _ in range(9)] for _ in range(9)]
        state[1][1] = 3
        state[3][4] = 7
        actions = [0, 10, 20]
        scores = self.target.model.score_actions(state, actions)
        self.assertEqual(scores.shape, (len(actions), 1))
        self.assertEqual(self.target.model.score_action(state, actions[0]).shape, (1,))


if __name__ == "__main__":
    unittest.main()
