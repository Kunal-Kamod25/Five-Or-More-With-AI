"""Load and validate the project's JSON configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from game.game import Game

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
REQUIRED_SECTIONS = (
    "training",
    "dqn",
    "exploration",
    "network",
    "environment",
    "reward",
)


class ConfigError(ValueError):
    """Raised when the JSON configuration is invalid."""


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_mapping(config: dict[str, Any], section: str, path: Path) -> dict[str, Any]:
    if section not in config:
        raise ConfigError(f"Configuration is missing required section '{section}' in {path}.")
    section_value = config[section]
    if not isinstance(section_value, dict):
        raise ConfigError(
            f"Configuration section '{section}' in {path} must be a JSON object."
        )
    return section_value


def _validate_positive_int(value: Any, name: str, path: Path) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError(f"'{name}' in {path} must be a positive integer.")
    return value


def _validate_non_negative_number(value: Any, name: str, path: Path) -> float:
    if not _is_number(value) or value < 0:
        raise ConfigError(f"'{name}' in {path} must be a non-negative number.")
    return float(value)


def _validate_positive_number(value: Any, name: str, path: Path) -> float:
    if not _is_number(value) or value <= 0:
        raise ConfigError(f"'{name}' in {path} must be a positive number.")
    return float(value)


def _validate_probability(value: Any, name: str, path: Path) -> float:
    if not _is_number(value) or not 0 <= value <= 1:
        raise ConfigError(f"'{name}' in {path} must be between 0 and 1 inclusive.")
    return float(value)


def validate_config(config: dict[str, Any], path: Path | str | None = None) -> dict[str, Any]:
    """Validate a configuration dict and return it if all checks pass."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not isinstance(config, dict):
        raise ConfigError(f"Configuration in {config_path} must be a JSON object.")

    for section_name in REQUIRED_SECTIONS:
        _require_mapping(config, section_name, config_path)

    training = config["training"]
    _validate_positive_int(training.get("episodes"), "training.episodes", config_path)
    _validate_positive_int(
        training.get("max_steps_per_episode"),
        "training.max_steps_per_episode",
        config_path,
    )
    if "seed" in training and (not isinstance(training["seed"], int) or isinstance(training["seed"], bool)):
        raise ConfigError(f"'training.seed' in {config_path} must be an integer.")
    if "train_frequency" in training:
        _validate_positive_int(training["train_frequency"], "training.train_frequency", config_path)
    if "torch_threads" in training:
        _validate_positive_int(training["torch_threads"], "training.torch_threads", config_path)

    dqn = config["dqn"]
    _validate_positive_number(dqn.get("learning_rate"), "dqn.learning_rate", config_path)
    gamma = dqn.get("gamma")
    if not _is_number(gamma) or not 0 < gamma < 1:
        raise ConfigError(f"'dqn.gamma' in {config_path} must be between 0 and 1 (exclusive).")
    _validate_positive_int(dqn.get("batch_size"), "dqn.batch_size", config_path)
    _validate_positive_int(dqn.get("replay_buffer_size"), "dqn.replay_buffer_size", config_path)
    _validate_positive_int(
        dqn.get("target_update_frequency"),
        "dqn.target_update_frequency",
        config_path,
    )

    exploration = config["exploration"]
    epsilon_start = _validate_probability(
        exploration.get("epsilon_start"),
        "exploration.epsilon_start",
        config_path,
    )
    epsilon_min = _validate_probability(
        exploration.get("epsilon_min"),
        "exploration.epsilon_min",
        config_path,
    )
    if epsilon_min > epsilon_start:
        raise ConfigError(
            f"'exploration.epsilon_min' in {config_path} must be less than or equal to 'exploration.epsilon_start'."
        )
    epsilon_decay = exploration.get("epsilon_decay")
    if not _is_number(epsilon_decay) or not 0 < epsilon_decay <= 1:
        raise ConfigError(
            f"'exploration.epsilon_decay' in {config_path} must be a number between 0 and 1 inclusive."
        )

    network = config["network"]
    if not isinstance(network.get("type"), str) or not network["type"]:
        raise ConfigError(f"'network.type' in {config_path} must be a non-empty string.")
    hidden_layers = network.get("hidden_layers")
    if not isinstance(hidden_layers, list) or not hidden_layers:
        raise ConfigError(f"'network.hidden_layers' in {config_path} must be a non-empty list.")
    for index, layer_size in enumerate(hidden_layers):
        _validate_positive_int(layer_size, f"network.hidden_layers[{index}]", config_path)

    cnn = network.get("cnn")
    if not isinstance(cnn, dict):
        raise ConfigError(f"'network.cnn' in {config_path} must be a JSON object.")
    channels = cnn.get("channels")
    if not isinstance(channels, list) or not channels:
        raise ConfigError(f"'network.cnn.channels' in {config_path} must be a non-empty list.")
    for index, channel_count in enumerate(channels):
        _validate_positive_int(channel_count, f"network.cnn.channels[{index}]", config_path)
    _validate_positive_int(cnn.get("kernel_size"), "network.cnn.kernel_size", config_path)
    _validate_positive_int(cnn.get("padding", 1), "network.cnn.padding", config_path)

    environment = config["environment"]
    difficulty = environment.get("difficulty")
    if not isinstance(difficulty, str) or difficulty not in Game.DIFFICULTY_SPAWN_AMOUNTS:
        raise ConfigError(
            f"'environment.difficulty' in {config_path} must be one of {tuple(Game.DIFFICULTY_SPAWN_AMOUNTS)}."
        )

    reward = config["reward"]
    if not _is_number(reward.get("invalid_action")):
        raise ConfigError(f"'reward.invalid_action' in {config_path} must be a number.")
    _validate_positive_number(reward.get("score_per_point"), "reward.score_per_point", config_path)
    _validate_non_negative_number(reward.get("step_penalty"), "reward.step_penalty", config_path)
    _validate_positive_number(reward.get("game_over_penalty"), "reward.game_over_penalty", config_path)

    return config


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load a JSON configuration and validate it."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Configuration file '{path}' contains invalid JSON: {exc.msg} (line {exc.lineno}, column {exc.colno})."
        ) from exc

    return validate_config(config, path)
