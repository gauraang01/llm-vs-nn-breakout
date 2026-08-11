from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenConfig:
    width: int = 1440
    height: int = 900
    fps: int = 60
    arena_width: int = 990
    sidebar_width: int = 450


@dataclass(frozen=True)
class VHALConfig:
    track_length_mm: float = 500.0
    max_velocity_right_mm_s: float = 320.0
    max_velocity_left_mm_s: float = 320.0
    max_acceleration_mm_s2: float = 1000.0
    steps_per_mm: float = 20.0


@dataclass(frozen=True)
class PaddleConfig:
    width: int = 148
    height: int = 20
    y_offset: int = 68


@dataclass(frozen=True)
class BallConfig:
    radius: int = 12
    speed_px_s: float = 300.0


@dataclass(frozen=True)
class BrickConfig:
    rows: int = 6
    columns: int = 8
    width: int = 96
    height: int = 26
    gap: int = 12
    top: int = 92


@dataclass(frozen=True)
class GameplayConfig:
    lives: int = 1


@dataclass(frozen=True)
class LLMConfig:
    model: str = "qwen2.5:7b"


SCREEN = ScreenConfig()

def _load_vhal_config() -> VHALConfig:
    import json
    from pathlib import Path
    config_path = Path(__file__).resolve().parent.parent.parent / "rail_config.json"
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
                return VHALConfig(
                    track_length_mm=cfg.get("track_length_mm", 500.0),
                    max_velocity_right_mm_s=cfg.get("max_velocity_right_mm_s", cfg.get("max_velocity_mm_s", 320.0)),
                    max_velocity_left_mm_s=cfg.get("max_velocity_left_mm_s", cfg.get("max_velocity_mm_s", 320.0)),
                    max_acceleration_mm_s2=cfg.get("max_acceleration_mm_s2", 1000.0),
                    steps_per_mm=cfg.get("steps_per_mm", 20.0)
                )
        except Exception:
            pass
    return VHALConfig()

VHAL = _load_vhal_config()
PADDLE = PaddleConfig()
BALL = BallConfig()
BRICKS = BrickConfig()
GAMEPLAY = GameplayConfig()
LLM = LLMConfig()


COLORS = {
    "background": (12, 14, 18),
    "field": (20, 24, 31),
    "field_border": (67, 75, 91),
    "text": (229, 233, 240),
    "muted_text": (151, 161, 178),
    "paddle": (76, 201, 240),
    "paddle_target": (248, 197, 85),
    "ball": (248, 248, 242),
    "overlay": (28, 33, 42),
    "danger": (255, 97, 109),
    "agentic_purple": (155, 89, 182),
}

BRICK_COLORS = [
    (240, 240, 240),  # White
    (210, 210, 210),  # Light Gray
    (180, 180, 180),  # Gray
    (150, 150, 150),  # Medium Gray
    (120, 120, 120),  # Dark Gray
    (90, 90, 90),     # Very Dark Gray
]
