from __future__ import annotations

import pygame

from ..config import BALL, COLORS, SCREEN
from .state import PlayState, ControlMode
from .time_utils import format_optional_time, format_time


class GameRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.Font(None, 22)
        self.large_font = pygame.font.Font(None, 48)
        self.medium_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 18)

    def draw(self, game) -> None:
        self.screen.fill(COLORS["background"])
        
        is_mode_4 = game.control_mode == ControlMode.LLM_AGENT
        field_border_color = COLORS["agentic_purple"] if is_mode_4 else COLORS["field_border"]
        
        pygame.draw.rect(self.screen, COLORS["field"], game.field_rect, border_radius=4)
        pygame.draw.rect(
            self.screen,
            field_border_color,
            game.field_rect,
            width=2,
            border_radius=4,
        )

        self._draw_bricks(game)
        self._draw_obstacle_lines(game)
        self._draw_paddle(game)
        pygame.draw.circle(
            self.screen,
            COLORS["ball"],
            (int(game.ball.x), int(game.ball.y)),
            BALL.radius,
        )
        self._draw_overlay(game)
        self._draw_sidebar(game)
        self._draw_state_message(game)
        self._draw_popups(game)
        pygame.display.flip()

    def _draw_bricks(self, game) -> None:
        for brick in game.bricks:
            if not brick.alive:
                continue
            pygame.draw.rect(self.screen, brick.color, brick.rect, border_radius=3)
            highlight = brick.rect.copy()
            highlight.height = 4
            pygame.draw.rect(self.screen, (255, 255, 255, 70), highlight, border_radius=3)

    def _draw_obstacle_lines(self, game) -> None:
        for line in game.obstacle_lines:
            pygame.draw.line(self.screen, line.color, line.start, line.end, 4)
            pygame.draw.circle(self.screen, line.color, line.start, 3)
            pygame.draw.circle(self.screen, line.color, line.end, 3)
        for circle in getattr(game, 'obstacle_circles', []):
            pygame.draw.circle(self.screen, circle.color, circle.center, circle.radius, 2)
            pygame.draw.circle(self.screen, circle.color, circle.center, 2)
        if game.drawing_line_start is not None and game.drawing_line_end is not None:
            pygame.draw.line(self.screen, (255, 255, 255), game.drawing_line_start, game.drawing_line_end, 2)

    def _draw_paddle(self, game) -> None:
        paddle_rect = game.paddle_rect()
        target_x = int(game.target_x())
        pygame.draw.line(
            self.screen,
            COLORS["paddle_target"],
            (target_x, paddle_rect.top - 14),
            (target_x, paddle_rect.bottom + 14),
            2,
        )
        pygame.draw.rect(self.screen, COLORS["paddle"], paddle_rect, border_radius=4)
        pygame.draw.rect(self.screen, (197, 244, 255), paddle_rect, width=2, border_radius=4)

    def _draw_overlay(self, game) -> None:
        # Move overlay to the bottom of the right sidebar to avoid obstructing the paddle
        overlay_rect = pygame.Rect(
            game.sidebar_rect.left + 24,
            SCREEN.height - 236,
            game.sidebar_rect.width - 48,
            188
        )
        pygame.draw.rect(self.screen, COLORS["background"], overlay_rect)
        pygame.draw.rect(self.screen, COLORS["field_border"], overlay_rect, width=2, border_radius=4)

        paddle_rect = game.paddle_rect()
        predicted_x = game.prediction.impact_x_px if game.prediction else game.ball.x
        target_x = game.prediction.target_x_px if game.prediction else game.target_x()
        angled = "yes" if game.prediction and game.prediction.angled_hit else "no"
        neural_status = "loaded" if game.neural_controller.available else game.neural_controller.load_error
        lines = [
            f"Mode: {game.control_mode.value}  (1 manual, 2 neural, 3 agent)",
            f"Time: {format_time(game.elapsed_time_s)} | Finish: {format_optional_time(game.final_time_s)}",
            f"Ball X,Y: {game.ball.x:7.1f}, {game.ball.y:7.1f}",
            f"Ball dX,dY: {game.ball.dx:7.1f}, {game.ball.dy:7.1f} px/s",
            f"Paddle: {paddle_rect.centerx:6.1f}px | {game.vhal.position_mm:6.1f}mm",
            f"Target: {game.vhal.target_mm:6.1f}mm | V: {game.vhal.velocity_mm_s:7.1f}mm/s",
            f"Impact X: {predicted_x:7.1f}px | Target X: {target_x:7.1f}px",
            f"Forced angled hit: {angled}",
            f"Neural model: {neural_status}",
            f"Vmax: {game.vhal.max_velocity_mm_s:.0f}mm/s | Amax: {game.vhal.max_acceleration_mm_s2:.0f}mm/s2",
        ]
        for index, line in enumerate(lines):
            color = COLORS["text"] if index < 3 else COLORS["muted_text"]
            surface = self.small_font.render(line, True, color)
            self.screen.blit(surface, (overlay_rect.left + 14, overlay_rect.top + 10 + index * 18))

        status = (
            f"Score {game.score}   Lives {game.lives}   Time {format_time(game.elapsed_time_s)}   "
            f"Finish {format_optional_time(game.final_time_s)}   State {game.state.value}   "
            f"Mode {game.control_mode.value}"
        )
        surface = self.font.render(status, True, COLORS["text"])
        self.screen.blit(surface, (game.field_rect.left, game.field_rect.top - 26))

    def _draw_state_message(self, game) -> None:
        messages = {
            PlayState.READY: "Press Space to Launch",
            PlayState.LOST_BALL: "Ball Lost - Press Space",
            PlayState.CLEARED: "Stage Clear - Press Space",
            PlayState.GAME_OVER: "Game Over - Press Space",
        }
        message = messages.get(game.state)
        if not message:
            return

        surface = self.large_font.render(message, True, COLORS["text"])
        shadow = self.large_font.render(message, True, (0, 0, 0))
        rect = surface.get_rect(center=(game.field_rect.centerx, game.field_rect.centery + 60))
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(surface, rect)
        
        if game.state in {PlayState.READY, PlayState.LOST_BALL}:
            map_msg = f"Map: {game.patterns[game.pattern_idx].upper()} (Use LEFT/RIGHT)"
            map_surface = self.medium_font.render(map_msg, True, COLORS["paddle"])
            map_shadow = self.medium_font.render(map_msg, True, (0, 0, 0))
            map_rect = map_surface.get_rect(center=(game.field_rect.centerx, game.field_rect.centery + 100))
            self.screen.blit(map_shadow, map_rect.move(2, 2))
            self.screen.blit(map_surface, map_rect)
            
            mode_msg = "Switch Modes: [1] Manual  [2] Neural Net  [3] LLM Agent"
            mode_surface = self.small_font.render(mode_msg, True, COLORS["muted_text"])
            mode_rect = mode_surface.get_rect(center=(game.field_rect.centerx, game.field_rect.centery + 140))
            self.screen.blit(mode_surface, mode_rect)

    def _draw_sidebar(self, game) -> None:
        sidebar_rect = game.sidebar_rect
        pygame.draw.rect(self.screen, COLORS["background"], sidebar_rect)
        
        is_mode_4 = game.control_mode == ControlMode.LLM_AGENT
        is_mode_3 = game.control_mode == ControlMode.NEURAL_NETWORK
        
        if is_mode_4:
            sidebar_border_color = COLORS["agentic_purple"]
            title_color = COLORS["agentic_purple"]
            title_text = "LLM Agent Telemetry"
        elif is_mode_3:
            sidebar_border_color = COLORS["paddle"]
            title_color = COLORS["paddle"]
            title_text = "Neural Net Telemetry"
        else:
            sidebar_border_color = COLORS["field_border"]
            title_color = COLORS["muted_text"]
            title_text = "Controller Telemetry"

        pygame.draw.line(self.screen, sidebar_border_color, sidebar_rect.topleft, sidebar_rect.bottomleft, 2)
        
        title = self.medium_font.render(title_text, True, title_color)
        self.screen.blit(title, (sidebar_rect.left + 24, sidebar_rect.top + 32))
        
        # Draw mode switcher segmented buttons
        modes = [
            (ControlMode.MANUAL, "1: Manual"),
            (ControlMode.NEURAL_NETWORK, "2: Neural Net"),
            (ControlMode.LLM_AGENT, "3: LLM Agent")
        ]
        
        mode_y = sidebar_rect.top + 76
        mode_w = (sidebar_rect.width - 48 - 16) / 3
        
        for idx, (mode, label) in enumerate(modes):
            is_active = game.control_mode == mode
            rect = pygame.Rect(sidebar_rect.left + 24 + idx * (mode_w + 8), mode_y, mode_w, 24)
            
            if is_active:
                pygame.draw.rect(self.screen, title_color, rect, border_radius=4)
                text_color = COLORS["background"]
            else:
                pygame.draw.rect(self.screen, COLORS["field_border"], rect, width=1, border_radius=4)
                text_color = COLORS["muted_text"]
                
            surf = self.small_font.render(label, True, text_color)
            surf_rect = surf.get_rect(center=rect.center)
            self.screen.blit(surf, surf_rect)
        
        y_offset = 120
        
        def draw_wrapped_text(text: str, color: tuple, y: int) -> int:
            words = text.split(' ')
            space_w, _ = self.small_font.size(' ')
            max_width = sidebar_rect.width - 48
            line_words = []
            current_w = 0
            
            for word in words:
                word_w, _ = self.small_font.size(word)
                if word_w > max_width:
                    if line_words:
                        surface = self.small_font.render(' '.join(line_words), True, color)
                        self.screen.blit(surface, (sidebar_rect.left + 24, sidebar_rect.top + y))
                        y += 24
                        line_words = []
                        current_w = 0
                        
                    char_line = ""
                    for char in word:
                        if self.small_font.size(char_line + char)[0] > max_width:
                            surface = self.small_font.render(char_line, True, color)
                            self.screen.blit(surface, (sidebar_rect.left + 24, sidebar_rect.top + y))
                            y += 24
                            char_line = char
                        else:
                            char_line += char
                    if char_line:
                        line_words = [char_line]
                        current_w = self.small_font.size(char_line)[0] + space_w
                elif current_w + word_w > max_width:
                    if line_words:
                        surface = self.small_font.render(' '.join(line_words), True, color)
                        self.screen.blit(surface, (sidebar_rect.left + 24, sidebar_rect.top + y))
                        y += 24
                    line_words = [word]
                    current_w = word_w + space_w
                else:
                    line_words.append(word)
                    current_w += word_w + space_w
            
            if line_words:
                surface = self.small_font.render(' '.join(line_words), True, color)
                self.screen.blit(surface, (sidebar_rect.left + 24, sidebar_rect.top + y))
                y += 24
            return y
        
        if is_mode_4:
            for trace in game.llm_controller.traces:
                y_offset = draw_wrapped_text(trace, COLORS["agentic_purple"], y_offset)
                
        elif is_mode_3:
            neural = game.neural_controller
            if neural.available:
                status = "Status: ONLINE (mlp_model.pt loaded)"
                
                left_d, center_d, right_d = game._calculate_brick_densities()
                features = f"Input Vector: [X={game.ball.x:.0f}, Y={game.ball.y:.0f}, dX={game.ball.dx:.0f}, dY={game.ball.dy:.0f}, L={left_d:.1f}, C={center_d:.1f}, R={right_d:.1f}]"
                target = f"Target Coordinate: {game.vhal.target_mm:.1f} mm"
                
                y_offset = draw_wrapped_text(status, COLORS["paddle"], y_offset)
                y_offset += 12
                y_offset = draw_wrapped_text(features, COLORS["text"], y_offset)
                y_offset += 12
                y_offset = draw_wrapped_text(target, COLORS["paddle_target"], y_offset)
            else:
                y_offset = draw_wrapped_text(f"Status: OFFLINE ({neural.load_error})", COLORS["danger"], y_offset)

    def _draw_popups(self, game) -> None:
        # 1. Mode Switch Popup
        if getattr(game, "popup_timer", 0) > 0 and getattr(game, "popup_message", ""):
            alpha = min(255, int(game.popup_timer * 255 * 2))
            
            surf = self.medium_font.render(game.popup_message, True, COLORS["background"])
            padding_x, padding_y = 40, 20
            rect = surf.get_rect(center=(game.field_rect.centerx, game.field_rect.top + 60))
            bg_rect = rect.inflate(padding_x, padding_y)
            
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            color = COLORS["paddle"] if game.control_mode == ControlMode.NEURAL_NETWORK else COLORS["agentic_purple"] if game.control_mode == ControlMode.LLM_AGENT else COLORS["text"]
            
            if len(color) == 3:
                color = (*color, 255)
            
            pygame.draw.rect(bg_surface, (*color[:3], alpha), bg_surface.get_rect(), border_radius=8)
            
            text_color = COLORS["background"]
            text_surf = self.medium_font.render(game.popup_message, True, (*text_color[:3], alpha))
            bg_surface.blit(text_surf, (padding_x // 2, padding_y // 2))
            
            self.screen.blit(bg_surface, bg_rect)
