import torch
import torch.nn as nn
import torch.optim as optim

from environment import TicTacToeEnv
from network import TicTacToeNetwork
from replay_buffer import ReplayBuffer
from dqn import select_action


# Training settings
GAMMA = 0.9
LEARNING_RATE = 0.001
BUFFER_SIZE = 10000
BATCH_SIZE = 32
EPISODES = 5000

# Exploration settings
EPSILON_START = 1.0
EPSILON_END = 0.1
EPSILON_DECAY = 0.995


def train_step(network, optimizer, buffer):
    # We cannot train until we have enough experiences
    if not buffer.can_sample(BATCH_SIZE):
        return None

    # Get a random batch of experiences
    batch = buffer.sample(BATCH_SIZE)

    states = []
    actions = []
    rewards = []
    next_states = []
    dones = []

    for state, action, reward, next_state, done in batch:
        states.append(state)
        actions.append(action)
        rewards.append(reward)
        next_states.append(next_state)
        dones.append(done)

    # Convert lists into PyTorch tensors
    states = torch.tensor(states, dtype=torch.float32)
    actions = torch.tensor(actions, dtype=torch.long)
    rewards = torch.tensor(rewards, dtype=torch.float32)
    next_states = torch.tensor(next_states, dtype=torch.float32)
    dones = torch.tensor(dones, dtype=torch.float32)

    # Get the Q-value for the action the AI actually took
    current_q_values = network(states).gather(
        1,
        actions.unsqueeze(1)
    ).squeeze(1)

    # Calculate the target Q-values
    with torch.no_grad():
        next_q_values = network(next_states).max(dim=1).values

        target_q_values = (
            rewards
            + GAMMA * next_q_values * (1 - dones)
        )

    # Calculate the loss
    loss_function = nn.MSELoss()

    loss = loss_function(
        current_q_values,
        target_q_values
    )

    # Backpropagation and weight update
    optimizer.zero_grad()

    loss.backward()

    optimizer.step()

    return loss.item()


def train():
    # Create environment
    env = TicTacToeEnv()

    # Create MLP
    network = TicTacToeNetwork()

    # Create optimizer
    optimizer = optim.Adam(
        network.parameters(),
        lr=LEARNING_RATE
    )

    # Create replay buffer
    buffer = ReplayBuffer(BUFFER_SIZE)

    # Start with maximum exploration
    epsilon = EPSILON_START

    for episode in range(1, EPISODES + 1):

        # Start a new game
        state = env.reset()

        total_reward = 0
        loss = None

        while True:

            # Find currently legal moves
            legal_actions = env.legal_actions()

            # Choose an action using epsilon-greedy
            action = select_action(
                network,
                state,
                legal_actions,
                epsilon
            )

            # Let the environment execute the action
            next_state, reward, done = env.step(action)

            # Store the experience
            buffer.add(
                state,
                action,
                reward,
                next_state,
                done
            )

            # Train the network
            loss = train_step(
                network,
                optimizer,
                buffer
            )

            # Move to the next state
            state = next_state

            total_reward += reward

            # Stop when the game ends
            if done:
                break

        # Reduce exploration
        epsilon = max(
            EPSILON_END,
            epsilon * EPSILON_DECAY
        )

        # Print progress every 100 episodes
        if episode % 100 == 0:
            print(
                f"Episode: {episode}, "
                f"Reward: {total_reward}, "
                f"Epsilon: {epsilon:.3f}, "
                f"Loss: {loss}"
            )

    # Save the trained network
    torch.save(
        network.state_dict(),
        "tictactoe_model.pth"
    )

    print("Training complete.")
    print("Model saved as tictactoe_model.pth")


if __name__ == "__main__":
    train()