from __future__ import annotations

from pathlib import Path
import sys
import argparse


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from breakout.app.game import main, BreakoutGame


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Breakout Game")
    parser.add_argument("--mode", choices=["virtual", "augmented"], default="virtual")
    parser.add_argument("--source", type=str, default="0")
    parser.add_argument("--hardware", action="store_true", help="Enable physical hardware output via Arduino.")
    parser.add_argument("--camera-config", action="store_true", help="Run the OpenCV camera calibration tool.")
    parser.add_argument("--rail-config", action="store_true", help="Run the interactive Rail/Stepper configuration.")
    args = parser.parse_args()
    
    import json
    
    if args.rail_config:
        print("\n=== Hardware Rail Configuration ===")
        print("This will configure the physical limits and speed of your stepper motor rail.")
        length = input("Enter track length (mm) [default: 500.0]: ") or "500.0"
        speed = input("Enter max stepper velocity (mm/s) [default: 320.0]: ") or "320.0"
        accel = input("Enter max acceleration (mm/s^2) [default: 1000.0]: ") or "1000.0"
        
        cfg = {
            "track_length_mm": float(length),
            "max_velocity_mm_s": float(speed),
            "max_acceleration_mm_s2": float(accel)
        }
        with open(ROOT / "rail_config.json", "w") as f:
            json.dump(cfg, f)
        print("[SUCCESS] rail_config.json saved!\n")
        sys.exit(0)
        
    if args.camera_config:
        import subprocess
        print("[INFO] Starting AR Calibration Tool...")
        print("[INFO] Press 's' inside the calibration window to save and exit.")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "test_camera.py"), "--source", str(args.source)])
        sys.exit(0)
    
    if args.mode == "augmented":
        config_path = ROOT / "cv_config.json"
        if not config_path.exists():
            print("[INFO] No cv_config.json found. Please run with --camera-config first.")
            sys.exit(1)
            
    BreakoutGame(environment_mode=args.mode, camera_source=args.source, enable_hardware=args.hardware).run()
