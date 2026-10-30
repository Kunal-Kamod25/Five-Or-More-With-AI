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
from .parallel_env import ParallelEnvManager
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

    torch_threads = training_config.get("torch_threads")
    if torch_threads is not None:
        torch.set_num_threads(int(torch_threads))

    train_frequency = int(training_config.get("train_frequency", 1))
    num_workers = int(training_config.get("num_workers", 1))

    if env is None and num_workers > 1:
        return _train_dqn_parallel(
            config=config,
            num_workers=num_workers,
            agent=agent,
            experiment_manager=experiment_manager,
            experiment_dir=experiment_dir,
            device=device,
            verbose=verbose,
        )

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
            last_action: int | None = None
            last_reward: float = 0.0

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

                avoid_actions = []
                if last_action is not None and last_reward <= 0.0:
                    src_idx, dst_idx = divmod(int(last_action), 81)
                    reverse_action = dst_idx * 81 + src_idx
                    avoid_actions.append(reverse_action)

                try:
                    action = agent.select_action(
                        state,
                        legal_actions,
                        epsilon=epsilon,
                        avoid_actions=avoid_actions if avoid_actions else None,
                    )
                except TypeError:
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

                environment_steps += 1
                episode_steps += 1
                total_reward += float(reward)
                final_done = bool(done)
                last_action = action
                last_reward = float(reward)

                update_result = {"updated": False, "loss": None}
                if environment_steps % train_frequency == 0:
                    update_result = agent.learn_step()

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


def _train_dqn_parallel(
    config: dict[str, Any],
    num_workers: int,
    agent: Any | None = None,
    experiment_manager: Any | None = None,
    experiment_dir: str | Path | None = None,
    device: torch.device | str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Train using parallel environment worker processes across CPU cores."""
    training_config = config["training"]
    exploration_config = config["exploration"]
    episodes = training_config["episodes"]
    max_steps_per_episode = training_config["max_steps_per_episode"]
    seed = training_config.get("seed")

    train_frequency = int(training_config.get("train_frequency", 1))

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

    last_action: list[int | None] = [None] * num_workers
    last_reward: list[float] = [0.0] * num_workers
    worker_episode_steps = [0] * num_workers
    worker_episode_reward = [0.0] * num_workers
    worker_episode_losses: list[list[float]] = [[] for _ in range(num_workers)]

    difficulty = config.get("environment", {}).get("difficulty", "Medium")

    with ParallelEnvManager(num_workers=num_workers, difficulty=difficulty, base_seed=seed) as parallel_envs:
        states, legal_actions_list = parallel_envs.reset()

        while len(scores) < episodes:
            epsilon = epsilon_after_steps(
                epsilon_start,
                epsilon_min,
                epsilon_decay,
                environment_steps,
            )
            final_epsilon = epsilon

            actions: list[int] = []
            for w in range(num_workers):
                legals = legal_actions_list[w]
                if not legals:
                    actions.append(0)
                    continue

                avoid_actions = []
                if last_action[w] is not None and last_reward[w] <= 0.0:
                    src_idx, dst_idx = divmod(int(last_action[w]), 81)
                    avoid_actions.append(dst_idx * 81 + src_idx)

                try:
                    act = agent.select_action(
                        states[w],
                        legals,
                        epsilon=epsilon,
                        avoid_actions=avoid_actions if avoid_actions else None,
                    )
                except TypeError:
                    act = agent.select_action(states[w], legals, epsilon=epsilon)

                if act is None:
                    act = legals[0]
                actions.append(act)

            step_results = parallel_envs.step(actions)

            for w, res in enumerate(step_results):
                agent.store_transition(
                    state=res["state"],
                    action=res["action"],
                    reward=res["reward"],
                    next_state=res["next_state"],
                    done=res["done"],
                    next_legal_actions=res["next_legal_actions"],
                )

                environment_steps += 1
                worker_episode_steps[w] += 1
                worker_episode_reward[w] += res["reward"]
                last_action[w] = res["action"]
                last_reward[w] = res["reward"]
                final_done = bool(res["done"])

                update_result = {"updated": False, "loss": None}
                if environment_steps % train_frequency == 0:
                    update_result = agent.learn_step()

                if update_result["updated"]:
                    optimizer_updates += 1
                    loss = update_result["loss"]
                    if loss is not None:
                        worker_episode_losses[w].append(float(loss))
                        all_losses.append(float(loss))
                    if optimizer_updates % target_update_frequency == 0:
                        agent.synchronize_target_network()

                is_done = res["done"] or worker_episode_steps[w] >= max_steps_per_episode
                if is_done and len(scores) < episodes:
                    ep_num = len(scores) + 1
                    score = res["score"]
                    scores.append(score)
                    rewards.append(worker_episode_reward[w])
                    episode_lengths.append(worker_episode_steps[w])
                    stop_reason = "environment_done" if res["done"] else "max_steps"
                    episode_stop_reasons.append(stop_reason)

                    ep_losses = worker_episode_losses[w]
                    experiment_manager.log_episode(
                        episode=ep_num,
                        score=score,
                        reward=worker_episode_reward[w],
                        steps=worker_episode_steps[w],
                        done=bool(res["done"]),
                        epsilon=epsilon,
                        loss=mean(ep_losses) if ep_losses else None,
                        average_score=mean(scores),
                        average_reward=mean(rewards),
                    )

                    if verbose:
                        loss_display = (
                            f"{mean(ep_losses):.4f}" if ep_losses else "N/A (buffer filling)"
                        )
                        print(
                            f"Episode {ep_num:4d}/{episodes} (Worker {w}) | "
                            f"Steps: {worker_episode_steps[w]:3d} | "
                            f"Score: {score:4.0f} | "
                            f"Reward: {worker_episode_reward[w]:6.2f} | "
                            f"Avg Reward: {mean(rewards):6.2f} | "
                            f"Loss: {loss_display} | "
                            f"Epsilon: {epsilon:.4f}"
                        )

                    worker_episode_steps[w] = 0
                    worker_episode_reward[w] = 0.0
                    worker_episode_losses[w] = []
                    last_action[w] = None
                    last_reward[w] = 0.0

            states = parallel_envs.current_states
            legal_actions_list = parallel_envs.current_legal_actions

    summary = {
        "status": "completed",
        "episodes": episodes,
        "final_score": scores[-1] if scores else 0.0,
        "average_score": mean(scores) if scores else 0.0,
        "best_score": max(scores) if scores else 0.0,
        "average_reward": mean(rewards) if rewards else 0.0,
        "best_reward": max(rewards) if rewards else 0.0,
        "average_episode_length": mean(episode_lengths) if episode_lengths else 0.0,
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
