"""Automated hyperparameter tuning runner and leaderboard generator."""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from config.config_loader import load_config, validate_config
from .compare_experiments import collect_experiments
from .surveillance import format_duration
from .train_dqn import train_dqn


DEFAULT_SEARCH_SPACE: dict[str, list[Any]] = {
    "dqn.learning_rate": [0.0001, 0.00025, 0.0005],
    "training.train_frequency": [2, 4, 8],
    "dqn.gamma": [0.95, 0.99],
    "reward.step_penalty": [0.0005, 0.001, 0.002],
    "reward.score_per_point": [1.0],
}


def _set_nested(dictionary: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict using dot-notation ('a.b.c')."""
    keys = path.split(".")
    target = dictionary
    for key in keys[:-1]:
        target = target.setdefault(key, {})
    target[keys[-1]] = value


def _get_nested(dictionary: dict[str, Any], path: str, default: Any = None) -> Any:
    """Get a value from a nested dict using dot-notation ('a.b.c')."""
    keys = path.split(".")
    target = dictionary
    for key in keys:
        if not isinstance(target, dict) or key not in target:
            return default
        target = target[key]
    return target


def generate_configurations(
    base_config: dict[str, Any],
    search_space: dict[str, list[Any]],
    strategy: str = "random",
    max_trials: int = 6,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate candidate configurations using either grid or random search."""
    if strategy not in ("grid", "random"):
        raise ValueError("strategy must be either 'grid' or 'random'.")
    if not isinstance(max_trials, int) or isinstance(max_trials, bool) or max_trials <= 0:
        raise ValueError("max_trials must be a positive integer.")

    keys = list(search_space.keys())
    value_lists = [search_space[k] for k in keys]

    all_combinations = list(itertools.product(*value_lists))

    if strategy == "random":
        rng = random.Random(seed)
        if len(all_combinations) > max_trials:
            sampled_combinations = rng.sample(all_combinations, max_trials)
        else:
            sampled_combinations = list(all_combinations)
            rng.shuffle(sampled_combinations)
    else:  # grid
        sampled_combinations = all_combinations[:max_trials]

    configs: list[dict[str, Any]] = []
    for combo in sampled_combinations:
        cfg = copy.deepcopy(base_config)
        for key, val in zip(keys, combo):
            _set_nested(cfg, key, val)
        configs.append(validate_config(cfg))

    return configs


def run_tuning_sweep(
    base_config: dict[str, Any] | None = None,
    search_space: dict[str, list[Any]] | None = None,
    episodes_per_trial: int = 500,
    max_trials: int = 6,
    strategy: str = "random",
    output_dir: str | Path | None = None,
    device: str = "cpu",
    seed: int = 42,
    num_nodes: int = 1,
    node_rank: int = 0,
    verbose: bool = True,
) -> dict[str, Any]:
    """Execute hyperparameter sweep across candidate trials and compile a ranked leaderboard."""
    if num_nodes < 1:
        raise ValueError("num_nodes must be a positive integer.")
    if not (0 <= node_rank < num_nodes):
        raise ValueError(f"node_rank must be in range [0, {num_nodes - 1}].")

    if base_config is None:
        base_config = load_config()
    else:
        base_config = validate_config(base_config)

    space = search_space if search_space is not None else DEFAULT_SEARCH_SPACE

    sweep_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = (
        Path(output_dir)
        if output_dir is not None
        else Path("data/experiments") / f"sweep_{sweep_timestamp}"
    )
    base_dir.mkdir(parents=True, exist_ok=True)

    # Prepare base config template
    template_config = copy.deepcopy(base_config)
    template_config["training"]["episodes"] = episodes_per_trial
    template_config["training"]["evaluation_interval"] = max(1, episodes_per_trial)
    template_config["training"]["evaluation_episodes"] = 25
    template_config["training"]["surveillance_interval"] = max(10, episodes_per_trial // 5)

    trial_configs = generate_configurations(
        template_config,
        space,
        strategy=strategy,
        max_trials=max_trials,
        seed=seed,
    )

    # Partition trials across nodes if distributed across multiple PCs
    if num_nodes > 1:
        indexed_configs = [
            (idx, cfg)
            for idx, cfg in enumerate(trial_configs, start=1)
            if (idx - 1) % num_nodes == node_rank
        ]
    else:
        indexed_configs = list(enumerate(trial_configs, start=1))

    if verbose:
        print("\n" + "=" * 72)
        print(" [AUTOMATED HYPERPARAMETER TUNING SWEEP]".center(72))
        print("=" * 72)
        print(f"  Total trials in sweep: {len(trial_configs)}")
        if num_nodes > 1:
            print(f"  Distributed Nodes:    {num_nodes} (This node rank: {node_rank})")
            assigned_ids = [idx for idx, _ in indexed_configs]
            print(f"  Trials on this node:  {len(indexed_configs)} {assigned_ids}")
        else:
            print(f"  Trials to evaluate:   {len(trial_configs)}")
        print(f"  Episodes per trial:   {episodes_per_trial:,}")
        print(f"  Strategy:             {strategy.upper()}")
        print(f"  Sweep Directory:      {base_dir}")
        print("=" * 72 + "\n")

    trial_results: list[dict[str, Any]] = []
    total_start = time.time()

    for idx, trial_config in indexed_configs:
        trial_dir = base_dir / f"trial_{idx:03d}"
        if verbose:
            print(f"\n--- [TRIAL {idx}/{len(trial_configs)}] ---")
            print(
                f"  LR: {trial_config['dqn']['learning_rate']} | "
                f"Gamma: {trial_config['dqn']['gamma']} | "
                f"TrainFreq: {trial_config['training']['train_frequency']} | "
                f"StepPenalty: {trial_config['reward']['step_penalty']} | "
                f"Workers: {trial_config['training']['num_workers']}"
            )

        trial_start = time.time()
        summary = train_dqn(
            trial_config,
            device=device,
            experiment_dir=trial_dir,
            verbose=verbose,
            surveillance_interval=trial_config["training"]["surveillance_interval"],
        )
        trial_time = time.time() - trial_start

        best_eval = summary.get("best_evaluation") or {}
        baseline = summary.get("random_baseline") or {}
        eval_score = best_eval.get("average_score", 0.0)
        baseline_score = baseline.get("average_score", 0.0)
        delta = eval_score - baseline_score

        record = {
            "trial": idx,
            "trial_dir": str(trial_dir),
            "run_dir": summary.get("model_path", ""),
            "learning_rate": trial_config["dqn"]["learning_rate"],
            "gamma": trial_config["dqn"]["gamma"],
            "train_frequency": trial_config["training"]["train_frequency"],
            "batch_size": trial_config["dqn"]["batch_size"],
            "step_penalty": trial_config["reward"]["step_penalty"],
            "score_per_point": trial_config["reward"]["score_per_point"],
            "num_workers": trial_config["training"]["num_workers"],
            "average_score": summary.get("average_score", 0.0),
            "best_score": summary.get("best_score", 0.0),
            "eval_average_score": eval_score,
            "baseline_score": baseline_score,
            "eval_score_delta": delta,
            "duration_seconds": round(trial_time, 2),
            "duration_formatted": format_duration(trial_time),
            "best_model_path": summary.get("best_model_path", summary.get("model_path", "")),
            "config": trial_config,
        }
        trial_results.append(record)

    total_duration = time.time() - total_start

    # Rank by eval_score_delta descending, then eval_average_score
    ranked_results = sorted(
        trial_results,
        key=lambda r: (r["eval_score_delta"], r["eval_average_score"]),
        reverse=True,
    )
    for rank, rec in enumerate(ranked_results, start=1):
        rec["rank"] = rank

    # Write leaderboard CSV & JSON
    leaderboard_csv = base_dir / "leaderboard.csv"
    leaderboard_json = base_dir / "leaderboard.json"

    fieldnames = [
        "rank",
        "trial",
        "eval_score_delta",
        "eval_average_score",
        "baseline_score",
        "average_score",
        "best_score",
        "learning_rate",
        "gamma",
        "train_frequency",
        "batch_size",
        "step_penalty",
        "score_per_point",
        "num_workers",
        "duration_formatted",
        "duration_seconds",
        "best_model_path",
    ]
    with leaderboard_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ranked_results)

    with leaderboard_json.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_duration_sec": round(total_duration, 2),
                "total_duration_formatted": format_duration(total_duration),
                "trials_evaluated": len(ranked_results),
                "leaderboard": ranked_results,
            },
            handle,
            indent=2,
        )

    winning_trial = ranked_results[0] if ranked_results else None

    if verbose:
        print_leaderboard(ranked_results, total_duration)

    return {
        "status": "completed",
        "sweep_dir": str(base_dir),
        "leaderboard_csv": str(leaderboard_csv),
        "leaderboard_json": str(leaderboard_json),
        "total_duration_sec": total_duration,
        "trials_evaluated": len(ranked_results),
        "winner": winning_trial,
        "ranked_results": ranked_results,
    }


