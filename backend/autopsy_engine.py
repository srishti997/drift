from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns
from backend.productivity_score_engine import build_productivity_score


def build_mission_autopsy(activity_logs):
    if not activity_logs:
        return {
            "mission": None,
            "summary": "No activity recorded yet.",
            "failure_reason": None,
            "recommendation": "Run the tracker to collect activity data."
        }

    missions = build_mission_summary(activity_logs)
    deep_work = build_deep_work_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)
    patterns = detect_behavior_patterns(activity_logs)
    score = build_productivity_score(activity_logs)

    top_mission = missions.get("top_mission")

    if not top_mission:
        return {
            "mission": None,
            "summary": "No dominant mission found.",
            "failure_reason": "Insufficient mission data.",
            "recommendation": "Collect more activity data."
        }

    mission_name = top_mission["mission"]
    mission_time_seconds = top_mission["time_seconds"]
    mission_percentage = top_mission["percentage"]

    context_switches = switches.get("total_switches", 0)
    distraction_switches = switches.get("distraction_switches", 0)
    deep_work_minutes = deep_work.get("total_deep_work_minutes", 0)
    productivity_score = score.get("overall_score", 0)

    abandonment_count = 0
    recovery_count = 0
    ping_pong_count = 0

    for pattern in patterns.get("patterns", []):
        if pattern.get("type") == "Mission Abandonment":
            abandonment_count = pattern.get("count", 0)
        elif pattern.get("type") == "Mission Recovery":
            recovery_count = pattern.get("count", 0)
        elif pattern.get("type") == "App Ping-Pong":
            ping_pong_count = pattern.get("count", 0)

    recovery_cost_minutes = round((context_switches * 2) + (distraction_switches * 3), 2)

    success_probability = _calculate_success_probability(
        productivity_score,
        mission_percentage,
        deep_work_minutes,
        context_switches,
        abandonment_count
    )

    failure_reason = _infer_failure_reason(
        context_switches,
        distraction_switches,
        abandonment_count,
        ping_pong_count,
        deep_work_minutes
    )

    recommendation = _build_recommendation(failure_reason)

    return {
        "mission": mission_name,
        "mission_time_minutes": round(mission_time_seconds / 60, 2),
        "mission_alignment_percentage": mission_percentage,
        "productivity_score": productivity_score,
        "deep_work_minutes": deep_work_minutes,
        "context_switches": context_switches,
        "distraction_switches": distraction_switches,
        "mission_recoveries": recovery_count,
        "mission_abandonments": abandonment_count,
        "app_ping_pong_events": ping_pong_count,
        "estimated_recovery_cost_minutes": recovery_cost_minutes,
        "success_probability": success_probability,
        "failure_reason": failure_reason,
        "recommendation": recommendation,
        "summary": (
            f"Your dominant mission was '{mission_name}'. "
            f"You spent {round(mission_time_seconds / 60, 2)} minutes on it, "
            f"with {context_switches} context switches and "
            f"{deep_work_minutes} minutes of deep work."
        )
    }


def _calculate_success_probability(
    productivity_score,
    mission_percentage,
    deep_work_minutes,
    context_switches,
    abandonment_count
):
    probability = 0.5

    probability += (productivity_score / 100) * 0.25
    probability += (mission_percentage / 100) * 0.25

    if deep_work_minutes >= 60:
        probability += 0.20
    elif deep_work_minutes >= 30:
        probability += 0.10

    probability -= min(context_switches * 0.02, 0.25)
    probability -= min(abandonment_count * 0.10, 0.25)

    probability = max(0, min(probability, 1))

    return round(probability, 2)


def _infer_failure_reason(
    context_switches,
    distraction_switches,
    abandonment_count,
    ping_pong_count,
    deep_work_minutes
):
    if abandonment_count > 0:
        return "Mission abandonment"

    if distraction_switches >= 3:
        return "Distraction-heavy workflow"

    if context_switches >= 10:
        return "High context fragmentation"

    if ping_pong_count >= 3:
        return "App ping-pong behavior"

    if deep_work_minutes < 30:
        return "Insufficient deep work"

    return "No major failure signal detected"


def _build_recommendation(failure_reason):
    recommendations = {
        "Mission abandonment": "Before leaving a task, write the next action so you can return quickly.",
        "Distraction-heavy workflow": "Close distracting apps during productive missions and batch breaks separately.",
        "High context fragmentation": "Group research, coding, and communication into separate work blocks.",
        "App ping-pong behavior": "Reduce back-and-forth switching by keeping only mission-critical tools open.",
        "Insufficient deep work": "Protect at least one uninterrupted 30-minute focus block.",
        "No major failure signal detected": "Your mission execution looks stable. Continue the same work pattern."
    }

    return recommendations.get(
        failure_reason,
        "Collect more data so Drift can generate better recommendations."
    )