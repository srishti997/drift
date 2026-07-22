from __future__ import annotations

from typing import Any

from backend.mission_engine import infer_mission_for_log


PRODUCTIVE_MISSIONS = {
    "Build Drift",
    "Career Growth",
    "Skill Development",
}

DISTRACTION_MISSIONS = {
    "Break / Distraction",
}

# Ignore tiny interruptions that are likely normal tab or app changes.
MIN_INTERRUPTION_SECONDS = 30

# Prevent one unusually long log from creating an unrealistic recovery cost.
MAX_INTERRUPTION_SECONDS = 30 * 60

# Look ahead through a few logs to determine whether the user recovered.
RECOVERY_LOOKAHEAD_LOGS = 12

# Recovery cost should represent cognitive recovery overhead,
# not the entire interruption duration.
MAX_RECOVERY_OVERHEAD_MINUTES = 15


def build_recovery_summary(
    activity_logs: list[Any],
) -> dict[str, Any]:
    if len(activity_logs) < 2:
        return _empty_summary(
            "Not enough activity to calculate recovery cost."
        )

    inferred_logs = []

    for log in activity_logs:
        inferred = infer_mission_for_log(log)

        inferred_logs.append(
            {
                "log": log,
                "mission": inferred.get(
                    "mission",
                    "Unclassified Mission",
                ),
                "intent": inferred.get(
                    "intent",
                    "OTHER",
                ),
                "duration_seconds": _safe_seconds(
                    getattr(
                        log,
                        "duration_seconds",
                        0,
                    )
                ),
                "timestamp": getattr(
                    log,
                    "timestamp",
                    None,
                ),
            }
        )

    recovery_events: list[dict[str, Any]] = []

    index = 0

    while index < len(inferred_logs) - 1:
        current = inferred_logs[index]
        following = inferred_logs[index + 1]

        current_mission = current["mission"]
        following_mission = following["mission"]

        started_productive = (
            current_mission in PRODUCTIVE_MISSIONS
        )

        switched_away = (
            following_mission != current_mission
        )

        if not started_productive or not switched_away:
            index += 1
            continue

        interruption_start = index + 1
        interruption_end = interruption_start

        interruption_seconds = 0
        interruption_missions: list[str] = []
        interruption_intents: list[str] = []

        recovered = False
        recovery_index = None

        lookahead_limit = min(
            len(inferred_logs),
            interruption_start
            + RECOVERY_LOOKAHEAD_LOGS
            + 1,
        )

        for candidate_index in range(
            interruption_start,
            lookahead_limit,
        ):
            candidate = inferred_logs[candidate_index]

            if candidate["mission"] == current_mission:
                recovered = True
                recovery_index = candidate_index
                break

            interruption_end = candidate_index
            interruption_seconds += candidate[
                "duration_seconds"
            ]

            interruption_missions.append(
                candidate["mission"]
            )

            interruption_intents.append(
                candidate["intent"]
            )

        interruption_seconds = min(
            interruption_seconds,
            MAX_INTERRUPTION_SECONDS,
        )

        if interruption_seconds < MIN_INTERRUPTION_SECONDS:
            index += 1
            continue

        dominant_interruption_mission = (
            _most_common(
                interruption_missions
            )
            or following_mission
        )

        estimated_cost_minutes = (
            _estimate_recovery_cost(
                interruption_mission=(
                    dominant_interruption_mission
                ),
                interruption_duration_seconds=(
                    interruption_seconds
                ),
                returned=recovered,
            )
        )

        recovery_events.append(
            {
                "from_mission": current_mission,
                "interrupted_by": (
                    dominant_interruption_mission
                ),
                "returned_to_mission": recovered,
                "interruption_duration_seconds": (
                    interruption_seconds
                ),
                "estimated_recovery_cost_minutes": (
                    estimated_cost_minutes
                ),
                "estimated_recovery_cost_seconds": round(
                    estimated_cost_minutes * 60,
                    2,
                ),
                "before_intent": current["intent"],
                "interruption_intent": (
                    _most_common(
                        interruption_intents
                    )
                    or following["intent"]
                ),
                "after_intent": (
                    inferred_logs[recovery_index][
                        "intent"
                    ]
                    if recovery_index is not None
                    else None
                ),
                "interruption_start": (
                    following["timestamp"]
                ),
                "recovery_timestamp": (
                    inferred_logs[recovery_index][
                        "timestamp"
                    ]
                    if recovery_index is not None
                    else None
                ),
            }
        )

        # Skip the full interruption sequence so overlapping
        # windows do not count the same interruption repeatedly.
        if recovery_index is not None:
            index = recovery_index
        else:
            index = max(
                interruption_end,
                index + 1,
            )

    total_cost_minutes = round(
        sum(
            event[
                "estimated_recovery_cost_minutes"
            ]
            for event in recovery_events
        ),
        2,
    )

    recovery_count = len(recovery_events)

    successful_recoveries = sum(
        1
        for event in recovery_events
        if event["returned_to_mission"]
    )

    recovery_rate = round(
        (
            successful_recoveries
            / recovery_count
            * 100
        )
        if recovery_count
        else 0,
        2,
    )

    average_cost_minutes = round(
        (
            total_cost_minutes
            / recovery_count
        )
        if recovery_count
        else 0,
        2,
    )

    insight = _build_insight(
        recovery_count=recovery_count,
        recovery_rate=recovery_rate,
        total_cost_minutes=total_cost_minutes,
        average_cost_minutes=average_cost_minutes,
    )

    return {
        # Keys expected by the current dashboard
        "count": recovery_count,
        "total_recovery_cost_seconds": round(
            total_cost_minutes * 60,
            2,
        ),
        "average_recovery_cost_seconds": round(
            average_cost_minutes * 60,
            2,
        ),

        # Human-readable values
        "total_recovery_cost_minutes": (
            total_cost_minutes
        ),
        "average_recovery_cost_minutes": (
            average_cost_minutes
        ),
        "recovery_rate": recovery_rate,
        "successful_recoveries": (
            successful_recoveries
        ),
        "recovery_events": recovery_events,
        "insight": insight,
    }