def print_leaderboard(ranked_results: list[dict[str, Any]], total_duration: float) -> None:
    """Print an ASCII leaderboard table of evaluated configurations."""
    print("\n" + "=" * 90)
    print(" [HYPERPARAMETER TUNING LEADERBOARD]".center(90))
    print("=" * 90)
    header = (
        f"{'Rank':<5} {'Trial':<7} {'Delta':<8} {'EvalAvg':<8} {'BaseAvg':<8} "
        f"{'LR':<9} {'Gamma':<6} {'TFreq':<6} {'StepPen':<8} {'Duration':<10}"
    )
    print(header)
    print("-" * 90)

    for r in ranked_results:
        print(
            f"#{r['rank']:<4} "
            f"T{r['trial']:<6} "
            f"{r['eval_score_delta']:+6.2f}  "
            f"{r['eval_average_score']:6.2f}  "
            f"{r['baseline_score']:6.2f}  "
            f"{r['learning_rate']:<9.5f} "
            f"{r['gamma']:<6.2f} "
            f"{r['train_frequency']:<6d} "
            f"{r['step_penalty']:<8.4f} "
            f"{r['duration_formatted']:<10}"
        )
    print("=" * 90)
    if ranked_results:
        winner = ranked_results[0]
        print(
            f" 🏆 WINNER: Trial #{winner['trial']} with Eval Delta: {winner['eval_score_delta']:+.2f} "
            f"(Score: {winner['eval_average_score']:.2f} vs Random: {winner['baseline_score']:.2f})"
        )
        print(f" Best Weights: {winner['best_model_path']}")
        print(f" Total Sweep Time: {format_duration(total_duration)}")
    print("=" * 90 + "\n")


