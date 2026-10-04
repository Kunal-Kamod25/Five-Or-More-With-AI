import unittest
from unittest.mock import patch

from .game import Game
from .piece import Piece


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.original_spawn = self.game.spawner.spawn

        with patch.object(
            self.game.spawner,
            "spawn",
            side_effect=self.spawn_nonmatching_initial_pieces,
        ):
            self.game.start_game()

    def spawn_nonmatching_initial_pieces(self, amount):
        if amount == self.game.INITIAL_PIECE_COUNT:
            for x, color in ((0, 1), (2, 2), (4, 3), (6, 4), (8, 5)):
                self.game.board_pieces.add_piece(Piece(x, 0, color))
            return self.game.get_pieces()
        return self.original_spawn(amount)

    def clear_pieces(self):
        for piece in self.game.get_pieces():
            x, y = piece.get_position()
            self.game.board_pieces.remove_piece(x, y)

    def test_starting_creates_exactly_five_pieces(self):
        self.assertTrue(self.game.game_started)
        self.assertEqual(len(self.game.get_pieces()), 5)

    def test_starting_resets_score(self):
        self.game.total_score = 42
        self.game.game_over = True

        with patch.object(
            self.game.spawner,
            "spawn",
            side_effect=self.spawn_nonmatching_initial_pieces,
        ):
            self.game.start_game()

        self.assertEqual(self.game.get_score(), 0)
        self.assertEqual(len(self.game.get_pieces()), 5)
        self.assertFalse(self.game.is_game_over())

    def test_restart_preserves_highest_score_and_selected_difficulty(self):
        self.game.highest_score = 73
        self.game.set_difficulty("Hard")

        self.game.restart_game()

        self.assertEqual(self.game.get_score(), 0)
        self.assertEqual(self.game.get_highest_score(), 73)
        self.assertEqual(self.game.difficulty, "Hard")
        self.assertEqual(len(self.game.get_pieces()), 5)

    def test_difficulty_selection_rejects_unknown_values(self):
        with self.assertRaises(ValueError):
            self.game.set_difficulty("Extreme")

    def test_valid_move_succeeds(self):
        self.clear_pieces()
        self.game.board_pieces.add_piece(Piece(4, 4, 1))

        self.assertTrue(self.game.make_move(4, 4, 5, 4))

    def test_invalid_move_fails_without_spawning(self):
        pieces_before = self.game.get_pieces()
        board_before = [row[:] for row in self.game.get_board().board]

        self.assertFalse(self.game.make_move(-1, 0, 0, 0))

        self.assertEqual(len(self.game.get_pieces()), len(pieces_before))
        self.assertEqual(self.game.get_board().board, board_before)

    def test_matching_move_increases_score_without_spawning(self):
        self.clear_pieces()
        for x in range(4):
            self.game.board_pieces.add_piece(Piece(x, 4, 1))
        moving_piece = Piece(4, 5, 1)
        self.game.board_pieces.add_piece(moving_piece)

        with patch.object(self.game.spawner, "spawn", wraps=self.game.spawner.spawn) as spawn:
            self.assertTrue(self.game.make_move(4, 5, 4, 4))

        self.assertEqual(self.game.get_score(), 10)
        self.assertEqual(self.game.get_highest_score(), 10)
        self.assertEqual(self.game.get_pieces(), ())
        spawn.assert_not_called()
        self.assertTrue(
            all(self.game.get_board().get_cell(4, x) == 0 for x in range(5))
        )

    def test_initial_spawned_line_is_resolved(self):
        self.clear_pieces()

        def spawn_initial_line(amount):
            self.assertEqual(amount, self.game.INITIAL_PIECE_COUNT)
            for x in range(5):
                self.game.board_pieces.add_piece(Piece(x, 0, 1))

        with patch.object(
            self.game.spawner,
            "spawn",
            side_effect=spawn_initial_line,
        ) as spawn:
            self.game.start_game()

        self.assertEqual(self.game.get_score(), 10)
        self.assertFalse(any(self.game.board.board[0][x] for x in range(5)))
        spawn.assert_called_once_with(self.game.INITIAL_PIECE_COUNT)

    def test_non_matching_move_spawns_exactly_three_pieces(self):
        self.clear_pieces()
        piece = Piece(0, 0, 1)
        self.game.board_pieces.add_piece(piece)

        with patch.object(
            self.game.spawner,
            "spawn",
            wraps=self.game.spawner.spawn,
        ) as spawn:
            self.assertTrue(self.game.make_move(0, 0, 1, 0))

        spawn.assert_called_once_with(2)
        self.assertEqual(len(self.game.get_pieces()), 3)
        self.assertEqual(self.game.get_board().get_cell(0, 1), 1)

    def test_easy_medium_and_hard_spawn_expected_amounts(self):
        for difficulty, expected_spawn in (
            ("Easy", 1),
            ("Medium", 2),
            ("Hard", 3),
        ):
            with self.subTest(difficulty=difficulty):
                self.game.restart_game()
                self.clear_pieces()
                self.game.set_difficulty(difficulty)
                self.game.board_pieces.add_piece(Piece(0, 0, 1))

                with patch.object(
                    self.game.spawner,
                    "spawn",
                    wraps=self.game.spawner.spawn,
                ) as spawn:
                    self.assertTrue(self.game.make_move(0, 0, 1, 0))

                spawn.assert_called_once_with(expected_spawn)

    def test_spawned_pieces_that_form_a_line_are_immediately_resolved(self):
        self.clear_pieces()
        for x in range(4):
            self.game.board_pieces.add_piece(Piece(x, 4, 1))
        self.game.board_pieces.add_piece(Piece(8, 8, 2))

        def spawn_line_and_two_other_pieces(amount):
            self.assertEqual(amount, 2)
            for piece in (
                Piece(4, 4, 1),
                Piece(5, 7, 3),
            ):
                self.game.board_pieces.add_piece(piece)

        with patch.object(
            self.game.spawner,
            "spawn",
            side_effect=spawn_line_and_two_other_pieces,
        ) as spawn:
            self.assertTrue(self.game.make_move(8, 8, 7, 8))

        spawn.assert_called_once_with(2)
        self.assertEqual(self.game.get_score(), 10)
        self.assertEqual(len(self.game.get_pieces()), 2)
        self.assertTrue(all(self.game.board.get_cell(4, x) == 0 for x in range(5)))

    def test_score_accumulates_across_matching_moves(self):
        self.clear_pieces()
        self.game.board_pieces.add_piece(Piece(0, 4, 1))
        self.game.board_pieces.add_piece(Piece(1, 4, 1))
        self.game.board_pieces.add_piece(Piece(2, 4, 1))
        self.game.board_pieces.add_piece(Piece(3, 4, 1))
        self.game.board_pieces.add_piece(Piece(4, 5, 1))
        self.game.board_pieces.add_piece(Piece(0, 6, 2))
        self.game.board_pieces.add_piece(Piece(1, 6, 2))
        self.game.board_pieces.add_piece(Piece(2, 6, 2))
        self.game.board_pieces.add_piece(Piece(3, 6, 2))
        self.game.board_pieces.add_piece(Piece(4, 7, 2))

        self.assertTrue(self.game.make_move(4, 5, 4, 4))
        self.assertEqual(self.game.get_score(), 10)
        self.assertTrue(self.game.make_move(4, 7, 4, 6))

        self.assertEqual(self.game.get_score(), 20)
        self.assertEqual(self.game.get_highest_score(), 20)

    def test_board_state_updates_after_successful_non_matching_move(self):
        self.clear_pieces()
        piece = Piece(2, 2, 7)
        self.game.board_pieces.add_piece(piece)

        def spawn_away_from_moved_piece(amount):
            self.assertEqual(amount, 2)
            self.game.board_pieces.add_piece(Piece(8, 0, 1))
            self.game.board_pieces.add_piece(Piece(8, 1, 2))

        with patch.object(
            self.game.spawner,
            "spawn",
            side_effect=spawn_away_from_moved_piece,
        ):
            self.assertTrue(self.game.make_move(2, 2, 3, 2))

        self.assertEqual(self.game.get_board().get_cell(2, 2), 0)
        self.assertEqual(self.game.get_board().get_cell(2, 3), 7)
        self.assertEqual(piece.get_position(), (3, 2))

    def test_game_ends_when_a_completed_turn_leaves_no_legal_moves(self):
        self.clear_pieces()
        for y in range(self.game.board.SIZE):
            for x in range(self.game.board.SIZE):
                if (x, y) not in ((0, 0), (1, 0)):
                    color = (x + 2 * y) % 7 + 1
                    self.game.board_pieces.add_piece(Piece(x, y, color))
        self.game.board_pieces.add_piece(Piece(0, 0, 1))

        with patch.object(
            self.game.match_resolver,
            "resolve_matches",
            return_value=(0, []),
        ):
            self.assertTrue(self.game.make_move(0, 0, 1, 0))

        self.assertTrue(self.game.is_game_over())
        self.assertEqual(len(self.game.get_pieces()), 81)

    def test_moves_are_rejected_after_game_over(self):
        self.clear_pieces()
        for y in range(self.game.board.SIZE):
            for x in range(self.game.board.SIZE):
                color = (x + 2 * y) % 7 + 1
                self.game.board_pieces.add_piece(Piece(x, y, color))
        self.game.game_over = True
        board_before = [row[:] for row in self.game.board.board]

        self.assertFalse(self.game.make_move(0, 0, 1, 0))

        self.assertEqual(self.game.board.board, board_before)

    def test_game_remains_active_when_a_legal_move_exists(self):
        self.clear_pieces()
        self.game.board_pieces.add_piece(Piece(4, 4, 1))

        self.assertTrue(self.game.make_move(4, 4, 5, 4))

        self.assertFalse(self.game.is_game_over())


if __name__ == "__main__":
    unittest.main()
