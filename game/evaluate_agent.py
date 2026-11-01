"""Backward-compatible launcher for agent evaluation."""

from .rl.evaluate_agent import evaluate_agent, main

__all__ = ["evaluate_agent", "main"]


if __name__ == "__main__":
    main()
