from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from backend.context_builder import build_behavior_context
from backend.llm_client import generate_ai_response
from backend.prompt_builder import build_drift_prompt

DEFAULT_FALLBACK_ANSWER = (
    "I could not generate an AI response right now. "
    "Please make sure the backend has activity data and the LLM provider is available."
)

def _prepare_activity_logs(
    activity_logs: list[Any] | None,
) -> list[Any]:
    """
    Convert dictionary activity records into attribute-based objects.

    Existing Drift engines expect fields such as:
        log.app_name
        log.window_title
        log.activity_type
    """

    if not isinstance(activity_logs, list):
        return []

    prepared_logs = []

    for log in activity_logs:
        if isinstance(log, dict):
            prepared_logs.append(
                SimpleNamespace(
                    app_name=log.get("app_name", "Unknown"),
                    window_title=log.get("window_title", ""),
                    activity_type=log.get(
                        "activity_type",
                        "UNKNOWN",
                    ),
                    start_time=log.get("start_time"),
                    end_time=log.get("end_time"),
                    duration_seconds=log.get(
                        "duration_seconds",
                        0,
                    ),
                    key_count=log.get("key_count", 0),
                    mouse_count=log.get("mouse_count", 0),
                    mission=log.get(
                        "mission",
                        "Unclassified Mission",
                    ),
                    goal=log.get("goal", "Unknown"),
                    intent=log.get("intent", "Unknown"),
                )
            )
        else:
            prepared_logs.append(log)

    return prepared_logs
