from datetime import datetime, UTC

from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.goal_engine import build_goal_summary
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns
from backend.productivity_score_engine import build_productivity_score
from backend.timeline_engine import build_timeline


def build_daily_report(activity_logs):
    if not activity_logs:
        return {
            "date": datetime.now(UTC).date().isoformat(),
            "summary": "No activity recorded yet.",
            "recommendations": []
        }

    score = build_productivity_score(activity_logs)
    missions = build_mission_summary(activity_logs)
    goals = build_goal_summary(activity_logs)
    deep_work = build_deep_work_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)
    patterns = detect_behavior_patterns(activity_logs)
    timeline = build_timeline(activity_logs)

    top_mission = missions.get("top_mission")
    top_goal = goals.get("top_goal")

    recommendations = _build_recommendations(
        score,
        deep_work,
        switches,
        patterns
    )

    executive_summary = _build_executive_summary(
        score,
        top_mission,
        deep_work,
        switches,
        patterns
    )

    return {
        "date": datetime.now(UTC).date().isoformat(),
        "productivity_score": score["overall_score"],
        "grade": score["grade"],
        "top_mission": top_mission["mission"] if top_mission else None,
        "top_goal": top_goal["goal"] if top_goal else None,
        "deep_work_minutes": deep_work["total_deep_work_minutes"],
        "deep_work_sessions": deep_work["count"],
        "context_switches": switches["total_switches"],
        "distraction_switches": switches["distraction_switches"],
        "patterns_detected": patterns["patterns"],
        "executive_summary": executive_summary,
        "recommendations": recommendations,
        "timeline": timeline["timeline"],
    }


def _build_executive_summary(score, top_mission, deep_work, switches, patterns):
    mission_name = top_mission["mission"] if top_mission else "no clear mission"

    if score["overall_score"] >= 85:
        opening = "You had a strong productivity pattern today."
    elif score["overall_score"] >= 70:
        opening = "You had a decent productivity pattern today."
    elif score["overall_score"] >= 50:
        opening = "Your productivity was moderate today."
    else:
        opening = "Your work pattern was highly fragmented today."

    return (
        f"{opening} Your dominant mission was '{mission_name}'. "
        f"You completed {deep_work['total_deep_work_minutes']} minutes of deep work "
        f"with {switches['total_switches']} context switches. "
        f"Drift detected {len(patterns['patterns'])} behavioral pattern type(s)."
    )


def _build_recommendations(score, deep_work, switches, patterns):
    recommendations = []

    if deep_work["total_deep_work_minutes"] < 30:
        recommendations.append(
            "Protect at least one uninterrupted 30-minute block for deep work."
        )

    if switches["total_switches"] > 10:
        recommendations.append(
            "Reduce context switching by batching research, coding, and communication separately."
        )

    if switches["distraction_switches"] > 3:
        recommendations.append(
            "Avoid switching to low-value activities during productive missions."
        )

    for pattern in patterns["patterns"]:
        if pattern["type"] == "App Ping-Pong":
            recommendations.append(
                "You repeatedly switched between apps. Try keeping only the required tools open."
            )

        if pattern["type"] == "Mission Abandonment":
            recommendations.append(
                "You abandoned a productive mission. Add a reminder to return before taking a break."
            )

    if score["overall_score"] >= 85:
        recommendations.append(
            "Your workflow looked strong today. Repeat the same working pattern tomorrow."
        )

    if not recommendations:
        recommendations.append(
            "Keep collecting more activity data so Drift can generate stronger recommendations."
        )

    return recommendations