# Manual ML Exercise - Superseded Campaign 0 Mission 0

This is a completed historical exercise from the earlier Gomoku direction. It
is retained for learning notes and is not part of the current RL workflow.

## Setup
- Board size used for this exercise: 5x5 toy board
- Number of hypothetical positions invented: 5

## The 5 Toy Positions

For each, describe the board (you can use simple text grids, e.g. `.` empty,
`X` black, `O` white) and state what move a "human" would plausibly play next.

### Position 1
```
[board here]
```
Human move: [cell]
Why a human might play this:

### Position 2
```
[board here]
```
Human move: [cell]
Why a human might play this:

### Position 3
```
[board here]
```
Human move: [cell]
Why a human might play this:

### Position 4
```
[board here]
```
Human move: [cell]
Why a human might play this:

### Position 5
```
[board here]
```
Human move: [cell]
Why a human might play this:

## Your Hand-Written Rule

> [Write the rule(s) you invented to try to predict all 5 moves correctly.
>   E.g. "if there are 2 in a row diagonally, play the cell that extends it."]

Did your rule correctly predict all 5? [Yes/No — be honest]

## The 6th Position (the breaking point)

Introduce a 6th, slightly different position and test your rule against it.

```
[board here]
```
What your rule predicts: [cell]
What a human would plausibly actually play: [cell]
Did it break? [Yes/No]

## Reflection Paragraph

> Write 4-6 sentences about why a small hand-written rule does not scale to
> the many possible board states in the current 9x9 game. Connect this to why
> we need a trained policy instead of an ever-growing list of exceptions.
