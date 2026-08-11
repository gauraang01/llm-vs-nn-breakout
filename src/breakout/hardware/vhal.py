from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class VirtualPaddleHAL:
    track_length_mm: float
    max_velocity_right_mm_s: float
    max_velocity_left_mm_s: float
    max_acceleration_mm_s2: float
    position_mm: float = 0.0
    target_mm: float = 0.0
    velocity_mm_s: float = 0.0
    
    @property
    def max_velocity_mm_s(self) -> float:
        return (self.max_velocity_right_mm_s + self.max_velocity_left_mm_s) / 2.0
    
    @max_velocity_mm_s.setter
    def max_velocity_mm_s(self, value: float) -> None:
        self.max_velocity_right_mm_s = value
        self.max_velocity_left_mm_s = value

    def __post_init__(self) -> None:
        self.position_mm = self._clamp(self.position_mm)
        self.target_mm = self._clamp(self.target_mm)

    @classmethod
    def centered(
        cls,
        track_length_mm: float,
        max_velocity_right_mm_s: float,
        max_velocity_left_mm_s: float,
        max_acceleration_mm_s2: float,
    ) -> "VirtualPaddleHAL":
        center = track_length_mm / 2.0
        return cls(
            track_length_mm=track_length_mm,
            max_velocity_right_mm_s=max_velocity_right_mm_s,
            max_velocity_left_mm_s=max_velocity_left_mm_s,
            max_acceleration_mm_s2=max_acceleration_mm_s2,
            position_mm=center,
            target_mm=center,
        )

    def set_target_mm(self, target_mm: float) -> None:
        self.target_mm = self._clamp(target_mm)

    def hold_position(self) -> None:
        self.target_mm = self.position_mm

    def update(self, dt_s: float) -> None:
        if dt_s <= 0:
            return

        distance = self.target_mm - self.position_mm
        if abs(distance) < 0.01 and abs(self.velocity_mm_s) < 0.05:
            self.position_mm = self.target_mm
            self.velocity_mm_s = 0.0
            return

        direction = _sign(distance)
        stopping_distance = (self.velocity_mm_s * self.velocity_mm_s) / (
            2.0 * self.max_acceleration_mm_s2
        )

        moving_toward_target = _sign(self.velocity_mm_s) == direction
        should_brake = moving_toward_target and stopping_distance >= abs(distance)

        if direction == 0:
            desired_velocity = 0.0
        elif should_brake:
            desired_velocity = 0.0
        else:
            desired_velocity = self.max_velocity_right_mm_s if direction > 0 else -self.max_velocity_left_mm_s

        self.velocity_mm_s = _approach(
            self.velocity_mm_s,
            desired_velocity,
            self.max_acceleration_mm_s2 * dt_s,
        )
        self.velocity_mm_s = max(
            -self.max_velocity_left_mm_s,
            min(self.max_velocity_right_mm_s, self.velocity_mm_s),
        )

        previous_position = self.position_mm
        self.position_mm = self._clamp(self.position_mm + self.velocity_mm_s * dt_s)

        crossed_target = (
            previous_position <= self.target_mm <= self.position_mm
            or self.position_mm <= self.target_mm <= previous_position
        )
        if should_brake and crossed_target:
            self.position_mm = self.target_mm
            self.velocity_mm_s = 0.0

        if self.position_mm in (0.0, self.track_length_mm):
            if (self.position_mm == 0.0 and self.velocity_mm_s < 0) or (
                self.position_mm == self.track_length_mm and self.velocity_mm_s > 0
            ):
                self.velocity_mm_s = 0.0

    def position_to_pixel_center(self, min_x: float, max_x: float) -> float:
        if math.isclose(self.track_length_mm, 0.0):
            return min_x
        normalized = self.position_mm / self.track_length_mm
        return min_x + normalized * (max_x - min_x)

    def target_to_pixel_center(self, min_x: float, max_x: float) -> float:
        if math.isclose(self.track_length_mm, 0.0):
            return min_x
        normalized = self.target_mm / self.track_length_mm
        return min_x + normalized * (max_x - min_x)

    def pixel_center_to_position_mm(self, pixel_x: float, min_x: float, max_x: float) -> float:
        if math.isclose(min_x, max_x):
            return 0.0
        normalized = (pixel_x - min_x) / (max_x - min_x)
        return self._clamp(normalized * self.track_length_mm)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(self.track_length_mm, value))


