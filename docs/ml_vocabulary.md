# ML Vocabulary — Campaign 0, Mission 0

Fill in EVERY definition in your own words, specific to OUR Gomoku project.
Do not copy generic textbook definitions — if you can't phrase it in terms
of Gomoku boards and moves, you haven't understood it yet. Discuss out loud
as a team before writing; both of you should be able to say these unprompted.

---

## Core Definitions

**Feature**
> [Your definition, in Gomoku terms — what IS the input to our model?]

**Label**
> [Your definition — what IS the "correct answer" we're training toward?]

**Model**
> [Your definition — what is it, conceptually, before we discuss architecture?]

**Parameters**
> [Your definition — what gets adjusted during training?]

**Training**
> [Your definition — what process are we actually running?]

**Inference**
> [Your definition — when does this happen in our final app?]

**Loss (Loss Function)**
> [Your definition — what is it measuring, in our specific case?]

**Overfitting**
> [Your definition + a concrete Gomoku example of what this would look like]

**Underfitting**
> [Your definition + a concrete Gomoku example]

**Generalization**
> [Your definition — why is this the actual goal, not just training accuracy?]

**Train / Validation / Test Split**
> [Your definition — why can't we evaluate on training data?]

---

## Concept Mapping Table

| Generic ML Concept | Our Project's Version |
|---|---|
| Feature | A 15x15 Gomoku board state at some point in a game |
| Label | The cell a human actually played next from that state |
| Dataset | Thousands of (board, human move) pairs from public game records |
| Model | A neural network (architecture TBD — Campaign 4) |
| Training | Adjusting the network's parameters using recorded human moves |
| Loss | How far off the model's predicted move is from the human's actual move |
| Overfitting risk | Model memorizes specific famous games instead of general human tendencies |
| Inference | The trained model predicting a move against a new, live opponent |
| [Your own row] | [Something Gomoku-specific you're still unsure about — this becomes an Open Question in PLAN.md] |

---

## Open Question Raised
> [What's the 9th row you added, and what specifically are you unsure about?
>   Copy this into PLAN.md's Open Questions section too.]
