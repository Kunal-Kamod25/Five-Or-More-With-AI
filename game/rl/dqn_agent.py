"""Minimal DQN agent connecting the Q-network, replay buffer, and target."""

from __future__ import annotations

import random
from numbers import Real
from typing import Any, Sequence

import torch
import torch.nn.functional as functional

from config.config_loader import load_config, validate_config
from .q_network import LegalActionQNetwork
from .replay_buffer import ExperienceReplayBuffer
from .target_network import TargetNetwork


class DQNAgent:
    """Select legal actions, store transitions, and perform one DQN update."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        *,
        online_network: LegalActionQNetwork | None = None,
        replay_buffer: ExperienceReplayBuffer | None = None,
        device: torch.device | str | None = None,
        rng: random.Random | None = None,
    ):
        self.config = load_config() if config is None else validate_config(config)
        dqn_config = self.config["dqn"]
        exploration_config = self.config["exploration"]

        self.online_network = (
            online_network
            if online_network is not None
            else LegalActionQNetwork(self.config)
        )
        if not isinstance(self.online_network, LegalActionQNetwork):
            raise TypeError("online_network must be a LegalActionQNetwork instance.")
        self.device = (
            torch.device(device)
            if device is not None
            else next(self.online_network.parameters()).device
        )
        self.online_network.to(self.device)

        self.target_network = TargetNetwork(self.online_network)
        self.target_network.to(self.device)

        self.replay_buffer = (
            replay_buffer
            if replay_buffer is not None
            else ExperienceReplayBuffer(
                capacity=dqn_config["replay_buffer_size"],
                seed=self.config["training"].get("seed"),
                deduplicate=bool(dqn_config.get("deduplicate_transitions", True)),
            )
        )
        if not isinstance(self.replay_buffer, ExperienceReplayBuffer):
            raise TypeError("replay_buffer must be an ExperienceReplayBuffer instance.")

        self.gamma = float(dqn_config["gamma"])
        self.batch_size = int(dqn_config["batch_size"])
        self.epsilon = float(exploration_config["epsilon_start"])
        self.rng = rng if rng is not None else random.Random(
            self.config["training"].get("seed")
        )
        self.optimizer = torch.optim.Adam(
            self.online_network.parameters(),
            lr=float(dqn_config["learning_rate"]),
        )

    def select_action(
        self,
        state: Any,
        legal_actions: Sequence[int],
        epsilon: float | None = None,
        avoid_actions: Sequence[int] | None = None,
    ) -> int | None:
        """Choose randomly or greedily from the supplied legal actions, avoiding cycle actions if alternatives exist."""
        actions = list(legal_actions)
        if not actions:
            return None

        if avoid_actions:
            avoid_set = set(avoid_actions)
            non_avoid = [a for a in actions if a not in avoid_set]
            if non_avoid:
                actions = non_avoid

        exploration_rate = self.epsilon if epsilon is None else epsilon
        if (
            isinstance(exploration_rate, bool)
            or not isinstance(exploration_rate, Real)
            or not 0.0 <= exploration_rate <= 1.0
        ):
            raise ValueError("epsilon must be a number between 0 and 1 inclusive.")

        if self.rng.random() < exploration_rate:
            return self.rng.choice(actions)

        with torch.no_grad():
            scores = self.online_network.score_actions(state, actions).reshape(-1)
            best_index = int(torch.argmax(scores).item())
        return actions[best_index]

    def store_transition(
        self,
        state: Any,
        action: int,
        reward: float,
        next_state: Any,
        done: bool,
        next_legal_actions: Sequence[int],
    ) -> None:
        """Store one environment transition using the replay buffer's copy semantics."""
        self.replay_buffer.append(
            {
                "state": state,
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
                "next_legal_actions": next_legal_actions,
            }
        )

    def learn_step(self) -> dict[str, float | bool | None]:
        """Perform one full-batch Huber-loss update, or skip when undersized."""
        if len(self.replay_buffer) < self.batch_size:
            return {"loss": None, "updated": False}

        transitions = self.replay_buffer.sample(self.batch_size)
        predicted_values = []
        target_values = []

        for transition in transitions:
            predicted_values.append(
                self.online_network.score_action(
                    transition["state"],
                    transition["action"],
                ).reshape(())
            )
            target_values.append(self._target_value(transition))

        predictions = torch.stack(predicted_values)
        targets = torch.stack(target_values)
        loss = functional.smooth_l1_loss(predictions, targets)

        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        self.optimizer.step()
        return {"loss": float(loss.detach().item()), "updated": True}

    def _target_value(self, transition: dict[str, Any]) -> torch.Tensor:
        reward = torch.as_tensor(
            transition["reward"],
            dtype=next(self.online_network.parameters()).dtype,
            device=self.device,
        )
        next_actions = transition["next_legal_actions"]
        if transition["done"] or not next_actions:
            return reward

        with torch.no_grad():
            next_q_values = self.target_network.model.score_actions(
                transition["next_state"],
                next_actions,
            )
            max_next_q = next_q_values.max()
        return reward + self.gamma * max_next_q

    def synchronize_target_network(self) -> None:
        """Request a hard copy of online parameters into the target network."""
        self.target_network.hard_update()

    def to(self, device: torch.device | str) -> DQNAgent:
        """Move both networks together; call this instead of moving either alone."""
        self.device = torch.device(device)
        self.online_network.to(self.device)
        self.target_network.to(self.device)
        return self


__all__ = ["DQNAgent"]
