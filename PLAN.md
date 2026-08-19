# Project Plan / Mission Log

## Current Campaign / Mission
**Campaign 1, Mission 1: Environment Setup & Integration**
Status: In Progress

## Mission History
| Campaign | Mission | Name | Status | Completed Date | Notes |
|----------|---------|------|--------|-----------------|-------|
| 1 | 1 | Environment Setup | In Progress | - | Rust game engine logic, Python bindings, basic state representation |

## Team Roles
- Khumba Lunganlung: Game Engine (Rust), Integration
- Kunal Kamod: RL Models, Training pipeline (Python)

## Open Questions
- [ ] Define the exact reward function for the RL agent (e.g., shaping rewards for almost-cleared lines).
- [ ] Finalize the Neural Network input structure (e.g., number of channels for board state vs upcoming balls).

## Timeline (high-level)
- Phase 1: Game engine development (Rust) and Python bridging.
- Phase 2: State representation, defining action space, and initial DRL setup.
- Phase 3: Model training, hyperparameter tuning, and reward shaping.
- Phase 4: Final evaluation and documentation.

## Decision Log
| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-08-19 | Transition from Gomoku to Five-or-More RL | Decided to pursue Deep RL in a highly stochastic environment instead of Behavioral Cloning. |
