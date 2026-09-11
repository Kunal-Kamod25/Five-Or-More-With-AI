# Tic-Tac-Toe DQN Experiment

This folder is a small reinforcement-learning experiment for our Five-or-More AI project.

The purpose is to first test the RL idea on an easier game: **Tic-Tac-Toe**.

The AI is **X**. The opponent is **O**, and O currently makes random moves.

## 1. Folder structure

```text
tictactoe/
├── game.py
├── environment.py
├── network.py
├── replay_buffer.py
├── dqn.py
├── dqn_trainer.py
├── random_agent.py
├── evaluate.py
└── tictactoe_model.pth
```

| File | Purpose |
|---|---|
| `game.py` | Basic Tic-Tac-Toe game rules |
| `environment.py` | RL environment: state, actions, rewards and opponent |
| `network.py` | MLP neural network |
| `replay_buffer.py` | Stores past experiences |
| `dqn.py` | DQN helper functions such as action selection |
| `dqn_trainer.py` | Main DQN training loop |
| `random_agent.py` | Random-player baseline |
| `evaluate.py` | Tests the trained model |
| `tictactoe_model.pth` | Saved trained network weights |

## 2. Board representation

We use a **1D vector of length 9**.

Example:

```text
X | O | .
---------
. | X | .
---------
O | . | .
```

becomes:

```text
[1, 2, 0,
 0, 1, 0,
 2, 0, 0]
```

Meaning:

```text
0 = empty
1 = X (AI)
2 = O (opponent)
```

Positions are:

```text
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

The 1D representation is intentional. The professor suggested trying an easier game and 1D data before moving to the larger Five-or-More problem.

## 3. Game

`game.py` contains the basic Tic-Tac-Toe rules.

Important functions:

```python
make_move(position)
```

Makes a move if it is legal.

```python
check_winner()
```

Returns:

```text
0 = nobody won
1 = X won
2 = O won
```

```python
is_draw()
```

Checks whether the board is full without a winner.

```python
legal_actions()
```

Returns the currently empty positions.

## 4. RL environment

`environment.py` connects the game to reinforcement learning.

Important functions:

```python
reset()
observation()
legal_actions()
step(action)
```

One call to:

```python
env.step(action)
```

means:

```text
AI/X chooses a move
        ↓
Check whether X won
        ↓
Check for draw
        ↓
O/random opponent makes a move
        ↓
Check whether O won
        ↓
Check for draw
        ↓
Return next state, reward, done
```

The AI always plays X.

### Rewards

Rewards are from X's point of view:

```text
X wins       → +1
O wins       → -1
Draw         →  0
Normal move  →  0
```

Currently an invalid AI action returns:

```text
reward = -1
done = True
```

The DQN uses legal-action masking, so it should normally avoid invalid actions.

## 5. MLP neural network

`network.py` contains the neural network.

Current architecture:

```text
9 → 64 → 64 → 9
```

Code:

```python
nn.Linear(9, 64)
nn.ReLU()

nn.Linear(64, 64)
nn.ReLU()

nn.Linear(64, 9)
```

### Why 9?

There are 9 board cells, so the input has 9 values.

### Why 64?

64 is the number of neurons in the hidden layer. It is a **hyperparameter**, not a fixed rule.

Possible experiments:

```text
9 → 16 → 16 → 9
9 → 32 → 32 → 9
9 → 64 → 64 → 9
9 → 90 → 90 → 9
9 → 128 → 128 → 9
```

The input and output remain 9 for this representation.

A larger network is not automatically better. Compare experiments.

## 6. Network outputs

The network produces **9 Q-values**.

For example:

```text
[0.2, 0.7, 0.1,
 0.3, 0.0, 0.4,
 0.1, 0.9, 0.2]
```

Each output corresponds to one move:

```text
Q0 → move 0
Q1 → move 1
...
Q8 → move 8
```

The network is trying to estimate how good each move is from the current board.

At the beginning the weights are random, so predictions are not meaningful yet.

## 7. Legal-action masking

The network always produces 9 values, even if some cells are occupied.

If:

```text
Legal actions = [1, 3, 5, 7, 8]
```

we only consider those Q-values:

```python
legal_q_values = q_values[legal_actions]
```

Then:

```python
best_index = torch.argmax(legal_q_values)
```

selects the best legal move.

## 8. DQN

DQN means **Deep Q-Network**.

MLP and DQN are different:

- **MLP** = neural-network architecture.
- **DQN** = reinforcement-learning method used to train the network.

Pipeline:

```text
Environment
    ↓
State
    ↓
MLP
    ↓
Q-values
    ↓
Choose action
    ↓
Environment
    ↓
Reward + next state
    ↓
Replay buffer
    ↓
Training
    ↓
Update MLP
```

## 9. Q-learning target

The basic target is:

```text
Q_target = reward + gamma × best future Q-value
```

or:

```text
Q_target = r + γ max Q(next_state, next_action)
```

Current gamma:

```python
GAMMA = 0.9
```

If the game has ended, there is no future state:

```text
Q_target = reward
```

Example:

```text
reward = 0
gamma = 0.9
best future Q = 0.7

target = 0 + 0.9 × 0.7
       = 0.63
```

## 10. Loss

The network has a current Q-value and a target Q-value.

We use mean squared error:

```python
loss_function = nn.MSELoss()
```

Conceptually:

```text
Loss = (current Q - target Q)²
```

Example:

```text
Current Q = 0.8
Target Q  = 0.63

Loss = (0.8 - 0.63)²
     = 0.0289
