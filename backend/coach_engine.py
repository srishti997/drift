from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns
from backend.productivity_score_engine import build_productivity_score


def build_coach_advice(activity_logs):
    if not activity_logs:
        return {
            "observation": "No activity recorded yet.",
            "impact": "Drift needs activity data before generating advice.",
            "suggestion": "Run the tracker for at least 10-15 minutes."
        }

    score = build_productivity_score(activity_logs)
    missions = build_mission_summary(activity_logs)
    deep_work = build_deep_work_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)
    patterns = detect_behavior_patterns(activity_logs)

    advice = []

    if score["overall_score"] < 50:
        advice.append({
            "observation": "Your overall productivity score is low.",
            "impact": "Your work pattern may be fragmented or distraction-heavy.",
            "suggestion": "Start with one focused 30-minute mission block and avoid switching apps."
        })

    if deep_work["total_deep_work_minutes"] < 30:
        advice.append({
            "observation": "You did not complete a meaningful deep work block.",
            "impact": "Without deep work, progress on difficult tasks may remain shallow.",
            "suggestion": "Protect one uninterrupted 30-minute coding or learning block."
        })

    if switches["total_switches"] > 10:
        advice.append({
            "observation": "You switched context frequently.",
            "impact": "Frequent switching increases recovery time and reduces flow.",
            "suggestion": "Batch research, communication, and coding into separate blocks."
        })

    if switches["distraction_switches"] > 3:
        advice.append({
            "observation": "You had multiple distraction switches.",
            "impact": "Distractions can break mission continuity and reduce output quality.",
            "suggestion": "Close WhatsApp, YouTube, and unrelated tabs during productive sessions."
        })

    for pattern in patterns["patterns"]:
        if pattern["type"] == "Mission Abandonment":
            advice.append({
                "observation": "You abandoned a productive mission.",
                "impact": "This suggests your work was interrupted before reaching completion.",
                "suggestion": "Before switching away, write down the next action so you can resume quickly."
            })

        if pattern["type"] == "App Ping-Pong":
            advice.append({
                "observation": "You repeatedly switched between apps.",
                "impact": "This may indicate uncertainty, debugging friction, or scattered attention.",
                "suggestion": "Keep only the tools needed for the current mission open."
            })

        if pattern["type"] == "Mission Recovery":
            advice.append({
                "observation": "You recovered after switching away from your mission.",
                "impact": "This is a positive sign of focus resilience.",
                "suggestion": "Repeat this pattern by returning quickly after small interruptions."
            })

    top_mission = missions.get("top_mission")

    if top_mission and top_mission["percentage"] >= 75:
        advice.append({
            "observation": f"Your dominant mission was '{top_mission['mission']}'.",
            "impact": "Most of your tracked activity aligned with one major objective.",
            "suggestion": "Continue grouping related tasks under a single mission to preserve momentum."
        })

    if not advice:
        advice.append({
            "observation": "Your current work pattern looks stable.",
            "impact": "No major productivity risk was detected.",
            "suggestion": "Keep collecting data so Drift can build stronger personalized recommendations."
        })

    return {
        "productivity_score": score["overall_score"],
        "grade": score["grade"],
        "advice": advice
    }