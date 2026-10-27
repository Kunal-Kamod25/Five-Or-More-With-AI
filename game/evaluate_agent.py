"""Evaluate a trained DQN model checkpoint over benchmark episodes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

import torch

from config.config_loader import load_config
from .dqn_agent import DQNAgent
from .rl_environment import FiveOrMoreEnv


def find_latest_checkpoint(base_dir: str | Path = "data/experiments") -> Path | None:
    """Find the most recent experiment model checkpoint."""
    experiments_path = Path(base_dir)
    if not experiments_path.exists():
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
        candidate = run / "model.pth"
        if candidate.exists():
            return candidate
    return None


def evaluate_agent(
    model_path: str | Path | None = None,
    episodes: int = 1000,
    *,
    config: dict[str, Any] | None = None,
    device: torch.device | str = "cpu",
    seed: int | None = 42,
    verbose: bool = True,
    log_interval: int = 100,
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
    if not model_file.exists():
        raise FileNotFoundError(f"Model checkpoint not found at: {model_file}")

    config = load_config() if config is None else config
    env = FiveOrMoreEnv(difficulty=config["environment"]["difficulty"])
    agent = DQNAgent(config, device=device)

    # Load checkpoint
    checkpoint = torch.load(model_file, map_location=device, weights_only=False)
    state_dict = checkpoint.get("online_state_dict", checkpoint)
    agent.online_network.load_state_dict(state_dict)
    agent.online_network.eval()

    scores: list[float] = []
    rewards: list[float] = []
    episode_lengths: list[int] = []

    print(f"\n{'=' * 60}")
    print(f"Starting Evaluation on {episodes} episodes (Greedy Policy: Epsilon=0.0)")
    print(f"Model Checkpoint: {model_file}")
    print(f"{'=' * 60}\n")

    for ep in range(1, episodes + 1):
        state = env.reset()
        total_reward = 0.0
        steps = 0
        done = False

        while not done:
            valid_actions = env.get_valid_actions()
            if not valid_actions:
                break

            action = agent.select_action(state, valid_actions, epsilon=0.0)
            if action is None:
                break

            next_state, reward, done, _ = env.step(action)
            steps += 1
            total_reward += float(reward)
            state = next_state

        score = float(env.game.get_score())
        scores.append(score)
        rewards.append(total_reward)
        episode_lengths.append(steps)

        if verbose and (ep % log_interval == 0 or ep == episodes or ep <= 10):
            print(
                f"Eval Episode {ep:6d}/{episodes} | "
                f"Steps: {steps:3d} | "
                f"Score: {score:4.0f} | "
                f"Avg Score: {mean(scores):6.2f} | "
                f"Max Score: {max(scores):4.0f} | "
                f"Avg Reward: {mean(rewards):6.2f}"
            )

    summary = {
        "status": "evaluation_completed",
        "model_path": str(model_file),
        "episodes": episodes,
        "average_score": mean(scores),
        "best_score": max(scores),
        "min_score": min(scores),
        "average_reward": mean(rewards),
        "average_steps": mean(episode_lengths),
    }

    print(f"\n{'=' * 60}")
    print("Evaluation Results Summary:")
    print(f"  Episodes Evaluated: {episodes}")
    print(f"  Average Score:      {summary['average_score']:.2f}")
    print(f"  Best Score:         {summary['best_score']:.0f}")
    print(f"  Average Steps:      {summary['average_steps']:.1f}")
    print(f"  Average Reward:     {summary['average_reward']:.2f}")
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
        help="path to model.pth checkpoint (default: latest in data/experiments)",
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
        log_interval=arguments.log_interval,
    )


if __name__ == "__main__":
    main()
