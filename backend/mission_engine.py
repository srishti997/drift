from backend.intent_engine import infer_intent


MISSION_RULES = {
    "Build Drift": [
        "Develop Drift platform",
        "Manage project code",
        "Research or build with AI support",
        "Build Drift backend",
        "Fix implementation issue",
        "Code Management",
        "Information Gathering",
    ],
    "Career Growth": [
        "Improve professional profile",
        "Prepare for technical interviews",
        "Job Preparation",
    ],
    "Skill Development": [
        "Skill development",
        "Improve AI/ML skills",
    ],
    "Communication": [
        "Message or collaboration",
    ],
    "Break / Distraction": [
        "No productive goal",
        "No active goal",
    ],
}


def map_goal_to_mission(goal: str) -> str:
    for mission, goals in MISSION_RULES.items():
        if goal in goals:
            return mission

    return "Unclassified Mission"


def build_mission_summary(activity_logs):
    if not activity_logs:
        return {
            "total_time": 0,
            "missions": [],
            "top_mission": None,
            "insight": "No activity recorded yet.",
        }

    mission_map = {}
    total_time = 0

    for log in activity_logs:
        intent_data = infer_intent(
            log.app_name,
            log.window_title,
            log.activity_type
        )

        goal = intent_data["goal"]
        intent = intent_data["intent"]
        mission = map_goal_to_mission(goal)

        duration = log.duration_seconds
        total_time += duration

        if mission not in mission_map:
            mission_map[mission] = {
                "mission": mission,
                "time_seconds": 0,
                "goals": {},
                "intents": {},
            }

        mission_map[mission]["time_seconds"] += duration

        if goal not in mission_map[mission]["goals"]:
            mission_map[mission]["goals"][goal] = 0

        mission_map[mission]["goals"][goal] += duration

        if intent not in mission_map[mission]["intents"]:
            mission_map[mission]["intents"][intent] = 0

        mission_map[mission]["intents"][intent] += duration

    missions = []

    for mission, data in mission_map.items():
        percentage = round((data["time_seconds"] / total_time) * 100, 2)

        missions.append({
            "mission": mission,
            "time_seconds": data["time_seconds"],
            "percentage": percentage,
            "goals": data["goals"],
            "intents": data["intents"],
        })

    missions.sort(key=lambda item: item["time_seconds"], reverse=True)

    top_mission = missions[0] if missions else None

    if top_mission:
        insight = (
            f"Your dominant mission was '{top_mission['mission']}', "
            f"using {top_mission['percentage']}% of tracked activity."
        )
    else:
        insight = "No dominant mission found."

    return {
        "total_time": total_time,
        "missions": missions,
        "top_mission": top_mission,
        "insight": insight,
    }


def infer_mission_for_log(log):
    intent_data = infer_intent(
        log.app_name,
        log.window_title,
        log.activity_type
    )

    mission = map_goal_to_mission(intent_data["goal"])

    return {
        "intent": intent_data["intent"],
        "goal": intent_data["goal"],
        "mission": mission,
        "confidence": intent_data["confidence"],
    }