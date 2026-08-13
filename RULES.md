# Five-Or-More Ruleset Decision

## Board Size
- **9x9** (matches the `game_engine` implementation)

## Ruleset
- [x] Freestyle Gomoku — first to 5-in-a-row (or more) wins, no restrictions
- [ ] Renju rules — Black (first player) has forbidden moves:
      double-three, double-four, and overline (6+ in a row does NOT count as a win for Black)

**Chosen: [FILL IN]**

## Why We Chose This
[Write your reasoning here. Important: check which ruleset your intended
training dataset uses BEFORE finalizing this — if your dataset is Renju-based
(e.g. RenjuNet) but your game engine is Freestyle, the model will learn moves
your own engine considers illegal. This must match Mission 2's dataset choice.]

## Win Condition (detail, fill in once ruleset chosen)
- Line directions checked: horizontal, vertical, diagonal (both directions)
- Exact-5 vs 5-or-more: [depends on ruleset above]

## Turn Order
- Black moves first, placing on... [center? any convention your dataset uses?]
- Players alternate turns

## Forbidden Moves (only if Renju chosen)
- Double-three: [explain in your own words]
- Double-four: [explain in your own words]
- Overline: [explain in your own words]

## Open Questions
- [ ] Confirm dataset ruleset matches this document (revisit in Mission 2)
