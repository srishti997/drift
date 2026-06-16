from backend.mission_engine import infer_mission_for_log


def detect_behavior_patterns(activity_logs):
    if len(activity_logs) < 3:
        return {
            "patterns": [],
            "insight": "Not enough activity to detect behavior patterns."
        }

    patterns = []
    missions = [infer_mission_for_log(log)["mission"] for log in activity_logs]
    apps = [log.app_name for log in activity_logs]

    # 1. Mission recovery: A -> B -> A
    recovery_count = 0
    for i in range(len(missions) - 2):
        if missions[i] == missions[i + 2] and missions[i] != missions[i + 1]:
            recovery_count += 1

    if recovery_count > 0:
        patterns.append({
            "type": "Mission Recovery",
            "count": recovery_count,
            "description": "You returned to your original mission after switching away."
        })

    # 2. Mission abandonment: productive mission -> distraction/break and no return
    abandonment_count = 0
    productive_missions = {"Build Drift", "Career Growth", "Skill Development"}
    distraction_missions = {"Break / Distraction", "Unclassified Mission"}

    for i in range(len(missions) - 1):
        if missions[i] in productive_missions and missions[i + 1] in distraction_missions:
            if missions[i] not in missions[i + 2:]:
                abandonment_count += 1

    if abandonment_count > 0:
        patterns.append({
            "type": "Mission Abandonment",
            "count": abandonment_count,
            "description": "You switched away from a productive mission and did not return."
        })

    # 3. App ping-pong: repeated switching between two apps
    ping_pong_count = 0
    for i in range(len(apps) - 2):
        if apps[i] == apps[i + 2] and apps[i] != apps[i + 1]:
            ping_pong_count += 1

    if ping_pong_count > 0:
        patterns.append({
            "type": "App Ping-Pong",
            "count": ping_pong_count,
            "description": "You repeatedly switched between two apps."
        })

    # 4. Long same-mission streak
    streaks = []
    current_mission = missions[0]
    current_duration = activity_logs[0].duration_seconds

    for i in range(1, len(activity_logs)):
        if missions[i] == current_mission:
            current_duration += activity_logs[i].duration_seconds
        else:
            streaks.append((current_mission, current_duration))
            current_mission = missions[i]
            current_duration = activity_logs[i].duration_seconds

    streaks.append((current_mission, current_duration))

    deep_work_streaks = [
        {"mission": mission, "duration_seconds": duration}
        for mission, duration in streaks
        if mission in productive_missions and duration >= 1800
    ]

    if deep_work_streaks:
        patterns.append({
            "type": "Deep Work",
            "count": len(deep_work_streaks),
            "sessions": deep_work_streaks,
            "description": "You had long uninterrupted productive mission blocks."
        })

    if not patterns:
        insight = "No strong behavior patterns detected yet."
    else:
        insight = f"Detected {len(patterns)} behavior pattern types from your activity."

    return {
        "patterns": patterns,
        "insight": insight
    }