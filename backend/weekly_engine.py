from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any


PRODUCTIVE_TYPES = {
    "coding",
    "focused",
    "deep_work",
    "research",
    "writing",
}

DISTRACTION_TYPES = {
    "idle",
    "distraction",
    "entertainment",
    "social_media",
}


def build_weekly_summary(
    activity_logs,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Build analytics for the current seven-day period and compare it
    with the previous seven-day period.
    """

    now = reference_date or datetime.now()

    current_start = _start_of_day(now - timedelta(days=6))
    current_end = _end_of_day(now)

    previous_start = current_start - timedelta(days=7)
    previous_end = current_start - timedelta(microseconds=1)

    current_logs = _filter_logs(
        activity_logs,
        current_start,
        current_end,
    )

    previous_logs = _filter_logs(
        activity_logs,
        previous_start,
        previous_end,
    )

    current_metrics = _calculate_period_metrics(
        current_logs,
        current_start,
        current_end,
    )

    previous_metrics = _calculate_period_metrics(
        previous_logs,
        previous_start,
        previous_end,
    )

    comparison = {
        "productive_minutes_change": _difference(
            current_metrics["productive_minutes"],
            previous_metrics["productive_minutes"],
        ),
        "deep_work_minutes_change": _difference(
            current_metrics["deep_work_minutes"],
            previous_metrics["deep_work_minutes"],
        ),
        "context_switches_change": _difference(
            current_metrics["context_switches"],
            previous_metrics["context_switches"],
        ),
        "recovery_rate_change": _difference(
            current_metrics["recovery_rate"],
            previous_metrics["recovery_rate"],
        ),
        "overall_score_change": _difference(
            current_metrics["overall_score"],
            previous_metrics["overall_score"],
        ),
    }

    current_metrics["comparison"] = comparison
    current_metrics["weekly_insight"] = _build_weekly_insight(
        current_metrics,
        previous_metrics,
    )

    return current_metrics


def build_weekly_trends(
    activity_logs,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    now = reference_date or datetime.now()
    week_start = _start_of_day(now - timedelta(days=6))
    week_end = _end_of_day(now)

    logs = _filter_logs(
        activity_logs,
        week_start,
        week_end,
    )

    daily_data = _build_daily_metrics(
        logs,
        week_start,
    )

    return {
        "start_date": week_start.date().isoformat(),
        "end_date": week_end.date().isoformat(),
        "days": daily_data,
    }


def build_weekly_habits(
    activity_logs,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    now = reference_date or datetime.now()
    week_start = _start_of_day(now - timedelta(days=6))
    week_end = _end_of_day(now)

    logs = _filter_logs(
        activity_logs,
        week_start,
        week_end,
    )

    if not logs:
        return {
            "best_focus_hour": None,
            "highest_distraction_hour": None,
            "best_day": None,
            "most_distracting_app": None,
            "longest_deep_work_day": None,
            "current_deep_work_streak": 0,
            "best_deep_work_streak": 0,
            "insight": "No weekly activity is available yet.",
        }

    productive_by_hour: dict[int, int] = defaultdict(int)
    distraction_by_hour: dict[int, int] = defaultdict(int)
    distracting_apps: dict[str, int] = defaultdict(int)
    deep_work_by_day: dict[str, int] = defaultdict(int)

    daily_metrics = _build_daily_metrics(
        logs,
        week_start,
    )

    for log in logs:
        start_time = _get_datetime(log, "start_time")

        if start_time is None:
            continue

        duration = _get_int(log, "duration_seconds")
        activity_type = _get_text(log, "activity_type").lower()
        app_name = _get_text(log, "app_name").strip() or "Unknown"

        day_key = start_time.date().isoformat()
        hour = start_time.hour

        if _is_productive(activity_type):
            productive_by_hour[hour] += duration

        if _is_distraction(activity_type):
            distraction_by_hour[hour] += duration
            distracting_apps[app_name] += duration

        if _is_deep_work(activity_type):
            deep_work_by_day[day_key] += duration

    best_focus_hour = _largest_key(productive_by_hour)
    highest_distraction_hour = _largest_key(
        distraction_by_hour
    )
    most_distracting_app = _largest_key(
        distracting_apps
    )
    longest_deep_work_day = _largest_key(
        deep_work_by_day
    )

    best_day_data = max(
        daily_metrics,
        key=lambda item: item["overall_score"],
        default=None,
    )

    streak_data = _calculate_deep_work_streak(
        daily_metrics
    )

    return {
        "best_focus_hour": (
            _format_hour_range(best_focus_hour)
            if best_focus_hour is not None
            else None
        ),
        "highest_distraction_hour": (
            _format_hour_range(highest_distraction_hour)
            if highest_distraction_hour is not None
            else None
        ),
        "best_day": (
            best_day_data["day_name"]
            if best_day_data
            else None
        ),
        "most_distracting_app": most_distracting_app,
        "longest_deep_work_day": (
            datetime.fromisoformat(
                longest_deep_work_day
            ).strftime("%A")
            if longest_deep_work_day
            else None
        ),
        "current_deep_work_streak": (
            streak_data["current"]
        ),
        "best_deep_work_streak": streak_data["best"],
        "insight": _build_habit_insight(
            best_focus_hour,
            highest_distraction_hour,
            most_distracting_app,
        ),
    }


def _calculate_period_metrics(
    logs,
    start_date: datetime,
    end_date: datetime,
) -> dict[str, Any]:
    productive_seconds = 0
    deep_work_seconds = 0
    distraction_seconds = 0
    idle_seconds = 0

    context_switches = 0
    focus_loss_events = 0
    recovery_events = 0

    previous_app: str | None = None

    app_seconds: dict[str, int] = defaultdict(int)

    for log in logs:
        duration = _get_int(log, "duration_seconds")
        activity_type = _get_text(
            log,
            "activity_type",
        ).lower()
        app_name = _get_text(
            log,
            "app_name",
        ).strip() or "Unknown"

        app_seconds[app_name] += duration

        if _is_productive(activity_type):
            productive_seconds += duration

        if _is_deep_work(activity_type):
            deep_work_seconds += duration

        if _is_distraction(activity_type):
            distraction_seconds += duration
            focus_loss_events += 1

        if activity_type == "idle":
            idle_seconds += duration

        normalized_app = app_name.lower()

        if (
            previous_app is not None
            and normalized_app != previous_app
        ):
            context_switches += 1

            if _is_productive(activity_type):
                recovery_events += 1

        previous_app = normalized_app

    tracked_seconds = sum(
        _get_int(log, "duration_seconds")
        for log in logs
    )

    productive_minutes = round(
        productive_seconds / 60,
        1,
    )
    deep_work_minutes = round(
        deep_work_seconds / 60,
        1,
    )
    distraction_minutes = round(
        distraction_seconds / 60,
        1,
    )
    idle_minutes = round(
        idle_seconds / 60,
        1,
    )

    recovery_rate = (
        round(
            min(
                100,
                recovery_events
                / focus_loss_events
                * 100,
            ),
            1,
        )
        if focus_loss_events
        else 100.0
    )

    productivity_ratio = (
        productive_seconds / tracked_seconds
        if tracked_seconds
        else 0
    )

    switch_penalty = min(
        35,
        context_switches * 0.7,
    )

    distraction_penalty = min(
        35,
        distraction_minutes * 0.25,
    )

    overall_score = round(
        max(
            0,
            min(
                100,
                productivity_ratio * 100
                - switch_penalty
                - distraction_penalty
                + recovery_rate * 0.25,
            ),
        )
    )

    daily_metrics = _build_daily_metrics(
        logs,
        start_date,
    )

    best_day = max(
        daily_metrics,
        key=lambda item: item["overall_score"],
        default=None,
    )

    worst_day = min(
        daily_metrics,
        key=lambda item: item["overall_score"],
        default=None,
    )

    top_app = _largest_key(app_seconds)

    return {
        "start_date": start_date.date().isoformat(),
        "end_date": end_date.date().isoformat(),
        "tracked_minutes": round(
            tracked_seconds / 60,
            1,
        ),
        "productive_minutes": productive_minutes,
        "deep_work_minutes": deep_work_minutes,
        "distraction_minutes": distraction_minutes,
        "idle_minutes": idle_minutes,
        "context_switches": context_switches,
        "focus_loss_events": focus_loss_events,
        "recovery_events": recovery_events,
        "recovery_rate": recovery_rate,
        "overall_score": overall_score,
        "top_app": top_app,
        "best_day": (
            best_day["day_name"]
            if best_day
            else None
        ),
        "worst_day": (
            worst_day["day_name"]
            if worst_day
            else None
        ),
        "days": daily_metrics,
    }


def _build_daily_metrics(
    logs,
    week_start: datetime,
) -> list[dict[str, Any]]:
    logs_by_date: dict[str, list[Any]] = defaultdict(list)

    for log in logs:
        start_time = _get_datetime(
            log,
            "start_time",
        )

        if start_time is None:
            continue

        logs_by_date[
            start_time.date().isoformat()
        ].append(log)

    results = []

    for offset in range(7):
        day_date = (
            week_start + timedelta(days=offset)
        ).date()

        day_logs = logs_by_date.get(
            day_date.isoformat(),
            [],
        )

        metrics = _calculate_day_metrics(day_logs)

        results.append(
            {
                "date": day_date.isoformat(),
                "day_name": day_date.strftime("%A"),
                "day_short": day_date.strftime("%a"),
                **metrics,
            }
        )

    return results


def _calculate_day_metrics(
    logs,
) -> dict[str, Any]:
    productive_seconds = 0
    deep_work_seconds = 0
    distraction_seconds = 0
    total_seconds = 0
    context_switches = 0
    previous_app: str | None = None

    for log in logs:
        duration = _get_int(
            log,
            "duration_seconds",
        )
        activity_type = _get_text(
            log,
            "activity_type",
        ).lower()
        app_name = _get_text(
            log,
            "app_name",
        ).strip().lower()

        total_seconds += duration

        if _is_productive(activity_type):
            productive_seconds += duration

        if _is_deep_work(activity_type):
            deep_work_seconds += duration

        if _is_distraction(activity_type):
            distraction_seconds += duration

        if (
            previous_app is not None
            and app_name != previous_app
        ):
            context_switches += 1

        previous_app = app_name

    productivity_ratio = (
        productive_seconds / total_seconds
        if total_seconds
        else 0
    )

    distraction_minutes = (
        distraction_seconds / 60
    )

    score = round(
        max(
            0,
            min(
                100,
                productivity_ratio * 100
                - context_switches * 0.7
                - distraction_minutes * 0.25,
            ),
        )
    )

    return {
        "tracked_minutes": round(
            total_seconds / 60,
            1,
        ),
        "productive_minutes": round(
            productive_seconds / 60,
            1,
        ),
        "deep_work_minutes": round(
            deep_work_seconds / 60,
            1,
        ),
        "distraction_minutes": round(
            distraction_seconds / 60,
            1,
        ),
        "context_switches": context_switches,
        "overall_score": score,
        "deep_work_goal_met": (
            deep_work_seconds >= 30 * 60
        ),
    }


def _calculate_deep_work_streak(
    daily_metrics: list[dict[str, Any]],
) -> dict[str, int]:
    best_streak = 0
    running_streak = 0

    for day in daily_metrics:
        if day["deep_work_goal_met"]:
            running_streak += 1
            best_streak = max(
                best_streak,
                running_streak,
            )
        else:
            running_streak = 0

    current_streak = 0

    for day in reversed(daily_metrics):
        if day["deep_work_goal_met"]:
            current_streak += 1
        else:
            break

    return {
        "current": current_streak,
        "best": best_streak,
    }


def _build_weekly_insight(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> str:
    deep_change = (
        current["deep_work_minutes"]
        - previous["deep_work_minutes"]
    )

    switch_change = (
        current["context_switches"]
        - previous["context_switches"]
    )

    if deep_change > 0 and switch_change < 0:
        return (
            f"Deep work increased by "
            f"{round(deep_change, 1)} minutes while "
            f"context switching decreased by "
            f"{abs(switch_change)}."
        )

    if deep_change > 0:
        return (
            f"Deep work improved by "
            f"{round(deep_change, 1)} minutes compared "
            f"with the previous week."
        )

    if switch_change > 0:
        return (
            f"Context switching increased by "
            f"{switch_change}. Protect longer uninterrupted "
            f"work blocks next week."
        )

    if current["productive_minutes"] == 0:
        return (
            "No productive activity was recorded during "
            "this weekly period."
        )

    return (
        "Your weekly productivity remained relatively "
        "stable compared with the previous period."
    )


def _build_habit_insight(
    best_focus_hour: int | None,
    distraction_hour: int | None,
    distracting_app: str | None,
) -> str:
    observations = []

    if best_focus_hour is not None:
        observations.append(
            f"Your strongest focus period begins around "
            f"{_format_hour(best_focus_hour)}."
        )

    if distraction_hour is not None:
        observations.append(
            f"Distractions peak around "
            f"{_format_hour(distraction_hour)}."
        )

    if distracting_app:
        observations.append(
            f"{distracting_app} was your most distracting app."
        )

    if not observations:
        return (
            "Keep tracking activity to identify recurring "
            "weekly habits."
        )

    return " ".join(observations)


def _filter_logs(
    activity_logs,
    start_date: datetime,
    end_date: datetime,
):
    filtered_logs = []

    for log in activity_logs:
        start_time = _get_datetime(
            log,
            "start_time",
        )

        if (
            start_time is not None
            and start_date <= start_time <= end_date
        ):
            filtered_logs.append(log)

    return filtered_logs


def _get_value(
    log,
    field_name: str,
    default=None,
):
    if isinstance(log, dict):
        return log.get(field_name, default)

    return getattr(log, field_name, default)


def _get_datetime(
    log,
    field_name: str,
) -> datetime | None:
    value = _get_value(
        log,
        field_name,
    )

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except ValueError:
            return None

    return None


def _get_int(
    log,
    field_name: str,
) -> int:
    value = _get_value(
        log,
        field_name,
        0,
    )

    try:
        return max(
            0,
            int(value),
        )
    except (TypeError, ValueError):
        return 0


def _get_text(
    log,
    field_name: str,
) -> str:
    value = _get_value(
        log,
        field_name,
        "",
    )

    return str(value or "")


def _is_productive(
    activity_type: str,
) -> bool:
    return activity_type in PRODUCTIVE_TYPES


def _is_deep_work(
    activity_type: str,
) -> bool:
    return activity_type in {
        "coding",
        "focused",
        "deep_work",
    }


def _is_distraction(
    activity_type: str,
) -> bool:
    return activity_type in DISTRACTION_TYPES


def _largest_key(
    values: dict,
):
    if not values:
        return None

    return max(
        values,
        key=values.get,
    )


def _difference(
    current: float,
    previous: float,
) -> float:
    return round(
        current - previous,
        1,
    )


def _start_of_day(
    value: datetime,
) -> datetime:
    return value.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _end_of_day(
    value: datetime,
) -> datetime:
    return value.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )


def _format_hour_range(
    hour: int,
) -> str:
    next_hour = (hour + 1) % 24

    return (
        f"{_format_hour(hour)}–"
        f"{_format_hour(next_hour)}"
    )


def _format_hour(
    hour: int,
) -> str:
    return datetime.strptime(
        str(hour),
        "%H",
    ).strftime("%I:%M %p").lstrip("0")