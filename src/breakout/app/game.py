from __future__ import annotations

import math
import random
from pathlib import Path

import pygame

from ..controllers.manual import ManualController
from ..tools.trajectory_predictor import TrajectoryPredictor, TrajectoryPrediction
from ..controllers.neural import NeuralNetworkController, NeuralPrediction
from ..controllers.llm import LLMAgentController
from ..config import BALL, GAMEPLAY, PADDLE, SCREEN, VHAL
from ..gameplay.collisions import (
    resolve_brick_collision,
    resolve_paddle_collision,
    resolve_wall_collisions,
    resolve_obstacle_line_collision,
)
from ..gameplay.entities import BallState, Brick, ObstacleLine, create_bricks
from ..hardware.vhal import VirtualPaddleHAL
from ..training.data_logger import TrainingDataLogger
from .renderer import GameRenderer
from .state import ControlMode, PlayState


class BreakoutGame:
    def __init__(self, environment_mode: str = "virtual") -> None:
        self.environment_mode = environment_mode
        pygame.init()
        title = "Breakout - Augmented Reality Mode" if self.environment_mode == "augmented" else "Breakout - Virtual Sandbox Mode"
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((SCREEN.width, SCREEN.height), pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.renderer = GameRenderer(self.screen)

        self.field_rect = pygame.Rect(32, 32, SCREEN.arena_width - 64, SCREEN.height - 64)
        self.sidebar_rect = pygame.Rect(SCREEN.arena_width, 0, SCREEN.sidebar_width, SCREEN.height)
        self.paddle_y = self.field_rect.bottom - PADDLE.y_offset
        self.paddle_min_center_x = self.field_rect.left + PADDLE.width / 2
        self.paddle_max_center_x = self.field_rect.right - PADDLE.width / 2

        self.vhal = self._new_vhal()
        self.ball = self._new_attached_ball()
        
        self.pattern_idx = 0
        self.patterns = ["solid", "checkerboard", "diamond", "hollow"]
        self.bricks: list[Brick] = create_bricks(self.field_rect, self.patterns[self.pattern_idx])
        
        self.obstacle_lines: list[ObstacleLine] = []
        self.drawing_line_start: tuple[int, int] | None = None
        self.drawing_line_end: tuple[int, int] | None = None

        self.manual_controller = ManualController()
        self.trajectory_predictor = TrajectoryPredictor()
        self.neural_controller = NeuralNetworkController()
        self.llm_controller = LLMAgentController(self.trajectory_predictor)
        self.llm_acted_this_fall = False
        self.harvest_training_data = False
        
        self.prediction: TrajectoryPrediction | None = None
        self.neural_prediction: NeuralPrediction | None = None
        self.training_logger = TrainingDataLogger(Path("training_data.csv"))

        self.control_mode = ControlMode.MANUAL
        self.state = PlayState.READY
        self.frame = 0
        self.score = 0
        self.lives = GAMEPLAY.lives
        self.elapsed_time_s = 0.0
        self.final_time_s: float | None = None
        self.popup_message = ""
        self.popup_timer = 0.0
        self.running = True

    def run(self) -> None:
        try:
            while self.running:
                dt_s = min(self.clock.tick(SCREEN.fps) / 1000.0, 1.0 / 30.0)
                if self.popup_timer > 0:
                    self.popup_timer = max(0.0, self.popup_timer - dt_s)
                self.frame += 1
                self._handle_events()
                self._handle_input()
                self._update(dt_s)
                self.renderer.draw(self)
        finally:
            self.training_logger.close()
            pygame.quit()

    def paddle_rect(self) -> pygame.Rect:
        center_x = self.vhal.position_to_pixel_center(
            self.paddle_min_center_x,
            self.paddle_max_center_x,
        )
        return pygame.Rect(
            int(center_x - PADDLE.width / 2),
            self.paddle_y,
            PADDLE.width,
            PADDLE.height,
        )

    def target_x(self) -> float:
        return self.vhal.target_to_pixel_center(
            self.paddle_min_center_x,
            self.paddle_max_center_x,
        )

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.environment_mode == "virtual":
                    self.drawing_line_start = event.pos
                    self.drawing_line_end = event.pos
            elif event.type == pygame.MOUSEMOTION:
                if self.drawing_line_start is not None and self.environment_mode == "virtual":
                    self.drawing_line_end = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.drawing_line_start is not None and self.environment_mode == "virtual":
                    self.obstacle_lines.append(ObstacleLine(
                        start=self.drawing_line_start,
                        end=event.pos,
                        color=(255, 97, 109)
                    ))
                    self.drawing_line_start = None
                    self.drawing_line_end = None

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self._handle_space()
        elif key == pygame.K_LEFT and self.state in {PlayState.READY, PlayState.LOST_BALL}:
            self.pattern_idx = (self.pattern_idx - 1) % len(self.patterns)
            self.bricks = create_bricks(self.field_rect, self.patterns[self.pattern_idx])
        elif key == pygame.K_RIGHT and self.state in {PlayState.READY, PlayState.LOST_BALL}:
            self.pattern_idx = (self.pattern_idx + 1) % len(self.patterns)
            self.bricks = create_bricks(self.field_rect, self.patterns[self.pattern_idx])
        elif key == pygame.K_1:
            self.control_mode = ControlMode.MANUAL
            self.prediction = None
            self.neural_prediction = None
            self.popup_message = "Mode: Manual Control"
            self.popup_timer = 2.0
        elif key == pygame.K_2:
            self.control_mode = ControlMode.NEURAL_NETWORK
            self.prediction = None
            self.popup_message = "Mode: Neural Network"
            self.popup_timer = 2.0
        elif key == pygame.K_3:
            self.control_mode = ControlMode.LLM_AGENT
            self.prediction = None
            self.neural_prediction = None
            self.llm_acted_this_flight = False
            self.llm_controller.clear_traces()
            self.popup_message = "Mode: LLM Agent"
            self.popup_timer = 2.0
        elif key == pygame.K_c and self.environment_mode == "virtual":
            self.obstacle_lines.clear()

    def _handle_space(self) -> None:
        if self.state in {PlayState.READY, PlayState.LOST_BALL}:
            self._launch_ball()
            self.state = PlayState.PLAYING
        elif self.state in {PlayState.CLEARED, PlayState.GAME_OVER}:
            self._restart_game()

    def _handle_input(self) -> None:
        if self.control_mode == ControlMode.NEURAL_NETWORK:
            self._handle_neural_controller_input()
            return
        if self.control_mode == ControlMode.LLM_AGENT:
            self._handle_llm_agent_input()
            return
        self._handle_manual_controller_input()

    def _handle_manual_controller_input(self) -> None:
        self.manual_controller.update_target(self.vhal, self.state)

    def force_predict_trajectory(self) -> None:
        self.neural_prediction = None
        self.prediction = self.trajectory_predictor.predict(
            ball_x=self.ball.x,
            ball_y=self.ball.y,
            ball_dx=self.ball.dx,
            ball_dy=self.ball.dy,
            strike_y=self.paddle_y - BALL.radius,
            field_rect=self.field_rect,
            paddle_min_center_x=self.paddle_min_center_x,
            paddle_max_center_x=self.paddle_max_center_x,
            track_length_mm=VHAL.track_length_mm,
            brick_rects=[brick.rect for brick in self.bricks if brick.alive],
        )
        self.vhal.set_target_mm(self.prediction.target_mm)

    def _handle_neural_controller_input(self) -> None:
        if self.neural_controller.available:
            self.force_predict_trajectory()
            base_target = self.prediction.target_mm if self.prediction else 250.0
            left_d, center_d, right_d = self._calculate_brick_densities()
            self.neural_prediction = self.neural_controller.predict_target_mm(
                ball_x=self.ball.x,
                ball_y=self.ball.y,
                ball_dx=self.ball.dx,
                ball_dy=self.ball.dy,
                left_d=left_d,
                center_d=center_d,
                right_d=right_d,
                base_target=base_target
            )
            self.vhal.set_target_mm(self.neural_prediction.target_mm)

    def _handle_llm_agent_input(self) -> None:
        if self.ball.dy > 0:
            return
            
        if self.ball.dy < 0 and not getattr(self, 'llm_acted_this_flight', False):
            self.llm_acted_this_flight = True
            
            self.llm_is_calculating = True
            
            def log_trace(msg: str):
                self.llm_controller.traces.append(msg)
                
            def do_llm_prediction():
                try:
                    target_mm = self.llm_controller.predict_target_mm(
                        ball_x=self.ball.x,
                        ball_y=self.ball.y,
                        ball_dx=self.ball.dx,
                        ball_dy=self.ball.dy,
                        strike_y=self.paddle_y - BALL.radius,
                        field_rect=self.field_rect,
                        paddle_min_center_x=self.paddle_min_center_x,
                        paddle_max_center_x=self.paddle_max_center_x,
                        track_length_mm=VHAL.track_length_mm,
                        brick_rects=[brick.rect for brick in self.bricks if brick.alive],
                        log_callback=log_trace,
                        draw_callback=lambda: None
                    )
                    self.vhal.set_target_mm(target_mm)
                except Exception as e:
                    print(f"LLM Thread Error: {e}")
                finally:
                    self.llm_is_calculating = False

            import threading
            threading.Thread(target=do_llm_prediction, daemon=True).start()

    def _update(self, dt_s: float) -> None:
        self.vhal.update(dt_s)
        if self.state in {PlayState.READY, PlayState.LOST_BALL}:
            self._attach_ball_to_paddle()
            return

        if self.state != PlayState.PLAYING:
            return

        self.elapsed_time_s += dt_s

        if getattr(self, "waiting_for_llm", False):
            if not getattr(self, "llm_is_calculating", False):
                self.waiting_for_llm = False
            else:
                return

        self.ball.x += self.ball.dx * dt_s
        self.ball.y += self.ball.dy * dt_s

        resolve_wall_collisions(self.ball, self.field_rect)
        
        old_dy = self.ball.dy
        resolve_paddle_collision(self.ball, self.paddle_rect())
        if old_dy > 0 and self.ball.dy < 0:
            self.llm_acted_this_flight = False
            
        self.score += resolve_brick_collision(self.ball, self.bricks)
        resolve_obstacle_line_collision(self.ball, self.obstacle_lines)
        
        if self.ball.dy > 0 and self.ball.y > 400 and getattr(self, "llm_is_calculating", False):
            self.waiting_for_llm = True

        if self.ball.y - BALL.radius > self.field_rect.bottom:
            self._lose_ball()
        elif all(not brick.alive for brick in self.bricks):
            self.state = PlayState.CLEARED
            self._finish_run()

        self._log_training_sample()

    def _lose_ball(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.state = PlayState.GAME_OVER
            self._finish_run()
        else:
            self.state = PlayState.LOST_BALL
        self.vhal.hold_position()
        self.ball = self._new_attached_ball()

    def _restart_game(self) -> None:
        self.score = 0
        self.lives = GAMEPLAY.lives
        self.elapsed_time_s = 0.0
        self.final_time_s = None
        self.bricks = create_bricks(self.field_rect, self.patterns[self.pattern_idx])
        self.vhal = self._new_vhal()
        self.ball = self._new_attached_ball()
        self.state = PlayState.READY
        self.prediction = None
        self.neural_prediction = None

    def _finish_run(self) -> None:
        if self.final_time_s is None:
            self.final_time_s = self.elapsed_time_s

    def _launch_ball(self) -> None:
        angle = math.radians(random.choice([58, 64, 116, 122]))
        self.ball.dx = math.cos(angle) * BALL.speed_px_s
        self.ball.dy = -abs(math.sin(angle) * BALL.speed_px_s)
        self.llm_acted_this_flight = False

    def _new_vhal(self) -> VirtualPaddleHAL:
        return VirtualPaddleHAL.centered(
            track_length_mm=VHAL.track_length_mm,
            max_velocity_mm_s=VHAL.max_velocity_mm_s,
            max_acceleration_mm_s2=VHAL.max_acceleration_mm_s2,
        )

    def _new_attached_ball(self) -> BallState:
        paddle_rect = self.paddle_rect()
        return BallState(
            x=float(paddle_rect.centerx),
            y=float(paddle_rect.top - BALL.radius - 2),
            dx=0.0,
            dy=0.0,
        )

    def _attach_ball_to_paddle(self) -> None:
        paddle_rect = self.paddle_rect()
        self.ball.x = float(paddle_rect.centerx)
        self.ball.y = float(paddle_rect.top - BALL.radius - 2)
        self.ball.dx = 0.0
        self.ball.dy = 0.0

    def _log_training_sample(self) -> None:
        if self.harvest_training_data:
            if self.prediction is not None:
                # Calculate strategic aiming offset for the training dataset
                alive_bricks = [b for b in self.bricks if b.alive]
                desired_offset = 0.0
                left_d, center_d, right_d = self._calculate_brick_densities()
                if alive_bricks:
                    # Target the highest density zone to perfectly correlate with the Neural Network's features
                    densities = [
                        (left_d, self.field_rect.left + self.field_rect.width / 6.0),
                        (center_d, self.field_rect.left + self.field_rect.width / 2.0),
                        (right_d, self.field_rect.left + 5.0 * self.field_rect.width / 6.0),
                    ]
                    densities.sort(key=lambda x: x[0], reverse=True)
                    best_target_x = densities[0][1]
                    
                    lowest_bottom = max(b.rect.bottom for b in alive_bricks)
                    
                    from ..config import BRICKS, PADDLE, VHAL, BALL
                    from ..tools.aim_predictor import calculate_paddle_offset
                    offset_px = calculate_paddle_offset(
                        landing_x=self.prediction.impact_x_px,
                        paddle_y=self.paddle_y - BALL.radius,
                        target_brick_x=best_target_x,
                        target_brick_y=lowest_bottom - BRICKS.height / 2,
                        paddle_width=PADDLE.width
                    )
                    
                    px_range = self.paddle_max_center_x - self.paddle_min_center_x
                    offset_mm = offset_px * (VHAL.track_length_mm / px_range) if px_range > 0 else 0.0
                    
                    # Paddle center must shift opposite to the desired ball impact point
                    desired_offset = -offset_mm

                self.training_logger.log(
                    frame=self.frame,
                    ball_x=self.ball.x,
                    ball_y=self.ball.y,
                    ball_dx=self.ball.dx,
                    ball_dy=self.ball.dy,
                    left_d=left_d,
                    center_d=center_d,
                    right_d=right_d,
                    target_paddle_mm=desired_offset,
                )

    def _calculate_brick_densities(self) -> tuple[float, float, float]:
        if not self.bricks:
            return 0.0, 0.0, 0.0
            
        third = self.field_rect.width / 3.0
        left_count = center_count = right_count = 0
        left_total = center_total = right_total = 0
        
        for brick in self.bricks:
            if brick.rect.centerx < self.field_rect.left + third:
                left_total += 1
                if brick.alive: left_count += 1
            elif brick.rect.centerx < self.field_rect.left + 2 * third:
                center_total += 1
                if brick.alive: center_count += 1
            else:
                right_total += 1
                if brick.alive: right_count += 1
                
        l_dens = left_count / left_total if left_total else 0.0
        c_dens = center_count / center_total if center_total else 0.0
        r_dens = right_count / right_total if right_total else 0.0
        
        return l_dens, c_dens, r_dens


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="AI Augmented Breakout")
    parser.add_argument("--mode", type=str, choices=["virtual", "augmented"], default="virtual", help="Environment mode: 'virtual' for mouse drawing, 'augmented' for camera tracking.")
    args = parser.parse_args()
    BreakoutGame(environment_mode=args.mode).run()
