from __future__ import annotations

from dataclasses import dataclass

import pygame

from ..config import BALL, BRICK_COLORS, BRICKS


@dataclass
class Brick:
    rect: pygame.Rect
    color: tuple[int, int, int]
    alive: bool = True


@dataclass
class ObstacleLine:
    start: tuple[int, int]
    end: tuple[int, int]
    color: tuple[int, int, int] = (255, 255, 255)


@dataclass
class ObstacleCircle:
    center: tuple[int, int]
    radius: int
    color: tuple[int, int, int] = (255, 255, 255)


@dataclass
class BallState:
    x: float
    y: float
    dx: float
    dy: float

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - BALL.radius),
            int(self.y - BALL.radius),
            BALL.radius * 2,
            BALL.radius * 2,
        )


def create_bricks(field_rect: pygame.Rect, pattern_type: str = "solid") -> list[Brick]:
    total_width = BRICKS.columns * BRICKS.width + (BRICKS.columns - 1) * BRICKS.gap
    left = field_rect.centerx - total_width // 2
    bricks: list[Brick] = []
    for row in range(BRICKS.rows):
        for column in range(BRICKS.columns):
            keep = True
            if pattern_type == "checkerboard":
                keep = (row + column) % 2 == 0
            elif pattern_type == "diamond":
                dist = abs(row - 2.5) + abs(column - 3.5)
                keep = dist <= 3.5
            elif pattern_type == "hollow":
                keep = row == 0 or row == BRICKS.rows - 1 or column == 0 or column == BRICKS.columns - 1
                
            rect = pygame.Rect(
                left + column * (BRICKS.width + BRICKS.gap),
                BRICKS.top + row * (BRICKS.height + BRICKS.gap),
                BRICKS.width,
                BRICKS.height,
            )
            brick = Brick(rect=rect, color=BRICK_COLORS[row % len(BRICK_COLORS)])
            if not keep:
                brick.alive = False
            bricks.append(brick)
    return bricks
