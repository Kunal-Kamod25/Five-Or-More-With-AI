# RL Environment Setup To-Do List

- [x] Write Python FFI / Wrapper for Rust Engine
  - [x] Configure `maturin` or `PyO3` in the Rust `Cargo.toml`.
  - [x] Expose `has_legal_move`, `find_path`, and `score_and_find_matched_pieces` to Python.
  - [x] Build the Rust library as a Python module.

- [x] Create Python RL Environment (`src/utils/env.py`)
  - [x] Define the Gym-style `__init__` (Observation Space and Action Space).
  - [x] Implement `reset()` to initialize an empty 9x9 board and spawn starting pieces.
  - [x] Implement `step(action)` to execute a move, clear lines, and assign rewards.
  - [x] Implement `action_masks()` to return a boolean array of valid actions for the current state.

- [ ] Setup Neural Network Models (`src/models/network.py`)
  - [ ] Build a Convolutional Neural Network (CNN) to process the 9x9 multi-channel board state.
  - [ ] Create Policy Head (outputs probabilities for the 6,561 actions).
  - [ ] Create Value Head (estimates the expected score of the current state).

- [ ] Write Basic Training Loop (`src/training/train.py`)
  - [ ] Setup masked PPO training loop.
  - [ ] Create data collection buffers for trajectories.
  - [ ] Implement loss functions and backpropagation.

- [ ] Testing & Evaluation
  - [ ] Test the environment with random valid actions.
  - [ ] Ensure the Python environment behaves identically to the Rust game.
