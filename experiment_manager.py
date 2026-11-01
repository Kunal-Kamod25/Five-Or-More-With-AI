"""Create and manage reproducible ML experiment runs."""

from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.config_loader import load_config, validate_config


class ExperimentManager:
    """Create a unique experiment directory and store its config + outputs."""

    def __init__(self, config: dict[str, Any] | None = None, base_dir: str | Path | None = None):
        if config is None:
            self.config = load_config()
        else:
            self.config = validate_config(config)
        project_root = Path(__file__).resolve().parent
        self.base_dir = Path(base_dir) if base_dir is not None else project_root / "data" / "experiments"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = self._next_run_id()
        self.run_dir = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.run_dir / "config.json"
        self.results_path = self.run_dir / "results.json"
        self.metrics_path = self.run_dir / "metrics.csv"
        self.model_path = self.run_dir / "model.pth"
        self.best_model_path = self.run_dir / "best_model.pth"
        self.evaluations_path = self.run_dir / "evaluations.jsonl"
        self.config_hash = hashlib.sha256(
            json.dumps(self.config, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        self._write_config_snapshot()
        self.results = self._initial_results()
        self._write_results(self.results)
        self._ensure_metrics_header()

    def _next_run_id(self) -> str:
        existing = []
        if self.base_dir.exists():
            for candidate in self.base_dir.iterdir():
                if candidate.is_dir() and candidate.name.startswith("run_"):
                    suffix = candidate.name.split("run_", 1)[1]
                    if suffix.isdigit():
                        existing.append(int(suffix))

        next_number = max(existing) + 1 if existing else 1
        return f"run_{next_number:03d}"

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _write_config_snapshot(self) -> None:
        with self.config_path.open("w", encoding="utf-8") as handle:
            json.dump(deepcopy(self.config), handle, indent=2, sort_keys=True)
            handle.write("\n")

    def _initial_results(self) -> dict[str, Any]:
        timestamp = self._timestamp()
        return {
            "run_id": self.run_id,
            "timestamp": timestamp,
            "start_time": timestamp,
            "end_time": None,
            "status": "initialized",
            "episodes": 0,
            "final_score": None,
            "average_score": None,
            "best_score": None,
            "average_reward": None,
            "best_reward": None,
            "average_episode_length": None,
            "final_epsilon": None,
            "average_loss": None,
            "config_hash": self.config_hash,
            "model_path": str(self.model_path),
            "best_model_path": str(self.best_model_path),
            "config_snapshot": str(self.config_path),
        }

    def _write_results(self, payload: dict[str, Any]) -> None:
        results = deepcopy(payload)
        results.setdefault("run_id", self.run_id)
        results.setdefault("timestamp", self._timestamp())
        results.setdefault("start_time", results["timestamp"])
        results.setdefault("config_snapshot", str(self.config_path))
        results.setdefault("config_hash", self.config_hash)
        results.setdefault("model_path", str(self.model_path))
        results.setdefault("best_model_path", str(self.best_model_path))
        with self.results_path.open("w", encoding="utf-8") as handle:
            json.dump(results, handle, indent=2, sort_keys=True)
            handle.write("\n")
        self.results = results

    def save_results(self, **updates: Any) -> dict[str, Any]:
        """Persist experiment summary information to results.json."""
        results = deepcopy(self.results)
        results.update(updates)
        results.setdefault("run_id", self.run_id)
        results.setdefault("timestamp", self._timestamp())
        results.setdefault("start_time", results["timestamp"])
        results.setdefault("status", "completed")
        results.setdefault("config_snapshot", str(self.config_path))
        results.setdefault("config_hash", self.config_hash)
        results.setdefault("model_path", str(self.model_path))
        results.setdefault("best_model_path", str(self.best_model_path))
        self._write_results(results)
        return self.results

    def _ensure_metrics_header(self) -> None:
        fieldnames = [
            "episode",
            "score",
            "reward",
            "steps",
            "done",
            "epsilon",
            "loss",
            "average_score",
            "average_reward",
            "truncated",
            "stop_reason",
        ]
        if not self.metrics_path.exists() or self.metrics_path.stat().st_size == 0:
            with self.metrics_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()

    def log_episode(
        self,
        *,
        episode: int,
        score: float | int,
        reward: float | int,
        steps: int,
        done: bool,
        epsilon: float | None = None,
        loss: float | None = None,
        average_score: float | None = None,
        average_reward: float | None = None,
        truncated: bool = False,
        stop_reason: str | None = None,
    ) -> dict[str, Any]:
        """Append one episode record to metrics.csv."""
        if not isinstance(episode, int) or isinstance(episode, bool) or episode <= 0:
            raise ValueError("episode must be a positive integer.")
        if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
            raise ValueError("steps must be a non-negative integer.")

        row = {
            "episode": episode,
            "score": score,
            "reward": reward,
            "steps": steps,
            "done": bool(done),
            "epsilon": epsilon,
            "loss": loss,
            "average_score": average_score,
            "average_reward": average_reward,
            "truncated": bool(truncated),
            "stop_reason": stop_reason,
        }
        self._ensure_metrics_header()
        with self.metrics_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "episode",
                    "score",
                    "reward",
                    "steps",
                    "done",
                    "epsilon",
                    "loss",
                    "average_score",
                    "average_reward",
                    "truncated",
                    "stop_reason",
                ],
            )
            writer.writerow(row)

        self.results["episodes"] = max(int(self.results.get("episodes", 0)), int(episode))
        self.results["status"] = "running"
        self._write_results(self.results)
        return row

    def log_evaluation(self, **metrics: Any) -> dict[str, Any]:
        """Append evaluation and baseline metrics to the run's JSONL history."""
        row = {
            "timestamp": self._timestamp(),
            "run_id": self.run_id,
            "config_hash": self.config_hash,
            **metrics,
        }
        with self.evaluations_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        return row

    def record_metrics(self, **kwargs: Any) -> dict[str, Any]:
        """Backward-compatible alias for log_episode."""
        return self.log_episode(**kwargs)

    @property
    def config_snapshot_path(self) -> str:
        return str(self.config_path)

    @property
    def metrics_file_path(self) -> str:
        return str(self.metrics_path)

    @property
    def results_file_path(self) -> str:
        return str(self.results_path)

    @property
    def model_file_path(self) -> str:
        return str(self.model_path)


__all__ = ["ExperimentManager"]
