import pygame

from .game import Game
from .input_controller import InputController
from .renderer import GameRenderer


def main():
    pygame.init()
    try:
        game = Game()
        renderer = GameRenderer(game)
        input_controller = InputController(game, renderer)
        screen = pygame.display.set_mode(renderer.window_size)
        pygame.display.set_caption("Five-or-More")
        clock = pygame.time.Clock()
        application_state = "menu"
        running = True

        while running:
            elapsed_seconds = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue
                if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                    if application_state == "playing":
                        input_controller.handle_event(event)
                    continue

                if application_state == "menu":
                    if renderer.menu_button_rect("quit").collidepoint(event.pos):
                        running = False
                    elif renderer.menu_button_rect("start").collidepoint(event.pos):
                        game.start_game()
                        input_controller.reset()
                        application_state = "playing"
                    else:
                        for difficulty in game.DIFFICULTY_SPAWN_AMOUNTS:
                            if renderer.menu_button_rect(difficulty).collidepoint(
                                event.pos
                            ):
                                game.set_difficulty(difficulty)
                                break
                elif application_state == "game_over":
                    if renderer.game_over_button_rect("quit").collidepoint(
                        event.pos
                    ):
                        running = False
                    elif renderer.game_over_button_rect("restart").collidepoint(
                        event.pos
                    ):
                        game.restart_game()
                        input_controller.reset()
                        application_state = "playing"
                elif application_state == "playing":
                    if renderer.gameplay_button_rect("quit").collidepoint(
                        event.pos
                    ):
                        running = False
                    elif renderer.gameplay_button_rect("restart").collidepoint(
                        event.pos
                    ):
                        game.restart_game()
                        input_controller.reset()
                    else:
                        input_controller.handle_event(event)

            if application_state == "playing":
                input_controller.update(elapsed_seconds)
                if game.is_game_over():
                    application_state = "game_over"

                renderer.draw(
                    screen,
                    selected_position=input_controller.selected_position,
                    movement_path=input_controller.movement_path,
                    moving_piece_color=input_controller.moving_piece_color,
                    movement_progress=input_controller.movement_progress,
                )
                if application_state == "game_over":
                    renderer.draw_game_over(screen)
            elif application_state == "game_over":
                renderer.draw(screen)
                renderer.draw_game_over(screen)
            else:
                renderer.draw_menu(screen)

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
