import serial
import time
from pynput import keyboard
import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
usb_ports = [p.device for p in ports if 'usbmodem' in p.device or 'usbserial' in p.device]
port = usb_ports[0] if usb_ports else '/dev/cu.usbmodem114301'

print(f"Connecting to {port}...")
arduino = serial.Serial(port, 115200, timeout=0.1)
time.sleep(2)
print("Connected! Hold LEFT or RIGHT arrows. Press ESC to quit.")

def on_press(key):
    try:
        if key == keyboard.Key.right:
            print("Sending R")
            arduino.write(b'R')
        elif key == keyboard.Key.left:
            print("Sending L")
            arduino.write(b'L')
    except AttributeError: pass

def on_release(key):
    if key == keyboard.Key.esc:
        arduino.close()
        return False
    arduino.write(b'S')

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
