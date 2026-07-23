# Project Specification

## Project Title
Human-Like Gomoku AI Using Behavioral Cloning and Player Modeling

## Goal
Train a neural network, via Behavioral Cloning, to imitate human Gomoku
gameplay — predicting the next move a human would make given a board state —
and evaluate how "human-like" the resulting AI plays, using recorded human
game datasets (plus optional self-collected gameplay).

## Fixed Decisions
(Do not change without both teammates agreeing — see AGENTS.md)

- Board size: 15x15
- Ruleset: [Freestyle / Renju] — TBD, finalize in RULES.md before Mission 2
- Language: Python 3.11
- ML Framework: PyTorch
- Training paradigm: Behavioral Cloning (supervised learning on
  (board_state, human_move) pairs) — NOT reinforcement learning / self-play
- Input representation: TBD (Mission 3 — likely multi-channel board tensor)
- Output representation: probability distribution over 225 board cells
  (15x15 flattened), with illegal-move masking applied at inference time

## Deliverables (final)
1. Working Gomoku game (human vs human, human vs AI)
2. Dataset pipeline (raw public dataset → cleaned, model-ready format)
3. Neural network architecture (PyTorch)
4. Trained model checkpoint(s)
5. Evaluation suite (accuracy vs held-out human moves, qualitative analysis,
   optional: human playtesting / Turing-style evaluation of "human-likeness")
6. Research report
7. Final presentation

## Out of Scope (explicitly NOT doing — prevents scope creep)
- Reinforcement learning / self-play / MCTS (AlphaZero-style) — future work only
- 19x19 board support
- Real-time online multiplayer
- Mobile app version

## Success Criteria
- Model predicts human moves on a held-out test set with measurable,
  reported accuracy (exact metric defined in evaluation mission)
- Game is fully playable end-to-end, no crashes, illegal moves impossible
- Report clearly documents methodology, results, and limitations
- Presentation communicates the project to a non-expert academic audience

## Team
- [Name 1] — [rough role, see docs/team_roles.md]
- [Name 2] — [rough role, see docs/team_roles.md]

## Revision Log
| Date | Change | Reason |
|------|--------|--------|
| [date] | Initial spec created | Mission 1 |
