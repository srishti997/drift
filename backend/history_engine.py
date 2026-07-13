"""
Historical analytics engine for Drift.

This module reads activity logs from data/activity_logs.json and builds
day-by-day productivity analytics for the History page.

It is intentionally independent from Streamlit so it can be called safely
from FastAPI.

Supported output:
- Daily productivity score
- Productive minutes
- Deep-work minutes
- Focus percentage
- Context switches
- Distraction minutes
- Recovery count
- Dominant mission
- Average score
- Best day
- Current streak
- Mission distribution
- Day-by-day history

The engine is defensive: missing or malformed fields do not crash the API.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ACTIVITY_FILE = PROJECT_ROOT / "data" / "activity_logs.json"

PRODUCTIVE_ACTIVITY_TYPES = {
    "CODING",
    "BROWSING",
    "COMMUNICATION",
}

DISTRACTION_ACTIVITY_TYPES = {
    "IDLE",
    "OTHER",
    "SYSTEM",
}

DEFAULT_DEEP_WORK_MINUTES = 30
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 365


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NormalizedActivity:
    timestamp: datetime
    duration_seconds: float
    activity_type: str
    mission: str
    app_name: str
    window_title: str
    is_distraction: bool


@dataclass
class DailyHistory:
    date: str
    weekday: str
    score: float
    grade: str
    productive_minutes: float
    distraction_minutes: float
    total_minutes: float
    deep_work_minutes: float
    focus_percentage: float
    context_switches: int
    recovery_events: int
    dominant_mission: str
    session_count: int
    tracked: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "weekday": self.weekday,
            "score": self.score,
            "grade": self.grade,
            "productive_minutes": self.productive_minutes,
            "distraction_minutes": self.distraction_minutes,
            "total_minutes": self.total_minutes,
            "deep_work_minutes": self.deep_work_minutes,
            "focus_percentage": self.focus_percentage,
            "context_switches": self.context_switches,
            "recovery_events": self.recovery_events,
            "dominant_mission": self.dominant_mission,
            "session_count": self.session_count,
            "tracked": self.tracked,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_history(
    days: int = DEFAULT_LOOKBACK_DAYS,
    activity_file: str | Path | None = None,
) -> dict[str, Any]:
    """
    Build historical analytics for the requested number of calendar days.

    Args:
        days:
            Number of calendar days to include, ending today.
        activity_file:
            Optional alternative path to activity_logs.json.

    Returns:
        JSON-serializable historical analytics dictionary.
    """

    safe_days = _sanitize_days(days)
    path = Path(activity_file) if activity_file else DEFAULT_ACTIVITY_FILE

    raw_logs = load_activity_logs(path)
    activities = normalize_activity_logs(raw_logs)

    start_day = date.today() - timedelta(days=safe_days - 1)
    end_day = date.today()

    activities = [
        activity
        for activity in activities
        if start_day <= activity.timestamp.date() <= end_day
    ]

    grouped = _group_by_date(activities)

    daily_history: list[DailyHistory] = []

    for current_day in _date_range(start_day, end_day):
        logs_for_day = grouped.get(current_day, [])
        daily_history.append(
            calculate_daily_history(
                current_day=current_day,
                activities=logs_for_day,
            )
        )

    history_dicts = [item.to_dict() for item in daily_history]
    tracked_days = [item for item in daily_history if item.tracked]

    mission_distribution = calculate_mission_distribution(activities)
    summary = calculate_history_summary(
        daily_history=daily_history,
        tracked_days=tracked_days,
    )

    return {
        "period": {
            "days": safe_days,
            "start_date": start_day.isoformat(),
            "end_date": end_day.isoformat(),
        },
        "summary": summary,
        "daily": history_dicts,
        "score_history": [
            {
                "date": item.date,
                "score": item.score,
                "tracked": item.tracked,
            }
            for item in daily_history
        ],
        "focus_history": [
            {
                "date": item.date,
                "focus_percentage": item.focus_percentage,
                "productive_minutes": item.productive_minutes,
                "tracked": item.tracked,
            }
            for item in daily_history
        ],
        "deep_work_history": [
            {
                "date": item.date,
                "deep_work_minutes": item.deep_work_minutes,
                "tracked": item.tracked,
            }
            for item in daily_history
        ],
        "context_switch_history": [
            {
                "date": item.date,
                "context_switches": item.context_switches,
                "tracked": item.tracked,
            }
            for item in daily_history
        ],
        "missions": mission_distribution,
        "heatmap": build_heatmap(history_dicts),
        "insight": build_history_insight(
            daily_history=daily_history,
            summary=summary,
        ),
    }


def load_activity_logs(
    activity_file: str | Path = DEFAULT_ACTIVITY_FILE,
) -> list[dict[str, Any]]:
    """
    Read activity logs from JSON.

    Supports:
    - A raw JSON list
    - {"logs": [...]}
    - {"activities": [...]}
    - {"activity_logs": [...]}
    """

    path = Path(activity_file)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError):
        return []

    if isinstance(payload, list):
        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    if isinstance(payload, dict):
        for key in (
            "logs",
            "activities",
            "activity_logs",
            "data",
            "items",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                return [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]

    return []


def normalize_activity_logs(
    logs: Iterable[dict[str, Any]],
) -> list[NormalizedActivity]:
    """
    Normalize different possible tracker log formats into one structure.
    """

    normalized: list[NormalizedActivity] = []

    for log in logs:
        timestamp = _extract_timestamp(log)

        if timestamp is None:
            continue

        duration_seconds = _extract_duration_seconds(log)
        activity_type = _extract_activity_type(log)
        mission = _extract_mission(log, activity_type)
        app_name = _extract_text(
            log,
            "app",
            "app_name",
            "application",
            "process_name",
            "process",
        )
        window_title = _extract_text(
            log,
            "window_title",
            "title",
            "active_window",
            "window",
        )

        explicit_distraction = log.get("is_distraction")

        if isinstance(explicit_distraction, bool):
            is_distraction = explicit_distraction
        else:
            is_distraction = (
                activity_type in DISTRACTION_ACTIVITY_TYPES
            )

        normalized.append(
            NormalizedActivity(
                timestamp=timestamp,
                duration_seconds=max(0.0, duration_seconds),
                activity_type=activity_type,
                mission=mission,
                app_name=app_name or "Unknown",
                window_title=window_title or "",
                is_distraction=is_distraction,
            )
        )

    normalized.sort(key=lambda item: item.timestamp)
    return normalized


def calculate_daily_history(
    current_day: date,
    activities: list[NormalizedActivity],
) -> DailyHistory:
    """
    Calculate all historical metrics for one calendar day.
    """

    if not activities:
        return DailyHistory(
            date=current_day.isoformat(),
            weekday=current_day.strftime("%A"),
            score=0.0,
            grade="N/A",
            productive_minutes=0.0,
            distraction_minutes=0.0,
            total_minutes=0.0,
            deep_work_minutes=0.0,
            focus_percentage=0.0,
            context_switches=0,
            recovery_events=0,
            dominant_mission="No activity",
            session_count=0,
            tracked=False,
        )

    productive_seconds = sum(
        activity.duration_seconds
        for activity in activities
        if not activity.is_distraction
    )

    distraction_seconds = sum(
        activity.duration_seconds
        for activity in activities
        if activity.is_distraction
    )

    total_seconds = productive_seconds + distraction_seconds

    focus_percentage = (
        productive_seconds / total_seconds * 100
        if total_seconds > 0
        else 0
    )

    sessions = _build_sessions(activities)
    deep_work_seconds = calculate_deep_work_seconds(sessions)
    context_switches = calculate_context_switches(activities)
    recovery_events = calculate_recovery_events(sessions)
    dominant_mission = calculate_dominant_mission(activities)

    score = calculate_productivity_score(
        focus_percentage=focus_percentage,
        deep_work_seconds=deep_work_seconds,
        productive_seconds=productive_seconds,
        context_switches=context_switches,
        recovery_events=recovery_events,
        distraction_seconds=distraction_seconds,
    )

    return DailyHistory(
        date=current_day.isoformat(),
        weekday=current_day.strftime("%A"),
        score=round(score, 2),
        grade=score_to_grade(score),
        productive_minutes=round(productive_seconds / 60, 2),
        distraction_minutes=round(distraction_seconds / 60, 2),
        total_minutes=round(total_seconds / 60, 2),
        deep_work_minutes=round(deep_work_seconds / 60, 2),
        focus_percentage=round(focus_percentage, 2),
        context_switches=context_switches,
        recovery_events=recovery_events,
        dominant_mission=dominant_mission,
        session_count=len(sessions),
        tracked=True,
    )


def calculate_productivity_score(
    focus_percentage: float,
    deep_work_seconds: float,
    productive_seconds: float,
    context_switches: int,
    recovery_events: int,
    distraction_seconds: float,
) -> float:
    """
    Calculate a 0-100 historical productivity score.

    This score is intentionally self-contained and stable so historical
    records can be compared even if other dashboard engines evolve.

    Weighting:
    - Focus ratio: 40%
    - Deep-work achievement: 25%
    - Productive duration: 15%
    - Switch control: 10%
    - Recovery ability: 10%
    """

    focus_component = _clamp(focus_percentage, 0, 100)

    deep_work_target_seconds = 120 * 60
    deep_work_component = _clamp(
        deep_work_seconds / deep_work_target_seconds * 100,
        0,
        100,
    )

    productive_target_seconds = 240 * 60
    productive_component = _clamp(
        productive_seconds / productive_target_seconds * 100,
        0,
        100,
    )

    switch_component = max(
        0,
        100 - context_switches * 2,
    )

    if distraction_seconds <= 0:
        recovery_component = 100
    else:
        expected_recoveries = max(
            1,
            math.ceil(distraction_seconds / (20 * 60)),
        )

        recovery_component = _clamp(
            recovery_events / expected_recoveries * 100,
            0,
            100,
        )

    score = (
        focus_component * 0.40
        + deep_work_component * 0.25
        + productive_component * 0.15
        + switch_component * 0.10
        + recovery_component * 0.10
    )

    return _clamp(score, 0, 100)


def calculate_deep_work_seconds(
    sessions: list[dict[str, Any]],
    minimum_minutes: int = DEFAULT_DEEP_WORK_MINUTES,
) -> float:
    """
    Count productive sessions lasting at least minimum_minutes as deep work.
    """

    threshold_seconds = minimum_minutes * 60

    return sum(
        float(session.get("duration_seconds", 0))
        for session in sessions
        if (
            not session.get("is_distraction", False)
            and float(session.get("duration_seconds", 0))
            >= threshold_seconds
        )
    )


def calculate_context_switches(
    activities: list[NormalizedActivity],
) -> int:
    """
    Count meaningful changes in mission, application, or activity type.
    """

    if len(activities) < 2:
        return 0

    switches = 0
    previous = activities[0]

    for current in activities[1:]:
        changed_mission = current.mission != previous.mission
        changed_type = (
            current.activity_type != previous.activity_type
        )
        changed_app = (
            current.app_name != previous.app_name
            and current.app_name != "Unknown"
            and previous.app_name != "Unknown"
        )

        if changed_mission or changed_type or changed_app:
            switches += 1

        previous = current

    return switches


def calculate_recovery_events(
    sessions: list[dict[str, Any]],
) -> int:
    """
    Count a recovery when a productive session follows a distraction session.
    """

    recoveries = 0

    for previous, current in zip(sessions, sessions[1:]):
        if (
            previous.get("is_distraction", False)
            and not current.get("is_distraction", False)
        ):
            recoveries += 1

    return recoveries


def calculate_dominant_mission(
    activities: list[NormalizedActivity],
) -> str:
    """
    Return the mission with the largest tracked duration.
    """

    mission_seconds: dict[str, float] = defaultdict(float)

    for activity in activities:
        mission_seconds[activity.mission] += (
            activity.duration_seconds
        )

    if not mission_seconds:
        return "No activity"

    return max(
        mission_seconds,
        key=mission_seconds.get,
    )


def calculate_mission_distribution(
    activities: list[NormalizedActivity],
) -> list[dict[str, Any]]:
    """
    Aggregate mission durations across the complete history period.
    """

    mission_seconds: dict[str, float] = defaultdict(float)

    for activity in activities:
        mission_seconds[activity.mission] += (
            activity.duration_seconds
        )

    total_seconds = sum(mission_seconds.values()) or 1

    distribution = []

    for mission, seconds in sorted(
        mission_seconds.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        distribution.append(
            {
                "mission": mission,
                "time_seconds": round(seconds, 2),
                "minutes": round(seconds / 60, 2),
                "percentage": round(
                    seconds / total_seconds * 100,
                    2,
                ),
            }
        )

    return distribution


def calculate_history_summary(
    daily_history: list[DailyHistory],
    tracked_days: list[DailyHistory],
) -> dict[str, Any]:
    """
    Build summary cards used by the History page.
    """

    if not tracked_days:
        return {
            "tracked_days": 0,
            "average_score": 0,
            "average_focus_percentage": 0,
            "total_productive_minutes": 0,
            "total_deep_work_minutes": 0,
            "total_context_switches": 0,
            "best_day": None,
            "current_streak": 0,
            "longest_streak": 0,
            "score_change_percentage": 0,
            "focus_change_percentage": 0,
        }

    average_score = _average(
        item.score
        for item in tracked_days
    )

    average_focus = _average(
        item.focus_percentage
        for item in tracked_days
    )

    best_day = max(
        tracked_days,
        key=lambda item: item.score,
    )

    current_streak = calculate_current_streak(daily_history)
    longest_streak = calculate_longest_streak(daily_history)

    score_change = calculate_period_change(
        [item.score for item in tracked_days]
    )

    focus_change = calculate_period_change(
        [
            item.focus_percentage
            for item in tracked_days
        ]
    )

    return {
        "tracked_days": len(tracked_days),
        "average_score": round(average_score, 2),
        "average_focus_percentage": round(
            average_focus,
            2,
        ),
        "total_productive_minutes": round(
            sum(
                item.productive_minutes
                for item in tracked_days
            ),
            2,
        ),
        "total_deep_work_minutes": round(
            sum(
                item.deep_work_minutes
                for item in tracked_days
            ),
            2,
        ),
        "total_context_switches": sum(
            item.context_switches
            for item in tracked_days
        ),
        "best_day": {
            "date": best_day.date,
            "weekday": best_day.weekday,
            "score": best_day.score,
            "dominant_mission": best_day.dominant_mission,
        },
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "score_change_percentage": score_change,
        "focus_change_percentage": focus_change,
    }


def calculate_current_streak(
    daily_history: list[DailyHistory],
) -> int:
    """
    Count consecutive tracked days ending at the most recent calendar day.
    """

    streak = 0

    for item in reversed(daily_history):
        if not item.tracked:
            break

        streak += 1

    return streak


def calculate_longest_streak(
    daily_history: list[DailyHistory],
) -> int:
    """
    Find the longest sequence of consecutive tracked days.
    """

    longest = 0
    current = 0

    for item in daily_history:
        if item.tracked:
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    return longest


def calculate_period_change(
    values: list[float],
) -> float:
    """
    Compare the average of the latest half with the earlier half.
    """

    if len(values) < 2:
        return 0.0

    midpoint = len(values) // 2

    previous_values = values[:midpoint]
    current_values = values[midpoint:]

    previous_average = _average(previous_values)
    current_average = _average(current_values)

    if previous_average == 0:
        return 0.0

    return round(
        (
            (current_average - previous_average)
            / previous_average
        )
        * 100,
        2,
    )


def build_heatmap(
    daily_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Create compact GitHub-style heatmap values for the UI.
    """

    heatmap = []

    for item in daily_history:
        score = float(item.get("score", 0))
        tracked = bool(item.get("tracked", False))

        if not tracked:
            level = 0
        elif score < 25:
            level = 1
        elif score < 50:
            level = 2
        elif score < 75:
            level = 3
        else:
            level = 4

        heatmap.append(
            {
                "date": item.get("date"),
                "weekday": item.get("weekday"),
                "score": score,
                "level": level,
                "tracked": tracked,
            }
        )

    return heatmap


