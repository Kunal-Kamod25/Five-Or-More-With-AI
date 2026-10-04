import unittest
from unittest.mock import Mock, patch

import pygame

from . import main as game_main


class MainIntegrationTests(unittest.TestCase):
    def test_main_shows_menu_and_quits_cleanly(self):
        game = Mock()
        game.DIFFICULTY_SPAWN_AMOUNTS = {
            "Easy": 1,
            "Medium": 2,
            "Hard": 3,
        }
        game.is_game_over.return_value = False
        renderer = Mock(window_size=(624, 716))
        input_controller = Mock()
        quit_event = pygame.event.Event(pygame.QUIT)
        clock = Mock()
        clock.tick.return_value = 16

        with (
            patch.object(game_main.pygame, "init") as initialize,
            patch.object(game_main.pygame, "quit") as quit_pygame,
            patch.object(game_main.pygame.display, "set_mode") as set_mode,
            patch.object(game_main.pygame.display, "set_caption") as set_caption,
            patch.object(game_main.pygame.display, "flip") as flip,
            patch.object(game_main.pygame.event, "get", return_value=[quit_event]),
            patch.object(game_main.pygame.time, "Clock", return_value=clock),
            patch.object(game_main, "Game", return_value=game),
            patch.object(game_main, "GameRenderer", return_value=renderer),
            patch.object(
                game_main,
                "InputController",
                return_value=input_controller,
            ),
        ):
            game_main.main()

        initialize.assert_called_once_with()
        game.start_game.assert_not_called()
        set_mode.assert_called_once_with((624, 716))
        set_caption.assert_called_once_with("Five-or-More")
        renderer.draw_menu.assert_called_once_with(set_mode.return_value)
        flip.assert_called_once_with()
        clock.tick.assert_called_once_with(60)
        input_controller.handle_event.assert_not_called()
        quit_pygame.assert_called_once_with()

    def test_menu_selects_difficulty_and_starts_game(self):
        game = Mock()
        game.DIFFICULTY_SPAWN_AMOUNTS = {
            "Easy": 1,
            "Medium": 2,
            "Hard": 3,
        }
        game.is_game_over.return_value = False
        renderer = Mock(window_size=(624, 716))
        renderer.menu_button_rect.side_effect = {
            "Easy": pygame.Rect(20, 20, 80, 40),
            "Medium": pygame.Rect(110, 20, 80, 40),
            "Hard": pygame.Rect(200, 20, 80, 40),
            "start": pygame.Rect(20, 80, 150, 40),
            "quit": pygame.Rect(200, 80, 100, 40),
        }.__getitem__
        renderer.gameplay_button_rect.side_effect = {
            "quit": pygame.Rect(400, 20, 80, 40),
            "restart": pygame.Rect(300, 20, 90, 40),
        }.__getitem__
        input_controller = Mock()
        easy_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (30, 30), "button": 1},
        )
        start_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (30, 90), "button": 1},
        )
        quit_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (410, 30), "button": 1},
        )
        clock = Mock()
        clock.tick.return_value = 16

        with (
            patch.object(game_main.pygame, "init"),
            patch.object(game_main.pygame, "quit") as quit_pygame,
            patch.object(game_main.pygame.display, "set_mode"),
            patch.object(game_main.pygame.display, "set_caption"),
            patch.object(game_main.pygame.display, "flip"),
            patch.object(
                game_main.pygame.event,
                "get",
                side_effect=[[easy_click], [start_click], [quit_click]],
            ),
            patch.object(game_main.pygame.time, "Clock", return_value=clock),
            patch.object(game_main, "Game", return_value=game),
            patch.object(game_main, "GameRenderer", return_value=renderer),
            patch.object(game_main, "InputController", return_value=input_controller),
        ):
            game_main.main()

        game.set_difficulty.assert_called_once_with("Easy")
        game.start_game.assert_called_once_with()
        input_controller.reset.assert_called_once_with()
        renderer.draw_menu.assert_has_calls(
            [unittest.mock.call(unittest.mock.ANY)]
        )
        self.assertEqual(renderer.draw.call_count, 2)
        quit_pygame.assert_called_once_with()

    def test_game_over_screen_can_restart_and_quit(self):
        game = Mock()
        game.DIFFICULTY_SPAWN_AMOUNTS = {
            "Easy": 1,
            "Medium": 2,
            "Hard": 3,
        }
        game.is_game_over.side_effect = [True, False, False]
        renderer = Mock(window_size=(624, 716))
        renderer.menu_button_rect.side_effect = {
            "start": pygame.Rect(20, 80, 150, 40),
            "quit": pygame.Rect(200, 80, 100, 40),
            "Easy": pygame.Rect(20, 20, 80, 40),
            "Medium": pygame.Rect(110, 20, 80, 40),
            "Hard": pygame.Rect(200, 20, 80, 40),
        }.__getitem__
        renderer.game_over_button_rect.side_effect = {
            "restart": pygame.Rect(200, 420, 224, 48),
            "quit": pygame.Rect(200, 482, 224, 48),
        }.__getitem__
        input_controller = Mock()
        start_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (30, 90), "button": 1},
        )
        restart_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (210, 430), "button": 1},
        )
        quit_click = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": (210, 490), "button": 1},
        )
        clock = Mock()
        clock.tick.return_value = 16

        with (
            patch.object(game_main.pygame, "init"),
            patch.object(game_main.pygame, "quit") as quit_pygame,
            patch.object(game_main.pygame.display, "set_mode"),
            patch.object(game_main.pygame.display, "set_caption"),
            patch.object(game_main.pygame.display, "flip"),
            patch.object(
                game_main.pygame.event,
                "get",
                side_effect=[[start_click], [restart_click], [quit_click]],
            ),
            patch.object(game_main.pygame.time, "Clock", return_value=clock),
            patch.object(game_main, "Game", return_value=game),
            patch.object(game_main, "GameRenderer", return_value=renderer),
            patch.object(game_main, "InputController", return_value=input_controller),
        ):
            game_main.main()

        game.start_game.assert_called_once_with()
        game.restart_game.assert_called_once_with()
        self.assertEqual(renderer.draw_game_over.call_count, 1)
        self.assertEqual(input_controller.reset.call_count, 2)
        quit_pygame.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
