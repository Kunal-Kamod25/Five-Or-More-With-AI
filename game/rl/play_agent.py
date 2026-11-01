"""Watch a trained DQN agent play a game in the Pygame window."""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

import pygame
import torch

from config.config_loader import load_config, validate_config
from ..ui.renderer import GameRenderer
from .dqn_agent import DQNAgent
from .evaluate_agent import find_latest_checkpoint
from .rl_environment import FiveOrMoreEnv


def play_agent(
    model_path: str | Path | None = None,
    *,
    device: torch.device | str = "cpu",
    delay_ms: int = 350,
    seed: int | None = 42,
) -> None:
    """Run one visual game; Space pauses, R restarts, and Escape quits."""
    if not isinstance(delay_ms, int) or isinstance(delay_ms, bool) or delay_ms < 0:
        raise ValueError("delay_ms must be a non-negative integer.")
    if model_path is None:
        model_path = find_latest_checkpoint()
        if model_path is None:
            raise FileNotFoundError(
                "No trained checkpoint found in data/experiments/. "
                "Train an agent or pass --model <path>."
            )
    checkpoint_path = Path(model_path)
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")

    checkpoint: dict[str, Any] = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )
    config = checkpoint.get("config")
    if config is None:
        config = load_config()
    config = validate_config(config)
    agent = DQNAgent(config, device=device)
    agent.online_network.load_state_dict(
        checkpoint.get("online_state_dict", checkpoint)
    )
    agent.online_network.eval()

    if seed is not None:
        random.seed(seed)
    reward_config = config["reward"]
    env = FiveOrMoreEnv(
        difficulty=config["environment"]["difficulty"],
        invalid_action_reward=reward_config["invalid_action"],
        score_per_point=reward_config["score_per_point"],
        step_penalty=reward_config["step_penalty"],
        game_over_penalty=reward_config["game_over_penalty"],
    )
    env.reset()
    renderer = GameRenderer(env.game)

    pygame.init()
    try:
        screen = pygame.display.set_mode(renderer.window_size)
        pygame.display.set_caption(
            "Five-or-More AI | Space: pause | R: restart | Esc: quit"
        )
        clock = pygame.time.Clock()
        paused = False
        game_over = False
        last_step = 0
        running = True

        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and not game_over:
                        paused = not paused
                    elif event.key == pygame.K_r:
                        env.reset()
                        game_over = False
                        paused = False
                        last_step = now

            if running and not paused and not game_over and now - last_step >= delay_ms:
                legal_actions = env.get_valid_actions()
                if not legal_actions:
                    game_over = True
                else:
                    action = agent.select_action(
                        env.get_state(),
                        legal_actions,
                        epsilon=0.0,
                    )
                    if action is None:
                        raise RuntimeError("The agent failed to choose a legal action.")
                    _, _, game_over, _ = env.step(action)
                last_step = now

            renderer.draw(screen)
            if game_over:
                renderer.draw_game_over(screen)
            pygame.display.flip()
            clock.tick(60)
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch a trained Five-or-More DQN agent play."
    )
    parser.add_argument("--model", default=None, help="checkpoint path (defaults to best run)")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--delay-ms", type=int, default=350)
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    play_agent(
        model_path=arguments.model,
        device=arguments.device,
        delay_ms=arguments.delay_ms,
        seed=arguments.seed,
    )


if __name__ == "__main__":
    main()
