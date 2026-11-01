"""Uniform replay buffer for storing legal-action transitions."""

from __future__ import annotations

import copy
import random
from typing import Any, Iterable, Sequence


class ExperienceReplayBuffer:
    """Store and sample past state-action-reward-next_state transitions."""

    def __init__(self, capacity: int, seed: int | None = None, deduplicate: bool = False):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError("capacity must be a positive integer.")

        self.capacity = capacity
        self.deduplicate = deduplicate
        self._rng = random.Random(seed)
        self._buffer: list[dict[str, Any]] = []
        self._seen_signatures: set[tuple[Any, Any]] = set()
        self._index = 0

    @property
    def size(self) -> int:
        return len(self._buffer)

    @staticmethod
    def _transition_signature(transition: dict[str, Any]) -> tuple | None:
        state = transition.get("state")
        action = transition.get("action")
        if isinstance(state, list):
            try:
                state_key = tuple(tuple(row) if isinstance(row, list) else row for row in state)
                return (state_key, action)
            except TypeError:
                return None
        return None

    def append(self, transition: dict[str, Any]) -> None:
        """Add a transition to the buffer, evicting the oldest experience when full."""
        if not isinstance(transition, dict):
            raise TypeError("transition must be a dictionary.")

        sig = self._transition_signature(transition) if self.deduplicate else None
        if self.deduplicate and sig is not None and sig in self._seen_signatures:
            return  # Skip duplicate state-action experience

        record = self._copy_transition(transition)
        if len(self._buffer) < self.capacity:
            self._buffer.append(record)
            if sig is not None:
                self._seen_signatures.add(sig)
        else:
            if self.deduplicate:
                old_sig = self._transition_signature(self._buffer[self._index])
                if old_sig is not None:
                    self._seen_signatures.discard(old_sig)
            self._buffer[self._index] = record
            if sig is not None:
                self._seen_signatures.add(sig)
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

        sampled = self._rng.sample(self._buffer, batch_size)
        return [self._copy_transition(item) for item in sampled]

    def clear(self) -> None:
        self._buffer.clear()
        self._seen_signatures.clear()
        self._index = 0

    @staticmethod
    def _copy_grid(grid: Any) -> Any:
        if isinstance(grid, list):
            return [row[:] if isinstance(row, list) else row for row in grid]
        return copy.deepcopy(grid)

    @classmethod
    def _copy_transition(cls, transition: dict[str, Any]) -> dict[str, Any]:
        state = transition.get("state")
        next_state = transition.get("next_state")
        next_legal_actions = transition.get("next_legal_actions")

        return {
            "state": cls._copy_grid(state),
            "action": transition.get("action"),
            "reward": transition.get("reward"),
            "next_state": cls._copy_grid(next_state),
            "done": transition.get("done"),
            "next_legal_actions": (
                list(next_legal_actions)
                if isinstance(next_legal_actions, list)
                else copy.deepcopy(next_legal_actions)
            ),
        }

    def __len__(self) -> int:
        return self.size


__all__ = ["ExperienceReplayBuffer"]