def answer_user_question(
    question: str,
    activity_logs: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """
    Answer a productivity question using Drift's recorded activity.

    The function:
    - validates the question,
    - builds a behavior context,
    - sends a grounded prompt to the configured LLM,
    - returns a safe fallback response if the LLM fails.
    """

    clean_question = _clean_question(question)

    if not clean_question:
        return {
            "answer": "Please ask a specific productivity question.",
            "provider": "drift",
            "success": False,
            "confidence": 0.0,
        }

    safe_logs = _prepare_activity_logs(activity_logs)

    try:
        context = build_behavior_context(safe_logs)
    except Exception as error:
        return {
            "answer": (
                "I could not analyse the activity data because the behavior "
                "context could not be built."
            ),
            "provider": "drift",
            "success": False,
            "confidence": 0.1,
            "error": str(error),
        }

    if not context:
        return {
            "answer": (
                "There is not enough tracked activity yet. "
                "Run Drift for a few minutes and ask again."
            ),
            "provider": "drift",
            "success": False,
            "confidence": 0.2,
        }

    try:
        prompt = build_drift_prompt(
            clean_question,
            context,
        )
    except Exception as error:
        return {
            "answer": (
                "I could not prepare the productivity question for analysis."
            ),
            "provider": "drift",
            "success": False,
            "confidence": 0.1,
            "error": str(error),
        }

    try:
        ai_response = generate_ai_response(prompt)
    except Exception as error:
        return {
            "answer": _build_rule_based_fallback(
                clean_question,
                context,
            ),
            "provider": "drift-fallback",
            "success": False,
            "confidence": 0.35,
            "error": str(error),
        }

    if not isinstance(ai_response, dict):
        return {
            "answer": _build_rule_based_fallback(
                clean_question,
                context,
            ),
            "provider": "drift-fallback",
            "success": False,
            "confidence": 0.35,
        }

    success = bool(ai_response.get("success", False))
    answer = str(
        ai_response.get("answer")
        or _build_rule_based_fallback(
            clean_question,
            context,
        )
        or DEFAULT_FALLBACK_ANSWER
    ).strip()

    provider = str(
        ai_response.get("provider")
        or "drift-fallback"
    )

    confidence = (
        0.9
        if success
        else 0.35
    )

    return {
        "answer": answer,
        "provider": provider,
        "success": success,
        "confidence": confidence,
    }


def _clean_question(question: Any) -> str:
    if question is None:
        return ""

    return " ".join(
        str(question).strip().split()
    )


def _build_rule_based_fallback(
    question: str,
    context: dict[str, Any],
) -> str:
    """
    Produce a grounded answer from available context when the LLM fails.

    This intentionally avoids inventing statistics.
    """

    lower_question = question.lower()

    summary = _get_dict(context, "summary")
    score = _get_dict(context, "score")
    deep_work = _get_dict(context, "deep_work")
    missions = _get_dict(context, "missions")
    patterns = _get_dict(context, "patterns")
    recovery = _get_dict(context, "recovery")
    history = _get_dict(context, "history")

    if any(
        keyword in lower_question
        for keyword in (
            "score",
            "productivity",
            "productive",
            "why was my day bad",
            "why was today bad",
        )
    ):
        overall_score = _first_value(
            score,
            "overall_score",
            "score",
            default=None,
        )
        grade = _first_value(
            score,
            "grade",
            default="N/A",
        )
        context_switches = _first_value(
            summary,
            "context_switches",
            default=None,
        )
        deep_minutes = _first_value(
            deep_work,
            "total_deep_work_minutes",
            "deep_work_minutes",
            default=None,
        )

        parts = []

        if overall_score is not None:
            parts.append(
                f"Your productivity score was {overall_score} with grade {grade}."
            )

        if deep_minutes is not None:
            parts.append(
                f"You completed {deep_minutes} minutes of deep work."
            )

        if context_switches is not None:
            parts.append(
                f"Drift recorded {context_switches} context switches."
            )

        if parts:
            return (
                " ".join(parts)
                + " The strongest improvement would be to protect one uninterrupted "
                "focus block and reduce unnecessary switching."
            )

    if any(
        keyword in lower_question
        for keyword in (
            "deep work",
            "focus block",
            "focused work",
        )
    ):
        deep_minutes = _first_value(
            deep_work,
            "total_deep_work_minutes",
            "deep_work_minutes",
            default=None,
        )
        count = _first_value(
            deep_work,
            "count",
            default=None,
        )

        if deep_minutes is not None:
            response = (
                f"You completed {deep_minutes} minutes of deep work."
            )

            if count is not None:
                response += f" Drift detected {count} deep-work session(s)."

            return response

    if any(
        keyword in lower_question
        for keyword in (
            "mission",
            "worked on",
            "main focus",
            "dominant",
        )
    ):
        top_mission = _first_value(
            summary,
            "top_mission",
            default=None,
        )

        if top_mission:
            return (
                f"Your dominant mission was {top_mission}. "
                "Open the Overview or History page to inspect its time distribution."
            )

        mission_items = missions.get("missions", [])

        if isinstance(mission_items, list) and mission_items:
            top_item = max(
                mission_items,
                key=lambda item: item.get(
                    "time_seconds",
                    0,
                ),
            )

            return (
                f"Your dominant mission was "
                f"{top_item.get('mission', 'Unknown')}."
            )

    if any(
        keyword in lower_question
        for keyword in (
            "distract",
            "context switch",
            "switching",
            "lose focus",
            "focus lost",
        )
    ):
        context_switches = _first_value(
            summary,
            "context_switches",
            default=None,
        )

        pattern_items = patterns.get("patterns", [])

        parts = []

        if context_switches is not None:
            parts.append(
                f"Drift recorded {context_switches} context switches."
            )

        if isinstance(pattern_items, list) and pattern_items:
            names = [
                str(item.get("type", "Pattern"))
                for item in pattern_items[:3]
            ]
            parts.append(
                "Detected patterns included "
                + ", ".join(names)
                + "."
            )

        if parts:
            return (
                " ".join(parts)
                + " Reduce app switching by grouping communication, browsing, "
                "and coding into separate blocks."
            )

    if any(
        keyword in lower_question
        for keyword in (
            "recover",
            "recovery",
            "return to focus",
        )
    ):
        count = _first_value(
            recovery,
            "count",
            default=None,
        )
        total_cost_seconds = _first_value(
            recovery,
            "total_recovery_cost_seconds",
            default=None,
        )

        parts = []

        if count is not None:
            parts.append(
                f"Drift detected {count} recovery event(s)."
            )

        if total_cost_seconds is not None:
            minutes = round(
                float(total_cost_seconds) / 60,
                1,
            )
            parts.append(
                f"The estimated total recovery cost was {minutes} minutes."
            )

        if parts:
            return " ".join(parts)

    if any(
        keyword in lower_question
        for keyword in (
            "history",
            "trend",
            "improving",
            "compare",
            "week",
        )
    ):
        history_summary = _get_dict(
            history,
            "summary",
        )

        average_score = _first_value(
            history_summary,
            "average_score",
            default=None,
        )
        tracked_days = _first_value(
            history_summary,
            "tracked_days",
            default=None,
        )
        current_streak = _first_value(
            history_summary,
            "current_streak",
            default=None,
        )

        parts = []

        if tracked_days is not None:
            parts.append(
                f"Historical analytics currently contain {tracked_days} tracked day(s)."
            )

        if average_score is not None:
            parts.append(
                f"The average historical score is {average_score}."
            )

        if current_streak is not None:
            parts.append(
                f"The current tracking streak is {current_streak} day(s)."
            )

        if parts:
            return " ".join(parts)

    recommendation_items = summary.get(
        "recommendations",
        [],
    )

    if isinstance(recommendation_items, list) and recommendation_items:
        return (
            "Based on the available productivity data, your next best action is: "
            + str(recommendation_items[0])
        )

    return (
        "I could not find enough specific data to answer that question. "
        "Try asking about your productivity score, deep work, dominant mission, "
        "context switches, recovery, or historical trend."
    )


def _get_dict(
    data: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    value = data.get(key, {})

    return value if isinstance(value, dict) else {}


def _first_value(
    data: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        value = data.get(key)

        if value is not None:
            return value

    return default