# Project Specification

## Project Title
Five-Or-More Deep Reinforcement Learning Agent

## Goal
Train a neural network via Deep Reinforcement Learning to play Five-or-More, focusing on strategic gameplay and optimizing for the highest score by aligning balls in a highly stochastic environment.

## Fixed Decisions
(Do not change without both teammates agreeing — see AGENTS.md)

- Board size: 9x9
- Ruleset: Five-or-More (see RULES.md)
- Language: Python 3.11, Rust (Game Engine)
- ML Framework: PyTorch
- Training paradigm: Deep Reinforcement Learning (Q-Learning / Actor-Critic) — NOT Behavioral Cloning
- Input representation: 9x9 grid state with upcoming balls
- Output representation: Value/Policy for selecting and moving balls

## Deliverables (final)
1. Working Five-or-More game environment (Rust logic, Python wrapper)
2. State representation and reward mechanism pipeline
3. Neural network architecture (PyTorch)
4. Trained model checkpoint(s)
5. Evaluation suite (performance vs random baseline, learning curves)
6. Research report
7. Final presentation

## Out of Scope (explicitly NOT doing — prevents scope creep)
- Behavioral cloning / player modeling (future work only)
- Real-time online multiplayer
- Mobile app version
- Gomoku rules

## Success Criteria
- Model shows quantifiable improvement over random baselines, showing clear learning curves
- Game environment successfully bridges Rust and Python without crashes
- Report clearly documents methodology, results, and limitations
- Presentation communicates the project effectively

## Team
- Khumba Lunganlung
- Kunal Kamod

## Revision Log
| Date | Change | Reason |
|------|--------|--------|
| 2026-08-19 | Updated spec for Five-or-More Deep RL | Transition from Gomoku |