def build_history_insight(
    daily_history: list[DailyHistory],
    summary: dict[str, Any],
) -> str:
    """
    Generate a concise narrative insight from historical trends.
    """

    tracked_days = [
        item
        for item in daily_history
        if item.tracked
    ]

    if not tracked_days:
        return (
            "No historical activity is available yet. "
            "Run the tracker across multiple days to unlock trends."
        )

    score_change = summary.get(
        "score_change_percentage",
        0,
    )
    current_streak = summary.get("current_streak", 0)
    best_day = summary.get("best_day") or {}

    if score_change >= 10:
        direction = (
            f"Your average productivity score improved by "
            f"{abs(score_change)}% during the latest part of this period."
        )
    elif score_change <= -10:
        direction = (
            f"Your average productivity score declined by "
            f"{abs(score_change)}% during the latest part of this period."
        )
    else:
        direction = (
            "Your productivity score remained relatively stable "
            "during this period."
        )

    streak_text = (
        f"You are currently on a {current_streak}-day tracking streak."
        if current_streak > 0
        else "Your current tracking streak is inactive."
    )

    best_day_text = ""

    if best_day:
        best_day_text = (
            f" Your strongest day was {best_day.get('weekday')} "
            f"with a score of {best_day.get('score')}."
        )

    return f"{direction} {streak_text}{best_day_text}"


