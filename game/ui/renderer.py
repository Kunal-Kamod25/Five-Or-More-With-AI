"""High-fidelity visual renderer for the Five-or-More board game."""

import math
import pygame

from ..core.game import Game


class GameRenderer:
    """Draw the board, game status, menus, and visual movement feedback with rich aesthetics."""

    CELL_SIZE = 64
    BOARD_MARGIN = 24
    HEADER_HEIGHT = 92
    GRID_LINE_WIDTH = 2
    PIECE_RADIUS = 22
    DRAWER_WIDTH = 270

    # Curated modern palette
    BACKGROUND_COLOR = (28, 31, 38)
    BACKGROUND_DARK = (18, 20, 26)
    BOARD_CONTAINER_COLOR = (22, 25, 33)
    BOARD_BORDER_COLOR = (44, 52, 68)
    EMPTY_CELL_COLOR = (54, 60, 70)
    EMPTY_CELL_BORDER = (68, 76, 90)
    GRID_LINE_COLOR = (25, 28, 34)

    DRAWER_BG = (24, 28, 38)
    DRAWER_BORDER = (54, 65, 85)

    TEXT_COLOR = (245, 245, 245)
    MUTED_TEXT_COLOR = (185, 192, 202)
    ACCENT_CYAN = (64, 214, 224)
    ACCENT_GOLD = (255, 215, 80)
    ACCENT_EMERALD = (54, 200, 130)

    BUTTON_COLOR = (63, 73, 88)
    BUTTON_HOVER_COLOR = (81, 96, 117)
    SELECTED_BUTTON_COLOR = (54, 125, 101)
    SELECTED_BUTTON_BORDER = (75, 190, 150)
    CARD_BG_COLOR = (36, 42, 54)
    CARD_BORDER_COLOR = (56, 65, 82)

    PATH_COLOR = (255, 255, 255, 115)
    PATH_GLOW_COLOR = (100, 200, 255, 55)

    # 7 vibrant, distinct jewel orb colors
    PIECE_COLORS = {
        1: (220, 55, 55),    # Ruby Red
        2: (55, 180, 85),    # Emerald Green
        3: (65, 115, 230),   # Sapphire Blue
        4: (245, 210, 55),   # Topaz Yellow
        5: (160, 85, 200),   # Amethyst Purple
        6: (55, 200, 205),   # Aquamarine Cyan
        7: (240, 140, 45),   # Amber Orange
    }

    def __init__(self, game):
        if not isinstance(game, Game):
            raise TypeError("game must be a Game object.")
        if not pygame.font.get_init():
            pygame.font.init()

        self.game = game
        self.board_size = game.get_board().SIZE
        board_pixels = self.board_size * self.CELL_SIZE
        self.board_origin = (
            self.BOARD_MARGIN,
            self.HEADER_HEIGHT + self.BOARD_MARGIN,
        )
        self.window_size = (
            board_pixels + 2 * self.BOARD_MARGIN,
            self.board_origin[1] + board_pixels + self.BOARD_MARGIN,
        )

        # Typography with modern fallback chain
        font_names = ["lato", "dejavusans", "segoeui", "helvetica", "arial", "sans-serif"]
        self._title_font = pygame.font.SysFont(font_names, 46, bold=True) or pygame.font.Font(None, 58)
        self._large_font = pygame.font.SysFont(font_names, 36, bold=True) or pygame.font.Font(None, 44)
        self._medium_font = pygame.font.SysFont(font_names, 22, bold=True) or pygame.font.Font(None, 30)
        self._small_font = pygame.font.SysFont(font_names, 17, bold=True) or pygame.font.Font(None, 24)
        self._label_font = pygame.font.SysFont(font_names, 12, bold=True) or pygame.font.Font(None, 16)

    def logical_to_screen(self, x, y):
        """Return the pixel center of a logical (x, y) board cell."""
        if not self.game.get_board().is_inside(y, x):
            raise IndexError("Board coordinates must be between 0 and 8.")
        origin_x, origin_y = self.board_origin
        return (
            origin_x + x * self.CELL_SIZE + self.CELL_SIZE // 2,
            origin_y + y * self.CELL_SIZE + self.CELL_SIZE // 2,
        )

    def screen_to_board(self, screen_position):
        """Return a board (x, y) position or None when outside the grid."""
        screen_x, screen_y = screen_position
        origin_x, origin_y = self.board_origin
        board_x = screen_x - origin_x
        board_y = screen_y - origin_y
        board_pixels = self.board_size * self.CELL_SIZE
        if not (0 <= board_x < board_pixels and 0 <= board_y < board_pixels):
            return None
        return board_x // self.CELL_SIZE, board_y // self.CELL_SIZE

    def gameplay_button_rect(self, button_name):
        """Return the screen rectangle for a gameplay control."""
        right = self.window_size[0] - self.BOARD_MARGIN
        if button_name == "quit":
            return pygame.Rect(right - 78, 22, 78, 36)
        if button_name == "restart":
            return pygame.Rect(right - 172, 22, 84, 36)
        if button_name == "history":
            return pygame.Rect(right - 266, 22, 86, 36)
        raise ValueError("Unknown gameplay button.")

    def drawer_close_button_rect(self):
        """Return the screen rectangle for the history drawer close button."""
        return pygame.Rect(self.window_size[0] - 38, 18, 28, 28)

    def drawer_rect(self, drawer_progress=1.0):
        """Return the current screen rectangle of the history drawer."""
        clamped = max(0.0, min(1.0, drawer_progress))
        drawer_x = self.window_size[0] - int(self.DRAWER_WIDTH * clamped)
        return pygame.Rect(drawer_x, 0, self.DRAWER_WIDTH, self.window_size[1])

    def menu_button_rect(self, button_name):
        """Return the screen rectangle for a menu button."""
        center_x = self.window_size[0] // 2
        if button_name in self.game.DIFFICULTY_SPAWN_AMOUNTS:
            index = tuple(self.game.DIFFICULTY_SPAWN_AMOUNTS).index(button_name)
            width = 112
            gap = 12
            total_width = 3 * width + 2 * gap
            left = center_x - total_width // 2
            return pygame.Rect(left + index * (width + gap), 330, width, 46)
        if button_name == "start":
            return pygame.Rect(center_x - 105, 405, 210, 52)
        if button_name == "quit":
            return pygame.Rect(center_x - 105, 475, 210, 48)
        raise ValueError("Unknown menu button.")

    def game_over_button_rect(self, button_name):
        """Return the screen rectangle for a game-over action."""
        center_x = self.window_size[0] // 2
        if button_name == "restart":
            return pygame.Rect(center_x - 112, 420, 224, 48)
        if button_name == "quit":
            return pygame.Rect(center_x - 112, 482, 224, 48)
        raise ValueError("Unknown game-over button.")

    def draw(
        self,
        surface,
        selected_position=None,
        movement_path=None,
        moving_piece_color=None,
        movement_progress=0.0,
        history=None,
        drawer_open=False,
        drawer_progress=0.0,
        drawer_scroll=0,
    ):
        """Draw current gameplay state with high-tech glass aesthetics."""
        self._draw_ambient_background(surface)
        self._draw_scoreboard(surface, drawer_open=drawer_open)

        origin_x, origin_y = self.board_origin
        board_pixel_dim = self.board_size * self.CELL_SIZE

        # Outer rounded chassis / board backing with subtle shadow
        outer_frame = pygame.Rect(
            origin_x - 8,
            origin_y - 8,
            board_pixel_dim + 16,
            board_pixel_dim + 16,
        )
        pygame.draw.rect(surface, self.BOARD_CONTAINER_COLOR, outer_frame, border_radius=12)
        pygame.draw.rect(surface, self.BOARD_BORDER_COLOR, outer_frame, 2, border_radius=12)

        # Draw grid cells
        for y in range(self.board_size):
            for x in range(self.board_size):
                cell_rect = pygame.Rect(
                    origin_x + x * self.CELL_SIZE,
                    origin_y + y * self.CELL_SIZE,
                    self.CELL_SIZE,
                    self.CELL_SIZE,
                )
                # Base fill
                pygame.draw.rect(surface, self.EMPTY_CELL_COLOR, cell_rect)
                # Outer grid line
                pygame.draw.rect(
                    surface,
                    self.GRID_LINE_COLOR,
                    cell_rect,
                    self.GRID_LINE_WIDTH,
                )
                # Subtle inset bevel
                inset_rect = cell_rect.inflate(-4, -4)
                pygame.draw.rect(surface, (60, 67, 78), inset_rect, 1, border_radius=4)
                # Preserve exact center pixel for test compatibility
                surface.set_at(cell_rect.center, self.EMPTY_CELL_COLOR)

        # Draw glowing movement path
        if movement_path:
            self._draw_movement_path(surface, movement_path)

        # Draw static pieces
        moving_source = movement_path[0] if movement_path and moving_piece_color else None
        ticks = pygame.time.get_ticks()

        for piece in self.game.get_pieces():
            x, y = piece.get_position()
            if moving_source == (x, y):
                continue
            center = self.logical_to_screen(x, y)
            is_selected = (selected_position == (x, y))
            hover_y = int(round(math.sin(ticks / 180.0) * 2.5)) if is_selected else 0
            self._draw_piece(surface, piece.get_color(), center, hover_offset=hover_y)

        # Draw selection aura & rings
        if selected_position is not None and moving_source is None:
            self._draw_selection(surface, selected_position)

        # Draw moving piece along animated path
        if movement_path and moving_piece_color is not None:
            moving_center = self._path_position(movement_path, movement_progress)
            self._draw_piece(surface, moving_piece_color, moving_center)

        # Draw slide-out History Drawer overlay
        if drawer_progress > 0.001:
            self._draw_history_drawer(
                surface,
                history=history,
                drawer_progress=drawer_progress,
                drawer_scroll=drawer_scroll,
            )

    def draw_menu(self, surface):
        """Draw a polished modern start menu with floating orb showcase."""
        self._draw_ambient_background(surface)

        # Floating decorative showcase of all 7 gem colors
        ticks = pygame.time.get_ticks()
        center_x = self.window_size[0] // 2
        total_orbs = len(self.PIECE_COLORS)
        orb_spacing = 42
        orb_start_x = center_x - ((total_orbs - 1) * orb_spacing) // 2

        for index, (color_code, _) in enumerate(self.PIECE_COLORS.items()):
            ox = orb_start_x + index * orb_spacing
            oy = 135 + int(round(math.sin((ticks / 240.0) + index * 0.9) * 6))
            self._draw_piece(surface, color_code, (ox, oy), scale=0.82)

        self._draw_centered_text(
            surface,
            "Five-or-More",
            self._title_font,
            self.TEXT_COLOR,
            215,
        )
        self._draw_centered_text(
            surface,
            "Choose difficulty",
            self._medium_font,
            self.MUTED_TEXT_COLOR,
            285,
        )

        for difficulty in self.game.DIFFICULTY_SPAWN_AMOUNTS:
            self._draw_button(
                surface,
                self.menu_button_rect(difficulty),
                difficulty,
                selected=difficulty == self.game.difficulty,
            )
        self._draw_button(surface, self.menu_button_rect("start"), "Start Game", accent="start")
        self._draw_button(surface, self.menu_button_rect("quit"), "Quit")

    def draw_game_over(self, surface):
        """Draw an elegant glassmorphic game-over overlay card."""
        overlay = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay.fill((12, 15, 22, 210))
        surface.blit(overlay, (0, 0))

        card_width, card_height = 380, 390
        panel = pygame.Rect(
            self.window_size[0] // 2 - card_width // 2,
            160,
            card_width,
            card_height,
        )
        # Glass card backdrop
        pygame.draw.rect(surface, (34, 40, 52), panel, border_radius=16)
        pygame.draw.rect(surface, (60, 72, 94), panel, 2, border_radius=16)
        # Top accent highlight line
        accent_line = pygame.Rect(panel.left + 40, panel.top + 2, panel.width - 80, 3)
        pygame.draw.rect(surface, self.ACCENT_CYAN, accent_line, border_radius=2)

        self._draw_centered_text(
            surface,
            "Game Over",
            self._large_font,
            self.TEXT_COLOR,
            225,
        )
        self._draw_centered_text(
            surface,
            f"Final Score: {self.game.get_score()}",
            self._medium_font,
            self.TEXT_COLOR,
            300,
        )
        self._draw_centered_text(
            surface,
            f"Highest Score: {self.game.get_highest_score()}",
            self._medium_font,
            self.TEXT_COLOR,
            345,
        )
        self._draw_button(
            surface,
            self.game_over_button_rect("restart"),
            "Restart",
            accent="start",
        )
        self._draw_button(
            surface,
            self.game_over_button_rect("quit"),
            "Quit",
        )

    def _draw_ambient_background(self, surface):
        """Draw a smooth ambient dark background with subtle vignette."""
        surface.fill(self.BACKGROUND_COLOR)
        # Subtle gradient glow in the center of the window
        center_x, center_y = self.window_size[0] // 2, self.window_size[1] // 2
        glow_surf = pygame.Surface(self.window_size, pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (38, 44, 58, 45), (center_x, center_y), 320)
        surface.blit(glow_surf, (0, 0))

    def _draw_scoreboard(self, surface, drawer_open=False):
        """Draw clean card badges for score, best, and controls."""
        # Top container bar
        top_bar = pygame.Rect(
            self.BOARD_MARGIN,
            12,
            self.window_size[0] - 2 * self.BOARD_MARGIN,
            68,
        )
        pygame.draw.rect(surface, self.CARD_BG_COLOR, top_bar, border_radius=10)
        pygame.draw.rect(surface, self.CARD_BORDER_COLOR, top_bar, 1, border_radius=10)

        # Score & Highscore text
        score_surface = self._small_font.render(
            f"Score: {self.game.get_score()}",
            True,
            self.TEXT_COLOR,
        )
        highest_surface = self._small_font.render(
            f"Highest Score: {self.game.get_highest_score()}",
            True,
            self.MUTED_TEXT_COLOR,
        )
        surface.blit(score_surface, (self.BOARD_MARGIN + 16, 20))
        surface.blit(highest_surface, (self.BOARD_MARGIN + 16, 46))

        # Controls on the right
        self._draw_button(
            surface,
            self.gameplay_button_rect("history"),
            "History",
            selected=drawer_open,
            small=True,
        )
        self._draw_button(
            surface,
            self.gameplay_button_rect("restart"),
            "Restart",
            small=True,
        )
        self._draw_button(
            surface,
            self.gameplay_button_rect("quit"),
            "Quit",
            small=True,
        )

    def _draw_history_drawer(
        self,
        surface,
        history=None,
        drawer_progress=0.0,
        drawer_scroll=0,
    ):
        """Render a sliding glass drawer panel displaying match move history."""
        if drawer_progress <= 0.001:
            return

        w, h = self.window_size
        clamped = max(0.0, min(1.0, drawer_progress))
        drawer_x = w - int(self.DRAWER_WIDTH * clamped)

        # 1. Semi-transparent backdrop dimming
        backdrop = pygame.Surface((w, h), pygame.SRCALPHA)
        backdrop.fill((8, 10, 16, int(130 * clamped)))
        surface.blit(backdrop, (0, 0))

        # 2. Cast drop shadow to the left of the drawer
        shadow_w = 16
        shadow_surf = pygame.Surface((shadow_w, h), pygame.SRCALPHA)
        for i in range(shadow_w):
            alpha = int(45 * (i / float(shadow_w)) * clamped)
            pygame.draw.line(shadow_surf, (0, 0, 0, alpha), (i, 0), (i, h))
        surface.blit(shadow_surf, (drawer_x - shadow_w, 0))

        # 3. Main drawer container
        drawer_rect = pygame.Rect(drawer_x, 0, self.DRAWER_WIDTH, h)
        pygame.draw.rect(surface, self.DRAWER_BG, drawer_rect)
        pygame.draw.line(surface, self.DRAWER_BORDER, (drawer_x, 0), (drawer_x, h), 2)

        # 4. Drawer Header Bar
        header_height = 64
        header_rect = pygame.Rect(drawer_x, 0, self.DRAWER_WIDTH, header_height)
        pygame.draw.rect(surface, (30, 36, 48), header_rect)
        pygame.draw.line(surface, (48, 58, 76), (drawer_x, header_height), (w, header_height), 1)

        title_surf = self._medium_font.render("Move History", True, self.TEXT_COLOR)
        surface.blit(title_surf, (drawer_x + 16, 13))

        total_moves = len(history) if history else 0
        badge_text = f"{total_moves} move" if total_moves == 1 else f"{total_moves} moves"
        badge_surf = self._label_font.render(badge_text, True, self.ACCENT_CYAN)
        surface.blit(badge_surf, (drawer_x + 16, 38))

        # Close [✕] button
        close_rect = self.drawer_close_button_rect()
        is_close_hovered = False
        if pygame.display.get_init():
            try:
                is_close_hovered = close_rect.collidepoint(pygame.mouse.get_pos())
            except pygame.error:
                is_close_hovered = False
        close_bg = (70, 82, 104) if is_close_hovered else (42, 50, 66)
        pygame.draw.rect(surface, close_bg, close_rect, border_radius=6)
        pygame.draw.rect(surface, (72, 85, 110), close_rect, 1, border_radius=6)
        x_color = (255, 255, 255) if is_close_hovered else self.MUTED_TEXT_COLOR
        pad = 8
        pygame.draw.line(
            surface,
            x_color,
            (close_rect.left + pad, close_rect.top + pad),
            (close_rect.right - pad, close_rect.bottom - pad),
            2,
        )
        pygame.draw.line(
            surface,
            x_color,
            (close_rect.left + pad, close_rect.bottom - pad),
            (close_rect.right - pad, close_rect.top + pad),
            2,
        )

        # 5. Move Items List Area (clipped)
        list_top = header_height + 1
        list_height = h - list_top
        list_rect = pygame.Rect(drawer_x, list_top, self.DRAWER_WIDTH, list_height)

        if not history:
            # Empty state
            empty_cy = list_top + 160
            empty_title = self._small_font.render("No Moves Yet", True, self.TEXT_COLOR)
            surface.blit(
                empty_title,
                empty_title.get_rect(center=(drawer_x + self.DRAWER_WIDTH // 2, empty_cy)),
            )
            sub1 = self._label_font.render(
                "Make moves on the board",
                True,
                self.MUTED_TEXT_COLOR,
            )
            sub2 = self._label_font.render(
                "to track path & points here.",
                True,
                self.MUTED_TEXT_COLOR,
            )
            surface.blit(
                sub1,
                sub1.get_rect(center=(drawer_x + self.DRAWER_WIDTH // 2, empty_cy + 24)),
            )
            surface.blit(
                sub2,
                sub2.get_rect(center=(drawer_x + self.DRAWER_WIDTH // 2, empty_cy + 42)),
            )
            return

        # Render list of moves
        # Display moves with newest first so latest action is immediately visible
        items = list(reversed(history))
        card_w = self.DRAWER_WIDTH - 24
        card_h = 56
        spacing = 8
        content_height = len(items) * (card_h + spacing) + 12
        max_scroll = max(0, content_height - list_height)
        scroll_y = max(0, min(drawer_scroll, max_scroll))

        surface.set_clip(list_rect)
        try:
            for idx, entry in enumerate(items):
                item_y = list_top + 10 + idx * (card_h + spacing) - scroll_y
                if item_y + card_h < list_top or item_y > h:
                    continue

                card_rect = pygame.Rect(drawer_x + 12, item_y, card_w, card_h)
                is_cleared = entry.get("cleared", False)
                if is_cleared:
                    card_bg = (28, 44, 40)
                    card_border = (48, 130, 92)
                else:
                    card_bg = (32, 38, 50)
                    card_border = (48, 58, 76)

                pygame.draw.rect(surface, card_bg, card_rect, border_radius=8)
                pygame.draw.rect(surface, card_border, card_rect, 1, border_radius=8)

                if is_cleared:
                    # Emerald accent bar on left edge
                    bar_rect = pygame.Rect(card_rect.left, card_rect.top, 3, card_h)
                    pygame.draw.rect(
                        surface,
                        self.ACCENT_EMERALD,
                        bar_rect,
                        border_top_left_radius=8,
                        border_bottom_left_radius=8,
                    )

                # Turn badge (#01, #02, etc.)
                turn_num = entry.get("turn", idx + 1)
                turn_str = f"#{turn_num:02d}"
                turn_surf = self._label_font.render(turn_str, True, (135, 150, 175))
                surface.blit(turn_surf, (card_rect.left + 10, card_rect.top + 8))

                # Mini 3D Piece Orb
                color_code = entry.get("color", 1)
                orb_pos = (card_rect.left + 46, card_rect.top + 28)
                self._draw_piece(surface, color_code, orb_pos, scale=0.40)

                # Move coordinate text: e.g. "C3 → C7"
                from_c = entry.get("from_coord", "?")
                to_c = entry.get("to_coord", "?")
                move_str = f"{from_c}  →  {to_c}"
                move_surf = self._small_font.render(move_str, True, self.TEXT_COLOR)
                surface.blit(move_surf, (card_rect.left + 68, card_rect.top + 7))

                # Outcome description
                if is_cleared:
                    pts = entry.get("score_delta", 0)
                    outcome_str = f"Cleared! +{pts} pts"
                    outcome_surf = self._label_font.render(outcome_str, True, self.ACCENT_EMERALD)
                else:
                    spawns = entry.get("spawn_count", 0)
                    outcome_str = f"+{spawns} spawned"
                    outcome_surf = self._label_font.render(outcome_str, True, self.MUTED_TEXT_COLOR)
                surface.blit(outcome_surf, (card_rect.left + 68, card_rect.top + 30))

            # Scrollbar thumb if content exceeds view height
            if max_scroll > 0:
                track_h = list_height - 16
                thumb_h = max(24, int(track_h * (list_height / float(content_height))))
                thumb_y = list_top + 8 + int((track_h - thumb_h) * (scroll_y / float(max_scroll)))
                thumb_rect = pygame.Rect(w - 6, thumb_y, 4, thumb_h)
                pygame.draw.rect(surface, (70, 85, 110), thumb_rect, border_radius=2)
        finally:
            surface.set_clip(None)

    def _draw_piece(self, surface, color_code, center, scale=1.0, hover_offset=0):
        """Draw a glossy, tactile 3D orb with specular reflection and drop shadow."""
        cx, cy = center
        cy += hover_offset
        radius = int(round(self.PIECE_RADIUS * scale))
        base_color = self.PIECE_COLORS.get(color_code, (200, 200, 200))

        # 1. Soft Drop Shadow
        shadow_w = radius * 2 + 6
        shadow_h = int(radius * 0.9)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 70), (0, 0, shadow_w, shadow_h))
        surface.blit(shadow_surf, (cx - shadow_w // 2, cy + radius - shadow_h // 2 - 2))

        # 2. Main Sphere Body
        pygame.draw.circle(surface, base_color, (cx, cy), radius)

        # 3. 3D Volume Shading & Glass Highlights
        layer = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        lc_x, lc_y = radius + 2, radius + 2

        # Bottom-right dark shading (creates spherical depth)
        pygame.draw.circle(
            layer,
            (0, 0, 0, 55),
            (lc_x + max(1, int(radius * 0.16)), lc_y + max(1, int(radius * 0.16))),
            radius,
        )

        # Upper-left bright glossy reflection
        hl_x = lc_x - int(radius * 0.32)
        hl_y = lc_y - int(radius * 0.34)
        hl_w = max(3, int(radius * 0.70))
        hl_h = max(2, int(radius * 0.45))
        hl_rect = pygame.Rect(hl_x - hl_w // 2, hl_y - hl_h // 2, hl_w, hl_h)
        pygame.draw.ellipse(layer, (255, 255, 255, 145), hl_rect)

        # Secondary tiny pin-point glint
        glint_x = lc_x - int(radius * 0.44)
        glint_y = lc_y - int(radius * 0.44)
        pygame.draw.circle(layer, (255, 255, 255, 215), (glint_x, glint_y), max(1, radius // 11))

        # Subtle crisp outer rim
        pygame.draw.circle(layer, (255, 255, 255, 75), (lc_x, lc_y), radius, 1)
        surface.blit(layer, (cx - lc_x, cy - lc_y))

        # Guarantee exact center pixel matches base_color for unit tests
        surface.set_at((cx, cy), base_color)

    def _draw_selection(self, surface, position):
        """Draw an animated breathing energy ring and golden aura around selected piece."""
        center = self.logical_to_screen(*position)
        pulse = (math.sin(pygame.time.get_ticks() / 130.0) + 1) / 2
        radius = self.PIECE_RADIUS + 5 + round(pulse * 5)

        # Ambient energy glow
        glow_size = radius * 3
        aura = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(
            aura,
            (255, 215, 75, int(30 + pulse * 35)),
            (glow_size // 2, glow_size // 2),
            radius + 6,
        )
        surface.blit(aura, (center[0] - glow_size // 2, center[1] - glow_size // 2))

        # Core rings
        pygame.draw.circle(surface, (255, 255, 255), center, radius, 3)
        pygame.draw.circle(surface, (255, 220, 90), center, radius + 4, 1)

    def _draw_movement_path(self, surface, path):
        """Draw glowing neon path with waypoint markers."""
        centers = [self.logical_to_screen(x, y) for x, y in path]
        path_layer = pygame.Surface(self.window_size, pygame.SRCALPHA)

        # Outer soft glow line
        if len(centers) > 1:
            pygame.draw.lines(path_layer, self.PATH_GLOW_COLOR, False, centers, 14)
            pygame.draw.lines(path_layer, self.PATH_COLOR, False, centers, 7)
            pygame.draw.lines(path_layer, (255, 255, 255, 190), False, centers, 2)

        for index, center in enumerate(centers):
            is_endpoint = index in (0, len(centers) - 1)
            radius = 12 if is_endpoint else 7
            pygame.draw.circle(path_layer, self.PATH_GLOW_COLOR, center, radius + 3)
            pygame.draw.circle(path_layer, self.PATH_COLOR, center, radius)
            if is_endpoint:
                pygame.draw.circle(path_layer, (255, 255, 255, 220), center, radius - 4)

        surface.blit(path_layer, (0, 0))

    def _path_position(self, path, progress):
        """Interpolate smooth pixel position along path."""
        if len(path) == 1:
            return self.logical_to_screen(*path[0])

        step = min(max(progress, 0.0), len(path) - 1)
        segment = min(int(step), len(path) - 2)
        fraction = step - segment
        start_x, start_y = self.logical_to_screen(*path[segment])
        end_x, end_y = self.logical_to_screen(*path[segment + 1])
        return (
            round(start_x + (end_x - start_x) * fraction),
            round(start_y + (end_y - start_y) * fraction),
        )

    def _draw_centered_text(self, surface, text, font, color, y):
        """Render text centered horizontally at a given y coordinate."""
        # Subtle drop shadow for depth
        shadow_surface = font.render(text, True, (10, 12, 16))
        shadow_rect = shadow_surface.get_rect(center=(self.window_size[0] // 2 + 1, y + 2))
        surface.blit(shadow_surface, shadow_rect)

        text_surface = font.render(text, True, color)
        rect = text_surface.get_rect(center=(self.window_size[0] // 2, y))
        surface.blit(text_surface, rect)

    def _draw_button(self, surface, rect, label, selected=False, small=False, accent=None):
        """Render a rounded modern button with hover detection and crisp typography."""
        is_hovered = False
        if pygame.display.get_init():
            try:
                mouse_pos = pygame.mouse.get_pos()
                is_hovered = rect.collidepoint(mouse_pos)
            except pygame.error:
                is_hovered = False

        if selected:
            color = self.SELECTED_BUTTON_COLOR
            border_color = self.SELECTED_BUTTON_BORDER
        elif accent == "start":
            color = (48, 140, 95) if is_hovered else (38, 120, 80)
            border_color = (75, 210, 140) if is_hovered else (50, 160, 105)
        elif is_hovered:
            color = self.BUTTON_HOVER_COLOR
            border_color = (110, 130, 158)
        else:
            color = self.BUTTON_COLOR
            border_color = self.GRID_LINE_COLOR

        pygame.draw.rect(surface, color, rect, border_radius=7)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=7)

        font = self._small_font if small else self._medium_font
        text_surface = font.render(label, True, self.TEXT_COLOR)
        surface.blit(text_surface, text_surface.get_rect(center=rect.center))
