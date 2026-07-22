from datetime import UTC, datetime
from typing import Any

from backend.context_switch_engine import analyze_context_switches
from backend.deep_work_engine import build_deep_work_summary
from backend.goal_engine import build_goal_summary
from backend.mission_engine import build_mission_summary
from backend.pattern_engine import detect_behavior_patterns
from backend.productivity_score_engine import build_productivity_score
from backend.timeline_engine import build_timeline


def build_daily_report(
    activity_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    report_date = datetime.now(UTC).date().isoformat()

    if not activity_logs:
        return {
            "date": report_date,
            "productivity_score": 0,
            "grade": "N/A",
            "top_mission": None,
            "top_goal": None,
            "deep_work_minutes": 0,
            "deep_work_sessions": 0,
            "context_switches": 0,
            "distraction_switches": 0,
            "ignored_micro_switches": 0,
            "estimated_focus_loss_seconds": 0,
            "patterns_detected": [],
            "executive_summary": "No activity recorded yet.",
            "summary": "No activity recorded yet.",
            "recommendations": [],
            "timeline": [],
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
        score=score,
        deep_work=deep_work,
        switches=switches,
        patterns=patterns,
    )

    executive_summary = _build_executive_summary(
        score=score,
        top_mission=top_mission,
        deep_work=deep_work,
        switches=switches,
        patterns=patterns,
    )

    return {
        "date": report_date,
        "productivity_score": score.get(
            "overall_score",
            0,
        ),
        "grade": score.get(
            "grade",
            "N/A",
        ),
        "top_mission": (
            top_mission.get("mission")
            if isinstance(top_mission, dict)
            else None
        ),
        "top_goal": (
            top_goal.get("goal")
            if isinstance(top_goal, dict)
            else None
        ),
        "deep_work_minutes": deep_work.get(
            "total_deep_work_minutes",
            0,
        ),
        "deep_work_sessions": deep_work.get(
            "count",
            0,
        ),
        "context_switches": switches.get(
            "total_switches",
            0,
        ),
        "attention_changes": switches.get(
            "total_switches",
            0,
        ),
        "distraction_switches": switches.get(
            "distraction_switches",
            0,
        ),
        "ignored_micro_switches": switches.get(
            "ignored_micro_switches",
            0,
        ),
        "estimated_focus_loss_seconds": switches.get(
            "estimated_focus_loss_seconds",
            0,
        ),
        "patterns_detected": patterns.get(
            "patterns",
            [],
        ),
        "executive_summary": executive_summary,
        "summary": executive_summary,
        "recommendations": recommendations,
        "timeline": timeline.get(
            "timeline",
            [],
        ),
    }


def _build_executive_summary(
    score: dict[str, Any],
    top_mission: dict[str, Any] | None,
    deep_work: dict[str, Any],
    switches: dict[str, Any],
    patterns: dict[str, Any],
) -> str:
    overall_score = float(
        score.get("overall_score", 0)
        or 0
    )

    mission_name = (
        top_mission.get("mission")
        if isinstance(top_mission, dict)
        else None
    ) or "no clearly identified mission"

    deep_work_minutes = round(
        float(
            deep_work.get(
                "total_deep_work_minutes",
                0,
            )
            or 0
        ),
        1,
    )

    attention_changes = int(
        float(
            switches.get(
                "total_switches",
                0,
            )
            or 0
        )
    )

    pattern_count = len(
        patterns.get("patterns", [])
    )

    if overall_score >= 85:
        opening = (
            "You maintained a strong productivity pattern today."
        )
    elif overall_score >= 70:
        opening = (
            "You made solid progress with a generally stable work pattern."
        )
    elif overall_score >= 50:
        opening = (
            "You were productive in parts, although interruptions "
            "reduced your momentum."
        )
    else:
        opening = (
            "Your work pattern was highly fragmented today."
        )

    return (
        f"{opening} Your dominant mission was "
        f"'{mission_name}'. You completed "
        f"{deep_work_minutes:g} minutes of deep work "
        f"with {attention_changes} meaningful attention changes. "
        f"Drift detected {pattern_count} behavioural "
        f"pattern type{'s' if pattern_count != 1 else ''}."
    )


def _build_recommendations(
    score: dict[str, Any],
    deep_work: dict[str, Any],
    switches: dict[str, Any],
    patterns: dict[str, Any],
) -> list[str]:
    recommendations: list[str] = []

    deep_work_minutes = float(
        deep_work.get(
            "total_deep_work_minutes",
            0,
        )
        or 0
    )

    total_switches = int(
        float(
            switches.get(
                "total_switches",
                0,
            )
            or 0
        )
    )

    distraction_switches = int(
        float(
            switches.get(
                "distraction_switches",
                0,
            )
            or 0
        )
    )

    overall_score = float(
        score.get(
            "overall_score",
            0,
        )
        or 0
    )

    if deep_work_minutes < 30:
        recommendations.append(
            "Protect at least one uninterrupted 30-minute "
            "block for deep work."
        )

    if total_switches > 20:
        recommendations.append(
            "Reduce attention changes by batching research, "
            "coding, and communication separately."
        )

    if distraction_switches > 3:
        recommendations.append(
            "Avoid switching to low-value activities during "
            "productive missions."
        )

    for pattern in patterns.get("patterns", []):
        pattern_type = pattern.get("type")

        if pattern_type == "App Ping-Pong":
            recommendations.append(
                "You repeatedly moved between the same applications. "
                "Keep only the tools required for the current task open."
            )

        elif pattern_type == "Mission Abandonment":
            recommendations.append(
                "You left a productive mission before returning. "
                "Write down the exact next step before taking a break."
            )

    if overall_score >= 85:
        recommendations.append(
            "Your workflow looked strong today. Repeat the same "
            "working pattern tomorrow."
        )

    if not recommendations:
        recommendations.append(
            "Keep tracking activity so Drift can generate "
            "more specific recommendations."
        )

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(recommendations))