"""Backward-compatible launcher for DQN training."""

from .rl.train_dqn import (
    apply_cli_overrides,
    build_parser,
    epsilon_after_steps,
    main,
    train_dqn,
)

__all__ = [
    "apply_cli_overrides",
    "build_parser",
    "epsilon_after_steps",
    "main",
    "train_dqn",
]


if __name__ == "__main__":
    main()
