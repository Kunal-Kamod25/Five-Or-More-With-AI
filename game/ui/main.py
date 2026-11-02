import pygame

from ..core.game import Game
from .input_controller import InputController
from .renderer import GameRenderer


def _is_history_button_click(renderer, pos):
    try:
        rect = renderer.gameplay_button_rect("history")
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


def _is_drawer_close_click(renderer, pos):
    try:
        rect = renderer.drawer_close_button_rect()
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


def _is_inside_drawer(renderer, pos, drawer_progress):
    try:
        rect = renderer.drawer_rect(drawer_progress)
        return rect.collidepoint(pos)
    except (KeyError, ValueError, AttributeError):
        return False


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
        drawer_open = False
        drawer_progress = 0.0
        drawer_scroll = 0

        while running:
            elapsed_seconds = clock.tick(60) / 1000.0

            # Advance smooth drawer sliding animation
            target_progress = 1.0 if drawer_open else 0.0
            if drawer_progress < target_progress:
                drawer_progress = min(target_progress, drawer_progress + 8.0 * elapsed_seconds)
            elif drawer_progress > target_progress:
                drawer_progress = max(target_progress, drawer_progress - 8.0 * elapsed_seconds)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    continue

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h and application_state == "playing":
                        drawer_open = not drawer_open
                        continue
                    if event.key == pygame.K_ESCAPE and drawer_open:
                        drawer_open = False
                        continue

                if event.type == pygame.MOUSEWHEEL and drawer_open:
                    drawer_scroll = max(0, drawer_scroll - event.y * 30)
                    continue

                if event.type != pygame.MOUSEBUTTONDOWN:
                    continue

                if event.button == 4 and drawer_open:
                    drawer_scroll = max(0, drawer_scroll - 30)
                    continue
                if event.button == 5 and drawer_open:
                    drawer_scroll += 30
                    continue

                if event.button == 3:
                    if application_state == "playing" and not drawer_open:
                        input_controller.handle_event(event)
                    continue

                if event.button != 1:
                    continue

                if application_state == "menu":
                    if renderer.menu_button_rect("quit").collidepoint(event.pos):
                        running = False
                    elif renderer.menu_button_rect("start").collidepoint(event.pos):
                        game.start_game()
                        input_controller.reset()
                        if hasattr(input_controller, "clear_history"):
                            input_controller.clear_history()
                        drawer_open = False
                        drawer_progress = 0.0
                        drawer_scroll = 0
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
                        if hasattr(input_controller, "clear_history"):
                            input_controller.clear_history()
                        drawer_open = False
                        drawer_progress = 0.0
                        drawer_scroll = 0
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
                        if hasattr(input_controller, "clear_history"):
                            input_controller.clear_history()
                        drawer_open = False
                        drawer_progress = 0.0
                        drawer_scroll = 0
                    elif _is_history_button_click(renderer, event.pos):
                        drawer_open = not drawer_open
                    elif drawer_open:
                        if _is_drawer_close_click(renderer, event.pos):
                            drawer_open = False
                        elif _is_inside_drawer(renderer, event.pos, drawer_progress):
                            pass
                        else:
                            drawer_open = False
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
                    history=getattr(input_controller, "history", []),
                    drawer_open=drawer_open,
                    drawer_progress=drawer_progress,
                    drawer_scroll=drawer_scroll,
                )
                if application_state == "game_over":
                    renderer.draw_game_over(screen)
            elif application_state == "game_over":
                renderer.draw(
                    screen,
                    history=getattr(input_controller, "history", []),
                    drawer_open=drawer_open,
                    drawer_progress=drawer_progress,
                    drawer_scroll=drawer_scroll,
                )
                renderer.draw_game_over(screen)
            else:
                renderer.draw_menu(screen)

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
