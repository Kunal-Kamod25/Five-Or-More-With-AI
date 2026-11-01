"""Summarize saved training runs and their configurations."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDNAMES = (
    "run_id",
    "status",
    "config_hash",
    "config_snapshot",
    "config_json",
    "episodes",
    "difficulty",
    "workers",
    "average_score",
    "best_score",
    "average_reward",
    "average_episode_length",
    "evaluation_average_score",
    "evaluation_seed",
    "evaluation_episodes",
    "random_baseline_average_score",
    "evaluation_score_delta",
    "reward_config",
)


def collect_experiments(base_dir: str | Path) -> list[dict[str, Any]]:
    """Load each run's final metrics and config snapshot for comparison."""
    root = Path(base_dir)
    if not root.exists():
        raise FileNotFoundError(f"Experiment directory not found: {root}")

    rows = []
    run_dirs = sorted(
        (path for path in root.glob("run_*") if path.is_dir()),
        key=lambda path: int(path.name.removeprefix("run_"))
        if path.name.removeprefix("run_").isdigit()
        else 0,
    )
    for run_dir in run_dirs:
        results_path = run_dir / "results.json"
        config_path = run_dir / "config.json"
        if not results_path.exists() or not config_path.exists():
            continue

        results = json.loads(results_path.read_text(encoding="utf-8"))
        config = json.loads(config_path.read_text(encoding="utf-8"))
        evaluation = results.get("best_evaluation", {})
        baseline = results.get("random_baseline", {})
        rows.append(
            {
                "run_id": results.get("run_id", run_dir.name),
                "status": results.get("status", "unknown"),
                "config_hash": results.get("config_hash", ""),
                "config_snapshot": str(config_path),
                "config_json": json.dumps(
                    config,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                "episodes": results.get("episodes", 0),
                "difficulty": config.get("environment", {}).get("difficulty", ""),
                "workers": config.get("training", {}).get("num_workers", 1),
                "average_score": results.get("average_score"),
                "best_score": results.get("best_score"),
                "average_reward": results.get("average_reward"),
                "average_episode_length": results.get("average_episode_length"),
                "evaluation_average_score": evaluation.get("average_score"),
                "evaluation_seed": evaluation.get("seed"),
                "evaluation_episodes": evaluation.get("episodes"),
                "random_baseline_average_score": baseline.get("average_score"),
                "evaluation_score_delta": results.get("evaluation_score_delta"),
                "reward_config": json.dumps(
                    config.get("reward", {}),
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )
    return rows


def write_comparison(rows: list[dict[str, Any]], output_path: str | Path) -> Path:
    """Write the run comparison to CSV and return its path."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare scores and configuration snapshots across experiment runs."
    )
    parser.add_argument("--experiments-dir", default="data/experiments")
    parser.add_argument("--output", default=None, help="output CSV path")
    arguments = parser.parse_args()

    rows = collect_experiments(arguments.experiments_dir)
    if not rows:
        raise FileNotFoundError(
            f"No experiment runs with config and results were found in {arguments.experiments_dir}."
        )
    output = write_comparison(
        rows,
        arguments.output or Path(arguments.experiments_dir) / "comparison.csv",
    )

    print(
        f"{'Run':<10} {'Status':<12} {'Episodes':>9} {'Avg score':>11} "
        f"{'Best':>8} {'Eval avg':>10} {'vs random':>11} {'Config hash':<12}"
    )
    for row in rows:
        def display(value: Any, precision: int = 2) -> str:
            return "-" if value is None else f"{value:.{precision}f}"

        print(
            f"{row['run_id']:<10} {row['status']:<12} {row['episodes']:>9} "
            f"{display(row['average_score']):>11} "
            f"{display(row['best_score'], 0):>8} "
            f"{display(row['evaluation_average_score']):>10} "
            f"{display(row['evaluation_score_delta']):>11} "
            f"{row['config_hash'][:12]:<12}"
        )
    print(f"\nComparison saved to {output}")


if __name__ == "__main__":
    main()
