# Breakout Project

This project builds a Breakout-style game in stages around a Virtual Hardware
Abstraction Layer (V-HAL). The game is intentionally constrained by physical
motion rules so the simulated paddle behaves like a real paddle driven along a
linear track by a NEMA 17 stepper motor.

## Current Stage

Stage 5: Augmented Reality Setup (Current)

- Human control through left and right arrow keys (Mode 1).
- Neural-network control (Mode 2) after training.
- LLM Agent control (Mode 3) using a local Ollama model to predict targets via tool-calling.
- Virtual Obstacle Drawing: use the mouse to click-and-drag and draw indestructible line-segment obstacles into the game arena. Press `C` to clear them.
- Vector reflection mechanics handle dynamic Circle-Line segment collisions so the ball perfectly reflects off angled lines.
- A fully playable Breakout field with ball, bricks (Solid, Checkerboard, Diamond, Hollow), paddle, scoring, lives, and restart flow.
- Maps can be switched before launching the ball using the Left/Right arrow keys.
- The game currently uses one life and records elapsed/finish time in the UI.
- The paddle is not moved directly by keyboard input. Keyboard input updates a V-HAL target position, and the V-HAL moves the paddle using velocity and acceleration limits.
- The Trajectory Predictor predicts the paddle target with reflection geometry and can silently write training samples to `training_data.csv`.
- The Neural Network Controller loads `mlp_model.pt` and `scaler.json`, predicts the paddle target from observed ball state, and routes that target through V-HAL.
- A dynamic UI featuring mode-switch popups and a segmented telemetry sidebar exposes ball coordinates, tool-calling traces, and V-HAL physical limits.

## Documentation Map

- [Architecture](architecture.md): module layout, runtime flow, and extension
  points.
- [V-HAL Specification](vhal.md): physical model, coordinate mapping, and
  constraints.
- [Stage 1 Manual Sandbox](stage-1-manual-sandbox.md): gameplay scope and manual
  control behavior.
- [Stage 2 Mathematical Controller](stage-2-mathematical-controller.md): autonomous
  geometry controller and data harvesting schema.
- [Stage 3 Neural Network Controller](stage-3-neural-network-controller.md): data
  acquisition, MLP training, and neural runtime control.
- [Stage 4 LLM Agent](stage-4-llm-agent.md): Local Ollama Tool-calling loop and Bullet Time architecture.
- [Stage 5 Augmented Reality](stage-5-augmented-reality.md): Virtual obstacle drawing and circle-line segment collision physics preparation.

## Run

```bash
python3 start.py
```

Stage 3 training workflow:

```bash
python3 scripts/collect_training_data.py --rows 20000
python3 scripts/train_mlp_model.py
python3 start.py
```

Or install the package in editable mode:

```bash
python3 -m pip install -e .
python3 -m breakout
```
