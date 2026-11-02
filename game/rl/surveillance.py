"""Training surveillance, resource profiling, and ETA estimation."""

from __future__ import annotations

import json
import os
import resource
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    if seconds < 0:
        return "0s"
    seconds = int(round(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes:02d}m")
    parts.append(f"{secs:02d}s")
    return " ".join(parts)


def get_process_memory_mb() -> float:
    """Return total resident set size (RSS) memory in MB for process and children."""
    if psutil is not None:
        try:
            current = psutil.Process()
            rss = current.memory_info().rss
            for child in current.children(recursive=True):
                try:
                    rss += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return round(rss / (1024.0 * 1024.0), 2)
        except Exception:
            pass

    # Fallback to standard library resource
    try:
        max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in kilobytes
        return round(float(max_rss) / 1024.0, 2)
    except Exception:
        return 0.0


def get_cpu_percent() -> float:
    """Return current CPU utilization percentage."""
    if psutil is not None:
        try:
            return round(psutil.cpu_percent(interval=None), 1)
        except Exception:
            pass
    try:
        load1, _, _ = os.getloadavg()
        cpu_count = os.cpu_count() or 1
        return round(min(100.0, (load1 / cpu_count) * 100.0), 1)
    except Exception:
        return 0.0


class TrainingSurveillance:
    """Monitor training speed, system resource usage, and projected completion time."""

    def __init__(
        self,
        total_episodes: int,
        interval: int = 100,
        experiment_manager: Any | None = None,
        log_path: Path | str | None = None,
        verbose: bool = True,
    ):
        if not isinstance(total_episodes, int) or isinstance(total_episodes, bool) or total_episodes <= 0:
            raise ValueError("total_episodes must be a positive integer.")
        if not isinstance(interval, int) or isinstance(interval, bool) or interval <= 0:
            raise ValueError("interval must be a positive integer.")

        self.total_episodes = total_episodes
        self.interval = interval
        self.experiment_manager = experiment_manager
        self.verbose = verbose

        if log_path is not None:
            self.log_path = Path(log_path)
        elif experiment_manager is not None and hasattr(experiment_manager, "run_dir"):
            self.log_path = experiment_manager.run_dir / "surveillance.jsonl"
        else:
            self.log_path = None

        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.start_time = time.time()
        self.last_interval_time = self.start_time
        self.last_interval_episodes = 0
        self.last_interval_steps = 0

        self.recent_scores: list[float] = []
        self.recent_rewards: list[float] = []
        self.recent_steps: list[int] = []
        self.recent_losses: list[float] = []
        self.best_score: float = float("-inf")
        self.total_steps: int = 0
        self.history: list[dict[str, Any]] = []

    def record_episode(
        self,
        episode: int,
        steps: int,
        score: float,
        reward: float,
        loss: float | None = None,
        epsilon: float = 1.0,
        environment_steps: int | None = None,
    ) -> dict[str, Any] | None:
        """Record an episode transition and trigger a surveillance report on interval."""
        self.recent_scores.append(float(score))
        self.recent_rewards.append(float(reward))
        self.recent_steps.append(int(steps))
        if loss is not None:
            self.recent_losses.append(float(loss))
        if score > self.best_score:
            self.best_score = float(score)

        if environment_steps is not None:
            self.total_steps = environment_steps
        else:
            self.total_steps += steps

        is_interval = (episode % self.interval == 0)
        is_final = (episode >= self.total_episodes)

        if not (is_interval or is_final):
            return None

        report = self._generate_report(episode, epsilon)
        self.history.append(report)

        if self.log_path is not None:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(report, sort_keys=True) + "\n")

        if self.verbose:
            self.print_report(report)

        # Reset interval baselines
        self.last_interval_time = time.time()
        self.last_interval_episodes = episode
        self.last_interval_steps = self.total_steps
        self.recent_scores.clear()
        self.recent_rewards.clear()
        self.recent_steps.clear()
        self.recent_losses.clear()

        return report

    def _generate_report(self, episode: int, epsilon: float) -> dict[str, Any]:
        now = time.time()
        elapsed_total = max(0.001, now - self.start_time)
        interval_duration = max(0.001, now - self.last_interval_time)

        episodes_in_interval = episode - self.last_interval_episodes
        steps_in_interval = self.total_steps - self.last_interval_steps

        overall_ep_per_sec = episode / elapsed_total
        interval_ep_per_sec = episodes_in_interval / interval_duration if interval_duration > 0 else overall_ep_per_sec

        overall_steps_per_sec = self.total_steps / elapsed_total
        interval_steps_per_sec = steps_in_interval / interval_duration if interval_duration > 0 else overall_steps_per_sec

        # Speeds per 100 and per 1,000 episodes
        rate_for_estimate = interval_ep_per_sec if interval_ep_per_sec > 0 else overall_ep_per_sec
        time_per_100_sec = (100.0 / rate_for_estimate) if rate_for_estimate > 0 else 0.0
        time_per_1000_sec = (1000.0 / rate_for_estimate) if rate_for_estimate > 0 else 0.0

        remaining_episodes = max(0, self.total_episodes - episode)
        eta_seconds = (remaining_episodes / rate_for_estimate) if rate_for_estimate > 0 else 0.0
        projected_time = datetime.now() + timedelta(seconds=eta_seconds)

        ram_mb = get_process_memory_mb()
        cpu_pct = get_cpu_percent()

        avg_score = mean(self.recent_scores) if self.recent_scores else 0.0
        avg_reward = mean(self.recent_rewards) if self.recent_rewards else 0.0
        avg_steps = mean(self.recent_steps) if self.recent_steps else 0.0
        avg_loss = mean(self.recent_losses) if self.recent_losses else None

        progress_pct = round((episode / self.total_episodes) * 100.0, 2)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "episode": episode,
            "total_episodes": self.total_episodes,
            "progress_percent": progress_pct,
            "elapsed_seconds": round(elapsed_total, 2),
            "elapsed_formatted": format_duration(elapsed_total),
            "interval_duration_sec": round(interval_duration, 2),
            "interval_episodes": episodes_in_interval,
            "episodes_per_sec": round(interval_ep_per_sec, 2),
            "steps_per_sec": round(interval_steps_per_sec, 2),
            "time_per_100_episodes_sec": round(time_per_100_sec, 2),
            "time_per_100_formatted": format_duration(time_per_100_sec),
            "time_per_1000_episodes_sec": round(time_per_1000_sec, 2),
            "time_per_1000_formatted": format_duration(time_per_1000_sec),
            "eta_seconds": round(eta_seconds, 2),
            "eta_formatted": format_duration(eta_seconds),
            "projected_completion": projected_time.strftime("%Y-%m-%d %H:%M:%S"),
            "cpu_percent": cpu_pct,
            "ram_rss_mb": ram_mb,
            "ram_rss_gb": round(ram_mb / 1024.0, 2),
            "rolling_average_score": round(avg_score, 2),
            "best_score": round(self.best_score, 2),
            "rolling_average_reward": round(avg_reward, 2),
            "rolling_average_steps": round(avg_steps, 2),
            "rolling_average_loss": round(avg_loss, 6) if avg_loss is not None else None,
            "epsilon": round(epsilon, 4),
        }

    def print_report(self, report: dict[str, Any]) -> None:
        """Print an eye-catching surveillance summary box to stdout."""
        loss_str = (
            f"{report['rolling_average_loss']:.4f}"
            if report["rolling_average_loss"] is not None
            else "N/A"
        )
        print("\n" + "=" * 68)
        print(" [TRAINING SURVEILLANCE & RESOURCE PROFILE]".center(68))
        print("=" * 68)
        print(
            f"  Progress:     {report['episode']:,} / {report['total_episodes']:,} "
            f"({report['progress_percent']:.1f}%)"
        )
        print(
            f"  Time Elapsed: {report['elapsed_formatted']:<12} "
            f"ETA: {report['eta_formatted']:<12} "
            f"(Target: {report['projected_completion']})"
        )
        print(
            f"  Throughput:   {report['episodes_per_sec']:.2f} ep/s  |  "
            f"{report['steps_per_sec']:.1f} steps/s"
        )
        print(
            f"  Estimates:    {report['time_per_100_formatted']} / 100 eps  |  "
            f"{report['time_per_1000_formatted']} / 1,000 eps"
        )
        print(
            f"  Resources:    CPU: {report['cpu_percent']:.1f}%  |  "
            f"RAM (RSS): {report['ram_rss_mb']:.1f} MB ({report['ram_rss_gb']:.2f} GB)"
        )
        print(
            f"  Performance:  Avg Score: {report['rolling_average_score']:.2f} "
            f"(Best: {report['best_score']:.0f})  |  "
            f"Avg Reward: {report['rolling_average_reward']:+.2f}  |  "
            f"Loss: {loss_str}"
        )
        print(f"  Exploration:  Epsilon: {report['epsilon']:.4f}")
        print("=" * 68 + "\n")