def score_to_grade(score: float) -> str:
    """
    Convert a 0-100 score to a letter grade.
    """

    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    return "F"


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_sessions(
    activities: list[NormalizedActivity],
) -> list[dict[str, Any]]:
    """
    Merge consecutive activities with the same activity type and mission.
    """

    if not activities:
        return []

    sessions: list[dict[str, Any]] = []

    for activity in activities:
        if not sessions:
            sessions.append(
                {
                    "activity_type": activity.activity_type,
                    "mission": activity.mission,
                    "duration_seconds": (
                        activity.duration_seconds
                    ),
                    "is_distraction": activity.is_distraction,
                    "started_at": activity.timestamp,
                    "ended_at": activity.timestamp,
                }
            )
            continue

        previous = sessions[-1]

        same_type = (
            previous["activity_type"]
            == activity.activity_type
        )
        same_mission = (
            previous["mission"]
            == activity.mission
        )
        same_distraction_state = (
            previous["is_distraction"]
            == activity.is_distraction
        )

        if (
            same_type
            and same_mission
            and same_distraction_state
        ):
            previous["duration_seconds"] += (
                activity.duration_seconds
            )
            previous["ended_at"] = activity.timestamp
        else:
            sessions.append(
                {
                    "activity_type": activity.activity_type,
                    "mission": activity.mission,
                    "duration_seconds": (
                        activity.duration_seconds
                    ),
                    "is_distraction": activity.is_distraction,
                    "started_at": activity.timestamp,
                    "ended_at": activity.timestamp,
                }
            )

    return sessions


