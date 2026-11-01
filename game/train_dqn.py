"""Backward-compatible launcher for DQN training."""

from .rl.train_dqn import epsilon_after_steps, main, train_dqn

__all__ = ["epsilon_after_steps", "main", "train_dqn"]


if __name__ == "__main__":
    main()
