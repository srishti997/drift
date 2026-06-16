from backend.intent_engine import infer_intent


def analyze_context_switches(activity_logs):
    if len(activity_logs) < 2:
        return {
            "total_switches": 0,
            "goal_switches": 0,
            "distraction_switches": 0,
            "estimated_focus_loss_seconds": 0,
            "switches": [],
            "insight": "Not enough activity to analyze context switches."
        }

    switches = []
    goal_switches = 0
    distraction_switches = 0

    distraction_goals = {
        "No productive goal",
        "Information Gathering",
        "No active goal",
        "Needs Better Classification"
    }

    previous = activity_logs[0]
    previous_intent = infer_intent(
        previous.app_name,
        previous.window_title,
        previous.activity_type
    )

    for current in activity_logs[1:]:
        current_intent = infer_intent(
            current.app_name,
            current.window_title,
            current.activity_type
        )

        if previous_intent["goal"] != current_intent["goal"]:
            goal_switches += 1

            is_distraction = current_intent["goal"] in distraction_goals

            if is_distraction:
                distraction_switches += 1

            switches.append({
                "from_goal": previous_intent["goal"],
                "to_goal": current_intent["goal"],
                "from_intent": previous_intent["intent"],
                "to_intent": current_intent["intent"],
                "is_distraction": is_distraction
            })

        previous_intent = current_intent

    estimated_focus_loss_seconds = goal_switches * 120

    if distraction_switches == 0:
        insight = "Your context switches were mostly goal-aligned."
    elif distraction_switches <= 2:
        insight = "Minor distraction switching detected."
    else:
        insight = "High distraction switching detected. Your work pattern is fragmented."

    return {
        "total_switches": len(switches),
        "goal_switches": goal_switches,
        "distraction_switches": distraction_switches,
        "estimated_focus_loss_seconds": estimated_focus_loss_seconds,
        "switches": switches,
        "insight": insight
    }