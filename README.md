# Five or More with AI

**A Master's research project focused on training a Reinforcement Learning agent to play the game "Five or More" (Color Lines).**

## 🎯 Project Goal
To train a Reinforcement Learning (RL) agent using PyTorch to play the classic puzzle game "Five or More". The project leverages a Rust-based game engine and aims to bridge the internal game state with a Python-based RL environment, eventually training algorithms like DQN to master the game. 

## 🧠 Key Features & Scope
- **Game Engine**: A Rust/Bevy implementation of Five or More ([jackinf/lines](https://github.com/jackinf/lines)).
- **Architecture**: 
  - **Environment**: Rust game engine exposing a 9x9 board state (0 for empty, 1-7 for colors).
  - **AI Agent**: PyTorch-based RL Agent (Python 3.12).
  - **Interface**: Internal state/action communication between Rust and Python (avoiding slow computer vision/mouse automation during training).
- **Final Demonstration**: Potential use of mouse automation to let the trained AI visually play the actual Rust GUI game.

## 📂 Project Structure
```text
Five-Or-More-With-AI/
├── game_engine/       # Contains the Rust game engine (jackinf/lines)
├── src/               # Python source code for the RL agent
├── notebooks/         # Exploration, EDA, prototyping
├── data/              # Datasets / replay buffers (Gitignored)
├── docs/              # Additional documentation
├── experiments/       # Logs, checkpoints, outputs (Gitignored)
└── report/            # Drafts and final paper
```

## 🚀 Quick Setup

**1. Python Environment (Windows)**
```powershell
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install torch numpy matplotlib
```

**2. Rust Environment**
Ensure you have [Rust](https://rustup.rs/) installed (along with MSVC build tools for Windows).

```powershell
# Navigate to the game engine
cd game_engine/lines

# Run the original game to verify it works
cargo run
```

## 📈 Current Status & Milestones
We are taking an incremental approach to building the RL environment:
- [x] Run the original Rust game natively.
- [x] Analyze game state (9x9 grid, 7 colors) and action pipeline (reusing built-in A* pathfinding).
- [ ] **Next up:** Create a minimal RL interface to expose the board state to Python.
- [ ] Implement a baseline strategy / random agent.
- [ ] Implement DQN and train the model.
- [ ] Connect the trained AI to the visual game.

*For a detailed step-by-step log of commands and progress, refer to `Five-Or-More-AI_Setup-Commands-and-Steps.txt`.*
