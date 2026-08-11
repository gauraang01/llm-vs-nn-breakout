import cv2
import json
import multiprocessing as mp
import time
import numpy as np
from pathlib import Path

class VisionThread:
    """Renamed internally to use Multiprocessing to avoid Mac OS SDL library collisions."""
    def __init__(self, source: str):
        self.source = int(source) if isinstance(source, str) and source.isdigit() else source
        self.queue = mp.Queue()
        self.process = None
        self._last_obstacles = []

    def start(self):
        self.process = mp.Process(target=self._run, args=(self.source, self.queue), daemon=True)
        self.process.start()

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.join()

    def get_obstacles(self):
        latest = None
        # Drain the queue to get the absolute newest frame's data
        while not self.queue.empty():
            try:
                latest = self.queue.get_nowait()
            except:
                break
        
        if latest is not None:
            self._last_obstacles = latest
            
        return self._last_obstacles

    @staticmethod
    def _run(source, queue):
        # Target dimensions
        target_w, target_h = 926, 836

        # Load config inside the isolated process
        config_path = Path(__file__).resolve().parent.parent.parent.parent / "cv_config.json"
        
        hsv_lower = np.array([0, 50, 50])
        hsv_upper = np.array([179, 255, 255])
        rotation = 0
        homography = None

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                hsv_lower = np.array(config["hsv_lower"])
                hsv_upper = np.array(config["hsv_upper"])
                rotation = config["rotation"]
                h_matrix = config.get("homography")
                if h_matrix:
                    homography = np.array(h_matrix, dtype=float)

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"[ERROR] VisionProcess could not open source {source}")
            return

        print("[INFO] VisionProcess started successfully on an isolated CPU core.")

        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            if rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            height, width = frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                frame = cv2.resize(frame, (int(width * scale), int(height * scale)))

            if homography is not None:
                frame = cv2.warpPerspective(frame, homography, (target_w, target_h))

            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
            
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            current_circles = []
            for cnt in contours:
                if cv2.contourArea(cnt) > 500: 
                    (x, y), radius = cv2.minEnclosingCircle(cnt)
                    current_circles.append((int(x), int(y), int(radius + 2)))

            # Send to Pygame via IPC Queue
            queue.put(current_circles)
            
            time.sleep(1/30.0) 
