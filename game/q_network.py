"""CNN-based legal-action Q-network for the Five-or-More board state."""

from __future__ import annotations

from numbers import Integral

import torch
from torch import nn

from config.config_loader import load_config, validate_config
from .board import Board
from .rl_environment import FiveOrMoreEnv


class LegalActionQNetwork(nn.Module):
    """Estimate Q-values for legal actions from a 9x9 board state."""

    def __init__(self, config: dict | None = None):
        super().__init__()
        if config is None:
            config = load_config()
        else:
            config = validate_config(config)

        network_config = config["network"]
        cnn_config = network_config["cnn"]
        hidden_layers = network_config.get("hidden_layers", [128, 128])

        if not isinstance(hidden_layers, list) or not hidden_layers:
            raise ValueError("network.hidden_layers must be a non-empty list.")

        self.input_channels = Board.MAX_CELL_VALUE
        self.conv_channels = tuple(int(channel) for channel in cnn_config["channels"])
        self.kernel_size = int(cnn_config["kernel_size"])
        self.padding = int(cnn_config.get("padding", 1))
        self.board_summary_size = int(hidden_layers[0])
        self.action_hidden_size = int(hidden_layers[1]) if len(hidden_layers) > 1 else int(hidden_layers[0])
        self.feature_channels = self.conv_channels[-1]
        self.flattened_size = Board.SIZE * Board.SIZE * self.feature_channels

        self.conv1 = nn.Conv2d(
            in_channels=self.input_channels,
            out_channels=self.conv_channels[0],
            kernel_size=self.kernel_size,
            stride=1,
            padding=self.padding,
        )
        self.conv2 = nn.Conv2d(
            in_channels=self.conv_channels[0],
            out_channels=self.conv_channels[1],
            kernel_size=self.kernel_size,
            stride=1,
            padding=self.padding,
        )
        self.relu = nn.ReLU()
        self.board_summary_layer = nn.Linear(self.flattened_size, self.board_summary_size)
        self.action_scorer = nn.Sequential(
            nn.Linear(self.feature_channels * 2 + self.board_summary_size, self.action_hidden_size),
            nn.ReLU(),
            nn.Linear(self.action_hidden_size, 1),
        )

    @staticmethod
    def validate_state(state):
        """Return a copy of a 9x9 integer board, validating its shape and values."""
        if isinstance(state, torch.Tensor):
            state = state.detach().cpu().tolist()
        if not isinstance(state, list):
            raise TypeError("state must be a list of 9 rows or a 2D tensor.")
        if len(state) != Board.SIZE:
            raise ValueError(f"state must have {Board.SIZE} rows.")

        validated = []
        for row_index, row in enumerate(state):
            if not isinstance(row, list):
                raise TypeError(f"row {row_index} must be a list of integers.")
            if len(row) != Board.SIZE:
                raise ValueError(f"row {row_index} must contain {Board.SIZE} values.")
            checked_row = []
            for column_index, value in enumerate(row):
                if isinstance(value, bool) or not isinstance(value, Integral):
                    raise TypeError(
                        f"state[{row_index}][{column_index}] must be an integer cell value."
                    )
                value = int(value)
                if not Board.MIN_CELL_VALUE <= value <= Board.MAX_CELL_VALUE:
                    raise ValueError(
                        f"state[{row_index}][{column_index}] must be between "
                        f"{Board.MIN_CELL_VALUE} and {Board.MAX_CELL_VALUE}."
                    )
                checked_row.append(value)
            validated.append(checked_row)
        return validated

    @classmethod
    def state_to_channels(cls, state, device=None):
        """Convert a 9x9 integer board into binary colour channels shaped [C, 9, 9]."""
        validated_state = cls.validate_state(state)
        device = torch.device(device) if device is not None else torch.device("cpu")
        channels = torch.zeros(
            Board.MAX_CELL_VALUE,
            Board.SIZE,
            Board.SIZE,
            dtype=torch.float32,
            device=device,
        )
        for row_index, row in enumerate(validated_state):
            for column_index, value in enumerate(row):
                if value == Board.EMPTY:
                    continue
                channels[value - 1, row_index, column_index] = 1.0
        return channels

    def _action_feature_vector(self, feature_maps, board_summary, action):
        """Build the source + destination + board-summary feature vector for one action."""
        board_summary_vector = board_summary[0] if board_summary.dim() > 1 else board_summary
        source_index, destination_index = divmod(int(action), 81)
        source_y, source_x = divmod(source_index, Board.SIZE)
        destination_y, destination_x = divmod(destination_index, Board.SIZE)

        source_features = feature_maps[0, :, source_y, source_x]
        destination_features = feature_maps[0, :, destination_y, destination_x]
        return torch.cat(
            [source_features, destination_features, board_summary_vector],
            dim=0,
        )

    def _forward_features(self, state):
        state_tensor = self.state_to_channels(state, device=self.conv1.weight.device).unsqueeze(0)
        x = self.relu(self.conv1(state_tensor))
        x = self.relu(self.conv2(x))
        flat = torch.flatten(x, start_dim=1)
        summary = self.relu(self.board_summary_layer(flat))
        return x, summary

    def score_action(self, state, action):
        """Return the estimated Q-value for one encoded legal action."""
        if isinstance(action, bool) or not isinstance(action, Integral):
            raise TypeError("action must be an integer action index.")
        action = int(action)
        if not 0 <= action < FiveOrMoreEnv.ACTION_COUNT:
            raise ValueError(
                "action must be an integer in the range [0, {0}].".format(
                    FiveOrMoreEnv.ACTION_COUNT - 1
                )
            )
        feature_maps, board_summary = self._forward_features(state)
        combined = self._action_feature_vector(feature_maps, board_summary, action)
        return self.action_scorer(combined.unsqueeze(0)).squeeze(0)

    def score_actions(self, state, actions):
        """Return one Q-value per supplied legal action in the same order."""
        if actions is None:
            raise TypeError("actions must be a sequence of legal encoded actions.")
        legal_actions = list(actions)
        if not legal_actions:
            return torch.empty(0, dtype=torch.float32)

        for action in legal_actions:
            if isinstance(action, bool) or not isinstance(action, Integral):
                raise TypeError("all actions must be integers.")
            action = int(action)
            if not 0 <= action < FiveOrMoreEnv.ACTION_COUNT:
                raise ValueError(
                    "all actions must be integers in the range [0, {0}].".format(
                        FiveOrMoreEnv.ACTION_COUNT - 1
                    )
                )

        feature_maps, board_summary = self._forward_features(state)
        device = feature_maps.device
        actions_tensor = torch.as_tensor(legal_actions, dtype=torch.long, device=device)

        source_indices = actions_tensor // 81
        destination_indices = actions_tensor % 81
        source_y = source_indices // Board.SIZE
        source_x = source_indices % Board.SIZE
        destination_y = destination_indices // Board.SIZE
        destination_x = destination_indices % Board.SIZE

        feature_maps_spatial = feature_maps[0].permute(1, 2, 0)
        source_features = feature_maps_spatial[source_y, source_x]
        destination_features = feature_maps_spatial[destination_y, destination_x]

        board_summary_vector = board_summary[0] if board_summary.dim() > 1 else board_summary
        summary_expanded = board_summary_vector.unsqueeze(0).expand(len(legal_actions), -1)

        combined = torch.cat(
            [source_features, destination_features, summary_expanded],
            dim=1,
        )
        return self.action_scorer(combined)

    def select_best_action(self, state, actions):
        """Return the highest-scoring legal action and its estimated value."""
        legal_actions = list(actions)
        if not legal_actions:
            return None, None
        scores = self.score_actions(state, legal_actions)
        best_index = int(torch.argmax(scores).item())
        return legal_actions[best_index], float(scores[best_index].item())

    def forward(self, state, actions=None):
        if actions is None:
            raise TypeError("actions must be provided to score legal actions.")
        return self.score_actions(state, actions)


__all__ = ["LegalActionQNetwork"]
