# Stage 5: Augmented Reality Setup

The goal of Stage 5 is to bridge the digital physics engine with a physical whiteboard environment, where users can draw arbitrary marker lines that instantly become indestructible obstacles in the game.

## Phase 1: Virtual Drawing (Completed)
Before integrating computer vision, we upgraded the game's core physics engine to support arbitrary angled obstacles.

- **`ObstacleLine` Entity**: We abandoned grid-snapped Axis-Aligned Bounding Box (AABB) bricks in favor of arbitrary line-segments.
- **Circle-Line Segment Collision**: The engine uses vector math to calculate the closest point on any drawn line-segment to the ball's center. When a collision occurs, it reflects the ball's velocity vector precisely across the line's normal vector.
- **Mouse Controls**: Users can click and drag on the Pygame window to draw virtual lines. Pressing `C` clears the board.

## Phase 2: Computer Vision Integration (Completed)
- We have integrated an OpenCV (`cv2`) pipeline via a lock-free `multiprocessing` `VisionThread` that captures a webcam feed pointing at a physical whiteboard.
- Using a Perspective Transform (4-point homography calibration via `scripts/test_camera.py`), the webcam feed maps 1:1 onto the digital Pygame coordinate space.
- Color thresholding and contour detection identify physical objects (like magnets) and inject their coordinates directly into the game.
- The pipeline uses an Exponential Moving Average (EMA) to smooth the position of the objects.
- It includes a 6-frame arming mechanic to prevent hand interference from causing false collisions. Objects must be stable for 6 frames before they become solid obstacles.

## Phase 3: Hardware Integration (Completed)
- The game can communicate with an Arduino (`rail.ino`) to drive a physical NEMA-17 stepper motor.
- Uses an Absolute Position Step protocol via `PhysicalPaddleHAL` (`--hardware`).
- Includes a Jog Mode (`Press J`) to manually calibrate the bounds of the physical rail to the virtual screen.
