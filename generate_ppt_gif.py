"""Generate PowerPoint-ready 16:9 animated GIF demonstrating AI gameplay & cluster telemetry."""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

# Ensure headless pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from PIL import Image
import torch

from config.config_loader import load_config, validate_config
from game.core.game import Game
from game.ui.renderer import GameRenderer
from game.rl.dqn_agent import DQNAgent
from game.rl.evaluate_agent import find_latest_checkpoint
from game.rl.rl_environment import FiveOrMoreEnv


def create_slide_surface(
    game_surface: pygame.Surface,
    turn: int,
    score: int,
    action_text: str,
    status_text: str,
    slide_w: int = 1280,
    slide_h: int = 720,
) -> pygame.Surface:
    """Composite the game surface into a 16:9 widescreen PPT slide with dark glassmorphism telemetry."""
    slide = pygame.Surface((slide_w, slide_h))
    slide.fill((16, 18, 26))  # Deep slate navy background

    # Subtle background gradient grid lines
    grid_color = (25, 29, 42)
    for x in range(0, slide_w, 40):
        pygame.draw.line(slide, grid_color, (x, 0), (x, slide_h), 1)
    for y in range(0, slide_h, 40):
        pygame.draw.line(slide, grid_color, (0, y), (slide_w, y), 1)

    # 1. Scale and position the Game Board on the left
    # Original game window is ~624 x 716
    gw_w, gw_h = game_surface.get_size()
    target_gw_h = slide_h - 40  # 680
    scale_ratio = target_gw_h / gw_h
    target_gw_w = int(gw_w * scale_ratio)

    scaled_game = pygame.transform.smoothscale(game_surface, (target_gw_w, target_gw_h))
    game_x = 30
    game_y = 20

    # Draw border glow for game container
    glow_rect = pygame.Rect(game_x - 3, game_y - 3, target_gw_w + 6, target_gw_h + 6)
    pygame.draw.rect(slide, (45, 55, 80), glow_rect, border_radius=14)
    pygame.draw.rect(slide, (64, 214, 224), glow_rect, width=1, border_radius=14)
    slide.blit(scaled_game, (game_x, game_y))

    # 2. Right Side: Presentation Dashboard
    dash_x = game_x + target_gw_w + 30
    dash_y = 20
    dash_w = slide_w - dash_x - 30
    dash_h = target_gw_h

    # Card background
    card_bg = pygame.Rect(dash_x, dash_y, dash_w, dash_h)
    pygame.draw.rect(slide, (22, 26, 38), card_bg, border_radius=14)
    pygame.draw.rect(slide, (40, 48, 70), card_bg, width=2, border_radius=14)

    # Initialize fonts
    font_large = pygame.font.SysFont(["lato", "dejavusans", "arial"], 28, bold=True)
    font_mid = pygame.font.SysFont(["lato", "dejavusans", "arial"], 19, bold=True)
    font_small = pygame.font.SysFont(["lato", "dejavusans", "arial"], 14, bold=False)
    font_mono = pygame.font.SysFont(["monospace", "courier"], 14, bold=True)

    pad_x = dash_x + 24
    curr_y = dash_y + 24

    # Title & Badge
    title_surf = font_large.render("FIVE OR MORE — AI", True, (255, 255, 255))
    slide.blit(title_surf, (pad_x, curr_y))
    curr_y += 36

    sub_surf = font_small.render("Distributed Deep Q-Network (DQN) Reinforcement Learning", True, (130, 145, 175))
    slide.blit(sub_surf, (pad_x, curr_y))
    curr_y += 28

    # Separator line
    pygame.draw.line(slide, (44, 52, 75), (pad_x, curr_y), (dash_x + dash_w - 24, curr_y), 1)
    curr_y += 18

    # Section 1: Live Agent Telemetry
    sec1_title = font_mid.render("● LIVE AGENT STATUS", True, (64, 214, 224))
    slide.blit(sec1_title, (pad_x, curr_y))
    curr_y += 30

    # Metrics Grid inside a box
    box1 = pygame.Rect(pad_x, curr_y, dash_w - 48, 140)
    pygame.draw.rect(slide, (28, 33, 48), box1, border_radius=8)
    pygame.draw.rect(slide, (50, 60, 85), box1, width=1, border_radius=8)

    labels = [
        ("Policy:", "Deep Q-Network (Greedy argmax Q)", (240, 240, 240)),
        ("Current Score:", f"{score} Points", (255, 215, 80)),
        ("Move Turn:", f"#{turn}", (240, 240, 240)),
        ("Action Decided:", action_text, (54, 200, 130)),
        ("Agent Status:", status_text, (64, 214, 224)),
    ]

    item_y = curr_y + 12
    for lbl, val, val_col in labels:
        lbl_s = font_small.render(lbl, True, (150, 165, 190))
        val_s = font_mono.render(val, True, val_col)
        slide.blit(lbl_s, (pad_x + 14, item_y))
        slide.blit(val_s, (pad_x + 150, item_y))
        item_y += 24

    curr_y += 158

    # Section 2: Distributed Cluster Architecture
    sec2_title = font_mid.render("● DISTRIBUTED RAY CLUSTER", True, (54, 200, 130))
    slide.blit(sec2_title, (pad_x, curr_y))
    curr_y += 30

    box2 = pygame.Rect(pad_x, curr_y, dash_w - 48, 200)
    pygame.draw.rect(slide, (28, 33, 48), box2, border_radius=8)
    pygame.draw.rect(slide, (50, 60, 85), box2, width=1, border_radius=8)

    cluster_info = [
        ("Architecture:", "Actor-Learner Ray Distributed Cluster", (255, 255, 255)),
        ("Head Node (PC 1):", "192.168.6.106  [DQN Learner + 6 Workers]", (200, 220, 255)),
        ("Worker Node 2:", "192.168.6.125  [8 Simulation Workers]", (200, 220, 255)),
        ("Worker Node 3 (Siddhesh):", "192.168.6.110  [8 Simulation Workers]", (200, 220, 255)),
        ("Active Workers:", "22 Parallel Rollout Workers", (54, 200, 130)),
        ("Cluster Capacity:", "36 Logical CPUs  |  LAN Connected", (245, 215, 80)),
        ("Target Episodes:", "100,000 Episodes", (64, 214, 224)),
    ]

    item_y2 = curr_y + 12
    for lbl, val, val_col in cluster_info:
        lbl_s = font_small.render(lbl, True, (150, 165, 190))
        val_s = font_mono.render(val, True, val_col)
        slide.blit(lbl_s, (pad_x + 14, item_y2))
        slide.blit(val_s, (pad_x + 210, item_y2))
        item_y2 += 25

    curr_y += 218

    # Section 3: Bottom Presentation Pill / Tag
    tag_rect = pygame.Rect(pad_x, curr_y, dash_w - 48, 48)
    pygame.draw.rect(slide, (35, 42, 60), tag_rect, border_radius=8)
    pygame.draw.rect(slide, (64, 214, 224), tag_rect, width=1, border_radius=8)

    tag_text = font_mid.render("Autonomous High-Speed Rollouts across 3 PCs", True, (240, 245, 255))
    tag_rect_inner = tag_text.get_rect(center=tag_rect.center)
    slide.blit(tag_text, tag_rect_inner)

    return slide


