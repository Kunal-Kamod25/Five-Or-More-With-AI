"""Target-network wrapper for the legal-action Q-network."""

from __future__ import annotations

import copy

import torch

from .q_network import LegalActionQNetwork


class TargetNetwork:
    """Maintain a frozen copy of the online network for DQN target values."""

    def __init__(self, online_network: LegalActionQNetwork):
        if not isinstance(online_network, LegalActionQNetwork):
            raise TypeError("online_network must be a LegalActionQNetwork instance.")

        self.online_network = online_network
        self.model = copy.deepcopy(online_network)
        self.model.eval()
        self.model.requires_grad_(False)
        for parameter in self.model.parameters():
            parameter.requires_grad = False

    def hard_update(self) -> None:
        """Copy the online network's full state into the target network."""
        self.model.load_state_dict(self.online_network.state_dict())
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad = False

    def __call__(self, *args, **kwargs):
        with torch.no_grad():
            return self.model(*args, **kwargs)

    def state_dict(self):
        return self.model.state_dict()

    def to(self, device):
        return self.model.to(device)


__all__ = ["TargetNetwork"]
