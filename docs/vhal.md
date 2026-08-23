# V-HAL Specification

## Purpose

The Virtual Hardware Abstraction Layer constrains the digital paddle to move like
a physical paddle on a linear rail. This prevents impossible game behavior such
as instantaneous teleporting to the ball.

## Physical Track

- Track minimum: `0 mm`
- Track maximum: `500 mm`
- The full physical track maps to the playable horizontal paddle range on the
  screen.
- The paddle center is represented internally in millimeters.

## Motion Model

The V-HAL stores:

- `position_mm`: current paddle center on the simulated rail.
- `target_mm`: requested paddle center.
- `velocity_mm_s`: current rail velocity.
- `max_velocity_mm_s`: simulated maximum motor-driven rail speed.
- `max_acceleration_mm_s2`: simulated acceleration and braking limit.

Each frame, the V-HAL:

1. Clamps the target to the rail.
2. Computes the distance from current position to target.
3. Selects a desired velocity toward the target.
4. Applies acceleration limits to approach that desired velocity.
5. Brakes when stopping distance would overshoot the target.
6. Clamps final position and velocity at the rail boundaries.

## Default Constants

The first-stage defaults are deliberately conservative and visible in the
telemetry overlay. They are tuned to feel closer to an Arduino-driven NEMA 17
prototype on a rail, where the paddle has noticeable travel time and braking
latency:

- `TRACK_LENGTH_MM = 500`
- `MAX_VELOCITY_MM_S = 320`
- `MAX_ACCELERATION_MM_S2 = 1000`

With these defaults, moving across the full 500 mm track takes about 1.9 seconds
including acceleration and braking. These values are still placeholders; the
final numbers should be adjusted after measuring the real mechanical system,
driver microstepping, belt or lead-screw pitch, supply voltage, and moving mass.

## Control Contract
 
 All paddle movement must go through:
 
 ```python
 vhal.set_target_mm(target_mm)
 vhal.update(dt_seconds)
 ```
 
 Game code should then read `vhal.position_mm` or use the mapping helper to derive
 the paddle's pixel position.
 
 ## Physical Hardware (`PhysicalPaddleHAL`)
 
 When the game is launched with the `--hardware` flag, the engine swaps `VirtualPaddleHAL` for `PhysicalPaddleHAL`.
 
 - Connects to an Arduino running `arduino/rail.ino` over a Serial USB connection at 115200 baud.
 - Runs an asynchronous thread at 120Hz to send an Absolute Position Step protocol (e.g., `P<step_count>\n`).
 - **Jog Calibration**: Users can press `j` in-game to enter Calibration Mode. This allows the user to manually jog the motor to the left and right bounds to calculate the exact `steps_per_mm` multiplier, ensuring the physical paddle aligns flawlessly with the virtual projection.
 - Speeds and acceleration limits can be configured interactively using `python start.py --rail-config` and are saved to `rail_config.json`.
