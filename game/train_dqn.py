"""Episode-based training runner for the existing Five-or-More DQN components."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from statistics import mean
from typing import Any

import torch

from config.config_loader import load_config, validate_config
from experiment_manager import ExperimentManager
from .dqn_agent import DQNAgent
from .rl_environment import FiveOrMoreEnv


def epsilon_after_steps(
    epsilon_start: float,
    epsilon_min: float,
    epsilon_decay: float,
    environment_steps: int,
) -> float:
    """Apply the configured multiplicative decay once per environment step."""
    return max(epsilon_min, epsilon_start * epsilon_decay**environment_steps)


def train_dqn(
    config: dict[str, Any] | None = None,
    *,
    env: Any | None = None,
    agent: Any | None = None,
    experiment_manager: Any | None = None,
    experiment_dir: str | Path | None = None,
    device: torch.device | str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Train for the configured episode count and persist metrics/checkpoint."""
    config = load_config() if config is None else validate_config(config)
    training_config = config["training"]
    exploration_config = config["exploration"]
    episodes = training_config["episodes"]
    max_steps_per_episode = training_config["max_steps_per_episode"]
    seed = training_config.get("seed")

    if env is None:
        env = FiveOrMoreEnv(difficulty=config["environment"]["difficulty"])
    if agent is None:
        agent = DQNAgent(config, device=device)
    if experiment_manager is None:
        experiment_manager = ExperimentManager(config, base_dir=experiment_dir)

    epsilon_start = float(exploration_config["epsilon_start"])
    epsilon_min = float(exploration_config["epsilon_min"])
    epsilon_decay = float(exploration_config["epsilon_decay"])
    target_update_frequency = config["dqn"]["target_update_frequency"]

    environment_steps = 0
    optimizer_updates = 0
    scores: list[float] = []
    rewards: list[float] = []
    episode_lengths: list[int] = []
    all_losses: list[float] = []
    episode_stop_reasons: list[str] = []
    final_epsilon = epsilon_start
    final_done = False

    previous_random_state = random.getstate()
    if seed is not None:
        random.seed(seed)
    try:
        for episode_number in range(1, episodes + 1):
            state = env.reset()
            episode_epsilon = epsilon_after_steps(
                epsilon_start,
                epsilon_min,
                epsilon_decay,
                environment_steps,
            )
            final_epsilon = episode_epsilon
            total_reward = 0.0
            episode_steps = 0
            episode_losses: list[float] = []
            done = False
            stop_reason = "max_steps"

            while episode_steps < max_steps_per_episode:
                legal_actions = env.get_valid_actions()
                if not legal_actions:
                    stop_reason = "no_legal_actions"
                    break

                epsilon = epsilon_after_steps(
                    epsilon_start,
                    epsilon_min,
                    epsilon_decay,
                    environment_steps,
                )
                action = agent.select_action(state, legal_actions, epsilon=epsilon)
                if action is None:
                    stop_reason = "no_legal_actions"
                    break
                if action not in legal_actions:
                    raise RuntimeError(
                        "DQN agent selected an action outside the current legal-action list."
                    )

                next_state, reward, done, _info = env.step(action)
                next_legal_actions = [] if done else env.get_valid_actions()
                agent.store_transition(
                    state=state,
                    action=action,
                    reward=reward,
                    next_state=next_state,
                    done=done,
                    next_legal_actions=next_legal_actions,
                )

                update_result = agent.learn_step()
                environment_steps += 1
                episode_steps += 1
                total_reward += float(reward)
                final_done = bool(done)

                if update_result["updated"]:
                    optimizer_updates += 1
                    loss = update_result["loss"]
                    if loss is not None:
                        episode_losses.append(float(loss))
                        all_losses.append(float(loss))
                    if optimizer_updates % target_update_frequency == 0:
                        agent.synchronize_target_network()

                state = next_state
                if done:
                    stop_reason = "environment_done"
                    break
                if not next_legal_actions:
                    stop_reason = "no_legal_actions"
                    break
            else:
                stop_reason = "max_steps"

            score = float(env.game.get_score())
            scores.append(score)
            rewards.append(total_reward)
            episode_lengths.append(episode_steps)
            episode_stop_reasons.append(stop_reason)
            final_epsilon = epsilon_after_steps(
                epsilon_start,
                epsilon_min,
                epsilon_decay,
                environment_steps,
            )

            experiment_manager.log_episode(
                episode=episode_number,
                score=score,
                reward=total_reward,
                steps=episode_steps,
                done=bool(done),
                epsilon=episode_epsilon,
                loss=mean(episode_losses) if episode_losses else None,
                average_score=mean(scores),
                average_reward=mean(rewards),
            )
            if verbose:
                loss_display = (
                    f"{mean(episode_losses):.4f}"
                    if episode_losses
                    else "N/A (buffer filling)"
                )
                print(
                    f"Episode {episode_number:4d}/{episodes} | "
                    f"Steps: {episode_steps:3d} | "
                    f"Score: {score:4.0f} | "
                    f"Reward: {total_reward:6.2f} | "
                    f"Avg Reward: {mean(rewards):6.2f} | "
                    f"Loss: {loss_display} | "
                    f"Epsilon: {episode_epsilon:.4f}"
                )
    finally:
        random.setstate(previous_random_state)

    summary = {
        "status": "completed",
        "episodes": episodes,
        "final_score": scores[-1],
        "average_score": mean(scores),
        "best_score": max(scores),
        "average_reward": mean(rewards),
        "best_reward": max(rewards),
        "average_episode_length": mean(episode_lengths),
        "final_epsilon": final_epsilon,
        "average_loss": mean(all_losses) if all_losses else None,
        "environment_steps": environment_steps,
        "optimizer_updates": optimizer_updates,
        "final_done": final_done,
        "episode_stop_reasons": episode_stop_reasons,
        "model_path": str(experiment_manager.model_path),
    }

    model_state = {
        key: value.detach().cpu().clone()
        for key, value in agent.online_network.state_dict().items()
    }
    torch.save(
        {
            "online_state_dict": model_state,
            "optimizer_state_dict": agent.optimizer.state_dict(),
            "run_id": experiment_manager.run_id,
            "config": config,
            "environment_steps": environment_steps,
            "optimizer_updates": optimizer_updates,
            "final_epsilon": final_epsilon,
        },
        experiment_manager.model_path,
    )
    experiment_manager.save_results(**summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train the Five-or-More DQN agent using the configured episode count."
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=None,
        help="override the configured episode count",
    )
    parser.add_argument("--device", default="cpu", help="torch device (default: cpu)")
    parser.add_argument(
        "--experiment-dir",
        default=None,
        help="optional base directory for experiment runs",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress live per-episode progress output",
    )
    arguments = parser.parse_args()
    config = load_config()
    if arguments.episodes is not None:
        config["training"]["episodes"] = arguments.episodes
        config = validate_config(config)
    summary = train_dqn(
        config,
        device=arguments.device,
        experiment_dir=arguments.experiment_dir,
        verbose=not arguments.quiet,
    )
    print(summary)


if __name__ == "__main__":
    main()
