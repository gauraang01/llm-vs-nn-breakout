import cv2
import argparse
import sys
import numpy as np
import json
from pathlib import Path

def nothing(x):
    pass

# Global variables for homography calibration
pts_src = []
homography_matrix = None
calibration_mode = True
mouse_pos = (0, 0)

def mouse_handler(event, x, y, flags, param):
    global pts_src, calibration_mode, mouse_pos
    mouse_pos = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN and calibration_mode:
        if len(pts_src) < 4:
            pts_src.append([x, y])
            print(f"[*] Point {len(pts_src)} captured at ({x}, {y}) (via Click)")

def main():
    global pts_src, homography_matrix, calibration_mode, mouse_pos

    parser = argparse.ArgumentParser(description="Homography & Blob Dashboard")
    parser.add_argument("--source", type=str, default="0")
    parser.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0)
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print("[ERROR] Could not open video source.")
        sys.exit(1)

    cv2.namedWindow("Camera Feed")
    cv2.waitKey(1) # Force window initialization on Mac
    cv2.setMouseCallback("Camera Feed", mouse_handler)

    print("\n=======================================================")
    print("STEP 1: SETUP YOUR DISPLAYS")
    print("1. Set your projector as an EXTENDED DISPLAY (not mirrored).")
    print("2. Run your Breakout game, drag it to the projector, and make it fullscreen.")
    print("3. Keep this OpenCV window on your laptop screen.")
    print("=======================================================\n")
    print("STEP 2: HOMOGRAPHY CALIBRATION (Fixing the Capture Area)")
    print("Click the 4 corners of the GAME ARENA in this exact order:")
    print("1. Top-Left  2. Top-Right  3. Bottom-Right  4. Bottom-Left")
    print("\n[!] MAC WORKAROUND: If clicking does nothing, just hover your mouse")
    print("over the corner and press the SPACEBAR to lock the point!")
    print("=======================================================\n")

    target_w, target_h = 926, 836 
    pts_dst = np.array([
        [0, 0],
        [target_w - 1, 0],
        [target_w - 1, target_h - 1],
        [0, target_h - 1]
    ], dtype=float)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if args.rotate == 90:
            frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif args.rotate == 180:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        elif args.rotate == 270:
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        height, width = frame.shape[:2]
        if width > 1280:
            scale = 1280 / width
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))

        display_frame = frame.copy()

        if calibration_mode:
            # Draw crosshair
            cv2.line(display_frame, (mouse_pos[0] - 15, mouse_pos[1]), (mouse_pos[0] + 15, mouse_pos[1]), (0, 255, 255), 2)
            cv2.line(display_frame, (mouse_pos[0], mouse_pos[1] - 15), (mouse_pos[0], mouse_pos[1] + 15), (0, 255, 255), 2)

            for pt in pts_src:
                cv2.circle(display_frame, tuple(pt), 6, (0, 0, 255), -1)
            
            if len(pts_src) == 4:
                homography_matrix, status = cv2.findHomography(np.array(pts_src), pts_dst)
                calibration_mode = False
                
                print("\n[SUCCESS] Homography locked! The feed is now cropped perfectly.")
                print("STEP 3: COLOR TUNING")
                print("Adjust the HSV sliders to isolate your magnets. Press 's' to save when done.")
                
                cv2.namedWindow("Mask")
                cv2.namedWindow("Calibration (HSV)")
                cv2.createTrackbar("Hue Min", "Calibration (HSV)", 0, 179, nothing)
                cv2.createTrackbar("Hue Max", "Calibration (HSV)", 179, 179, nothing)
                cv2.createTrackbar("Sat Min", "Calibration (HSV)", 50, 255, nothing)
                cv2.createTrackbar("Sat Max", "Calibration (HSV)", 255, 255, nothing)
                cv2.createTrackbar("Val Min", "Calibration (HSV)", 50, 255, nothing)
                cv2.createTrackbar("Val Max", "Calibration (HSV)", 255, 255, nothing)
                cv2.createTrackbar("Min Area", "Calibration (HSV)", 500, 5000, nothing)
        else:
            warped_frame = cv2.warpPerspective(frame, homography_matrix, (target_w, target_h))
            display_frame = warped_frame.copy()

            blurred = cv2.GaussianBlur(warped_frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            h_min = cv2.getTrackbarPos("Hue Min", "Calibration (HSV)")
            h_max = cv2.getTrackbarPos("Hue Max", "Calibration (HSV)")
            s_min = cv2.getTrackbarPos("Sat Min", "Calibration (HSV)")
            s_max = cv2.getTrackbarPos("Sat Max", "Calibration (HSV)")
            v_min = cv2.getTrackbarPos("Val Min", "Calibration (HSV)")
            v_max = cv2.getTrackbarPos("Val Max", "Calibration (HSV)")
            min_area = cv2.getTrackbarPos("Min Area", "Calibration (HSV)")

            lower_bound = np.array([h_min, s_min, v_min])
            upper_bound = np.array([h_max, s_max, v_max])

            mask = cv2.inRange(hsv, lower_bound, upper_bound)
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) > max(1, min_area):
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                        (x, y), radius = cv2.minEnclosingCircle(cnt)
                        cv2.circle(display_frame, (int(x), int(y)), int(radius), (0, 255, 0), 3)
                        cv2.circle(display_frame, (cX, cY), 3, (0, 0, 255), -1)

            cv2.imshow("Mask", mask)

        cv2.imshow("Camera Feed", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            if calibration_mode and len(pts_src) < 4:
                pts_src.append(list(mouse_pos))
                print(f"[*] Point {len(pts_src)} captured at {mouse_pos} (via Spacebar)")
        elif key == ord('s') and not calibration_mode:
            config = {
                "hsv_lower": [h_min, s_min, v_min],
                "hsv_upper": [h_max, s_max, v_max],
                "rotation": args.rotate,
                "homography": homography_matrix.tolist()
            }
            config_path = Path(__file__).resolve().parent.parent / "cv_config.json"
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"[SUCCESS] Saved Homography and Color config to {config_path}")
        elif key == ord('r'):
            pts_src.clear()
            calibration_mode = True
            try:
                cv2.destroyWindow("Mask")
                cv2.destroyWindow("Calibration (HSV)")
            except:
                pass
            print("[*] Calibration reset. Click the 4 corners again.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
