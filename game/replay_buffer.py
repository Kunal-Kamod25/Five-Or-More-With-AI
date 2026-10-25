"""Uniform replay buffer for storing legal-action transitions."""

from __future__ import annotations

import copy
import random
from typing import Any, Iterable, Sequence


class ExperienceReplayBuffer:
    """Store and sample past state-action-reward-next_state transitions."""

    def __init__(self, capacity: int, seed: int | None = None):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError("capacity must be a positive integer.")

        self.capacity = capacity
        self._rng = random.Random(seed)
        self._buffer: list[dict[str, Any]] = []
        self._index = 0

    @property
    def size(self) -> int:
        return len(self._buffer)

    def append(self, transition: dict[str, Any]) -> None:
        """Add a transition to the buffer, evicting the oldest experience when full."""
        if not isinstance(transition, dict):
            raise TypeError("transition must be a dictionary.")

        record = self._copy_transition(transition)
        if len(self._buffer) < self.capacity:
            self._buffer.append(record)
        else:
            self._buffer[self._index] = record
            self._index = (self._index + 1) % self.capacity

        if len(self._buffer) == self.capacity:
            self._index = self._index % self.capacity

    def sample(self, batch_size: int) -> list[dict[str, Any]]:
        """Sample a uniformly random batch without replacement."""
        if not isinstance(batch_size, int) or isinstance(batch_size, bool):
            raise ValueError("batch_size must be a positive integer.")
        if batch_size <= 0:
            raise ValueError("batch_size must be a positive integer.")
        if not self._buffer:
            raise ValueError("cannot sample from an empty replay buffer.")
        if batch_size > len(self._buffer):
            raise ValueError(
                "batch_size cannot exceed the number of stored transitions."
            )

        return [copy.deepcopy(item) for item in self._rng.sample(self._buffer, batch_size)]

    def clear(self) -> None:
        self._buffer.clear()
        self._index = 0

    @staticmethod
    def _copy_transition(transition: dict[str, Any]) -> dict[str, Any]:
        state = transition.get("state")
        next_state = transition.get("next_state")
        next_legal_actions = transition.get("next_legal_actions")

        copied = {
            "state": copy.deepcopy(state),
            "action": copy.deepcopy(transition.get("action")),
            "reward": copy.deepcopy(transition.get("reward")),
            "next_state": copy.deepcopy(next_state),
            "done": copy.deepcopy(transition.get("done")),
            "next_legal_actions": copy.deepcopy(next_legal_actions),
        }
        return copied

    def __len__(self) -> int:
        return self.size


__all__ = ["ExperienceReplayBuffer"]
