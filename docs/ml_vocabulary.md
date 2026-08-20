# ML Vocabulary - RL Environment

Fill in every definition in your own words, specific to our Five-or-More RL project.
Do not copy generic textbook definitions - if you cannot phrase it in terms
of board states, legal actions, and rewards, discuss it out loud as a team.
as a team before writing; both of you should be able to say these unprompted.

---

## Core Definitions

**Observation**
> The 9x9 colored board and metadata returned to the agent.

**Action**
> A source cell and reachable destination selected by the agent.

**Model**
> [Your definition — what is it, conceptually, before we discuss architecture?]

**Parameters**
> [Your definition — what gets adjusted during training?]

**Training**
> [Your definition — what process are we actually running?]

**Inference**
> [Your definition — when does this happen in our final app?]

**Reward**
> The immediate score change and terminal outcome returned after an action.

**Action Mask**
> A filter that prevents the policy from selecting invalid source/destination pairs.

**Episode**
> One complete game from reset until game over or the time limit.

**Generalization**
> [Your definition — why is this the actual goal, not just training accuracy?]

**Baseline**
> A simple agent, such as random legal play, used to judge whether learning helps.

---

## Concept Mapping Table

| Generic ML Concept | Our Project's Version |
|---|---|
| Observation | A 9x9 colored board plus environment metadata |
| Action | A legal source cell to destination cell movement |
| Reward | Score change and terminal outcomes returned by the environment |
| Policy | A model distribution over possible actions |
| Value | The model's estimate of future episode return |
| Training | Updating the policy and value model from collected episodes |
| Action mask | The legal-action filter applied before selecting a move |
| Inference | The trained policy selecting a move in the live game |

---

## Open Question Raised
> [What's the 9th row you added, and what specifically are you unsure about?
>   Copy this into PLAN.md's Open Questions section too.]
