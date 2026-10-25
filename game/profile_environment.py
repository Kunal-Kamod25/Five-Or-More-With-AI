"""Measure headless environment performance without changing game behavior.

Example:
    python -m game.profile_environment --games 5 --difficulty Easy
"""

import argparse
import random
import time
from contextlib import contextmanager
from statistics import mean

from .game import Game
from .movement import PieceMover
from .random_agent import play_random_game
from .rl_environment import FiveOrMoreEnv


class EnvironmentProfiler:
    """Temporarily time environment and pathfinding calls."""

    def __init__(self):
        self.metrics = None
        self.inside_step = False

    @contextmanager
    def instrument(self):
        originals = {
            (FiveOrMoreEnv, "get_valid_actions"):
                FiveOrMoreEnv.get_valid_actions,
            (FiveOrMoreEnv, "step"): FiveOrMoreEnv.step,
            (Game, "find_path"): Game.find_path,
            (PieceMover, "find_path"): PieceMover.find_path,
        }

        def timed_get_valid_actions(env):
            start = time.perf_counter()
            try:
                actions = originals[(FiveOrMoreEnv, "get_valid_actions")](env)
            finally:
                elapsed = time.perf_counter() - start
                self.metrics["get_valid_actions_calls"] += 1
                self.metrics["get_valid_actions_seconds"] += elapsed
                if self.inside_step:
                    self.metrics["nested_valid_actions_calls"] += 1
                    self.metrics["nested_valid_actions_seconds"] += elapsed
            if not self.inside_step:
                self.metrics["states_queried"] += 1
                self.metrics["valid_actions_per_state_total"] += len(actions)
            return actions

        def timed_step(env, action):
            start = time.perf_counter()
            self.inside_step = True
            try:
                return originals[(FiveOrMoreEnv, "step")](env, action)
            finally:
                self.inside_step = False
                self.metrics["step_calls"] += 1
                self.metrics["step_seconds"] += time.perf_counter() - start

        def timed_game_find_path(game, *args, **kwargs):
            start = time.perf_counter()
            try:
                return originals[(Game, "find_path")](game, *args, **kwargs)
            finally:
                self.metrics["game_find_path_calls"] += 1
                self.metrics["game_find_path_seconds"] += (
                    time.perf_counter() - start
                )

        def timed_astar_find_path(mover, *args, **kwargs):
            start = time.perf_counter()
            try:
                return originals[(PieceMover, "find_path")](
                    mover,
                    *args,
                    **kwargs,
                )
            finally:
                self.metrics["astar_calls"] += 1
                self.metrics["astar_seconds"] += time.perf_counter() - start

        FiveOrMoreEnv.get_valid_actions = timed_get_valid_actions
        FiveOrMoreEnv.step = timed_step
        Game.find_path = timed_game_find_path
        PieceMover.find_path = timed_astar_find_path
        try:
            yield
        finally:
            for (owner, name), method in originals.items():
                setattr(owner, name, method)

    def new_game_metrics(self):
        self.metrics = {
            "get_valid_actions_calls": 0,
            "get_valid_actions_seconds": 0.0,
            "nested_valid_actions_calls": 0,
            "nested_valid_actions_seconds": 0.0,
            "states_queried": 0,
            "valid_actions_per_state_total": 0,
            "step_calls": 0,
            "step_seconds": 0.0,
            "game_find_path_calls": 0,
            "game_find_path_seconds": 0.0,
            "astar_calls": 0,
            "astar_seconds": 0.0,
        }
        self.inside_step = False
        return self.metrics


def profile_games(num_games=3, difficulty="Easy", seed=None):
    """Run random games and print average timings and projected run times."""
    if not isinstance(num_games, int) or isinstance(num_games, bool):
        raise ValueError("num_games must be a positive integer.")
    if num_games <= 0:
        raise ValueError("num_games must be a positive integer.")
    if difficulty not in Game.DIFFICULTY_SPAWN_AMOUNTS:
        raise ValueError("difficulty must be Easy, Medium, or Hard.")

    profiler = EnvironmentProfiler()
    rng = random.Random(seed)
    game_results = []
    with profiler.instrument():
        for game_number in range(1, num_games + 1):
            metrics = profiler.new_game_metrics()
            env = FiveOrMoreEnv(difficulty=difficulty)
            start = time.perf_counter()
            result = play_random_game(env=env, rng=rng)
            elapsed = time.perf_counter() - start
            game_results.append(
                {
                    "elapsed_seconds": elapsed,
                    "steps": result["steps"],
                    **metrics,
                }
            )
            print(
                f"Game {game_number}: {result['steps']} steps, "
                f"{result['score']} points, {elapsed:.2f} seconds"
            )

    average_game_seconds = mean(
        game["elapsed_seconds"] for game in game_results
    )
    average_steps = mean(game["steps"] for game in game_results)
    average_valid_actions = (
        sum(game["valid_actions_per_state_total"] for game in game_results)
        / sum(game["states_queried"] for game in game_results)
    )
    average_values = {
        key: mean(game[key] for game in game_results)
        for key in (
            "get_valid_actions_seconds",
            "nested_valid_actions_seconds",
            "step_seconds",
            "game_find_path_calls",
            "game_find_path_seconds",
            "astar_calls",
            "astar_seconds",
        )
    }

    print(f"\nGames: {num_games}")
    print(f"Difficulty: {difficulty}")
    print(f"Average game time: {average_game_seconds:.2f} seconds")
    print(f"Average steps/game: {average_steps:.1f}")
    print(
        "Average get_valid_actions time: "
        f"{average_values['get_valid_actions_seconds']:.2f} seconds/game "
        f"(includes {average_values['nested_valid_actions_seconds']:.2f}s "
        "called from step)"
    )
    print(
        "Average step time: "
        f"{average_values['step_seconds']:.2f} seconds/game "
        "(inclusive of the nested legal-action validation)"
    )
    print(f"Average valid actions/state: {average_valid_actions:.1f}")
    print(
        "Average Game.find_path calls/game: "
        f"{average_values['game_find_path_calls']:.0f}"
    )
    print(
        "Average Game.find_path time/game: "
        f"{average_values['game_find_path_seconds']:.2f} seconds"
    )
    print(
        "Average A* calls/game (including actual move validation): "
        f"{average_values['astar_calls']:.0f}"
    )
    print(
        "Average A* time/game: "
        f"{average_values['astar_seconds']:.2f} seconds"
    )
    print(
        "Approximate projected runtime at this average: "
        f"100 games = {average_game_seconds * 100 / 60:.1f} minutes; "
        f"1,000 games = {average_game_seconds * 1000 / 3600:.2f} hours; "
        f"10,000 games = {average_game_seconds * 10000 / 3600:.1f} hours"
    )

    return game_results


def main():
    parser = argparse.ArgumentParser(
        description="Profile complete random games in the headless environment."
    )
    parser.add_argument("--games", type=int, default=3)
    parser.add_argument(
        "--difficulty",
        choices=tuple(Game.DIFFICULTY_SPAWN_AMOUNTS),
        default="Easy",
    )
    parser.add_argument("--seed", type=int, default=17)
    arguments = parser.parse_args()
    profile_games(
        num_games=arguments.games,
        difficulty=arguments.difficulty,
        seed=arguments.seed,
    )


if __name__ == "__main__":
    main()
