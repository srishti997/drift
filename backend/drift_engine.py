def calculate_drift_metrics(activity_logs):
    if not activity_logs:
        return {
            "drift_index": 0,
            "focus_score": 0,
            "total_time": 0,
            "productive_time": 0,
            "distraction_time": 0,
            "idle_time": 0,
            "context_switches": 0,
            "insight": "No activity recorded yet."
        }

    total_time = sum(log.duration_seconds for log in activity_logs)

    productive_types = ["CODING", "LEARNING"]
    distraction_types = ["ENTERTAINMENT", "BROWSING", "COMMUNICATION"]
    idle_types = ["IDLE"]

    productive_time = sum(
        log.duration_seconds for log in activity_logs
        if log.activity_type in productive_types
    )

    distraction_time = sum(
        log.duration_seconds for log in activity_logs
        if log.activity_type in distraction_types
    )

    idle_time = sum(
        log.duration_seconds for log in activity_logs
        if log.activity_type in idle_types
    )

    context_switches = 0
    for i in range(1, len(activity_logs)):
        if activity_logs[i].activity_type != activity_logs[i - 1].activity_type:
            context_switches += 1

    focus_score = round((productive_time / total_time) * 100, 2) if total_time else 0

    distraction_ratio = distraction_time / total_time if total_time else 0
    idle_ratio = idle_time / total_time if total_time else 0
    switch_penalty = min(context_switches * 5, 30)

    drift_index = round(
        (distraction_ratio * 45)
        + (idle_ratio * 25)
        + switch_penalty,
        2
    )

    drift_index = min(drift_index, 100)

    if drift_index < 25:
        insight = "Stable work pattern. Your activity is mostly focused."
    elif drift_index < 50:
        insight = "Minor drift detected. Some browsing or switching is affecting focus."
    elif drift_index < 75:
        insight = "Significant drift detected. Distractions and context switching are increasing."
    else:
        insight = "Critical drift detected. Your work pattern is highly fragmented."

    return {
        "drift_index": drift_index,
        "focus_score": focus_score,
        "total_time": total_time,
        "productive_time": productive_time,
        "distraction_time": distraction_time,
        "idle_time": idle_time,
        "context_switches": context_switches,
        "insight": insight
    }