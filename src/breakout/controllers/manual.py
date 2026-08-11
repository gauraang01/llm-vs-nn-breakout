from __future__ import annotations

import pygame

from ..config import VHAL
from ..app.state import PlayState
from ..hardware.vhal import VirtualPaddleHAL


class ManualController:
    def update_target(self, vhal: VirtualPaddleHAL, play_state: PlayState) -> None:
        keys = pygame.key.get_pressed()
        
        if play_state != PlayState.PLAYING:
            vhal.hold_position()
            return
            
        if keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            vhal.set_target_mm(0.0)
        elif keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
            vhal.set_target_mm(VHAL.track_length_mm)
        else:
            vhal.hold_position()
