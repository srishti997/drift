from __future__ import annotations

from typing import Any


def build_sessions(
    activity_logs: list[Any],
) -> list[dict[str, Any]]:
    """
    Group consecutive activities of the same type into sessions.

    Supports both:
    - dictionaries loaded from JSON
    - activity model/object instances

    Example:
    CODING + CODING = one CODING session
    CODING -> BROWSING -> CODING = three sessions
    """

    if not activity_logs:
        return []

    sessions: list[dict[str, Any]] = []

    first_log = activity_logs[0]

    current_type = _get_value(
        first_log,
        "activity_type",
        "UNKNOWN",
    )

    current_duration = _safe_number(
        _get_value(
            first_log,
            "duration_seconds",
            0,
        )
    )

    for log in activity_logs[1:]:
        activity_type = _get_value(
            log,
            "activity_type",
            "UNKNOWN",
        )

        duration = _safe_number(
            _get_value(
                log,
                "duration_seconds",
                0,
            )
        )

        if activity_type == current_type:
            current_duration += duration

        else:
            sessions.append(
                {
                    "activity_type": current_type,
                    "duration": current_duration,
                    "duration_seconds": current_duration,
                }
            )

            current_type = activity_type
            current_duration = duration

    sessions.append(
        {
            "activity_type": current_type,
            "duration": current_duration,
            "duration_seconds": current_duration,
        }
    )

    return sessions


def _get_value(
    log: Any,
    field: str,
    default: Any = None,
) -> Any:
    """
    Read a value from either a dictionary or an object.
    """

    if isinstance(log, dict):
        return log.get(field, default)

    return getattr(log, field, default)


def _safe_number(value: Any) -> float:
    """
    Convert a duration value into a safe numeric value.
    """

    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0