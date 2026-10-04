<div align="center">

# FIVE OR MORE

### *Learning to Play Using Deep Reinforcement Learning*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-00A86B?style=for-the-badge)](https://www.pygame.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![NumPy](https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)

</div>

---

## About

**Five Or More with AI** is a Master's project focused on applying Deep Reinforcement Learning to the classic **Five or More / Color Lines** puzzle game.

The game is played on a **9×9 board**. Players move colored pieces through empty cells to form lines of five or more pieces of the same color. Matching lines are removed and points are awarded, while new pieces are added as the game progresses.

The original game was developed in **Rust + Bevy**. The active implementation is now written in **Python + Pygame**.

---

## Current Game

The Python version currently supports:

- 9×9 board
- Seven piece colors
- Random piece spawning
- A* pathfinding
- Horizontal, vertical, and diagonal line detection
- 5+ line clearing
- Score and highest score
- Easy, Medium, and Hard difficulty
- Start menu
- Restart and quit controls
- Game-over detection
- Piece selection feedback
- Movement animation
- Movement path visualization

### Scoring

| Line Length | Score |
|---:|---:|
| 5 | 10 |
| 6 | 12 |
| 7 | 14 |
| 8 | 16 |
| 9 | 18 |

### Difficulty

| Difficulty | New Pieces After a Normal Move |
|---|---:|
| Easy | 1 |
| Medium | 2 |
| Hard | 3 |

---

## Game State Representation

The board is represented as a **9×9 matrix** using:

| Value | Color |
|---:|---|
| 0 | Empty |
| 1 | Red |
| 2 | Green |
| 3 | Blue |
| 4 | Yellow |
| 5 | Purple |
| 6 | Cyan |
| 7 | Orange |

This representation will later be used as the input state for the reinforcement learning environment.

---

## Reinforcement Learning

The reinforcement learning phase is the next stage of development.

The current research direction is **CNN + DQN**.

```text
Game State
    ↓
9×9 State Representation
    ↓
CNN
    ↓
Spatial Features
    ↓
DQN
    ↓
Action
    ↓
Game Environment
    ↓
Reward
    ↓
Next State
```

The final state representation, action space, reward function, network architecture, and training procedure will be defined during the RL phase.

---

## Project Structure

```text
Five-Or-More-With-AI/
│
├── game/
│   ├── board.py
│   ├── piece.py
│   ├── board_pieces.py
│   ├── spawner.py
│   ├── movement.py
│   ├── line_detector.py
│   ├── scoring.py
│   ├── match_resolver.py
│   ├── game_over.py
│   ├── game.py
│   ├── state.py
│   ├── renderer.py
│   ├── input_controller.py
│   └── main.py
│
├── data/
├── docs/
├── experiments/
└── README.md
```

---

## Development Log

### Version 0.5 — 2026-10-05

- Ported the game from Rust + Bevy to Python + Pygame.
- Rebuilt the core game as modular Python components.
- Implemented board and piece management.
- Implemented random spawning.
- Implemented A* movement.
- Implemented line detection, scoring, and match resolution.
- Added difficulty selection, menus, restart/quit controls, score tracking, animation, and path visualization.
- Prepared the project for the reinforcement learning phase.

### Version 0.4 — 2026-09-05

- Explored an early Python reinforcement learning environment.
- Investigated 9×9 state representation.
- Explored source-to-destination action representation.
- Investigated legal-action filtering.

### Version 0.3 — 2026-08-28

- Worked on connecting game state with Python.
- Added 9×9 board-state logging and visualization.

### Version 0.2 — 2026-08-26

- Added game-state extraction into 9×9 matrix form.
- Tested state recording and fixed bugs.

### Version 0.1 — 2026-08-15

- Fixed early gameplay issues.
- Began studying reinforcement learning environment design.

---



## Team

**Khumba Lunganlung**  https://github.com/Old-Daoist
**Kunal Kamod**        https://github.com/Kunal-Kamod25