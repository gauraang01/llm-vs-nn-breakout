# 🤖 AI-Augmented Breakout: An Architecture Showcase

> **A real-time physics playground built to test and compare fundamentally different AI control architectures (LLMs vs. Neural Networks) in a simulated robotics environment.**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-Enabled-EE4C2C.svg)
![Ollama](https://img.shields.io/badge/Ollama-LLM_Agent-white.svg)

---

## 🎥 Demos

### Virtual Sandbox Demo
https://github.com/user-attachments/assets/72b850f6-8b25-4491-a542-902b229aa763

### Augmented Reality & Hardware Demo
[![Watch the Augmented Reality Demo](https://img.shields.io/badge/🎥_Watch_Video-Augmented_Reality_Demo-blue?style=for-the-badge)](https://github.com/gauraang01/llm-vs-nn-breakout/blob/main/assets/augmented_breakout.mp4)

*(Click the button above to watch the full 31-second AR and physical hardware demo!)*

---

## 🧠 The Concept

Can an LLM Agent play a real-time physics game? How does it compare to a traditional Neural Network?

To answer this, I built a custom Breakout engine featuring a **Virtual Hardware Abstraction Layer (V-HAL)**. The paddle doesn't just teleport—it simulates a physical NEMA-17 stepper motor on a 500mm rail, complete with strict physical limits for maximum velocity and acceleration. 
   
The engine also features an **Augmented Reality (AR) Pipeline** using OpenCV. You can project the game onto a whiteboard and drop physical magnets onto the board—the game detects them via a separate multiprocessed computer vision pipeline and calculates real-time elastic physics collisions against them!

The engine allows you to hot-swap between three distinct "brains" mid-flight to see how different architectures handle spatial reasoning, latency, and real-time execution.

## 🎮 The Three Architectures (Hot-Swappable)

### 1️⃣ Manual Control (`Press 1`)
The baseline control loop. Flawless tracking and zero software latency, but entirely bound by human reaction times. You are constrained by the exact same physical motor limits as the AI.

### 2️⃣ Neural Network (MLP) (`Press 2`)
An optimized statistical guesser. By using spatial pooling to reduce the entire brick grid into localized density zones, the model runs inference in under a millisecond. 
- **The Result:** Absolute perfection. It calculates the exact physical paddle offsets in microseconds, executing real-time control effortlessly.

### 3️⃣ LLM Agent (Local 8B Parameter) (`Press 3`)
Instead of guessing, the LLM uses intelligent **tool-calling** to delegate to a Python `TrajectoryPredictor`. It orchestrates the logic, reads the environment, and synthesizes JSON commands to drive the motor.
- **The Result:** It perfectly highlights the limitations of Generative AI in robotics. The latency of the cognitive loop forces the game to pause, and occasional "hallucinated" numbers lead to missed shots. It’s a brilliant thinker, but struggles in high-frequency spatial loops.

---

## 🛠️ Technical Highlights

* **Virtual Hardware Abstraction (V-HAL):** Maps sub-pixel game coordinates to physical millimeters, simulating mass and momentum.
* **Augmented Reality Tracking (OpenCV):** Features a lock-free `multiprocessing` vision pipeline to track physical objects on a whiteboard without blocking the 60 FPS Pygame loop. Includes temporal smoothing (EMA), 3-second arming mechanics to prevent hand interference, and 4-point homography calibration.
* **The "Ghost Brick" Delusion:** The project involved heavy debugging of geometric folding equations. We discovered that forcing models to predict upward flights accidentally trained them to clone mathematical delusions of an empty room, requiring dynamic ray-casting for true clairvoyance.
* **Dynamic Telemetry UI:** A custom Pygame UI featuring segmented mode buttons, tool-calling traces, and fading badges to clearly expose the active architecture's inner workings to the viewer.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) (Required for Mode 3)
- PyTorch (Required for Mode 2)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/gauraang01/llm-vs-nn-breakout.git
   cd llm-vs-nn-breakout
   ```

2. **Install dependencies**
   ```bash
   python3 -m pip install -e .
   ```

3. **Pull the LLM** (Ensure Ollama is running)
   ```bash
   ollama pull qwen2.5:7b
   ```

### Run the Game (Virtual Mode)
```bash
python3 start.py
```

### Run the Game (Augmented Reality Mode)
1. Mount your phone and start an IP Webcam stream.
2. Calibrate the camera's perspective and color tracking:
   ```bash
   python3 start.py --camera-config --source "http://<IP>:8080/video"
   ```
3. Play the game with the AR pipeline enabled:
   ```bash
   python3 start.py --mode augmented --source "http://<IP>:8080/video"
   ```

### Run the Game (Physical Hardware Mode)
Want the AI to control a physical stepper motor on a desk? Connect an Arduino running `arduino/rail.ino` via USB and append the `--hardware` flag.
```bash
python3 start.py --mode augmented --hardware --source "http://<IP>:8080/video"
```
**Hardware Calibration:** The engine uses an Absolute Position Step protocol to prevent physical drift. 
1. Run the interactive rail setup to set max speed and track length:
   ```bash
   python3 start.py --rail-config
   ```
2. Press `j` in-game to enter Calibration Mode.
3. Jog to the left wall using your arrow keys. Press `Space`.
4. Jog to the right wall using your arrow keys. Press `Space`.
The game calculates exact sub-millimeter steps and perfectly locks the physical trolley to the digital paddle.

### Controls
- `1`: Manual Mode
- `2`: Neural Network Mode
- `3`: LLM Agent Mode
- `Left/Right Arrows`: Switch Maps / Jog Hardware
- `Space`: Launch Ball / Restart / Confirm Calibration
- `j`: Enter/Exit Hardware Calibration Mode
- `c`: Clear Obstacles (Virtual Mode)
- `s`: Save active configuration (`display_config.json`, `rail_config.json`) (AR Mode)
- `f`: Toggle Fullscreen
- `=`, `-`: Adjust Projection Scale (AR Mode)
- `[`, `]`, `Up`, `Down`: Pan Projection (AR Mode)
- `<`, `>`: Adjust max hardware velocity
- `Escape`: Quit

---

## 🧪 Training the Neural Network from Scratch

Want to train your own model? The engine includes an automated headless data harvester.

```bash
# 1. Harvest 20,000 frames of flawless geometric gameplay
python3 scripts/collect_training_data.py --rows 20000

# 2. Train the Multi-Layer Perceptron (Generates mlp_model.pt)
python3 scripts/train_mlp_model.py

# 3. Play the game!
python3 start.py
```

---

## 📚 Documentation
For a deeper dive into the physics engine, coordinate mapping, and runtime flow, check out the [Architecture Docs](docs/README.md).

---
*Built as a showcase for AI Architecture, Machine Learning, and Software Engineering.*
