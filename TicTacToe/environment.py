import random

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
        # AI (X) tries to make a move
        if action not in self.game.legal_actions():
            return self.observation(), -1, True

        self.game.make_move(action)

        # AI (X) won
        if self.game.check_winner() == 1:
            return self.observation(), 1, True

        # AI's move resulted in a draw
        if self.game.is_draw():
            return self.observation(), 0, True

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