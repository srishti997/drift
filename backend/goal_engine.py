from backend.intent_engine import infer_intent


def build_goal_summary(activity_logs):
    if not activity_logs:
        return {
            "total_time": 0,
            "goals": [],
            "top_goal": None,
            "insight": "No activity recorded yet."
        }

    goal_map = {}
    total_time = 0

    for log in activity_logs:
        intent_data = infer_intent(
            log.app_name,
            log.window_title,
            log.activity_type
        )

        goal = intent_data["goal"]
        duration = log.duration_seconds
        total_time += duration

        if goal not in goal_map:
            goal_map[goal] = {
                "goal": goal,
                "time_seconds": 0,
                "intents": {}
            }

        goal_map[goal]["time_seconds"] += duration

        intent = intent_data["intent"]

        if intent not in goal_map[goal]["intents"]:
            goal_map[goal]["intents"][intent] = 0

        goal_map[goal]["intents"][intent] += duration

    goals = []

    for goal, data in goal_map.items():
        percentage = round((data["time_seconds"] / total_time) * 100, 2)

        goals.append({
            "goal": goal,
            "time_seconds": data["time_seconds"],
            "percentage": percentage,
            "intents": data["intents"]
        })

    goals.sort(key=lambda item: item["time_seconds"], reverse=True)

    top_goal = goals[0] if goals else None

    if top_goal:
        insight = f"Most of your time went into '{top_goal['goal']}' with {top_goal['percentage']}% of tracked activity."
    else:
        insight = "No dominant goal found."

    return {
        "total_time": total_time,
        "goals": goals,
        "top_goal": top_goal,
        "insight": insight
    }