"""Distributed Ray-based vectorized environment manager for Five-or-More RL training."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from .rl_environment import FiveOrMoreEnv

try:
    import ray
except ImportError:
    ray = None


class _WorkerLogic:
    """Encapsulates isolated environment logic used by Ray actor."""

    def __init__(
        self,
        worker_id: int,
        difficulty: str = "Medium",
        seed: int | None = 42,
        invalid_action_reward: float = FiveOrMoreEnv.INVALID_ACTION_REWARD,
        score_per_point: float = FiveOrMoreEnv.REWARD_PER_SCORE_POINT,
        step_penalty: float = FiveOrMoreEnv.STEP_PENALTY,
        game_over_penalty: float = FiveOrMoreEnv.GAME_OVER_PENALTY,
        line_rewards: dict[int | str, float] | None = None,
    ) -> None:
        self.worker_id = worker_id
        if seed is not None:
            random.seed(seed + worker_id * 1000 + 7)

        self.env = FiveOrMoreEnv(
            difficulty=difficulty,
            invalid_action_reward=invalid_action_reward,
            score_per_point=score_per_point,
            step_penalty=step_penalty,
            game_over_penalty=game_over_penalty,
            line_rewards=line_rewards,
        )

    def reset(self) -> tuple[Any, list[int]]:
        state = self.env.reset()
        legal_actions = self.env.get_valid_actions()
        return state, legal_actions

    def reset_worker(self) -> tuple[Any, list[int]]:
        return self.reset()

    def step(self, action: int) -> tuple[Any, float, bool, list[int], float, Any, list[int] | None, dict[str, Any]]:
        next_state, reward, done, info = self.env.step(action)
        terminal_legal_actions = [] if done else self.env.get_valid_actions()
        score = float(self.env.game.get_score()) if self.env.game else 0.0

        reset_state = None
        reset_legal_actions = None
        if done:
            reset_state = self.env.reset()
            reset_legal_actions = self.env.get_valid_actions()

        return (
            next_state,
            float(reward),
            bool(done),
            terminal_legal_actions,
            score,
            reset_state,
            reset_legal_actions,
            info,
        )


if ray is not None:
    @ray.remote(num_cpus=1)
    class RayEnvWorker:
        """Top-level Ray actor class for cluster-wide serialization."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._logic = _WorkerLogic(*args, **kwargs)

        def reset(self) -> tuple[Any, list[int]]:
            return self._logic.reset()

        def reset_worker(self) -> tuple[Any, list[int]]:
            return self._logic.reset_worker()

        def step(self, action: int) -> tuple[Any, float, bool, list[int], float, Any, list[int] | None, dict[str, Any]]:
            return self._logic.step(action)
else:
    RayEnvWorker = None


