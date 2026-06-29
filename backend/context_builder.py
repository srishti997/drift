from backend.productivity_score_engine import build_productivity_score
from backend.daily_report_engine import build_daily_report
from backend.mission_engine import build_mission_summary
from backend.deep_work_engine import build_deep_work_summary
from backend.context_switch_engine import analyze_context_switches
from backend.recovery_engine import build_recovery_summary
from backend.autopsy_engine import build_mission_autopsy
from backend.coach_engine import build_coach_advice


def build_behavior_context(activity_logs):
    if not activity_logs:
        return {
            "has_data": False,
            "message": "No activity data available."
        }

    score = build_productivity_score(activity_logs)
    report = build_daily_report(activity_logs)
    missions = build_mission_summary(activity_logs)
    deep_work = build_deep_work_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)
    recovery = build_recovery_summary(activity_logs)
    autopsy = build_mission_autopsy(activity_logs)
    coach = build_coach_advice(activity_logs)

    top_mission = missions.get("top_mission")

    return {
        "has_data": True,
        "productivity": {
            "score": score.get("overall_score"),
            "grade": score.get("grade"),
            "summary": score.get("summary"),
            "focus_score": score.get("focus_score"),
            "mission_score": score.get("mission_score"),
            "recovery_score": score.get("recovery_score"),
            "switch_score": score.get("switch_score"),
        },
        "mission": {
            "top_mission": top_mission.get("mission") if top_mission else None,
            "top_mission_percentage": top_mission.get("percentage") if top_mission else None,
            "summary": missions.get("insight"),
        },
        "deep_work": {
            "minutes": deep_work.get("total_deep_work_minutes"),
            "sessions": deep_work.get("count"),
            "longest_session_minutes": deep_work.get("longest_session_minutes"),
            "insight": deep_work.get("insight"),
        },
        "context_switching": {
            "total_switches": switches.get("total_switches"),
            "distraction_switches": switches.get("distraction_switches"),
            "insight": switches.get("insight"),
        },
        "recovery": {
            "total_recovery_cost_minutes": recovery.get("total_recovery_cost_minutes"),
            "recovery_rate": recovery.get("recovery_rate"),
            "insight": recovery.get("insight"),
        },
        "autopsy": {
            "mission": autopsy.get("mission"),
            "success_probability": autopsy.get("success_probability"),
            "failure_reason": autopsy.get("failure_reason"),
            "recommendation": autopsy.get("recommendation"),
            "summary": autopsy.get("summary"),
        },
        "daily_report": {
            "summary": report.get("executive_summary"),
            "recommendations": report.get("recommendations"),
        },
        "coach": coach.get("advice", []),
    }