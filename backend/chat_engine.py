from backend.daily_report_engine import build_daily_report
from backend.productivity_score_engine import build_productivity_score
from backend.recovery_engine import build_recovery_summary
from backend.mission_engine import build_mission_summary
from backend.deep_work_engine import build_deep_work_summary
from backend.context_switch_engine import analyze_context_switches


def answer_user_question(question: str, activity_logs):
    q = question.lower()

    score = build_productivity_score(activity_logs)
    report = build_daily_report(activity_logs)
    recovery = build_recovery_summary(activity_logs)
    missions = build_mission_summary(activity_logs)
    deep_work = build_deep_work_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)

    if not activity_logs:
        return {
            "answer": "I do not have enough activity data yet. Run the tracker for some time and ask again.",
            "confidence": 0.3
        }

    if "productive" in q or "score" in q:
        return {
            "answer": (
                f"Your productivity score is {score.get('overall_score')} "
                f"with grade {score.get('grade')}. "
                f"{score.get('summary')}"
            ),
            "confidence": 0.9
        }

    if "distracted" in q or "distraction" in q:
        return {
            "answer": (
                f"You had {switches.get('distraction_switches')} distraction switches today. "
                f"Your estimated recovery cost is {recovery.get('total_recovery_cost_minutes')} minutes. "
                f"{recovery.get('insight')}"
            ),
            "confidence": 0.85
        }

    if "deep work" in q or "focus" in q:
        return {
            "answer": (
                f"You completed {deep_work.get('count')} deep work session(s), "
                f"with {deep_work.get('total_deep_work_minutes')} total deep work minutes. "
                f"{deep_work.get('insight')}"
            ),
            "confidence": 0.85
        }

    if "mission" in q or "goal" in q:
        top = missions.get("top_mission")
        if top:
            return {
                "answer": (
                    f"Your dominant mission was {top.get('mission')}, "
                    f"which took {top.get('percentage')}% of your tracked activity."
                ),
                "confidence": 0.85
            }

    if "summary" in q or "today" in q:
        return {
            "answer": report.get("executive_summary", "No daily summary available yet."),
            "confidence": 0.8
        }

    return {
        "answer": (
            "I can answer questions about productivity score, distractions, deep work, "
            "missions, goals, and your daily summary. Try asking: "
            "'Why was I distracted today?' or 'How productive was I?'"
        ),
        "confidence": 0.5
    }