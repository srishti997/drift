import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "activity_logs.json"


def save_activity_logs(activity_logs):
    DATA_DIR.mkdir(exist_ok=True)

    data = []

    for log in activity_logs:
        data.append({
            "app_name": log.app_name,
            "window_title": log.window_title,
            "activity_type": log.activity_type,
            "start_time": log.start_time.isoformat(),
            "end_time": log.end_time.isoformat(),
            "duration_seconds": log.duration_seconds,
            "key_count": log.key_count,
            "mouse_count": log.mouse_count,
        })

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_activity_logs(ActivityLog):
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return [ActivityLog(**item) for item in data]