def build_tuning_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the automated tuning orchestrator."""
    parser = argparse.ArgumentParser(
        description="Run automated hyperparameter sweep and rank models for Five-or-More RL."
    )
    parser.add_argument(
        "--config",
        default=None,
        help="path to base JSON config template (default: config/config.json)",
    )
    parser.add_argument(
        "--episodes-per-trial",
        type=int,
        default=500,
        help="episodes to train per trial configuration (default: 500)",
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=6,
        help="maximum number of trials to run (default: 6)",
    )
    parser.add_argument(
        "--strategy",
        choices=["grid", "random"],
        default="random",
        help="search strategy: random or grid (default: random)",
    )
    parser.add_argument(
        "--lr",
        nargs="+",
        type=float,
        default=None,
        help="list of candidate learning rates to sweep",
    )
    parser.add_argument(
        "--train-freq",
        nargs="+",
        type=int,
        default=None,
        help="list of candidate training frequencies to sweep",
    )
    parser.add_argument(
        "--gamma",
        nargs="+",
        type=float,
        default=None,
        help="list of candidate discount factors to sweep",
    )
    parser.add_argument(
        "--step-penalty",
        nargs="+",
        type=float,
        default=None,
        help="list of candidate step penalties to sweep",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="override num_workers for all trials (default: from config)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to save the sweep runs and leaderboard",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="torch device (default: cpu)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for trial sampling (default: 42)",
    )
    parser.add_argument(
        "--num-nodes",
        type=int,
        default=1,
        help="total number of participating machines/nodes (default: 1)",
    )
    parser.add_argument(
        "--node-rank",
        type=int,
        default=0,
        help="zero-indexed rank of this machine in multi-PC sweep (0 to num_nodes - 1, default: 0)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress detailed per-episode output during trials",
    )
    parser.add_argument(
        "--use-ray",
        action="store_true",
        help="use distributed Ray actors for parallel environment rollouts across cluster",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_tuning_parser()
    args = parser.parse_args(argv)

    base_config = load_config(args.config)
    if args.workers is not None:
        base_config["training"]["num_workers"] = args.workers
    if args.use_ray:
        base_config["training"]["use_ray"] = True

    search_space = copy.deepcopy(DEFAULT_SEARCH_SPACE)
    if args.lr is not None:
        search_space["dqn.learning_rate"] = args.lr
    if args.train_freq is not None:
        search_space["training.train_frequency"] = args.train_freq
    if args.gamma is not None:
        search_space["dqn.gamma"] = args.gamma
    if args.step_penalty is not None:
        search_space["reward.step_penalty"] = args.step_penalty

    results = run_tuning_sweep(
        base_config=base_config,
        search_space=search_space,
        episodes_per_trial=args.episodes_per_trial,
        max_trials=args.max_trials,
        strategy=args.strategy,
        output_dir=args.output_dir,
        device=args.device,
        seed=args.seed,
        num_nodes=args.num_nodes,
        node_rank=args.node_rank,
        verbose=not args.quiet,
    )
    if args.quiet:
        print(f"Sweep complete. Leaderboard saved to: {results['leaderboard_csv']}")


if __name__ == "__main__":
    main()