def _estimate_recovery_cost(
    interruption_mission: str,
    interruption_duration_seconds: float,
    returned: bool,
) -> float:
    interruption_minutes = min(
        max(
            interruption_duration_seconds / 60,
            0,
        ),
        MAX_INTERRUPTION_SECONDS / 60,
    )

    # Recovery cost is cognitive overhead after an interruption.
    # It should not duplicate the entire interruption duration.
    if interruption_mission in DISTRACTION_MISSIONS:
        base_overhead = 3.0
        duration_factor = 0.20
    elif interruption_mission == "Unclassified Mission":
        base_overhead = 1.0
        duration_factor = 0.10
    else:
        base_overhead = 1.5
        duration_factor = 0.15

    cost = (
        base_overhead
        + interruption_minutes
        * duration_factor
    )

    if not returned:
        cost += 2.0

    return round(
        min(
            cost,
            MAX_RECOVERY_OVERHEAD_MINUTES,
        ),
        2,
    )


def _build_insight(
    recovery_count: int,
    recovery_rate: float,
    total_cost_minutes: float,
    average_cost_minutes: float,
) -> str:
    if recovery_count == 0:
        return (
            "No meaningful recovery events were detected."
        )

    if recovery_rate >= 75:
        return (
            f"You recovered well after interruptions, "
            f"with a {recovery_rate:g}% recovery rate. "
            f"The average estimated recovery overhead "
            f"was {average_cost_minutes:g} minutes."
        )

    if recovery_rate >= 40:
        return (
            f"You recovered after some interruptions. "
            f"Drift estimates a total recovery overhead "
            f"of {total_cost_minutes:g} minutes."
        )

    return (
        f"Your recovery rate was low. Interruptions "
        f"created an estimated {total_cost_minutes:g} "
        f"minutes of recovery overhead."
    )


def _empty_summary(
    insight: str,
) -> dict[str, Any]:
    return {
        "count": 0,
        "total_recovery_cost_seconds": 0,
        "average_recovery_cost_seconds": 0,
        "total_recovery_cost_minutes": 0,
        "average_recovery_cost_minutes": 0,
        "recovery_rate": 0,
        "successful_recoveries": 0,
        "recovery_events": [],
        "insight": insight,
    }


def _safe_seconds(
    value: Any,
) -> float:
    try:
        seconds = float(value or 0)
    except (TypeError, ValueError):
        return 0

    return max(0, seconds)


def _most_common(
    values: list[str],
) -> str | None:
    if not values:
        return None

    return max(
        set(values),
        key=values.count,
    )