def _group_by_date(
    activities: list[NormalizedActivity],
) -> dict[date, list[NormalizedActivity]]:
    grouped: dict[date, list[NormalizedActivity]] = defaultdict(list)

    for activity in activities:
        grouped[activity.timestamp.date()].append(activity)

    return grouped


def _date_range(
    start_date: date,
    end_date: date,
) -> Iterable[date]:
    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _extract_timestamp(
    log: dict[str, Any],
) -> Optional[datetime]:
    possible_values = [
        log.get("timestamp"),
        log.get("created_at"),
        log.get("recorded_at"),
        log.get("time"),
        log.get("datetime"),
        log.get("date_time"),
        log.get("start_time"),
    ]

    for value in possible_values:
        parsed = _parse_datetime(value)

        if parsed is not None:
            return parsed

    raw_date = log.get("date")
    raw_time = log.get("time")

    if raw_date:
        combined = (
            f"{raw_date}T{raw_time}"
            if raw_time
            else str(raw_date)
        )

        return _parse_datetime(combined)

    return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return _to_local_naive(value)

    if isinstance(value, (int, float)):
        try:
            timestamp = float(value)

            if timestamp > 10_000_000_000:
                timestamp /= 1000

            return datetime.fromtimestamp(timestamp)
        except (ValueError, OSError, OverflowError):
            return None

    text = str(value).strip()

    if not text:
        return None

    normalized = text.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
        return _to_local_naive(parsed)
    except ValueError:
        pass

    supported_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%m/%d/%Y %H:%M:%S",
    ]

    for date_format in supported_formats:
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue

    return None