def generate_ppt_gif(
    output_path: str = "presentation_slide.gif",
    standalone_output: str = "gameplay_only.gif",
    num_moves: int = 5,
    fps: int = 15,
) -> None:
    """Simulate DQN agent playing and capture animated frames for PowerPoint."""
    print("Initializing environment and loading agent...")
    checkpoint_path = find_latest_checkpoint()
    if checkpoint_path is None:
        raise FileNotFoundError("No checkpoint found.")

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    config = validate_config(checkpoint.get("config") or load_config())

    agent = DQNAgent(config, device="cpu")
    agent.online_network.load_state_dict(checkpoint.get("online_state_dict", checkpoint))
    agent.online_network.eval()

    env = FiveOrMoreEnv(
        difficulty=config["environment"].get("difficulty", "Medium"),
        invalid_action_reward=config["reward"]["invalid_action"],
        score_per_point=config["reward"]["score_per_point"],
        step_penalty=config["reward"]["step_penalty"],
        game_over_penalty=config["reward"]["game_over_penalty"],
        line_rewards=config["reward"].get("line_rewards"),
    )
    env.reset()

    renderer = GameRenderer(env.game)
    gw_w, gw_h = renderer.window_size
    game_surface = pygame.Surface((gw_w, gw_h))

    slide_frames: list[Image.Image] = []
    game_frames: list[Image.Image] = []

    MOVE_STEP_SECONDS = 0.08  # Swift, crisp movement for GIF presentation

    turn_count = 0
    print(f"Recording {num_moves} intelligent AI moves...")

    while turn_count < num_moves and not env.game.is_game_over():
        turn_count += 1
        legal_actions = env.get_valid_actions()
        if not legal_actions:
            break

        # Select action using DQN agent
        state = env.get_state()
        action = agent.select_action(state, legal_actions, epsilon=0.0)
        source_x, source_y, dest_x, dest_y = env.decode_action(action)
        src_coord = f"{chr(ord('A') + source_x)}{source_y + 1}"
        dst_coord = f"{chr(ord('A') + dest_x)}{dest_y + 1}"
        action_text = f"{src_coord} ➔ {dst_coord}"

        moving_color = env.game.get_board().get_cell(source_y, source_x)
        path = env.game.find_path(source_x, source_y, dest_x, dest_y)
        score = env.game.get_score()

        # Phase 1: Highlighting selected ball (4 frames)
        for _ in range(4):
            renderer.draw(
                game_surface,
                selected_position=(source_x, source_y),
            )
            slide = create_slide_surface(
                game_surface,
                turn=turn_count,
                score=score,
                action_text=action_text,
                status_text="Planning optimal path...",
            )

            # Convert to PIL
            raw_slide = pygame.image.tostring(slide, "RGB")
            slide_img = Image.frombytes("RGB", slide.get_size(), raw_slide)
            slide_frames.append(slide_img)

            raw_game = pygame.image.tostring(game_surface, "RGB")
            game_img = Image.frombytes("RGB", game_surface.get_size(), raw_game)
            game_frames.append(game_img)

        # Phase 2: Gliding along path
        steps_count = max(1, len(path) - 1) if path else 1
        total_glide_time = steps_count * MOVE_STEP_SECONDS
        num_glide_frames = max(6, int(total_glide_time * fps) + 2)

        for f_idx in range(num_glide_frames):
            prog = (f_idx / num_glide_frames) * steps_count
            renderer.draw(
                game_surface,
                movement_path=path,
                moving_piece_color=moving_color,
                movement_progress=prog,
            )
            slide = create_slide_surface(
                game_surface,
                turn=turn_count,
                score=score,
                action_text=action_text,
                status_text="Gliding to destination...",
            )

            raw_slide = pygame.image.tostring(slide, "RGB")
            slide_img = Image.frombytes("RGB", slide.get_size(), raw_slide)
            slide_frames.append(slide_img)

            raw_game = pygame.image.tostring(game_surface, "RGB")
            game_img = Image.frombytes("RGB", game_surface.get_size(), raw_game)
            game_frames.append(game_img)

        # Commit move
        score_before = env.game.get_score()
        env.step(action)
        score_after = env.game.get_score()
        cleared = score_after > score_before
        status_after = f"Line Cleared! (+{score_after - score_before} pts)" if cleared else "Balls spawned"

        # Phase 3: Post-move rest (5 frames)
        for _ in range(5):
            renderer.draw(game_surface)
            slide = create_slide_surface(
                game_surface,
                turn=turn_count,
                score=score_after,
                action_text=action_text,
                status_text=status_after,
            )

            raw_slide = pygame.image.tostring(slide, "RGB")
            slide_img = Image.frombytes("RGB", slide.get_size(), raw_slide)
            slide_frames.append(slide_img)

            raw_game = pygame.image.tostring(game_surface, "RGB")
            game_img = Image.frombytes("RGB", game_surface.get_size(), raw_game)
            game_frames.append(game_img)

    print(f"Captured {len(slide_frames)} frames. Encoding PowerPoint 16:9 GIF ({output_path})...")
    # Save slide-sized GIF with optimized palette
    duration_ms = int(1000 / fps)
    slide_frames[0].save(
        output_path,
        save_all=True,
        append_images=slide_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    print(f"Successfully generated: {output_path} ({os.path.getsize(output_path) / 1024 / 1024:.2f} MB)")

    print(f"Encoding standalone game GIF ({standalone_output})...")
    game_frames[0].save(
        standalone_output,
        save_all=True,
        append_images=game_frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    print(f"Successfully generated: {standalone_output} ({os.path.getsize(standalone_output) / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    generate_ppt_gif()
