class TicTacToe:
    def __init__(self):
        self.board = [0] * 9
        self.current_player = 1

    def make_move(self, position):
        if self.game_over():
            return False

        if position < 0 or position > 8:
            return False

        if self.board[position] != 0:
            return False

        self.board[position] = self.current_player

        if self.current_player == 1:
            self.current_player = 2
        else:
            self.current_player = 1

        return True

    def display_board(self):
        symbols = {
            0: " ",
            1: "X",
            2: "O"
        }

        print(f" {symbols[self.board[0]]} | {symbols[self.board[1]]} | {symbols[self.board[2]]}")
        print("---+---+---")
        print(f" {symbols[self.board[3]]} | {symbols[self.board[4]]} | {symbols[self.board[5]]}")
        print("---+---+---")
        print(f" {symbols[self.board[6]]} | {symbols[self.board[7]]} | {symbols[self.board[8]]}")

    def check_winner(self):
        winning_combinations = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6)
        ]

        for a, b, c in winning_combinations:
            if self.board[a] != 0:
                if self.board[a] == self.board[b] == self.board[c]:
                    return self.board[a]

        return 0

    def is_draw(self):
        return 0 not in self.board and self.check_winner() == 0

    def game_over(self):
        return self.check_winner() != 0 or self.is_draw()

    def reset(self):
        self.board = [0] * 9
        self.current_player = 1

    def legal_actions(self):
        return [i for i in range(9) if self.board[i] == 0]

    def play(self):
        self.reset()

        while not self.game_over():
            self.display_board()

            print(f"Player {self.current_player}'s turn")

            try:
                position = int(input("Choose a position (0-8): "))
            except ValueError:
                print("Please enter a number.")
                continue

            if not self.make_move(position):
                print("Invalid move. Try again.")
                continue

        self.display_board()

        winner = self.check_winner()

        if winner == 1:
            print("X wins!")
        elif winner == 2:
            print("O wins!")
        else:
            print("It's a draw!")


if __name__ == "__main__":
    game = TicTacToe()
    game.play()