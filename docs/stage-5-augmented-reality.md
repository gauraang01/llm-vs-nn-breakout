# Stage 5: Augmented Reality Setup

The goal of Stage 5 is to bridge the digital physics engine with a physical whiteboard environment, where users can draw arbitrary marker lines that instantly become indestructible obstacles in the game.

## Phase 1: Virtual Drawing (Completed)
Before integrating computer vision, we upgraded the game's core physics engine to support arbitrary angled obstacles.

- **`ObstacleLine` Entity**: We abandoned grid-snapped Axis-Aligned Bounding Box (AABB) bricks in favor of arbitrary line-segments.
- **Circle-Line Segment Collision**: The engine uses vector math to calculate the closest point on any drawn line-segment to the ball's center. When a collision occurs, it reflects the ball's velocity vector precisely across the line's normal vector.
- **Mouse Controls**: Users can click and drag on the Pygame window to draw virtual lines. Pressing `C` clears the board.

## Phase 2: Computer Vision Integration (Upcoming)
- We will integrate an OpenCV (`cv2`) pipeline to capture a webcam feed pointing at a physical whiteboard.
- Using a Perspective Transform (homography), the webcam feed will map 1:1 onto the digital Pygame coordinate space.
- Color thresholding and contour detection will identify physical marker drawings and inject their coordinates directly into the `game.obstacle_lines` list, allowing the digital ball to bounce off real-world marker drawings in real time.
