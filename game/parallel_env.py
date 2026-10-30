"""Parallel vectorized environment manager for Five-or-More RL training."""

from __future__ import annotations

import random
from typing import Any

import torch.multiprocessing as mp

from .rl_environment import FiveOrMoreEnv


def _worker_loop(
    worker_id: int,
    remote: mp.connection.Connection,
    parent_remote: mp.connection.Connection,
    difficulty: str,
    seed: int | None,
) -> None:
    """Run an isolated FiveOrMoreEnv instance in a worker process."""
    parent_remote.close()

    if seed is not None:
        random.seed(seed + worker_id * 1000 + 7)

    env = FiveOrMoreEnv(difficulty=difficulty)

    while True:
        try:
            cmd, data = remote.recv()
        except EOFError:
            break

        if cmd == "reset":
            state = env.reset()
            legal_actions = env.get_valid_actions()
            remote.send((state, legal_actions))

        elif cmd == "step":
            action = data
            next_state, reward, done, info = env.step(action)
            terminal_legal_actions = [] if done else env.get_valid_actions()
            score = float(env.game.get_score()) if env.game else 0.0

            reset_state = None
            reset_legal_actions = None
            if done:
                reset_state = env.reset()
                reset_legal_actions = env.get_valid_actions()

            remote.send(
                (
                    next_state,
                    float(reward),
                    bool(done),
                    terminal_legal_actions,
                    score,
                    reset_state,
                    reset_legal_actions,
                    info,
                )
            )

        elif cmd == "get_valid_actions":
            remote.send(env.get_valid_actions())

        elif cmd == "close":
            remote.close()
            break

        else:
            remote.close()
            raise ValueError(f"Unknown command received by worker: {cmd}")


class ParallelEnvManager:
    """Manage multiple parallel FiveOrMoreEnv instances across CPU cores."""

    def __init__(
        self,
        num_workers: int = 8,
        difficulty: str = "Medium",
        base_seed: int | None = 42,
    ) -> None:
        self.closed = True
        if not isinstance(num_workers, int) or isinstance(num_workers, bool) or num_workers <= 0:
            raise ValueError("num_workers must be a positive integer.")

        self.num_workers = num_workers
        self.difficulty = difficulty
        self.base_seed = base_seed

        self.remotes: list[mp.connection.Connection] = []
        self.work_remotes: list[mp.connection.Connection] = []
        self.processes: list[mp.Process] = []

        ctx = mp.get_context("spawn")
        for worker_id in range(self.num_workers):
            parent_remote, work_remote = ctx.Pipe()
            process = ctx.Process(
                target=_worker_loop,
                args=(worker_id, work_remote, parent_remote, self.difficulty, self.base_seed),
                daemon=True,
            )
            process.start()
            work_remote.close()

            self.remotes.append(parent_remote)
            self.work_remotes.append(work_remote)
            self.processes.append(process)

        self.current_states: list[Any] = [None] * self.num_workers
        self.current_legal_actions: list[list[int]] = [[] for _ in range(self.num_workers)]
        self.closed = False

    def reset(self) -> tuple[list[Any], list[list[int]]]:
        """Reset all parallel environments and return their initial states and valid actions."""
        self._check_closed()
        for remote in self.remotes:
            remote.send(("reset", None))

        for worker_id, remote in enumerate(self.remotes):
            state, legal_actions = remote.recv()
            self.current_states[worker_id] = state
            self.current_legal_actions[worker_id] = legal_actions

        return list(self.current_states), [list(a) for a in self.current_legal_actions]

    def step(self, actions: list[int]) -> list[dict[str, Any]]:
        """Step each environment with its corresponding action in parallel."""
        self._check_closed()
        if len(actions) != self.num_workers:
            raise ValueError(
                f"actions length ({len(actions)}) must equal num_workers ({self.num_workers})."
            )

        for remote, action in zip(self.remotes, actions):
            remote.send(("step", action))

        results: list[dict[str, Any]] = []
        for worker_id, (remote, action) in enumerate(zip(self.remotes, actions)):
            (
                next_state,
                reward,
                done,
                terminal_legal_actions,
                score,
                reset_state,
                reset_legal_actions,
                info,
            ) = remote.recv()

            transition = {
                "worker_id": worker_id,
                "state": self.current_states[worker_id],
                "action": action,
                "reward": reward,
                "next_state": next_state,
                "done": done,
                "next_legal_actions": terminal_legal_actions,
                "score": score,
                "reset_occurred": done,
            }
            results.append(transition)

            if done:
                self.current_states[worker_id] = reset_state
                self.current_legal_actions[worker_id] = reset_legal_actions or []
            else:
                self.current_states[worker_id] = next_state
                self.current_legal_actions[worker_id] = terminal_legal_actions

        return results

    def close(self) -> None:
        """Cleanly terminate worker processes and close IPC pipes."""
        if getattr(self, "closed", True):
            return
        self.closed = True
        for remote in getattr(self, "remotes", []):
            try:
                remote.send(("close", None))
                remote.close()
            except (BrokenPipeError, OSError):
                pass

        for process in getattr(self, "processes", []):
            process.join(timeout=2.0)
            if process.is_alive():
                process.terminate()

    def _check_closed(self) -> None:
        if self.closed:
            raise RuntimeError("Cannot operate on a closed ParallelEnvManager.")

    def __enter__(self) -> ParallelEnvManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


__all__ = ["ParallelEnvManager"]
