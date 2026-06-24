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


def calculate_recovery_cost(activity_logs):
    if len(activity_logs) < 3:
        return {
            "recovery_events": [],
            "total_recovery_cost_seconds": 0,
            "average_recovery_cost_seconds": 0,
            "count": 0,
            "insight": "Not enough activity to calculate recovery cost."
        }

    recovery_events = []

    i = 0

    while i < len(activity_logs) - 2:
        start_log = activity_logs[i]
        start_mission = infer_mission_for_log(start_log)["mission"]

        if start_mission not in PRODUCTIVE_MISSIONS:
            i += 1
            continue

        j = i + 1
        distraction_duration = 0

        while j < len(activity_logs):
            current_log = activity_logs[j]
            current_mission = infer_mission_for_log(current_log)["mission"]

            if current_mission == start_mission:
                break

            distraction_duration += current_log.duration_seconds
            j += 1

        if j < len(activity_logs) and distraction_duration > 0:
            recovery_events.append({
                "original_mission": start_mission,
                "returned_at_index": j,
                "distraction_duration_seconds": distraction_duration,
                "estimated_recovery_cost_seconds": distraction_duration,
                "total_focus_cost_seconds": distraction_duration * 2,
            })

            i = j
        else:
            i += 1

    total_recovery_cost = sum(
        event["estimated_recovery_cost_seconds"]
        for event in recovery_events
    )

    count = len(recovery_events)

    average = round(total_recovery_cost / count, 2) if count else 0

    if count == 0:
        insight = "No recovery events detected yet."
    else:
        insight = (
            f"Detected {count} recovery event(s). "
            f"Average estimated recovery cost is {average} seconds."
        )

    return {
        "recovery_events": recovery_events,
        "total_recovery_cost_seconds": total_recovery_cost,
        "average_recovery_cost_seconds": average,
        "count": count,
        "insight": insight
    }