from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "activity_logs.json"


def save_activity_logs(activity_logs: list[Any]) -> None:
    """
    Save activity logs to data/activity_logs.json.

    Supports both:
    - model/object instances with attributes
    - plain dictionaries
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    serialized_logs: list[dict[str, Any]] = []

    for log in activity_logs:
        serialized_logs.append(_serialize_activity_log(log))

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            serialized_logs,
            file,
            indent=4,
            ensure_ascii=False,
        )


def load_activity_logs() -> list[dict[str, Any]]:
    """
    Load activity logs as plain dictionaries.

    Returning dictionaries avoids circular imports between storage.py
    and backend.main while remaining compatible with the chat and
    historical analytics engines.
    """

    if not DATA_FILE.exists():
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
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


def append_activity_log(activity_log: Any) -> None:
    """
    Append one activity log without removing existing records.
    """

    existing_logs = load_activity_logs()
    existing_logs.append(
        _serialize_activity_log(activity_log)
    )

    save_activity_logs(existing_logs)


def clear_activity_logs() -> None:
    """
    Remove all saved activity logs.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump([], file, indent=4)


def _serialize_activity_log(log: Any) -> dict[str, Any]:
    """
    Convert either an activity object or dictionary into JSON-safe data.
    """

    if isinstance(log, dict):
        serialized = dict(log)
    else:
        serialized = {
            "app_name": getattr(log, "app_name", "Unknown"),
            "window_title": getattr(log, "window_title", ""),
            "activity_type": getattr(log, "activity_type", "UNKNOWN"),
            "start_time": _serialize_datetime(
                getattr(log, "start_time", None)
            ),
            "end_time": _serialize_datetime(
                getattr(log, "end_time", None)
            ),
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
    Convert datetime-like values into ISO strings.
    """

    if value is None:
        return None

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return value