from backend.mission_engine import infer_mission_for_log


def build_timeline(activity_logs):
    if not activity_logs:
        return {
            "timeline": [],
            "insight": "No activity recorded yet."
        }

    timeline = []

    first = activity_logs[0]
    first_data = infer_mission_for_log(first)

    current_block = {
        "mission": first_data["mission"],
        "duration_seconds": first.duration_seconds,
        "goals": {first_data["goal"]: first.duration_seconds},
        "intents": {first_data["intent"]: first.duration_seconds},
        "apps": {first.app_name: first.duration_seconds},
    }

    for log in activity_logs[1:]:
        data = infer_mission_for_log(log)
        mission = data["mission"]

        if mission == current_block["mission"]:
            current_block["duration_seconds"] += log.duration_seconds

            current_block["goals"][data["goal"]] = (
                current_block["goals"].get(data["goal"], 0) + log.duration_seconds
            )

            current_block["intents"][data["intent"]] = (
                current_block["intents"].get(data["intent"], 0) + log.duration_seconds
            )

            current_block["apps"][log.app_name] = (
                current_block["apps"].get(log.app_name, 0) + log.duration_seconds
            )

        else:
            timeline.append(current_block)

            current_block = {
                "mission": mission,
                "duration_seconds": log.duration_seconds,
                "goals": {data["goal"]: log.duration_seconds},
                "intents": {data["intent"]: log.duration_seconds},
                "apps": {log.app_name: log.duration_seconds},
            }

    timeline.append(current_block)

    insight = f"Your day was divided into {len(timeline)} mission blocks."

    return {
        "timeline": timeline,
        "insight": insight
    }