def _to_local_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value

    local_value = value.astimezone()
    return local_value.replace(tzinfo=None)


def _extract_duration_seconds(
    log: dict[str, Any],
) -> float:
    second_fields = (
        "duration_seconds",
        "duration",
        "seconds",
        "elapsed_seconds",
        "active_seconds",
    )

    for field in second_fields:
        value = log.get(field)

        if value is not None:
            parsed = _safe_float(value)

            if parsed is not None:
                return parsed

    minute_fields = (
        "duration_minutes",
        "minutes",
        "elapsed_minutes",
    )

    for field in minute_fields:
        value = log.get(field)

        if value is not None:
            parsed = _safe_float(value)

            if parsed is not None:
                return parsed * 60

    return 0.0


def _extract_activity_type(
    log: dict[str, Any],
) -> str:
    value = _extract_text(
        log,
        "activity_type",
        "type",
        "category",
        "activity",
        "classification",
    )

    if not value:
        return "UNKNOWN"

    return value.strip().upper()


def _extract_mission(
    log: dict[str, Any],
    activity_type: str,
) -> str:
    explicit_mission = _extract_text(
        log,
        "mission",
        "mission_name",
        "goal",
        "intent",
        "project",
    )

    if explicit_mission:
        return explicit_mission

    fallback_mapping = {
        "CODING": "Build Drift",
        "BROWSING": "Research / Information Gathering",
        "COMMUNICATION": "Communication",
        "IDLE": "Break / Distraction",
        "OTHER": "Unclassified Mission",
        "SYSTEM": "System Activity",
    }

    return fallback_mapping.get(
        activity_type,
        "Unclassified Mission",
    )


def _extract_text(
    data: dict[str, Any],
    *fields: str,
) -> str:
    for field in fields:
        value = data.get(field)

        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return ""


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sanitize_days(days: Any) -> int:
    try:
        parsed = int(days)
    except (TypeError, ValueError):
        parsed = DEFAULT_LOOKBACK_DAYS

    return max(
        1,
        min(parsed, MAX_LOOKBACK_DAYS),
    )


def _average(values: Iterable[float]) -> float:
    values_list = list(values)

    if not values_list:
        return 0.0

    return sum(values_list) / len(values_list)


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Local testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = build_history(days=7)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )