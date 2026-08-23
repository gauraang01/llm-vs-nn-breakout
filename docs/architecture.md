# Architecture

## Goals

The game should be useful as both a playable Breakout sandbox and a hardware
simulation harness. Every stage must keep the V-HAL as the only path for paddle
movement so later autonomous controllers, serial bridges, or real hardware
drivers can replace manual input without changing game physics.

## Module Layout

```text
src/breakout_vhal/
  __main__.py             # module entrypoint
  config.py               # dimensions, colors, gameplay constants, V-HAL constants
  app/
    game.py               # Pygame loop orchestration, input routing, run state
    renderer.py           # all Pygame drawing, overlay, and status text
    state.py              # play-state and control-mode enums
    time_utils.py         # elapsed/finish time formatting
  controllers/
    llm.py                # Ollama tool-calling agent controller
    manual.py             # keyboard target generation
    mathematical.py       # deterministic reflection-geometry controller
    neural.py             # PyTorch model loader and inference controller
  gameplay/
    collisions.py         # wall, paddle, and brick collision resolution
    entities.py           # ball and brick data structures plus brick factory
  hardware/
    vhal.py               # virtual & physical hardware motion model (Serial Arduino)
    vision.py             # multiprocessing OpenCV pipeline for Augmented Reality
  tools/
    aim_predictor.py          # tool for the LLM to predict paddle offset
    trajectory_predictor.py   # tool for the LLM to predict ball bounce trajectory
  training/
    data_logger.py        # CSV writer for supervised training samples
    mlp_model.py          # shared PyTorch MLP architecture
scripts/
  collect_training_data.py # fast headless Stage 2 data collector
  train_mlp_model.py       # offline MLP training/export script
```

Package ownership:

- `app/` owns runtime orchestration and visual presentation.
- `controllers/` owns all paddle target policies.
- `gameplay/` owns game-world entities and collision rules.
- `hardware/` owns V-HAL and later physical-device abstractions.
- `training/` owns dataset and model-training support code.

## Runtime Flow

1. Pygame initializes the window and game entities.
2. The active controller updates a target position in the V-HAL:
   - Manual mode:
     - Left arrow means target = 0 mm.
     - Right arrow means target = 500 mm.
     - No horizontal input means target = current paddle position, causing a
       controlled stop.
   - Mathematical Controller mode:
     - The ball trajectory is projected to the paddle strike line.
     - The predicted impact X coordinate is converted to a 0-500 mm rail target.
   - Neural Network Controller mode:
     - Upward ball motion sends the paddle to the center rest position.
     - Downward ball motion is scaled and passed through the trained MLP.
     - The predicted target is clamped to the 0-500 mm track.
   - LLM Agent Controller mode:
     - If the ball is falling, an async thread is spawned to query the local Ollama model.
     - The LLM calls the `TrajectoryPredictor` and `AimPredictor` tools to gather environment data.
     - The LLM synthesizes a target JSON which is clamped to the 0-500 mm track.
     - The game continues playing while the async query resolves.
3. Each frame advances the V-HAL with `dt`.
4. The game reads the V-HAL paddle position and maps it to the screen.
5. Ball, brick, wall, paddle, scoring, and life collisions are resolved.
6. The overlay renders telemetry from the game, controller, prediction, and
   V-HAL.
7. When Mathematical Controller mode is active, a CSV row is written every 4 frames
   only if the ball is falling.

The run timer advances only while the ball is actively playing. It freezes into
`final_time_s` when the game ends through stage clear or game over.

## Separation Rules

- Input code may set V-HAL targets but must not directly edit paddle pixels.
- Game collision code may read paddle position but must not bypass V-HAL
  acceleration or velocity limits.
- Rendering code should read game state only; it should not mutate physics,
  controls, score, or timers.
- Entity modules should stay data-focused and avoid controller policy.
- Future controllers should call the same target-position API used by keyboard
  input.
- Hardware-specific details should stay outside the core Breakout game loop
  until a later hardware stage.
- Data harvesting should log controller labels separately from actual V-HAL
  position so later models can learn the ideal target and compare actuator lag.
- Neural runtime code may load a trained model, but model inference must still
  produce only V-HAL target coordinates.

## Extension Points

- Replace manual keyboard target generation with an AI/controller module.
- Add serial or GPIO output by adapting V-HAL state to real motor commands.
- Tune the V-HAL constants after measuring a physical NEMA 17 setup.
- Add logging or replay by recording V-HAL state and ball state each frame.
