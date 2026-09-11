import random

import torch

from network import TicTacToeNetwork


def select_action(network, state, legal_actions, epsilon):
    if random.random() < epsilon:
        return random.choice(legal_actions)

    state = torch.tensor(state, dtype=torch.float32)

    with torch.no_grad():
        q_values = network(state)

    legal_q_values = q_values[legal_actions]

    best_index = torch.argmax(legal_q_values)

    return legal_actions[best_index.item()]


def calculate_target(reward, next_q_value, done, gamma=0.9):
    if done:
        return reward

    return reward + gamma * next_q_value


def get_current_q_value(network, state, action):
    state = torch.tensor(state, dtype=torch.float32)

    q_values = network(state)

    return q_values[action]