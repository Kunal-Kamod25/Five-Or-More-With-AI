"""Backward-compatible launcher for environment profiling."""

from .rl.profile_environment import main, profile_games

__all__ = ["main", "profile_games"]


if __name__ == "__main__":
    main()