```

## 11. Backpropagation and optimizer

The trainer uses Adam:

```python
optimizer = optim.Adam(
    network.parameters(),
    lr=LEARNING_RATE
)
```

Current learning rate:

```python
LEARNING_RATE = 0.001
```

The update process is:

```python
optimizer.zero_grad()
loss.backward()
optimizer.step()
```

Meaning:

```text
zero_grad()
    ↓
clear old gradients

loss.backward()
    ↓
calculate gradients

optimizer.step()
    ↓
update network weights
```

## 12. Replay buffer

`replay_buffer.py` stores experiences.

Each experience is:

```text
(state, action, reward, next_state, done)
```

Example:

```text
(
    [0,0,0,0,0,0,0,0,0],
    4,
    0,
    [0,0,0,0,1,0,2,0,0],
    False
)
```

The buffer has a maximum capacity.

Current setting:

```python
BUFFER_SIZE = 10000
```

When full, the oldest experience is removed.

### Sampling

Current batch size:

```python
BATCH_SIZE = 32
```

Training randomly samples 32 stored experiences when enough are available.

## 13. Exploration vs exploitation

The AI uses epsilon-greedy action selection.

### Exploration

Choose a random legal move.

### Exploitation

Choose the legal move with the highest predicted Q-value.

Current settings:

```python
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995
```

So exploration decreases over training:

```text
1.0
 ↓
0.8
 ↓
0.5
 ↓
0.2
 ↓
0.1
```

The minimum is 0.1, so the AI still explores 10% of the time during training.

## 14. Main hyperparameters

All main training hyperparameters are at the top of `dqn_trainer.py`.

Current values:

```python
GAMMA = 0.9
LEARNING_RATE = 0.001
BUFFER_SIZE = 10000
BATCH_SIZE = 32
EPISODES = 5000

EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995
```

| Hyperparameter | Current | Meaning |
|---|---:|---|
| `GAMMA` | `0.9` | Importance of future rewards |
| `LEARNING_RATE` | `0.001` | Size of weight updates |
| `BUFFER_SIZE` | `10000` | Maximum stored experiences |
| `BATCH_SIZE` | `32` | Experiences per training update |
| `EPISODES` | `5000` | Number of training games |
| `EPSILON_START` | `1.0` | Initial exploration |
| `EPSILON_END` | `0.1` | Minimum exploration |
| `EPSILON_DECAY` | `0.995` | Exploration decay rate |

These are starting values, not guaranteed optimal values.

## 15. How to experiment

Change one thing at a time when possible.

Examples:

```python
LEARNING_RATE = 0.0005
```

or:

```python
BATCH_SIZE = 64
```

or change the MLP:

```text
9 → 32 → 32 → 9
```

Record every experiment:

```text
Network architecture:
Learning rate:
Gamma:
Batch size:
Buffer size:
Episodes:
Epsilon start:
Epsilon end:
Epsilon decay:

X wins:
O wins:
Draws:
Win rate:
```

This makes comparisons meaningful.

## 16. Baseline

A random-vs-random test was run for 1,000 games:

```text
Games: 1000
X wins: 592
O wins: 295
Draws: 113
```

This is the baseline to compare against.

The trained DQN was also tested for 10 games:

```text
Games: 10
X wins: 6
O wins: 0
Draws: 4
X win rate: 60.00%
```

This 10-game result is only an initial sanity check. It is too small for a reliable performance comparison.

For proper evaluation, use 1,000 games.

## 17. Training

From the project root:

```powershell
python tictactoe/dqn_trainer.py
```

The trained model is saved to:

```text
tictactoe/tictactoe_model.pth
```

## 18. Evaluation

Run:

```powershell
python tictactoe/evaluate.py
```

Set:

```python
GAMES = 1000
```

for a proper evaluation.

The important results are:

```text
X wins
O wins
Draws
X win rate
```

Do not judge RL performance from training loss alone.

## 19. Research purpose

This Tic-Tac-Toe experiment is a small RL laboratory before applying the approach to Five-or-More.

Current progression:

```text
Tic-Tac-Toe
    ↓
1D state representation
    ↓
Simple MLP
    ↓
DQN
    ↓
Train and evaluate
    ↓
Understand what works
    ↓
Move toward Five-or-More
```

Five-or-More has 81 cells compared with Tic-Tac-Toe's 9, so this smaller experiment helps us debug the RL pipeline first.

## 20. If you are taking over this experiment

Before changing code:

1. Read `environment.py`.
2. Understand that X is the AI and O is random.
3. Read `network.py`.
4. Understand the `9 → 64 → 64 → 9` MLP.
5. Read `replay_buffer.py`.
6. Read `dqn.py`.
7. Read `dqn_trainer.py`.
8. Run training.
9. Run evaluation.
10. Then experiment with hyperparameters.

Do not change several things at once if the goal is to understand which change affected performance.

## 21. Complete pipeline

```text
                 TIC-TAC-TOE
                      │
                      ↓
              9-value board
                      │
                      ↓
              ┌─────────────┐
              │     MLP     │
              │ 9 → 64 → 64 │
              │      → 9    │
              └──────┬──────┘
                     │
                     ↓
                 9 Q-values
                     │
                     ↓
             choose legal move
                     │
                     ↓
                Environment
                     │
              ┌──────┴──────┐
              ↓             ↓
           reward       next state
              │             │
              └──────┬──────┘
                     ↓
               Replay Buffer
                     │
                     ↓
                random batch
                     │
                     ↓
              Q-target + loss
                     │
                     ↓
              backpropagation
                     │
                     ↓
              update MLP weights
                     │
                     └──────────→ repeat
```

This is the current Tic-Tac-Toe DQN pipeline.
