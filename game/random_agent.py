"""Run random legal-action simulations through the headless environment."""

import argparse
import random
from statistics import mean

from .rl_environment import FiveOrMoreEnv


def play_random_game(env=None, rng=None):
    """Play one game by randomly choosing from the environment's valid actions.

    Returns per-game statistics. If a game reports no valid actions before
    returning ``done=True``, the simulation stops safely and records that
    outcome separately.
    """
    if env is None:
        env = FiveOrMoreEnv()
    if rng is None:
        rng = random

    env.reset()
    steps = 0
    total_reward = 0.0
    ended_normally = False
    stopped_no_valid_actions = False

    while True:
        valid_actions = env.get_valid_actions()
        if not valid_actions:
            stopped_no_valid_actions = True
            break

        action = rng.choice(valid_actions)
        _, reward, done, _ = env.step(action)
        steps += 1
        total_reward += reward
        if done:
            ended_normally = True
            break

    return {
        "score": env.game.get_score(),
        "steps": steps,
        "total_reward": total_reward,
        "game_over": ended_normally,
        "no_valid_actions": stopped_no_valid_actions,
    }


def run_random_games(
    num_games=1,
    difficulty="Medium",
    seed=None,
    verbose=True,
):
    """Run multiple games and print/return aggregate simulation statistics."""
    if not isinstance(num_games, int) or isinstance(num_games, bool):
        raise ValueError("num_games must be a positive integer.")
    if num_games <= 0:
        raise ValueError("num_games must be a positive integer.")

    rng = random.Random(seed)
    results = []
    for game_number in range(1, num_games + 1):
        result = play_random_game(
            env=FiveOrMoreEnv(difficulty=difficulty),
            rng=rng,
        )
        results.append(result)
        if verbose:
            status = (
                "game over"
                if result["game_over"]
                else "stopped: no valid actions"
            )
            print(
                f"Game {game_number} finished ({status}) - "
                f"Steps: {result['steps']}, "
                f"Final score: {result['score']}, "
                f"Total reward: {result['total_reward']:.2f}"
            )

    scores = [result["score"] for result in results]
    summary = {
        "games": num_games,
        "average_score": mean(scores),
        "maximum_score": max(scores),
        "minimum_score": min(scores),
        "average_steps": mean(result["steps"] for result in results),
        "average_total_reward": mean(
            result["total_reward"] for result in results
        ),
        "game_over_count": sum(result["game_over"] for result in results),
        "no_valid_actions_count": sum(
            result["no_valid_actions"] for result in results
        ),
    }

    print(
        f"\nGames: {summary['games']}\n"
        f"Average score: {summary['average_score']:.2f}\n"
        f"Maximum score: {summary['maximum_score']}\n"
        f"Minimum score: {summary['minimum_score']}\n"
        f"Average steps: {summary['average_steps']:.2f}\n"
        f"Average total reward: {summary['average_total_reward']:.2f}\n"
        f"Games reaching game-over normally: {summary['game_over_count']}\n"
        "Games stopped for no valid actions: "
        f"{summary['no_valid_actions_count']}"
    )
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Simulate Five-or-More games using random legal moves."
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1,
        help="number of complete games to simulate (default: 1)",
    )
    parser.add_argument(
        "--difficulty",
        choices=("Easy", "Medium", "Hard"),
        default="Medium",
        help="game difficulty (default: Medium)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="optional seed for repeatable random action selection",
    )
    arguments = parser.parse_args()
    run_random_games(
        num_games=arguments.games,
        difficulty=arguments.difficulty,
        seed=arguments.seed,
    )


if __name__ == "__main__":
    main()
