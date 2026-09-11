import random

from environment import TicTacToeEnv


def play_random_game():
    env = TicTacToeEnv()

    state = env.reset()

    while True:
        legal_actions = env.legal_actions()

        action = random.choice(legal_actions)

        state, reward, done = env.step(action)

        if done:
            return reward

from game import TicTacToe


class TicTacToeEnv:
    def __init__(self):
        self.game = TicTacToe()

    def reset(self):
        self.game.reset()
        return self.game.board.copy()

    def observation(self):
        return self.game.board.copy()

    def legal_actions(self):
        return self.game.legal_actions()

    def step(self, action):
        if action not in self.game.legal_actions():
            return self.observation(), -1, False

        self.game.make_move(action)

        if self.game.check_winner() == 1:
            return self.observation(), 1, True

        if self.game.check_winner() == 2:
            return self.observation(), -1, True

        if self.game.is_draw():
            return self.observation(), 0, True

        return self.observation(), 0, False


if __name__ == "__main__":
    env = TicTacToeEnv()

    print("Initial:", env.reset())
    print("Legal actions:", env.legal_actions())

    state, reward, done = env.step(4)

    print("After action 4:", state)
    print("Legal actions:", env.legal_actions())
    print("Reward:", reward)
    print("Done:", done)

if __name__ == "__main__":
    games = 1000

    x_wins = 0
    o_wins = 0
    draws = 0

    for _ in range(games):
        result = play_random_game()

        if result == 1:
            x_wins += 1
        elif result == -1:
            o_wins += 1
        else:
            draws += 1

    print("Games:", games)
    print("X wins:", x_wins)
    print("O wins:", o_wins)
    print("Draws:", draws)
