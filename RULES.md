# Five-or-More Rules

## Board Size
- **9x9** (matches the `game_engine` implementation)

## Ruleset
This project uses the Five-or-More movement game implemented in the Rust
engine. It is not Gomoku or Renju.

## Why We Chose This
The existing playable game and its tests already implement these mechanics.
Keeping one ruleset avoids training an agent against rules that differ from the
game the user sees.

## Objective and Scoring
- The board is a 9x9 grid.
- Pieces are moved from an occupied cell to an empty cell.
- A move is legal only when an orthogonal path exists through empty cells.
- Lines of five or more same-colored pieces are cleared.
- Horizontal, vertical, and both diagonal directions are checked.
- The current engine awards points based on line length.
- After a move that does not clear a line, new colored pieces are spawned.
- The game ends when no legal move remains or no space remains for spawning.

## Turn Order
- The player selects one existing piece and an empty reachable destination.
- The environment spawns new pieces after a move when no line was cleared.
- Difficulty controls the number of spawned pieces: Easy = 1, Medium = 2,
  Hard = 3.

## RL Environment Requirements
  spawning, and game-over logic.

## Open Questions
 [ ] Choose Easy, Medium, or Hard as the training default.
 [ ] Decide whether invalid actions are rejected with a penalty or exposed only through action masking.
