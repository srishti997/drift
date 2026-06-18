from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns


def build_productivity_score(activity_logs):
    if not activity_logs:
        return {
            "overall_score": 0,
            "grade": "N/A",
            "focus_score": 0,
            "mission_score": 0,
            "recovery_score": 0,
            "switch_score": 0,
            "summary": "No activity recorded yet."
        }

    deep_work = build_deep_work_summary(activity_logs)
    missions = build_mission_summary(activity_logs)
    switches = analyze_context_switches(activity_logs)
    patterns = detect_behavior_patterns(activity_logs)

    focus_score = _calculate_focus_score(deep_work)
    mission_score = _calculate_mission_score(missions)
    recovery_score = _calculate_recovery_score(patterns)
    switch_score = _calculate_switch_score(switches)

    overall_score = round(
        (0.40 * focus_score)
        + (0.25 * mission_score)
        + (0.20 * recovery_score)
        + (0.15 * switch_score),
        2
    )

    grade = _get_grade(overall_score)
    summary = _build_summary(overall_score, focus_score, mission_score, recovery_score, switch_score)

    return {
        "overall_score": overall_score,
        "grade": grade,
        "focus_score": focus_score,
        "mission_score": mission_score,
        "recovery_score": recovery_score,
        "switch_score": switch_score,
        "summary": summary,
        "signals": {
            "deep_work": deep_work,
            "missions": missions,
            "context_switches": switches,
            "patterns": patterns
        }
    }


def _calculate_focus_score(deep_work):
    minutes = deep_work.get("total_deep_work_minutes", 0)

    if minutes >= 120:
        return 100
    if minutes >= 90:
        return 90
    if minutes >= 60:
        return 80
    if minutes >= 30:
        return 60
    if minutes >= 10:
        return 40

    return 20


def _calculate_mission_score(missions):
    top_mission = missions.get("top_mission")

    if not top_mission:
        return 0

    percentage = top_mission.get("percentage", 0)

    if percentage >= 90:
        return 100
    if percentage >= 75:
        return 85
    if percentage >= 60:
        return 70
    if percentage >= 40:
        return 50

    return 30


def _calculate_recovery_score(patterns):
    pattern_list = patterns.get("patterns", [])

    recovery_count = 0
    abandonment_count = 0

    for pattern in pattern_list:
        if pattern.get("type") == "Mission Recovery":
            recovery_count = pattern.get("count", 0)

        if pattern.get("type") == "Mission Abandonment":
            abandonment_count = pattern.get("count", 0)

    total = recovery_count + abandonment_count

    if total == 0:
        return 70

    return round((recovery_count / total) * 100, 2)


def _calculate_switch_score(switches):
    total_switches = switches.get("total_switches", 0)

    if total_switches == 0:
        return 100
    if total_switches <= 5:
        return 85
    if total_switches <= 10:
        return 70
    if total_switches <= 20:
        return 50

    return 25


def _get_grade(score):
    if score >= 95:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"

    return "F"


def _build_summary(overall, focus, mission, recovery, switch):
    if overall >= 85:
        return "Strong productivity pattern with good mission alignment and focus."
    if overall >= 70:
        return "Good productivity with some room to reduce context switching."
    if overall >= 50:
        return "Moderate productivity. Focus and mission continuity need improvement."

    return "Low productivity pattern detected. Distractions and weak focus are affecting output."