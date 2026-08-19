# Five-Or-More Ruleset Decision

## Board Size
- **9x9** (matches the `game_engine` implementation)

## Ruleset
- **Five or More** rules

## Mechanics
- The game is played on a 9x9 grid.
- Players move one ball per turn to an empty cell.
- A ball can only be moved if there is a clear, unblocked path to the destination.
- Every turn, unless the player scores, 3 new balls of random colors are added to random empty cells.
- The player scores by aligning 5 or more balls of the same color horizontally, vertically, or diagonally.
- Aligned balls are removed from the board, and the player gets a turn without new balls being added.
- The game ends when the board is completely full and no more moves can be made.

## Why We Chose This
This ruleset provides a stochastic environment perfect for Deep Reinforcement Learning, challenging the agent to plan ahead and handle uncertainty in ball generation.

## Win Condition / Goal
- There is no traditional "win" condition against an opponent; the goal is to maximize the score before the board fills up.
- The RL agent will focus on maximizing cumulative rewards over an episode.

## Open Questions
- [ ] Define the exact reward shaping (e.g., intermediate rewards for 3 or 4 in a row, penalties for filling the board).
