# Project Specification

## Project Title
Five-or-More AI Using Reinforcement Learning

## Goal
Train an agent to play the existing 9x9 Five-or-More game through
reinforcement learning. The agent will learn from board states, legal movement
actions, line-clearing rewards, and game-over outcomes. The graphical Rust game
and the headless training environment must use the same game rules.

## Fixed Decisions
(Do not change without both teammates agreeing — see AGENTS.md)

- Board size: 9x9
- Ruleset: Five-or-More rules documented in RULES.md
- Game engine: Rust with Bevy for rendering
- Training language: Python 3.11
- ML Framework: PyTorch
- Training paradigm: Reinforcement learning, beginning with masked PPO
- Input representation: multi-channel 9x9 board tensor plus scalar metadata
- Action representation: source cell to destination cell, flattened to 6,561
  possible actions with an action mask for illegal moves

## Deliverables (final)
1. Working Five-or-More game (human play and human vs AI)
2. Headless, deterministic RL environment
3. Neural network policy and value model
4. Trained model checkpoint(s)
5. Evaluation suite against random and heuristic baselines
6. Research report
7. Final presentation

## Out of Scope (explicitly NOT doing — prevents scope creep)
- Gomoku or Renju rules and datasets
- MCTS or AlphaZero-style self-play for the first RL milestone
- Board sizes other than 9x9
- Real-time online multiplayer
- Mobile app version

## Success Criteria
- Environment reproduces the graphical game's rules in headless tests
- Training is reproducible from fixed random seeds
- Trained agent beats a random legal-action baseline
- Game is fully playable end-to-end, with illegal moves impossible
- Report clearly documents methodology, results, and limitations
- Presentation communicates the project to a non-expert academic audience

## Team
- [Name 1] — [rough role, see docs/team_roles.md]
- [Name 2] — [rough role, see docs/team_roles.md]

## Revision Log
| Date | Change | Reason |
|------|--------|--------|
| [date] | Initial spec created | Mission 1 |
