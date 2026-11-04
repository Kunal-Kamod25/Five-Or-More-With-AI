"""Watch a trained DQN agent play a game in the Pygame window with interactive difficulty selection."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path so the module can be run directly from any directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pygame
import torch

from config.config_loader import load_config, validate_config

try:
    from ..ui.renderer import GameRenderer
except (ImportError, ValueError):
    from game.ui.renderer import GameRenderer

try:
    from .dqn_agent import DQNAgent
    from .evaluate_agent import find_latest_checkpoint
    from .rl_environment import FiveOrMoreEnv
except (ImportError, ValueError):
    from game.rl.dqn_agent import DQNAgent
    from game.rl.evaluate_agent import find_latest_checkpoint
    from game.rl.rl_environment import FiveOrMoreEnv


def _is_history_button_click(renderer: Any, pos: tuple[int, int]) -> bool:
    try:
        rect = renderer.gameplay_button_rect("history")
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


def _is_drawer_close_click(renderer: Any, pos: tuple[int, int]) -> bool:
    try:
        rect = renderer.drawer_close_button_rect()
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


def _is_inside_drawer(renderer: Any, pos: tuple[int, int], drawer_progress: float) -> bool:
    try:
        rect = renderer.drawer_rect(drawer_progress)
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


def _create_env(chosen_difficulty: str, reward_config: dict[str, Any]) -> FiveOrMoreEnv:
    return FiveOrMoreEnv(
        difficulty=chosen_difficulty,
        invalid_action_reward=reward_config["invalid_action"],
        score_per_point=reward_config["score_per_point"],
        step_penalty=reward_config["step_penalty"],
        game_over_penalty=reward_config["game_over_penalty"],
        line_rewards=reward_config.get("line_rewards"),
    )


def play_agent(
    model_path: str | Path | None = None,
    *,
    device: torch.device | str = "cpu",
    delay_ms: int = 1200,
    seed: int | None = 42,
    difficulty: str | None = None,
) -> None:
    """Run interactive visual game: prompts for difficulty first, then animates slow, clear AI moves."""
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
    if not checkpoint_path.is_absolute() and not checkpoint_path.is_file():
        alt_path = _PROJECT_ROOT / checkpoint_path
        if alt_path.is_file():
            checkpoint_path = alt_path
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

    # If difficulty is not explicitly passed via CLI, start in MENU state to ask the user
    show_menu = difficulty is None
    chosen_difficulty = difficulty or "Easy"
    app_state = "MENU" if show_menu else "PLAYING"

    env = _create_env(chosen_difficulty, reward_config)
    env.reset()
    renderer = GameRenderer(env.game)

    # Slow, deliberate, and clear animation speeds
    MOVE_STEP_SECONDS = 0.22   # Smooth, slow glide per cell (easy to follow)
    SELECT_AURA_SECONDS = 0.40 # Clear pause showing selected ball breathing aura
    POST_MOVE_PAUSE = 0.55     # Clear pause showing lines cleared or new balls spawned
    current_delay_ms = delay_ms

    pygame.init()
    try:
        screen = pygame.display.set_mode(renderer.window_size)

        def update_caption():
            if app_state == "MENU":
                pygame.display.set_caption(
                    "Five-or-More AI | Select Difficulty [Easy / Medium / Hard] and Start"
                )
            else:
                status = "PAUSED" if paused else f"{current_delay_ms}ms"
                pygame.display.set_caption(
                    f"Five-or-More AI ({chosen_difficulty}) | Speed: {status} | [↑/↓] Speed | [Space] Pause | [R] Restart | [Esc] Menu"
                )

        def start_game_with_difficulty(diff: str):
            nonlocal chosen_difficulty, env, renderer, app_state, game_over, paused
            nonlocal move_phase, phase_timer, selected_pos, moving_path, moving_color, moving_progress
            chosen_difficulty = diff
            env = _create_env(chosen_difficulty, reward_config)
            env.reset()
            renderer = GameRenderer(env.game)
            history.clear()
            game_over = False
            paused = False
            move_phase = "IDLE"
            phase_timer = 0.0
            selected_pos = None
            moving_path = None
            moving_color = None
            moving_progress = 0.0
            app_state = "PLAYING"
            update_caption()

        clock = pygame.time.Clock()
        paused = False
        game_over = False
        running = True
        drawer_open = False
        drawer_progress = 0.0
        drawer_scroll = 0
        history: list[dict[str, Any]] = []

        # Animated move state machine
        move_phase = "IDLE"  # "IDLE", "SELECTING", "GLIDING", "COOLDOWN"
        phase_timer = 0.0
        pending_action = None
        pending_path: list[tuple[int, int]] | None = None
        moving_color: int | None = None
        selected_pos: tuple[int, int] | None = None
        moving_path: list[tuple[int, int]] | None = None
        moving_progress = 0.0
        glide_elapsed = 0.0

        update_caption()

        while running:
            elapsed_sec = clock.tick(60) / 1000.0

            # Advance smooth drawer sliding animation
            target_progress = 1.0 if drawer_open else 0.0
            if drawer_progress < target_progress:
                drawer_progress = min(target_progress, drawer_progress + 8.0 * elapsed_sec)
            elif drawer_progress > target_progress:
                drawer_progress = max(target_progress, drawer_progress - 8.0 * elapsed_sec)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # ------------------- MENU STATE EVENTS -------------------
                elif app_state == "MENU":
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_1, pygame.K_e):
                            chosen_difficulty = "Easy"
                            env.game.difficulty = "Easy"
                        elif event.key in (pygame.K_2, pygame.K_m):
                            chosen_difficulty = "Medium"
                            env.game.difficulty = "Medium"
                        elif event.key in (pygame.K_3, pygame.K_h):
                            chosen_difficulty = "Hard"
                            env.game.difficulty = "Hard"
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            start_game_with_difficulty(chosen_difficulty)
                        elif event.key == pygame.K_ESCAPE:
                            running = False

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # Check difficulty buttons
                        for diff_name in ("Easy", "Medium", "Hard"):
                            if renderer.menu_button_rect(diff_name).collidepoint(event.pos):
                                chosen_difficulty = diff_name
                                env.game.difficulty = diff_name

                        if renderer.menu_button_rect("start").collidepoint(event.pos):
                            start_game_with_difficulty(chosen_difficulty)
                        elif renderer.menu_button_rect("quit").collidepoint(event.pos):
                            running = False

                # ------------------- PLAYING STATE EVENTS -------------------
                elif app_state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if drawer_open:
                                drawer_open = False
                            else:
                                # Return to difficulty selection menu
                                app_state = "MENU"
                                update_caption()
                        elif event.key == pygame.K_h:
                            drawer_open = not drawer_open
                        elif event.key == pygame.K_SPACE and not game_over:
                            paused = not paused
                            update_caption()
                        elif event.key in (pygame.K_DOWN, pygame.K_MINUS):
                            current_delay_ms = min(4000, current_delay_ms + 200)
                            update_caption()
                        elif event.key in (pygame.K_UP, pygame.K_PLUS, pygame.K_EQUALS):
                            current_delay_ms = max(100, current_delay_ms - 200)
                            update_caption()
                        elif event.key == pygame.K_r:
                            start_game_with_difficulty(chosen_difficulty)

                    elif event.type == pygame.MOUSEWHEEL and drawer_open:
                        drawer_scroll = max(0, drawer_scroll - event.y * 30)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if renderer.gameplay_button_rect("quit").collidepoint(event.pos):
                            app_state = "MENU"
                            update_caption()
                        elif renderer.gameplay_button_rect("restart").collidepoint(event.pos):
                            start_game_with_difficulty(chosen_difficulty)
                        elif _is_history_button_click(renderer, event.pos):
                            drawer_open = not drawer_open
                        elif drawer_open:
                            if _is_drawer_close_click(renderer, event.pos):
                                drawer_open = False
                            elif _is_inside_drawer(renderer, event.pos, drawer_progress):
                                pass
                            else:
                                drawer_open = False

            # ------------------- PLAYING GAMEPLAY LOGIC -------------------
            if app_state == "PLAYING" and running and not paused and not game_over:
                if move_phase == "IDLE":
                    phase_timer += elapsed_sec
                    if phase_timer >= (current_delay_ms / 1000.0):
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

                            source_x, source_y, dest_x, dest_y = env.decode_action(action)
                            pending_action = action
                            moving_color = env.game.get_board().get_cell(source_y, source_x)
                            pending_path = env.game.find_path(source_x, source_y, dest_x, dest_y)

                            # Start Phase 1: Highlight selected piece with breathing aura
                            selected_pos = (source_x, source_y)
                            move_phase = "SELECTING"
                            phase_timer = 0.0

                elif move_phase == "SELECTING":
                    phase_timer += elapsed_sec
                    # Highlight selected piece clearly before moving
                    if phase_timer >= SELECT_AURA_SECONDS:
                        moving_path = pending_path
                        glide_elapsed = 0.0
                        move_phase = "GLIDING"
                        phase_timer = 0.0

                elif move_phase == "GLIDING":
                    glide_elapsed += elapsed_sec
                    steps_count = max(1, len(moving_path) - 1) if moving_path else 1
                    glide_duration = steps_count * MOVE_STEP_SECONDS
                    moving_progress = glide_elapsed / MOVE_STEP_SECONDS if moving_path else 0.0

                    if glide_elapsed >= glide_duration:
                        # Ball has reached destination: commit move to environment
                        score_before = env.game.get_score()
                        source_x, source_y, dest_x, dest_y = env.decode_action(pending_action)

                        _, _, game_over, _ = env.step(pending_action)
                        score_after = env.game.get_score()
                        score_delta = max(0, score_after - score_before)
                        cleared = score_delta > 0
                        spawn_amount = 0 if cleared else env.game.DIFFICULTY_SPAWN_AMOUNTS.get(chosen_difficulty, 2)

                        history.append({
                            "turn": len(history) + 1,
                            "color": moving_color,
                            "source": (source_x, source_y),
                            "destination": (dest_x, dest_y),
                            "from_coord": f"{chr(ord('A') + source_x)}{source_y + 1}",
                            "to_coord": f"{chr(ord('A') + dest_x)}{dest_y + 1}",
                            "score_delta": score_delta,
                            "cleared": cleared,
                            "spawn_count": spawn_amount,
                            "total_score": score_after,
                        })

                        # Clear movement visual and enter short cooldown pause
                        selected_pos = None
                        moving_path = None
                        moving_color = None
                        moving_progress = 0.0
                        move_phase = "COOLDOWN"
                        phase_timer = 0.0

                elif move_phase == "COOLDOWN":
                    phase_timer += elapsed_sec
                    # Pause so the viewer clearly sees the cleared line or newly spawned balls
                    if phase_timer >= POST_MOVE_PAUSE:
                        move_phase = "IDLE"
                        phase_timer = 0.0

            # ------------------- DRAWING -------------------
            if app_state == "MENU":
                renderer.draw_menu(screen)
            elif app_state == "PLAYING":
                renderer.draw(
                    screen,
                    selected_position=selected_pos if not game_over else None,
                    movement_path=moving_path if not game_over else None,
                    moving_piece_color=moving_color if not game_over else None,
                    movement_progress=moving_progress if not game_over else 0.0,
                    history=history,
                    drawer_open=drawer_open,
                    drawer_progress=drawer_progress,
                    drawer_scroll=drawer_scroll,
                )
                if game_over:
                    renderer.draw_game_over(screen)

            pygame.display.flip()
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch a trained Five-or-More DQN agent play with smooth visual animations."
    )
    parser.add_argument("--model", default=None, help="checkpoint path (defaults to best run)")
    parser.add_argument(
        "--difficulty",
        choices=["Easy", "Medium", "Hard"],
        default=None,
        help="difficulty level (default: None, opens interactive selection menu)",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=1200,
        help="delay in ms between agent moves (default: 1200ms for slow, clear moves)",
    )
    parser.add_argument("--seed", type=int, default=42)
    arguments = parser.parse_args()
    play_agent(
        model_path=arguments.model,
        difficulty=arguments.difficulty,
        device=arguments.device,
        delay_ms=arguments.delay_ms,
        seed=arguments.seed,
    )


if __name__ == "__main__":
    main()
