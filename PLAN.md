# Project Plan / Mission Log

## Current Campaign / Mission
**Campaign 1, Mission 1: RL Environment Foundation**
Status: Complete

## Mission History
| Campaign | Mission | Name | Status | Completed Date | Notes |
|----------|---------|------|--------|-----------------|-------|
| 1 | 2 | Python-Rust Interop & Live Logging | Complete | 2026-08-28 | Added PyO3 bindings for game logic and live matrix extraction tool |
| 1 | 1 | RL Environment Foundation | Complete | 2026-08-28 | Added a deterministic, Bevy-free Rust environment using shared game rules |
| 0 | 0 | ML Bootcamp — Mental Model | Superseded | 2026-08-20 | Earlier Gomoku/behavioral-cloning direction replaced by the RL scope |

## Team Roles
See `docs/team_roles.md` for detail.
- [Name 1]: leaning toward [game engine / data pipeline]
- [Name 2]: leaning toward [model / training / evaluation]

## Open Questions
(Unresolved decisions — check this before starting new work, resolve before
moving to the next mission)
- [x] Extract pure game state from Bevy systems
- [x] Choose training difficulty (Medium)
<<<<<<< HEAD
- [x] Choose Python/Rust bridge approach
=======
- [x] Validate the headless environment with a random legal-action agent
- [ ] Choose Python/Rust bridge approach
>>>>>>> f580572 (added test for environment, it is up and ready, tested for a random agent)
- [ ] Add Gymnasium and masked-PPO dependencies when implementation begins

## Timeline (high-level, 4 months — refine as missions complete)
- Month 1: Headless environment, deterministic tests, random baseline
- Month 2: Observation/action wrapper and first masked-PPO run
- Month 3: Evaluation, reward refinement, and Bevy integration
- Month 4: Final experiments, report writing, and presentation prep

## Decision Log
(One line per significant decision — keep this updated, it becomes your
report's methodology section)
| Date | Decision | Reasoning |
|------|----------|-----------|
| 2026-08-20 | Project scope changed to 9x9 Five-or-More RL | Matches the working Rust game and requested next phase |
| 2026-08-28 | RL environment uses Medium difficulty and seeded Rust RNG | Keeps the first API simple while enabling reproducible tests |
| 2026-08-28 | Selected PyO3 for Rust-Python interop | Avoids rewriting game logic in Python while keeping performance high |
| 2026-08-28 | Live matrix extraction via Bevy system | Safely dumps real-time state for RL observation without breaking graphics |

## Immediate Next Steps
1. Choose the Python/Rust bridge approach before implementing the first RL algorithm.
