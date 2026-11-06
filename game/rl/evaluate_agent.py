"""Evaluate a trained DQN model checkpoint over benchmark episodes."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable

import torch

from config.config_loader import load_config, validate_config
from .dqn_agent import DQNAgent
from .rl_environment import FiveOrMoreEnv


def find_latest_checkpoint(base_dir: str | Path = "data/experiments") -> Path | None:
    """Find the most recent experiment model checkpoint."""
    experiments_path = Path(base_dir)
    if not experiments_path.is_absolute() and not experiments_path.exists():
        project_root = Path(__file__).resolve().parent.parent.parent
        alt_path = project_root / base_dir
        if alt_path.exists():
            experiments_path = alt_path
        else:
            return None
    elif not experiments_path.exists():
        return None

    run_dirs = [
        d for d in experiments_path.iterdir()
        if d.is_dir() and d.name.startswith("run_")
    ]
    if not run_dirs:
        return None

    def run_number(path: Path) -> int:
        suffix = path.name.split("run_", 1)[1]
        return int(suffix) if suffix.isdigit() else 0

    sorted_runs = sorted(run_dirs, key=run_number, reverse=True)
    for run in sorted_runs:
        for filename in ("best_model.pth", "model.pth"):
            candidate = run / filename
            if candidate.exists():
                return candidate
    return None


def evaluate_policy(
    agent: DQNAgent | None,
    episodes: int,
    config: dict[str, Any],
    *,
    seed: int | None = 42,
    max_steps: int | None = None,
    progress_callback: Callable[[int, float, float, int], None] | None = None,
) -> dict[str, Any]:
    """Evaluate a greedy DQN or random legal-action policy on repeatable games."""
    if not isinstance(episodes, int) or isinstance(episodes, bool) or episodes <= 0:
        raise ValueError("episodes must be a positive integer.")
    config = validate_config(config)
    if max_steps is None:
        max_steps = config["training"]["max_steps_per_episode"]
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer.")

    reward_config = config["reward"]
    env = FiveOrMoreEnv(
        difficulty=config["environment"]["difficulty"],
        invalid_action_reward=reward_config["invalid_action"],
        score_per_point=reward_config["score_per_point"],
        step_penalty=reward_config["step_penalty"],
        game_over_penalty=reward_config["game_over_penalty"],
        line_rewards=reward_config.get("line_rewards"),
        same_color_connection_reward=reward_config.get(
            "same_color_connection_reward",
            FiveOrMoreEnv.SAME_COLOR_CONNECTION_REWARD,
        ),
        same_color_disconnection_penalty=reward_config.get(
            "same_color_disconnection_penalty",
            FiveOrMoreEnv.SAME_COLOR_DISCONNECTION_PENALTY,
        ),
    )
    policy_rng = random.Random(seed)
    previous_random_state = random.getstate()
    network_was_training = (
        agent.online_network.training if agent is not None else False
    )
    if agent is not None:
        agent.online_network.eval()

    scores: list[float] = []
    rewards: list[float] = []
    episode_lengths: list[int] = []
    completed_games: list[bool] = []
    try:
        for episode in range(episodes):
            if seed is not None:
                random.seed(seed + episode)
            state = env.reset()
            total_reward = 0.0
            steps = 0
            done = False

            while not done and steps < max_steps:
                valid_actions = env.get_valid_actions()
                if not valid_actions:
                    break
                if agent is None:
                    action = policy_rng.choice(valid_actions)
                else:
                    action = agent.select_action(state, valid_actions, epsilon=0.0)
                if action is None or action not in valid_actions:
                    raise RuntimeError("Evaluation policy returned an illegal action.")

                state, reward, done, _ = env.step(action)
                steps += 1
                total_reward += float(reward)

            scores.append(float(env.game.get_score()))
            rewards.append(total_reward)
            episode_lengths.append(steps)
            completed_games.append(bool(done))
            if progress_callback is not None:
                progress_callback(episode + 1, scores[-1], mean(scores), steps)
    finally:
        random.setstate(previous_random_state)
        if agent is not None:
            agent.online_network.train(network_was_training)

    return {
        "policy": "dqn" if agent is not None else "random_legal",
        "seed": seed,
        "episodes": episodes,
        "difficulty": config["environment"]["difficulty"],
        "average_score": mean(scores),
        "median_score": median(scores),
        "best_score": max(scores),
        "min_score": min(scores),
        "average_reward": mean(rewards),
        "average_steps": mean(episode_lengths),
        "game_over_count": sum(completed_games),
        "truncated_count": episodes - sum(completed_games),
    }


def benchmark_agent(
    agent: DQNAgent,
    episodes: int,
    config: dict[str, Any],
    *,
    seed: int | None = 42,
    progress_callback: Callable[[int, float, float, int], None] | None = None,
) -> dict[str, Any]:
    """Compare a greedy DQN against random legal play on identical game seeds."""
    dqn_results = evaluate_policy(
        agent,
        episodes,
        config,
        seed=seed,
        progress_callback=progress_callback,
    )
    baseline_results = evaluate_policy(None, episodes, config, seed=seed)
    return {
        "dqn": dqn_results,
        "random_baseline": baseline_results,
        "average_score_delta": (
            dqn_results["average_score"] - baseline_results["average_score"]
        ),
    }


def evaluate_agent(
    model_path: str | Path | None = None,
    episodes: int = 1000,
    *,
    config: dict[str, Any] | None = None,
    device: torch.device | str = "cpu",
    seed: int | None = 42,
    verbose: bool = True,
    log_interval: int = 100,
    compare_random: bool = True,
) -> dict[str, Any]:
    """Run greedy evaluation (epsilon=0) of a trained DQN model."""
    if model_path is None:
        model_path = find_latest_checkpoint()
        if model_path is None:
            raise FileNotFoundError(
                "No trained checkpoint found in data/experiments/. "
                "Please specify --model <path>."
            )

    model_file = Path(model_path)
    if not model_file.is_absolute() and not model_file.exists():
        project_root = Path(__file__).resolve().parent.parent.parent
        alt_path = project_root / model_path
        if alt_path.exists():
            model_file = alt_path
    if not model_file.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {model_file}")
    if not isinstance(log_interval, int) or isinstance(log_interval, bool) or log_interval <= 0:
        raise ValueError("log_interval must be a positive integer.")

    checkpoint = torch.load(model_file, map_location=device, weights_only=False)
    if config is None:
        config = checkpoint.get("config")
        if config is None:
            config = load_config()
    config = validate_config(config)
    agent = DQNAgent(config, device=device)
    state_dict = checkpoint.get("online_state_dict", checkpoint)
    agent.online_network.load_state_dict(state_dict)
    def report_progress(episode: int, score: float, average_score: float, steps: int) -> None:
        if verbose and (
            episode <= 10 or episode % log_interval == 0 or episode == episodes
        ):
            print(
                f"Episode {episode:5d}/{episodes} | Steps: {steps:3d} | "
                f"Score: {score:4.0f} | Average score: {average_score:7.2f}"
            )

    if compare_random:
        benchmark = benchmark_agent(
            agent,
            episodes,
            config,
            seed=seed,
            progress_callback=report_progress,
        )
        summary = {
            **benchmark["dqn"],
            "model_path": str(model_file),
            "random_baseline": benchmark["random_baseline"],
            "average_score_delta": benchmark["average_score_delta"],
        }
    else:
        summary = {
            **evaluate_policy(
                agent,
                episodes,
                config,
                seed=seed,
                progress_callback=report_progress,
            ),
            "model_path": str(model_file),
        }

    summary["status"] = "evaluation_completed"
    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Evaluation on {episodes} fixed-seed episodes")
        print(f"Model Checkpoint: {model_file}")
        print(f"{'=' * 60}\n")
        print(f"Average score: {summary['average_score']:.2f}")
        print(f"Median score:  {summary['median_score']:.2f}")
        print(f"Best score:    {summary['best_score']:.0f}")
        print(f"Average steps: {summary['average_steps']:.1f}")
        print(f"Average reward:{summary['average_reward']:6.2f}")
        if compare_random:
            print(
                f"Random baseline: {summary['random_baseline']['average_score']:.2f} "
                f"(delta {summary['average_score_delta']:+.2f})"
            )
        print(f"{'=' * 60}\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a trained Five-or-More DQN agent using greedy action selection."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="path to model checkpoint (default: latest best checkpoint in data/experiments)",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1000,
        help="number of evaluation episodes (default: 1000)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="torch device: 'cpu' or 'cuda' (default: cpu)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="seed for repeatable evaluation games (default: 42)",
    )
    parser.add_argument(
        "--log-interval",
        type=int,
        default=500,
        help="frequency of printing progress (default: every 500 episodes)",
    )
    arguments = parser.parse_args()

    evaluate_agent(
        model_path=arguments.model,
        episodes=arguments.episodes,
        device=arguments.device,
        seed=arguments.seed,
        log_interval=arguments.log_interval,
    )


if __name__ == "__main__":
    main()
