# Research Report — Running Notes

Keep this updated after every mission. Write in plain language now; it can be
polished into formal report prose later.

---

## 2026-08-20 - RL Scope Correction
- The project now targets the working 9x9 Five-or-More Rust game.
- Reinforcement learning is the training direction for the next milestone.
- The earlier 15x15 Gomoku behavioral-cloning documents were stale and have
  been superseded; they are not the rules for the current implementation.
- The next technical milestone is a deterministic headless environment with
  seeded resets and legal-action masking.

---

## [Date] — Campaign 0, Mission 0: ML Bootcamp / Mental Model
### What we did
- Learned the core ML vocabulary (feature, label, model, parameters,
  training, inference, loss, overfitting, underfitting, generalization,
  train/val/test split), defined specifically in Gomoku terms
- Completed the "Manual ML" exercise: attempted to hand-write rules to
  predict human moves on a toy 5x5 board, and observed where those rules
  broke down on a new position
- Drew the full pipeline diagram: Raw Human Games -> Dataset -> Model ->
  Training Loop -> Trained Model -> Inference -> Live App

### Why (how it connects to the final goal)
- Establishes the reasoning for using Behavioral Cloning instead of a
  hand-coded rule engine: rules don't scale to capturing human-like
  (imperfect, biased, stylistic) play across a 15x15 board
- This vocabulary is assumed as known in every future mission

### Decisions made
- [none yet — conceptual mission]

### Problems encountered
- [fill in: which concept took longest to click? overfitting? loss?]

### Results/metrics
- N/A (no code/training this mission)

### Open questions for next mission
- [Copy the "9th row" open question from docs/ml_vocabulary.md here]

---

## Template for future entries:

## [Date] — Mission N: [Name]
### What we did
-

### Why (how it connects to the final goal)
-

### Decisions made
-

### Problems encountered
-

### Results/metrics (if applicable)
-

### Open questions for next mission
-
