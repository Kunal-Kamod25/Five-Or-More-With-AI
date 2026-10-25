import unittest

import torch

from .board import Board
from .q_network import LegalActionQNetwork
from .rl_environment import FiveOrMoreEnv


class LegalActionQNetworkTests(unittest.TestCase):
    def setUp(self):
        self.model = LegalActionQNetwork()
        self.board = [[0 for _ in range(9)] for _ in range(9)]
        self.board[0][0] = 1
        self.board[2][4] = 3
        self.board[8][8] = 7

    def test_state_to_channels_preserves_colour_and_location(self):
        tensor = LegalActionQNetwork.state_to_channels(self.board)

        self.assertEqual(tensor.shape, (7, 9, 9))
        self.assertEqual(tensor[0, 0, 0].item(), 1.0)
        self.assertEqual(tensor[2, 2, 4].item(), 1.0)
        self.assertEqual(tensor[6, 8, 8].item(), 1.0)
        self.assertEqual(tensor[0, 1, 1].item(), 0.0)
        self.assertEqual(tensor[1, 0, 0].item(), 0.0)
        self.assertTrue(torch.all(tensor.sum(dim=0) <= 1))

    def test_state_to_channels_preserves_requested_device(self):
        tensor = LegalActionQNetwork.state_to_channels(self.board, device=torch.device("cpu"))
        self.assertEqual(str(tensor.device), "cpu")

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is not available")
    def test_model_inputs_match_parameter_device_on_cuda(self):
        model = LegalActionQNetwork().to(torch.device("cuda"))
        board = [[0 for _ in range(9)] for _ in range(9)]
        board[1][2] = 1
        board[5][6] = 4
        action = FiveOrMoreEnv.encode_action(2, 1, 6, 5)

        tensor = model.state_to_channels(board, device=model.conv1.weight.device)
        scores = model.score_actions(board, [action])

        self.assertEqual(str(tensor.device), str(model.conv1.weight.device))
        self.assertEqual(str(scores.device), str(model.conv1.weight.device))

    def test_action_feature_vector_extracts_source_and_destination_correctly(self):
        feature_maps = torch.zeros(1, 4, 9, 9, dtype=torch.float32)
        board_summary = torch.tensor([100.0, 101.0, 102.0], dtype=torch.float32)
        source_x, source_y = 2, 3
        destination_x, destination_y = 8, 5
        for channel in range(4):
            feature_maps[0, channel, source_y, source_x] = float(channel + 1)
            feature_maps[0, channel, destination_y, destination_x] = float(channel + 10)

        action = FiveOrMoreEnv.encode_action(source_x, source_y, destination_x, destination_y)
        combined = self.model._action_feature_vector(feature_maps, board_summary, action)
        expected = torch.cat(
            [
                feature_maps[0, :, source_y, source_x],
                feature_maps[0, :, destination_y, destination_x],
                board_summary,
            ],
            dim=0,
        )

        self.assertTrue(torch.equal(combined, expected))
        self.assertTrue(torch.equal(combined[:4], torch.tensor([1.0, 2.0, 3.0, 4.0])))
        self.assertTrue(torch.equal(combined[4:8], torch.tensor([10.0, 11.0, 12.0, 13.0])))
        self.assertTrue(torch.equal(combined[8:], board_summary))

    def test_convolutional_layers_keep_spatial_dimensions(self):
        board_tensor = LegalActionQNetwork.state_to_channels(self.board).unsqueeze(0)
        conv1 = self.model.relu(self.model.conv1(board_tensor))
        conv2 = self.model.relu(self.model.conv2(conv1))

        self.assertEqual(conv1.shape, (1, 16, 9, 9))
        self.assertEqual(conv2.shape, (1, 32, 9, 9))

    def test_flattened_board_summary_has_expected_size(self):
        _, summary = self.model._forward_features(self.board)
        self.assertEqual(summary.shape, (1, 128))

    def test_action_scores_match_candidate_count_and_order(self):
        env = FiveOrMoreEnv(difficulty="Easy")
        env.reset()
        legal_actions = env.get_valid_actions()
        if not legal_actions:
            self.skipTest("Environment produced no legal actions for this test board.")

        scores = self.model.score_actions(env.get_state(), legal_actions)
        self.assertEqual(scores.shape, (len(legal_actions), 1))

        first_value = self.model.score_action(env.get_state(), legal_actions[0])
        self.assertEqual(first_value.shape, (1,))
        self.assertTrue(torch.allclose(scores[0], first_value.unsqueeze(0)))

    def test_empty_action_list_is_handled_safely(self):
        scores = self.model.score_actions(self.board, [])
        self.assertEqual(scores.shape, (0,))
        best_action, best_value = self.model.select_best_action(self.board, [])
        self.assertIsNone(best_action)
        self.assertIsNone(best_value)

    def test_model_supports_backward_pass(self):
        env = FiveOrMoreEnv(difficulty="Easy")
        env.reset()
        legal_actions = env.get_valid_actions()
        if not legal_actions:
            self.skipTest("Environment produced no legal actions for this test board.")

        scores = self.model.score_actions(env.get_state(), legal_actions)
        loss = scores.sum()
        self.model.zero_grad()
        loss.backward()

        for parameter in self.model.parameters():
            self.assertFalse(torch.isnan(parameter.grad).any())
            self.assertFalse(torch.isinf(parameter.grad).any())

    def test_invalid_state_shapes_are_rejected(self):
        with self.assertRaises(ValueError):
            LegalActionQNetwork.state_to_channels([[1, 2, 3]])


if __name__ == "__main__":
    unittest.main()
