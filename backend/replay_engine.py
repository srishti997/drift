from backend.session_builder import build_sessions


DISTRACTION_TYPES = {"IDLE", "OTHER", "SYSTEM"}
PRODUCTIVE_TYPES = {"CODING", "BROWSING", "COMMUNICATION"}

MIN_SESSION_SECONDS = 60


def build_day_replay(activity_logs):
    if not activity_logs:
        return {
            "events": [],
            "summary": "No activity recorded yet.",
            "focus_lost_events": 0,
            "recovery_events": 0,
            "total_minutes": 0,
            "top_mission": "Unknown",
        }

    sessions = build_sessions(activity_logs)
    sessions = merge_small_sessions(sessions)

    if not sessions:
        return {
            "events": [],
            "summary": "No meaningful activity was tracked today.",
            "focus_lost_events": 0,
            "recovery_events": 0,
            "total_minutes": 0,
            "top_mission": "Unknown",
        }

    events = []
    focus_lost_events = 0
    recovery_events = 0
    previous_was_distraction = False

    for index, session in enumerate(sessions):
        activity_type = session.get("activity_type", "UNKNOWN")
        duration_seconds = session.get("duration", 0)
        duration_minutes = round(duration_seconds / 60, 2)

        is_distraction = activity_type in DISTRACTION_TYPES

        event_type = get_event_type(
            index=index,
            is_distraction=is_distraction,
            previous_was_distraction=previous_was_distraction
        )

        if event_type == "focus_lost":
            focus_lost_events += 1

        if event_type == "recovered":
            recovery_events += 1

        mission = map_activity_to_mission(activity_type)

        events.append({
            "time": f"Block {index + 1}",
            "duration_minutes": duration_minutes,
            "activity_type": activity_type,
            "mission": mission,
            "event_type": event_type,
            "is_distraction": is_distraction,
            "story": build_story_line(
                activity_type=activity_type,
                mission=mission,
                event_type=event_type,
                duration_minutes=duration_minutes
            )
        })

        previous_was_distraction = is_distraction

    total_minutes = round(
        sum(event["duration_minutes"] for event in events),
        2
    )

    top_mission = get_top_mission(events)

    return {
        "events": events,
        "summary": build_summary(
            total_minutes=total_minutes,
            top_mission=top_mission,
            focus_lost_events=focus_lost_events,
            recovery_events=recovery_events
        ),
        "focus_lost_events": focus_lost_events,
        "recovery_events": recovery_events,
        "total_minutes": total_minutes,
        "top_mission": top_mission,
    }


def merge_small_sessions(sessions, min_duration_seconds=MIN_SESSION_SECONDS):
    if not sessions:
        return []

    merged = []

    for session in sessions:
        activity_type = session.get("activity_type", "UNKNOWN")
        duration = session.get("duration", 0)

        if not merged:
            merged.append({
                "activity_type": activity_type,
                "duration": duration
            })
            continue

        previous = merged[-1]
        previous_type = previous.get("activity_type")

        if activity_type == previous_type:
            previous["duration"] += duration

        elif duration < min_duration_seconds:
            previous["duration"] += duration

        else:
            merged.append({
                "activity_type": activity_type,
                "duration": duration
            })

    return merged


def get_event_type(index, is_distraction, previous_was_distraction):
    if index == 0:
        return "start"

    if is_distraction:
        return "focus_lost"

    if previous_was_distraction and not is_distraction:
        return "recovered"

    return "focused"


def map_activity_to_mission(activity_type):
    mapping = {
        "CODING": "Build Drift",
        "BROWSING": "Research / Information Gathering",
        "COMMUNICATION": "Communication",
        "IDLE": "Break / Distraction",
        "OTHER": "Unclassified Activity",
        "SYSTEM": "System Activity",
    }

    return mapping.get(activity_type, "Unknown Mission")


def build_story_line(activity_type, mission, event_type, duration_minutes):
    if event_type == "start":
        return f"Started with {activity_type.lower()} for {duration_minutes} minutes."

    if event_type == "focus_lost":
        return f"Focus drifted into {activity_type.lower()} for {duration_minutes} minutes."

    if event_type == "recovered":
        return f"Recovered and returned to {activity_type.lower()} for {duration_minutes} minutes."

    return f"Continued with {activity_type.lower()} for {duration_minutes} minutes."


def get_top_mission(events):
    mission_time = {}

    for event in events:
        mission = event["mission"]
        mission_time[mission] = mission_time.get(mission, 0) + event["duration_minutes"]

    if not mission_time:
        return "Unknown"

    return max(mission_time, key=mission_time.get)


def build_summary(total_minutes, top_mission, focus_lost_events, recovery_events):
    return (
        f"You tracked {total_minutes} minutes across meaningful sessions. "
        f"Your dominant mission was '{top_mission}'. "
        f"Drift detected {focus_lost_events} focus-loss session(s) "
        f"and {recovery_events} recovery session(s)."
    )