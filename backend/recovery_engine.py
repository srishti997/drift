from backend.mission_engine import infer_mission_for_log


PRODUCTIVE_MISSIONS = {
    "Build Drift",
    "Career Growth",
    "Skill Development",
}

DISTRACTION_MISSIONS = {
    "Break / Distraction",
    "Unclassified Mission",
}


def build_recovery_summary(activity_logs):
    if len(activity_logs) < 3:
        return {
            "total_recovery_cost_minutes": 0,
            "recovery_events": [],
            "recovery_rate": 0,
            "insight": "Not enough activity to calculate recovery cost."
        }

    recovery_events = []

    for i in range(len(activity_logs) - 2):
        before = activity_logs[i]
        middle = activity_logs[i + 1]
        after = activity_logs[i + 2]

        before_data = infer_mission_for_log(before)
        middle_data = infer_mission_for_log(middle)
        after_data = infer_mission_for_log(after)

        before_mission = before_data["mission"]
        middle_mission = middle_data["mission"]
        after_mission = after_data["mission"]

        started_productive = before_mission in PRODUCTIVE_MISSIONS
        switched_away = middle_mission != before_mission
        returned = after_mission == before_mission

        if started_productive and switched_away:
            estimated_cost = _estimate_recovery_cost(
                middle_mission,
                middle.duration_seconds,
                returned
            )

            recovery_events.append({
                "from_mission": before_mission,
                "interrupted_by": middle_mission,
                "returned_to_mission": returned,
                "interruption_duration_seconds": middle.duration_seconds,
                "estimated_recovery_cost_minutes": estimated_cost,
                "before_intent": before_data["intent"],
                "interruption_intent": middle_data["intent"],
                "after_intent": after_data["intent"],
            })

    total_cost = round(
        sum(event["estimated_recovery_cost_minutes"] for event in recovery_events),
        2
    )

    successful_recoveries = sum(
        1 for event in recovery_events if event["returned_to_mission"]
    )

    recovery_rate = round(
        (successful_recoveries / len(recovery_events)) * 100,
        2
    ) if recovery_events else 0

    if not recovery_events:
        insight = "No major recovery events detected."
    elif recovery_rate >= 75:
        insight = f"You recovered well after interruptions, with a {recovery_rate}% recovery rate."
    elif recovery_rate >= 40:
        insight = f"You recovered from some interruptions, but lost around {total_cost} minutes to recovery cost."
    else:
        insight = f"Low recovery rate detected. Interruptions cost an estimated {total_cost} minutes."

    return {
        "total_recovery_cost_minutes": total_cost,
        "recovery_events": recovery_events,
        "recovery_rate": recovery_rate,
        "insight": insight
    }


def _estimate_recovery_cost(interruption_mission, interruption_duration_seconds, returned):
    interruption_minutes = interruption_duration_seconds / 60

    if interruption_mission in DISTRACTION_MISSIONS:
        multiplier = 2.0
    else:
        multiplier = 1.2

    if returned:
        cost = interruption_minutes * multiplier
    else:
        cost = interruption_minutes * multiplier + 5

    return round(cost, 2)