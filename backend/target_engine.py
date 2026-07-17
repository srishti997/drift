from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGETS_FILE = PROJECT_ROOT / "data" / "productivity_targets.json"


DEFAULT_TARGETS = {
    "deep_work_minutes": 180,
    "max_context_switches": 20,
    "max_idle_minutes": 30,
    "max_youtube_minutes": 45,
}


def load_targets() -> dict[str, int]:
    if not TARGETS_FILE.exists():
        save_targets(DEFAULT_TARGETS)
        return DEFAULT_TARGETS.copy()

    try:
        with TARGETS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return {
            "deep_work_minutes": int(
                data.get(
                    "deep_work_minutes",
                    DEFAULT_TARGETS["deep_work_minutes"],
                )
            ),
            "max_context_switches": int(
                data.get(
                    "max_context_switches",
                    DEFAULT_TARGETS["max_context_switches"],
                )
            ),
            "max_idle_minutes": int(
                data.get(
                    "max_idle_minutes",
                    DEFAULT_TARGETS["max_idle_minutes"],
                )
            ),
            "max_youtube_minutes": int(
                data.get(
                    "max_youtube_minutes",
                    DEFAULT_TARGETS["max_youtube_minutes"],
                )
            ),
        }

    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return DEFAULT_TARGETS.copy()


def save_targets(targets: dict[str, Any]) -> dict[str, int]:
    TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)

    cleaned_targets = {
        "deep_work_minutes": max(
            0,
            int(
                targets.get(
                    "deep_work_minutes",
                    DEFAULT_TARGETS["deep_work_minutes"],
                )
            ),
        ),
        "max_context_switches": max(
            0,
            int(
                targets.get(
                    "max_context_switches",
                    DEFAULT_TARGETS["max_context_switches"],
                )
            ),
        ),
        "max_idle_minutes": max(
            0,
            int(
                targets.get(
                    "max_idle_minutes",
                    DEFAULT_TARGETS["max_idle_minutes"],
                )
            ),
        ),
        "max_youtube_minutes": max(
            0,
            int(
                targets.get(
                    "max_youtube_minutes",
                    DEFAULT_TARGETS["max_youtube_minutes"],
                )
            ),
        ),
    }

    with TARGETS_FILE.open("w", encoding="utf-8") as file:
        json.dump(cleaned_targets, file, indent=2)

    return cleaned_targets


def evaluate_targets(activity_logs) -> dict[str, Any]:
    targets = load_targets()

    deep_work_seconds = 0
    idle_seconds = 0
    youtube_seconds = 0
    context_switches = 0
    previous_app = None

    for log in activity_logs:
        duration = max(0, int(log.duration_seconds))
        app_name = str(log.app_name).lower()
        window_title = str(log.window_title).lower()
        activity_type = str(log.activity_type).lower()

        if activity_type in {"coding", "focused", "deep_work"}:
            deep_work_seconds += duration

        if activity_type == "idle":
            idle_seconds += duration

        if "youtube" in app_name or "youtube" in window_title:
            youtube_seconds += duration

        current_app = str(log.app_name).strip().lower()

        if previous_app is not None and current_app != previous_app:
            context_switches += 1

        previous_app = current_app

    deep_work_minutes = round(deep_work_seconds / 60, 1)
    idle_minutes = round(idle_seconds / 60, 1)
    youtube_minutes = round(youtube_seconds / 60, 1)

    deep_work_target = targets["deep_work_minutes"]
    context_switch_target = targets["max_context_switches"]
    idle_target = targets["max_idle_minutes"]
    youtube_target = targets["max_youtube_minutes"]

    deep_work_progress = (
        min(100, round((deep_work_minutes / deep_work_target) * 100))
        if deep_work_target > 0
        else 100
    )

    return {
        "targets": targets,
        "metrics": {
            "deep_work": {
                "current": deep_work_minutes,
                "target": deep_work_target,
                "unit": "minutes",
                "progress": deep_work_progress,
                "status": (
                    "Completed"
                    if deep_work_minutes >= deep_work_target
                    else "In progress"
                ),
            },
            "context_switches": {
                "current": context_switches,
                "target": context_switch_target,
                "unit": "switches",
                "progress": _limit_progress(
                    context_switches,
                    context_switch_target,
                ),
                "status": (
                    "Within limit"
                    if context_switches <= context_switch_target
                    else "Exceeded"
                ),
            },
            "idle_time": {
                "current": idle_minutes,
                "target": idle_target,
                "unit": "minutes",
                "progress": _limit_progress(idle_minutes, idle_target),
                "status": (
                    "Within limit"
                    if idle_minutes <= idle_target
                    else "Exceeded"
                ),
            },
            "youtube_time": {
                "current": youtube_minutes,
                "target": youtube_target,
                "unit": "minutes",
                "progress": _limit_progress(
                    youtube_minutes,
                    youtube_target,
                ),
                "status": (
                    "Within limit"
                    if youtube_minutes <= youtube_target
                    else "Exceeded"
                ),
            },
        },
    }


def _limit_progress(current: float, target: float) -> int:
    if target <= 0:
        return 100 if current <= 0 else 0

    remaining_ratio = max(0, 1 - (current / target))
    return round(remaining_ratio * 100)