def _approach(current: float, target: float, max_delta: float) -> float:
    if current < target:
        return min(current + max_delta, target)
    if current > target:
        return max(current - max_delta, target)
    return target


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0

import serial
import serial.tools.list_ports
import threading
import time

class PhysicalPaddleHAL(VirtualPaddleHAL):
    def __init__(self, track_length_mm: float, max_velocity_right_mm_s: float, max_velocity_left_mm_s: float, max_acceleration_mm_s2: float, port: str = 'auto', baudrate: int = 115200):
        super().__init__(track_length_mm, max_velocity_right_mm_s, max_velocity_left_mm_s, max_acceleration_mm_s2)
        
        if port == 'auto':
            ports = list(serial.tools.list_ports.comports())
            usb_ports = [p.device for p in ports if 'usbmodem' in p.device or 'usbserial' in p.device]
            self.port = usb_ports[0] if usb_ports else '/dev/cu.usbmodem114301'
        else:
            self.port = port
            
        self.baudrate = baudrate
        self.baudrate = 115200
        self._running = True
        self.jog_direction = 'S'
        self.jog_target_step = 0
        self.steps_per_mm = 20.0 # Default, will be overwritten by calibration
        self.is_jogging = False
        self.is_calibrated = False
        
        try:
            print(f"[PhysicalHAL] Connecting to Arduino on {self.port}...")
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(2) # Wait for Arduino to wake up
            self.serial_conn.write(b"Z\n")
            print("[PhysicalHAL] Success! Arduino is ready.")
        except Exception as e:
            print(f"[PhysicalHAL] Error: Could not connect to {self.port}. Is the Serial Monitor closed?")
            self.serial_conn = None
            
        self.thread = threading.Thread(target=self._serial_loop, daemon=True)
        self.thread.start()
        
    @classmethod
    def centered(
        cls,
        track_length_mm: float,
        max_velocity_right_mm_s: float,
        max_velocity_left_mm_s: float,
        max_acceleration_mm_s2: float,
    ) -> "PhysicalPaddleHAL":
        center = track_length_mm / 2.0
        instance = cls(track_length_mm, max_velocity_right_mm_s, max_velocity_left_mm_s, max_acceleration_mm_s2)
        instance.position_mm = center
        instance.target_mm = center
        return instance
        
    def _serial_loop(self):
        while self._running:
            if self.serial_conn:
                if getattr(self, 'is_jogging', False):
                    # Manual Step Jogging
                    if getattr(self, 'jog_direction', 'S') == 'L':
                        self.jog_target_step -= 10
                    elif getattr(self, 'jog_direction', 'S') == 'R':
                        self.jog_target_step += 10
                    cmd = f"P{self.jog_target_step}\n"
                    try: self.serial_conn.write(cmd.encode())
                    except Exception: pass
                elif getattr(self, 'is_calibrated', False):
                    # Absolute Position Tracking
                    target_step = int(self.position_mm * self.steps_per_mm)
                    # Sync the jog target so it doesn't jump if we switch back to jog
                    self.jog_target_step = target_step 
                    cmd = f"P{target_step}\n"
                    try: self.serial_conn.write(cmd.encode())
                    except Exception: pass
            time.sleep(1/120.0) # 120Hz update rate
            
    def __del__(self):
        self._running = False
        if self.serial_conn:
            self.serial_conn.close()
