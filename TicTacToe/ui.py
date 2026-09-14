"""
Tic-Tac-Toe Graphical User Interface (GUI)
Built using standard Python Tkinter (no extra installation needed).
Supports:
  1. Playing against the Trained DQN AI (or Smart/Random fallback if not yet trained)
  2. 2-Player Local Mode (Human vs Human)
  3. Live score tracking and game reset
"""

import os
import random
import tkinter as tk
from tkinter import messagebox

# Try to import PyTorch and our DQN network for AI moves
try:
    import torch
    from network import TicTacToeNetwork
    TORCH_AVAILABLE = True
except ImportError:
    # If torch is not installed or network is missing, fallback gracefully
    TORCH_AVAILABLE = False


class TicTacToeGUI:
    def __init__(self, root):
        # Store the main window
        self.root = root
        self.root.title("Tic-Tac-Toe (RL AI)")
        self.root.resizable(False, False)

        # Game state: 0 = empty, 1 = X (Human / Player 1), 2 = O (AI / Player 2)
        self.board = [0] * 9

        # Turn indicator: 1 for X, 2 for O
        self.current_player = 1

        # Game mode: "ai" (play against DQN AI) or "human" (play with a friend)
        self.game_mode = "ai"

        # Win counters
        self.scores = {"X": 0, "O": 0, "Draws": 0}

        # Setup the DQN neural network if PyTorch and weights are available
        self.network = None
        self.load_ai_network()

        # Build the user interface components
        self.create_widgets()

    def load_ai_network(self):
        """Loads the trained PyTorch DQN model if available."""
        if not TORCH_AVAILABLE:
            return

        # Check possible locations for the trained model file
        possible_paths = [
            "tictactoe_model.pth",
            "TicTacToe/tictactoe_model.pth",
            os.path.join(os.path.dirname(__file__), "tictactoe_model.pth")
        ]

        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break

        if model_path:
            try:
                # Initialize network architecture: 9 -> 64 -> 64 -> 9
                self.network = TicTacToeNetwork()
                # Load saved weights into the network
                self.network.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
                # Set network to evaluation mode (no dropout/training adjustments)
                self.network.eval()
                print(f"[AI] Successfully loaded trained DQN weights from: {model_path}")
            except Exception as error:
                print(f"[AI] Error loading model weights: {error}. Falling back to smart moves.")
                self.network = None
        else:
            print("[AI] No trained model weights found yet. Will use heuristic moves until trained.")

    def create_widgets(self):
        """Creates the header, 3x3 button grid, scoreboard, and control buttons."""
        # Top title label
        self.title_label = tk.Label(
            self.root,
            text="Tic-Tac-Toe AI",
            font=("Arial", 18, "bold"),
            pady=8
        )
        self.title_label.pack()

        # Mode selection buttons (AI mode vs 2 Players)
        mode_frame = tk.Frame(self.root)
        mode_frame.pack(pady=4)

        self.ai_mode_btn = tk.Button(
            mode_frame,
            text="Vs AI (DQN)",
            font=("Arial", 10, "bold"),
            bg="#3b82f6",
            fg="white",
            relief="flat",
            padx=8,
            pady=4,
            command=lambda: self.change_mode("ai")
        )
        self.ai_mode_btn.pack(side=tk.LEFT, padx=4)

        self.human_mode_btn = tk.Button(
            mode_frame,
            text="2 Players",
            font=("Arial", 10),
            bg="#e2e8f0",
            fg="#1e293b",
            relief="flat",
            padx=8,
            pady=4,
            command=lambda: self.change_mode("human")
        )
        self.human_mode_btn.pack(side=tk.LEFT, padx=4)

        # Status text (shows who's turn or who won)
        self.status_label = tk.Label(
            self.root,
            text="Your Turn (X)",
            font=("Arial", 12, "bold"),
            fg="#1e293b",
            pady=4
        )
        self.status_label.pack()

        # Frame container for the 3x3 game board
        grid_frame = tk.Frame(self.root, bg="#64748b", padx=3, pady=3)
        grid_frame.pack(pady=6)

        # List of 9 grid buttons
        self.buttons = []
        for i in range(9):
            # Calculate row and column for each index 0..8
            row = i // 3
            col = i % 3

            # Create individual cell button
            button = tk.Button(
                grid_frame,
                text=" ",
                font=("Arial", 28, "bold"),
                width=3,
                height=1,
                bg="#f8fafc",
                relief="flat",
                command=lambda index=i: self.on_cell_click(index)
            )
            button.grid(row=row, column=col, padx=2, pady=2)
            self.buttons.append(button)

        # Scoreboard displaying X wins, O wins, and Draws
        self.score_label = tk.Label(
            self.root,
            text=f"X: {self.scores['X']}   |   O: {self.scores['O']}   |   Draws: {self.scores['Draws']}",
            font=("Arial", 11),
            pady=4
        )
        self.score_label.pack()

        # Bottom buttons: Restart and Exit
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10)

        restart_btn = tk.Button(
            bottom_frame,
            text="Restart Game",
            font=("Arial", 10, "bold"),
            bg="#10b981",
            fg="white",
            relief="flat",
            padx=10,
            pady=5,
            command=self.reset_board
        )
        restart_btn.pack(side=tk.LEFT, padx=6)

        reset_score_btn = tk.Button(
            bottom_frame,
            text="Reset Score",
            font=("Arial", 10),
            bg="#ef4444",
            fg="white",
            relief="flat",
            padx=10,
            pady=5,
            command=self.reset_scores
        )
        reset_score_btn.pack(side=tk.LEFT, padx=6)

    def change_mode(self, mode):
        """Switches between Playing against AI and Playing against Human."""
        self.game_mode = mode
        if mode == "ai":
            self.ai_mode_btn.config(bg="#3b82f6", fg="white", font=("Arial", 10, "bold"))
            self.human_mode_btn.config(bg="#e2e8f0", fg="#1e293b", font=("Arial", 10))
        else:
            self.human_mode_btn.config(bg="#3b82f6", fg="white", font=("Arial", 10, "bold"))
            self.ai_mode_btn.config(bg="#e2e8f0", fg="#1e293b", font=("Arial", 10))
        self.reset_board()

    def on_cell_click(self, index):
        """Called whenever the player clicks a board square."""
        # 1. Reject click if the cell is already occupied or game ended
        if self.board[index] != 0 or self.check_winner() != 0 or self.is_draw():
            return

        # 2. Make the human move (Player 1 / X)
        self.make_move(index, self.current_player)

        # 3. Check if human won or drew
        if self.handle_game_end():
            return

        # 4. If playing vs AI, let the AI make its response move
        if self.game_mode == "ai":
            self.current_player = 2
            self.status_label.config(text="AI is thinking...", fg="#dc2626")
            # Disable clicking temporarily and delay AI move slightly for realistic feel
            self.root.after(300, self.ai_turn)
        else:
            # Switch to Player 2 (O)
            self.current_player = 2 if self.current_player == 1 else 1
            symbol = "X" if self.current_player == 1 else "O"
            self.status_label.config(text=f"Player {symbol}'s Turn", fg="#1e293b")

    def make_move(self, index, player):
        """Updates internal board and button text with the player's mark."""
        self.board[index] = player
        symbol = "X" if player == 1 else "O"
        color = "#2563eb" if player == 1 else "#dc2626"
        self.buttons[index].config(text=symbol, fg=color)

    def ai_turn(self):
        """Selects the AI move using DQN Q-values or smart fallback."""
        empty_cells = [i for i in range(9) if self.board[i] == 0]
        if not empty_cells or self.check_winner() != 0:
            return

        # Choose move
        chosen_move = self.get_best_ai_move(empty_cells)

        # Apply AI move
        self.make_move(chosen_move, 2)

        # Check if AI won or drew
        if self.handle_game_end():
            return

        # Return turn to human player
        self.current_player = 1
        self.status_label.config(text="Your Turn (X)", fg="#1e293b")

    def get_best_ai_move(self, legal_actions):
        """Uses trained PyTorch network Q-values, or smart fallback if weights not loaded."""
        # Method A: Use Neural Network DQN predictions
        if self.network is not None and TORCH_AVAILABLE:
            try:
                # Convert current 1D board list into PyTorch tensor
                state_tensor = torch.tensor(self.board, dtype=torch.float32)
                with torch.no_grad():
                    # Predict all 9 Q-values
                    q_values = self.network(state_tensor)

                # Filter Q-values only for legal (empty) squares
                legal_q_values = q_values[legal_actions]
                # Pick the legal move with highest estimated score
                best_legal_idx = torch.argmax(legal_q_values).item()
                return legal_actions[best_legal_idx]
            except Exception as e:
                print(f"[AI Error] {e}")

        # Method B: Smart fallback (Wins if can, blocks player win, picks center, or random)
        # 1. Check if AI can win in 1 move
        for move in legal_actions:
            self.board[move] = 2
            if self.check_winner() == 2:
                self.board[move] = 0
                return move
            self.board[move] = 0

        # 2. Check if player can win in 1 move and block them
        for move in legal_actions:
            self.board[move] = 1
            if self.check_winner() == 1:
                self.board[move] = 0
                return move
            self.board[move] = 0

        # 3. Take center cell if available
        if 4 in legal_actions:
            return 4

        # 4. Otherwise pick any random legal move
        return random.choice(legal_actions)

    def check_winner(self):
        """Checks if there is a 3-in-a-row winner. Returns 1 for X, 2 for O, 0 for none."""
        combos = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
            (0, 4, 8), (2, 4, 6)              # Diagonals
        ]
        for a, b, c in combos:
            if self.board[a] != 0 and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return 0

    def is_draw(self):
        """Returns True if the board is full with no winner."""
        return 0 not in self.board and self.check_winner() == 0

    def handle_game_end(self):
        """Checks if the game has concluded and updates scores and UI message."""
        winner = self.check_winner()
        if winner == 1:
            self.status_label.config(text="🎉 Player X Wins!", fg="#16a34a")
            self.scores["X"] += 1
            self.update_score_display()
            return True
        elif winner == 2:
            name = "AI (O)" if self.game_mode == "ai" else "Player O"
            self.status_label.config(text=f"🤖 {name} Wins!", fg="#dc2626")
            self.scores["O"] += 1
            self.update_score_display()
            return True
        elif self.is_draw():
            self.status_label.config(text="🤝 It's a Draw!", fg="#d97706")
            self.scores["Draws"] += 1
            self.update_score_display()
            return True

        return False

    def update_score_display(self):
        """Refreshes the scoreboard text."""
        self.score_label.config(
            text=f"X: {self.scores['X']}   |   O: {self.scores['O']}   |   Draws: {self.scores['Draws']}"
        )

    def reset_board(self):
        """Clears the board for a new game without wiping total scores."""
        self.board = [0] * 9
        self.current_player = 1
        for button in self.buttons:
            button.config(text=" ", fg="#1e293b", bg="#f8fafc")
        self.status_label.config(text="Your Turn (X)", fg="#1e293b")

    def reset_scores(self):
        """Resets the win/loss counters to 0."""
        self.scores = {"X": 0, "O": 0, "Draws": 0}
        self.update_score_display()
        self.reset_board()


def run():
    """Main entry point to start the Tkinter application."""
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()
