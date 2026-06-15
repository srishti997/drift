import time
from datetime import datetime, UTC

import psutil
import requests
import win32gui
import win32process
from pynput import keyboard, mouse

from app_classifier import classify_activity

# -----------------------------
# Configuration
# -----------------------------

API_URL = "http://127.0.0.1:8000/activity"
CHECK_INTERVAL_SECONDS = 10

# -----------------------------
# Global Counters
# -----------------------------

key_count = 0
mouse_count = 0


# -----------------------------
# Keyboard Listener
# -----------------------------

def on_key_press(key):
    global key_count
    key_count += 1


# -----------------------------
# Mouse Listener
# -----------------------------

def on_mouse_click(x, y, button, pressed):
    global mouse_count

    if pressed:
        mouse_count += 1


# -----------------------------
# Active Window
# -----------------------------

def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()

        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        process = psutil.Process(pid)

        app_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)

        return app_name, window_title

    except Exception:
        return "unknown", "unknown"


# -----------------------------
# Send to Backend
# -----------------------------

def send_activity(payload):
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        print("Sent:", response.status_code)

    except Exception as e:
        print("Error:", e)


# -----------------------------
# Main Loop
# -----------------------------

def main():
    global key_count
    global mouse_count

    keyboard.Listener(on_press=on_key_press).start()
    mouse.Listener(on_click=on_mouse_click).start()

    print("Drift Tracker Started...")

    while True:

        time.sleep(CHECK_INTERVAL_SECONDS)

        now = datetime.now(UTC)

        app_name, window_title = get_active_window()

        activity_type = classify_activity(app_name, window_title)

        # -------------------------
        # Idle Detection
        # -------------------------

        if key_count == 0 and mouse_count == 0:
            activity_type = "IDLE"

        payload = {
            "app_name": app_name,
            "window_title": window_title,
            "activity_type": activity_type,
            "start_time": now.isoformat(),
            "end_time": now.isoformat(),
            "duration_seconds": CHECK_INTERVAL_SECONDS,
            "key_count": key_count,
            "mouse_count": mouse_count,
        }

        print(payload)

        send_activity(payload)

        # Reset counters

        key_count = 0
        mouse_count = 0


if __name__ == "__main__":
    main()