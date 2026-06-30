import time
from datetime import datetime, UTC

import psutil
import requests
import win32gui
import win32process
from pynput import keyboard, mouse

from app_classifier import classify_activity


API_URL = "http://127.0.0.1:8000/activity"
CHECK_INTERVAL_SECONDS = 10

key_count = 0
mouse_count = 0


def on_key_press(key):
    global key_count
    key_count += 1


def on_mouse_click(x, y, button, pressed):
    global mouse_count

    if pressed:
        mouse_count += 1


def get_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()

        if hwnd == 0:
            return "unknown", "unknown"

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)

        app_name = process.name()
        window_title = win32gui.GetWindowText(hwnd)

        return app_name, window_title

    except Exception:
        return "unknown", "unknown"


def send_activity(payload):
    try:
        response = requests.post(API_URL, json=payload, timeout=5)

        if response.status_code == 200:
            print("Sent activity:", payload["app_name"], payload["activity_type"])
        else:
            print("Backend error:", response.status_code, response.text)

    except requests.exceptions.ConnectionError:
        print("Backend not running. Start FastAPI first.")

    except Exception as error:
        print("Tracker error:", error)


def main():
    global key_count
    global mouse_count

    keyboard.Listener(on_press=on_key_press).start()
    mouse.Listener(on_click=on_mouse_click).start()

    print("Drift Tracker Started...")
    print("Sending activity every", CHECK_INTERVAL_SECONDS, "seconds")

    while True:
        start_time = datetime.now(UTC)

        current_key_count = key_count
        current_mouse_count = mouse_count

        time.sleep(CHECK_INTERVAL_SECONDS)

        end_time = datetime.now(UTC)

        app_name, window_title = get_active_window()
        activity_type = classify_activity(app_name, window_title)

        duration_seconds = int((end_time - start_time).total_seconds())

        if key_count == current_key_count and mouse_count == current_mouse_count:
            activity_type = "IDLE"

        payload = {
            "app_name": app_name,
            "window_title": window_title,
            "activity_type": activity_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration_seconds,
            "key_count": key_count - current_key_count,
            "mouse_count": mouse_count - current_mouse_count,
        }

        send_activity(payload)


if __name__ == "__main__":
    main()