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

DEEP_WORK_THRESHOLD_SECONDS = 30 * 60


def build_deep_work_summary(activity_logs):
    if not activity_logs:
        return {
            "deep_work_sessions": [],
            "total_deep_work_minutes": 0,
            "longest_session_minutes": 0,
            "count": 0,
            "insight": "No activity recorded yet."
        }

    deep_work_sessions = []
    current_session = None

    for log in activity_logs:
        mission_data = infer_mission_for_log(log)
        mission = mission_data["mission"]
        goal = mission_data["goal"]
        intent = mission_data["intent"]

        is_productive = mission in PRODUCTIVE_MISSIONS
        is_distraction = mission in DISTRACTION_MISSIONS

        if is_productive:
            if current_session is None:
                current_session = {
                    "mission": mission,
                    "goal": goal,
                    "intents": {intent: log.duration_seconds},
                    "duration_seconds": log.duration_seconds,
                    "apps": {log.app_name: log.duration_seconds},
                }
            elif current_session["mission"] == mission:
                current_session["duration_seconds"] += log.duration_seconds
                current_session["intents"][intent] = (
                    current_session["intents"].get(intent, 0) + log.duration_seconds
                )
                current_session["apps"][log.app_name] = (
                    current_session["apps"].get(log.app_name, 0) + log.duration_seconds
                )
            else:
                _finalize_session(current_session, deep_work_sessions)
                current_session = {
                    "mission": mission,
                    "goal": goal,
                    "intents": {intent: log.duration_seconds},
                    "duration_seconds": log.duration_seconds,
                    "apps": {log.app_name: log.duration_seconds},
                }

        elif is_distraction:
            if current_session is not None:
                _finalize_session(current_session, deep_work_sessions)
                current_session = None

        else:
            if current_session is not None:
                current_session["duration_seconds"] += log.duration_seconds
                current_session["intents"][intent] = (
                    current_session["intents"].get(intent, 0) + log.duration_seconds
                )
                current_session["apps"][log.app_name] = (
                    current_session["apps"].get(log.app_name, 0) + log.duration_seconds
                )

    if current_session is not None:
        _finalize_session(current_session, deep_work_sessions)

    total_deep_work_seconds = sum(
        session["duration_seconds"] for session in deep_work_sessions
    )

    longest_session_seconds = max(
        [session["duration_seconds"] for session in deep_work_sessions],
        default=0
    )

    if deep_work_sessions:
        insight = f"You completed {len(deep_work_sessions)} deep work session(s)."
    else:
        insight = "No deep work sessions detected yet. Try staying on one productive mission for at least 30 minutes."

    return {
        "deep_work_sessions": deep_work_sessions,
        "total_deep_work_minutes": round(total_deep_work_seconds / 60, 2),
        "longest_session_minutes": round(longest_session_seconds / 60, 2),
        "count": len(deep_work_sessions),
        "insight": insight
    }


def _finalize_session(session, deep_work_sessions):
    if session["duration_seconds"] >= DEEP_WORK_THRESHOLD_SECONDS:
        deep_work_sessions.append({
            "mission": session["mission"],
            "goal": session["goal"],
            "duration_seconds": session["duration_seconds"],
            "duration_minutes": round(session["duration_seconds"] / 60, 2),
            "intents": session["intents"],
            "apps": session["apps"],
        })