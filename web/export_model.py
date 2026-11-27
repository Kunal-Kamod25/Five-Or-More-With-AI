"""Export a trained Five-or-More checkpoint as browser-friendly JSON weights."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch


def export_model(checkpoint_path: Path, output_path: Path) -> None:
    checkpoint: dict[str, Any] = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )
    config = checkpoint.get("config")
    if not isinstance(config, dict):
        raise ValueError(f"{checkpoint_path} does not contain its training config.")
    if config.get("environment", {}).get("color_count") != 2:
        raise ValueError("The browser demo currently bundles the trained two-color model.")

    state_dict = checkpoint.get("online_state_dict")
    if not isinstance(state_dict, dict):
        raise ValueError(f"{checkpoint_path} does not contain online_state_dict weights.")

    mapping = {
        "conv1": ("conv1.weight", "conv1.bias"),
        "conv2": ("conv2.weight", "conv2.bias"),
        "board_summary_layer": ("board_summary_layer.weight", "board_summary_layer.bias"),
        "action_scorer_0": ("action_scorer.0.weight", "action_scorer.0.bias"),
        "action_scorer_2": ("action_scorer.2.weight", "action_scorer.2.bias"),
    }
    weights = {
        name: {
            "weight": state_dict[weight_key].detach().cpu().float().reshape(-1).tolist(),
            "bias": state_dict[bias_key].detach().cpu().float().reshape(-1).tolist(),
        }
        for name, (weight_key, bias_key) in mapping.items()
    }
    model = {
        "format": "five-or-more-dqn-v1",
        "meta": {
            "runId": checkpoint.get("run_id", "unknown"),
            "environmentSteps": checkpoint.get("environment_steps", 0),
            "boardSize": 9,
            "colorChannels": 7,
            "colorCount": 2,
            "network": config["network"],
        },
        "weights": weights,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(model, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    print(f"Exported {checkpoint_path} to {output_path} ({output_path.stat().st_size:,} bytes).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("model.json"))
    arguments = parser.parse_args()
    export_model(arguments.checkpoint, arguments.output)


if __name__ == "__main__":
    main()
