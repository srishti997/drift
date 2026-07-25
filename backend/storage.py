from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

DATA_FILE = DATA_DIR / "activity_logs.json"
DEMO_DATA_FILE = DATA_DIR / "demo_activity_logs.json"

DEMO_MODE = os.getenv("DRIFT_DEMO_MODE", "false").strip().lower() == "true"


def save_activity_logs(activity_logs: list[Any]) -> None:
    """
    Save activity logs to data/activity_logs.json.

    Demo data is never overwritten.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    serialized_logs = [
        _serialize_activity_log(log)
        for log in activity_logs
    ]

    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                serialized_logs,
                file,
                indent=4,
                ensure_ascii=False,
            )
    except OSError:
        return


def load_activity_logs() -> list[dict[str, Any]]:
    """
    Load activity logs as plain dictionaries.

    In demo mode, demo_activity_logs.json is loaded and its timestamps
    are shifted so the latest demo date becomes today.
    """

    selected_file = DEMO_DATA_FILE if DEMO_MODE else DATA_FILE
    logs = _load_json_logs(selected_file)

    if DEMO_MODE and logs:
        logs = _shift_demo_logs_to_today(logs)

    

    return logs


def load_real_activity_logs() -> list[dict[str, Any]]:
    """
    Load real activity logs regardless of demo mode.

    This is used when appending tracker activity so demo records
    are never copied into activity_logs.json.
    """

    return _load_json_logs(DATA_FILE)


def append_activity_log(activity_log: Any) -> None:
    """
    Append one activity log to the real activity log file.

    Demo data is never modified.
    """

    existing_logs = load_real_activity_logs()
    existing_logs.append(
        _serialize_activity_log(activity_log)
    )

    save_activity_logs(existing_logs)


def clear_activity_logs() -> None:
    """
    Remove all real activity logs.

    demo_activity_logs.json remains unchanged.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump([], file, indent=4)
    except OSError:
        return


def _load_json_logs(file_path: Path) -> list[dict[str, Any]]:
    """
    Safely load a JSON list containing activity-log dictionaries.
    """

    if not file_path.exists():
        return []

    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


def _shift_demo_logs_to_today(
    logs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Shift demo timestamps so the latest date in the demo dataset is today.

    The time of day and spacing between records are preserved.
    The demo JSON file itself is not changed.
    """

    demo_dates: list[date] = []

    for log in logs:
        for field in ("start_time", "end_time", "timestamp"):
            parsed_value = _parse_datetime(log.get(field))

            if parsed_value is not None:
                demo_dates.append(parsed_value.date())

    if not demo_dates:
        return logs

    latest_demo_date = max(demo_dates)
    date_offset = date.today() - latest_demo_date

    shifted_logs: list[dict[str, Any]] = []

    for log in logs:
        shifted_log = dict(log)

        for field in ("start_time", "end_time", "timestamp"):
            original_value = shifted_log.get(field)
            parsed_value = _parse_datetime(original_value)

            if parsed_value is None:
                continue

            shifted_value = parsed_value + date_offset
            shifted_log[field] = shifted_value.isoformat()

        shifted_logs.append(shifted_log)

    return shifted_logs


def _parse_datetime(value: Any) -> datetime | None:
    """
    Parse an ISO-8601 datetime string.

    Supports timestamps ending in Z.
    """

    if not isinstance(value, str) or not value.strip():
        return None

    normalized_value = value.strip()

    if normalized_value.endswith("Z"):
        normalized_value = (
            normalized_value[:-1] + "+00:00"
        )

    try:
        return datetime.fromisoformat(normalized_value)
    except ValueError:
        return None


def _serialize_activity_log(log: Any) -> dict[str, Any]:
    """
    Convert an activity object or dictionary into JSON-safe data.
    """

    if isinstance(log, dict):
        serialized = dict(log)

    else:
        serialized = {
            "app_name": getattr(log, "app_name", "Unknown"),
            "window_title": getattr(log, "window_title", ""),
            "activity_type": getattr(
                log,
                "activity_type",
                "UNKNOWN",
            ),
            "start_time": getattr(log, "start_time", None),
            "end_time": getattr(log, "end_time", None),
            "duration_seconds": getattr(
                log,
                "duration_seconds",
                0,
            ),
            "key_count": getattr(log, "key_count", 0),
            "mouse_count": getattr(log, "mouse_count", 0),
        }

    for field in ("start_time", "end_time", "timestamp"):
        if field in serialized:
            serialized[field] = _serialize_datetime(
                serialized[field]
            )

    return serialized


def _serialize_datetime(value: Any) -> Any:
    """
    Convert datetime-like values into ISO-8601 strings.
    """

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            return value

    return value