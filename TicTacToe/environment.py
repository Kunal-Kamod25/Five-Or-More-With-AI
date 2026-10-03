import random

from game import TicTacToe


class TicTacToeEnv:
    def __init__(self):
        self.game = TicTacToe()

    def reset(self):
        self.game.reset()
        return self.observation()

    def observation(self):
        return [1 if x == 1 else -1 if x == 2 else 0 for x in self.game.board]

    def legal_actions(self):
        return self.game.legal_actions()

    def step(self, action):
        # AI (X) tries to make a move
        if action not in self.game.legal_actions():
            return self.observation(), -1, True

        self.game.make_move(action)

        # AI (X) won
        if self.game.check_winner() == 1:
            return self.observation(), 1, True

        # AI's move resulted in a draw
        if self.game.is_draw():
            return self.observation(), 0.5, True

        # Opponent (O) makes a random move
        self.opponent_move()

        # Opponent (O) won
        if self.game.check_winner() == 2:
            return self.observation(), -1, True

        # Opponent's move resulted in a draw
        if self.game.is_draw():
            return self.observation(), 0, True

        # Game continues
        return self.observation(), 0, False

    def opponent_move(self):
        legal_actions = self.legal_actions()

        if not legal_actions:
            return

        action = random.choice(legal_actions)
        self.game.make_move(action)


if __name__ == "__main__":
    env = TicTacToeEnv()

    print("Initial:", env.reset())
    print("Legal actions:", env.legal_actions())

    state, reward, done = env.step(4)

    print("After AI action + opponent:", state)
    print("Legal actions:", env.legal_actions())
    print("Reward:", reward)
    print("Done:", done)