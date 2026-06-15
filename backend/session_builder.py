def build_sessions(activity_logs):
    """
    Groups consecutive activities of the same type into sessions.
    Example:
    CODING + CODING = one CODING session
    CODING -> BROWSING -> CODING = three sessions
    """

    if not activity_logs:
        return []

    sessions = []

    current_type = activity_logs[0].activity_type
    current_duration = activity_logs[0].duration_seconds

    for log in activity_logs[1:]:

        if log.activity_type == current_type:
            current_duration += log.duration_seconds

        else:
            sessions.append({
                "activity_type": current_type,
                "duration": current_duration
            })

            current_type = log.activity_type
            current_duration = log.duration_seconds

    sessions.append({
        "activity_type": current_type,
        "duration": current_duration
    })

    return sessions