class RayEnvManager:
    """Manage multiple distributed FiveOrMoreEnv instances across a Ray cluster."""

    def __init__(
        self,
        num_workers: int | None = None,
        difficulty: str = "Medium",
        base_seed: int | None = 42,
        invalid_action_reward: float = FiveOrMoreEnv.INVALID_ACTION_REWARD,
        score_per_point: float = FiveOrMoreEnv.REWARD_PER_SCORE_POINT,
        step_penalty: float = FiveOrMoreEnv.STEP_PENALTY,
        game_over_penalty: float = FiveOrMoreEnv.GAME_OVER_PENALTY,
        line_rewards: dict[int | str, float] | None = None,
        ray_address: str | None = None,
        node_workers: dict[str, int] | str | None = None,
    ) -> None:
        self.closed = True
        if ray is None:
            raise ImportError(
                "Ray is required for RayEnvManager. Install with `pip install 'ray[default]'`."
            )

        parsed_node_workers: dict[str, int] = {}
        if isinstance(node_workers, str):
            for part in node_workers.split(","):
                part = part.strip()
                if ":" in part:
                    node_key, cnt = part.split(":", 1)
                    parsed_node_workers[node_key.strip()] = int(cnt.strip())
        elif isinstance(node_workers, dict):
            parsed_node_workers = {str(k).strip(): int(v) for k, v in node_workers.items()}

        total_pinned = sum(parsed_node_workers.values()) if parsed_node_workers else 0
        if num_workers is None:
            num_workers = total_pinned if total_pinned > 0 else 12
        elif total_pinned > 0:
            num_workers = max(num_workers, total_pinned)

        if not isinstance(num_workers, int) or isinstance(num_workers, bool) or num_workers <= 0:
            raise ValueError("num_workers must be a positive integer.")

        self.num_workers = num_workers
        self.difficulty = difficulty
        self.base_seed = base_seed
        self.line_rewards = line_rewards

        project_root = Path(__file__).resolve().parent.parent.parent
        runtime_env = {
            "working_dir": str(project_root),
            "excludes": [".venv", "data", ".git", "__pycache__", ".pytest_cache", "*.log"],
        }

        import os

        target_address = ray_address or os.environ.get("RAY_ADDRESS", "192.168.6.106:6379")
        if not ray.is_initialized():
            try:
                ray.init(address=target_address, runtime_env=runtime_env, ignore_reinit_error=True)
            except Exception:
                ray.init(address=None, runtime_env=runtime_env, ignore_reinit_error=True)

        worker_strategies: list[Any] = []
        if parsed_node_workers:
            from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

            alive_nodes = {n["NodeManagerAddress"]: n["NodeID"] for n in ray.nodes() if n.get("Alive")}
            alive_by_id = {n["NodeID"]: n["NodeID"] for n in ray.nodes() if n.get("Alive")}

            target_node_ids: list[str | None] = []
            for target_key, count in parsed_node_workers.items():
                nid = alive_nodes.get(target_key) or alive_by_id.get(target_key)
                target_node_ids.extend([nid] * count)

            if len(target_node_ids) < self.num_workers:
                target_node_ids.extend([None] * (self.num_workers - len(target_node_ids)))
            elif len(target_node_ids) > self.num_workers:
                self.num_workers = len(target_node_ids)

            for nid in target_node_ids:
                if nid is not None:
                    worker_strategies.append(
                        NodeAffinitySchedulingStrategy(node_id=nid, soft=False)
                    )
                else:
                    worker_strategies.append(None)
        else:
            worker_strategies = [None] * self.num_workers

        self.workers: list[Any] = []
        for worker_id in range(self.num_workers):
            strat = worker_strategies[worker_id]
            actor_cls = RayEnvWorker.options(scheduling_strategy=strat) if strat is not None else RayEnvWorker
            actor = actor_cls.remote(
                worker_id=worker_id,
                difficulty=self.difficulty,
                seed=self.base_seed,
                invalid_action_reward=invalid_action_reward,
                score_per_point=score_per_point,
                step_penalty=step_penalty,
                game_over_penalty=game_over_penalty,
                line_rewards=self.line_rewards,
            )
            self.workers.append(actor)

        self.current_states: list[Any] = [None] * self.num_workers
        self.current_legal_actions: list[list[int]] = [[] for _ in range(self.num_workers)]
        self.closed = False

    def reset(self) -> tuple[list[Any], list[list[int]]]:
        """Reset all distributed environments and return initial states and legal actions."""
        self._check_closed()
        futures = [w.reset.remote() for w in self.workers]
        results = ray.get(futures)

        for worker_id, (state, legal_actions) in enumerate(results):
            self.current_states[worker_id] = state
            self.current_legal_actions[worker_id] = legal_actions

        return list(self.current_states), [list(a) for a in self.current_legal_actions]

    def step(self, actions: list[int]) -> list[dict[str, Any]]:
        """Step each distributed environment with its assigned action."""
        self._check_closed()
        if len(actions) != self.num_workers:
            raise ValueError(
                f"actions length ({len(actions)}) must equal num_workers ({self.num_workers})."
            )

        futures = [w.step.remote(action) for w, action in zip(self.workers, actions)]
        raw_results = ray.get(futures)

        results: list[dict[str, Any]] = []
        for worker_id, (action, raw) in enumerate(zip(actions, raw_results)):
            (
                next_state,
                reward,
                done,
                terminal_legal_actions,
                score,
                reset_state,
                reset_legal_actions,
                info,
            ) = raw

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

    def reset_workers(self, worker_ids: list[int]) -> None:
        """Reset selected workers after time-limit truncation."""
        self._check_closed()
        if len(set(worker_ids)) != len(worker_ids):
            raise ValueError("worker_ids must not contain duplicates.")
        if any(
            not isinstance(worker_id, int)
            or isinstance(worker_id, bool)
            or not 0 <= worker_id < self.num_workers
            for worker_id in worker_ids
        ):
            raise ValueError("worker_ids must contain valid worker indexes.")

        futures = [self.workers[wid].reset_worker.remote() for wid in worker_ids]
        results = ray.get(futures)
        for wid, (state, legal_actions) in zip(worker_ids, results):
            self.current_states[wid] = state
            self.current_legal_actions[wid] = legal_actions

    def close(self) -> None:
        """Clean up Ray actor handles."""
        if getattr(self, "closed", True):
            return
        self.closed = True
        workers = getattr(self, "workers", [])
        for w in workers:
            try:
                ray.kill(w)
            except Exception:
                pass
        self.workers = []

    def _check_closed(self) -> None:
        if self.closed:
            raise RuntimeError("Cannot operate on a closed RayEnvManager.")

    def __enter__(self) -> RayEnvManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


__all__ = ["RayEnvManager"]
