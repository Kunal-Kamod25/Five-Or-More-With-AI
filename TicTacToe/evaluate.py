import random

import torch

from environment import TicTacToeEnv
from network import TicTacToeNetwork


MODEL_PATH = "tictactoe/tictactoe_model.pth"
GAMES = 10000



def select_best_action(network, state, legal_actions):
    state = torch.tensor(state, dtype=torch.float32)

    with torch.no_grad():
        q_values = network(state)

    legal_q_values = q_values[legal_actions]

    best_index = torch.argmax(legal_q_values)

    return legal_actions[best_index.item()]


def play_game(network):
    env = TicTacToeEnv()

    state = env.reset()

    while True:
        legal_actions = env.legal_actions()

        # Trained AI chooses X's move
        action = select_best_action(
            network,
            state,
            legal_actions
        )

        state, reward, done = env.step(action)

        if done:
            return reward


def evaluate():
    network = TicTacToeNetwork()

    network.load_state_dict(
        torch.load(
            MODEL_PATH,
            weights_only=True
        )
    )

    network.eval()

    x_wins = 0
    o_wins = 0
    draws = 0

    for _ in range(GAMES):
        result = play_game(network)

        if result == 1:
            x_wins += 1
        elif result == -1:
            o_wins += 1
        else:
            draws += 1

    print("Games:", GAMES)
    print("X wins:", x_wins)
    print("O wins:", o_wins)
    print("Draws:", draws)

    print(
        "X win rate:",
        f"{x_wins / GAMES * 100:.2f}%"
    )


if __name__ == "__main__":
    evaluate()