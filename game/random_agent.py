"""Backward-compatible launcher for random-agent simulations."""

from .rl.random_agent import main, play_random_game, run_random_games

__all__ = ["main", "play_random_game", "run_random_games"]


if __name__ == "__main__":
    main()
