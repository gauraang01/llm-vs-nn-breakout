from __future__ import annotations

import math

import pygame

from ..config import BALL, PADDLE
from .entities import BallState, Brick, ObstacleLine, ObstacleCircle


def resolve_wall_collisions(ball: BallState, field_rect: pygame.Rect) -> None:
    if ball.x - BALL.radius <= field_rect.left:
        ball.x = field_rect.left + BALL.radius
        ball.dx = abs(ball.dx)
    elif ball.x + BALL.radius >= field_rect.right:
        ball.x = field_rect.right - BALL.radius
        ball.dx = -abs(ball.dx)

    if ball.y - BALL.radius <= field_rect.top:
        ball.y = field_rect.top + BALL.radius
        ball.dy = abs(ball.dy)


def resolve_paddle_collision(ball: BallState, paddle_rect: pygame.Rect) -> None:
    if ball.dy <= 0 or not ball.rect.colliderect(paddle_rect):
        return

    ball.y = paddle_rect.top - BALL.radius
    offset = (ball.x - paddle_rect.centerx) / (PADDLE.width / 2)
    offset = max(-1.0, min(1.0, offset))
    angle = math.radians(90 - offset * 58)
    speed = max(BALL.speed_px_s, math.hypot(ball.dx, ball.dy) * 1.01)
    ball.dx = math.cos(angle) * speed
    ball.dy = -abs(math.sin(angle) * speed)


def resolve_brick_collision(ball: BallState, bricks: list[Brick]) -> int:
    ball_rect = ball.rect
    for brick in bricks:
        if not brick.alive or not ball_rect.colliderect(brick.rect):
            continue

        brick.alive = False

        # Determine collision face by normalizing the distance from the brick's center
        dx = ball.x - brick.rect.centerx
        dy = ball.y - brick.rect.centery
        
        # Normalize by the brick's dimensions
        norm_x = abs(dx) / (brick.rect.width / 2)
        norm_y = abs(dy) / (brick.rect.height / 2)
        
        if norm_x > norm_y:
            ball.dx *= -1
        else:
            ball.dy *= -1
        return 100

    return 0

def resolve_obstacle_line_collision(ball: BallState, lines: list[ObstacleLine]) -> None:
    for line in lines:
        lx = line.end[0] - line.start[0]
        ly = line.end[1] - line.start[1]
        line_len_sq = lx**2 + ly**2
        
        if line_len_sq == 0:
            continue
            
        vx = ball.x - line.start[0]
        vy = ball.y - line.start[1]
        
        t = (vx * lx + vy * ly) / line_len_sq
        t = max(0.0, min(1.0, t))
        
        closest_x = line.start[0] + t * lx
        closest_y = line.start[1] + t * ly
        
        dx = ball.x - closest_x
        dy = ball.y - closest_y
        dist_sq = dx**2 + dy**2
        
        if dist_sq <= BALL.radius**2:
            dist = math.sqrt(dist_sq)
            if dist == 0:
                dist = 0.0001
                dx = 1
                dy = 0
                
            nx = dx / dist
            ny = dy / dist
            
            overlap = BALL.radius - dist
            ball.x += nx * overlap
            ball.y += ny * overlap
            
            dot = ball.dx * nx + ball.dy * ny
            
            if dot < 0:
                ball.dx -= 2 * dot * nx
                ball.dy -= 2 * dot * ny


def resolve_obstacle_circle_collision(ball: BallState, circles: list[ObstacleCircle]) -> None:
    for circle in circles:
        dx = ball.x - circle.center[0]
        dy = ball.y - circle.center[1]
        dist_sq = dx**2 + dy**2
        min_dist = BALL.radius + circle.radius
        
        if dist_sq <= min_dist**2:
            dist = math.sqrt(dist_sq)
            if dist == 0:
                dist = 0.0001
                dx = 1
                dy = 0
                
            nx = dx / dist
            ny = dy / dist
            
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.y += ny * overlap
            
            dot = ball.dx * nx + ball.dy * ny
            
            if dot < 0:
                ball.dx -= 2 * dot * nx
                ball.dy -= 2 * dot * ny
                return # Only bounce once per frame to prevent infinite ping-pong between overlapping magnets!
