from datetime import datetime
from typing import Any

from backend.intent_engine import infer_intent


# A different context must remain active for this long
# before Drift treats it as a meaningful switch.
MIN_SWITCH_SECONDS = 120

# Your tracker currently records activity roughly every 10 seconds.
DEFAULT_SAMPLE_SECONDS = 10


PRODUCTIVE_GOALS = {
    "Coding",
    "Development",
    "Debugging",
    "Research",
    "Documentation",
    "Studying",
    "Learning",
    "Writing",
    "Planning",
    "Project Work",
}

COMMUNICATION_GOALS = {
    "Communication",
    "Meeting",
    "Email",
    "Messaging",
    "Collaboration",
}

DISTRACTION_GOALS = {
    "No productive goal",
    "No active goal",
    "Needs Better Classification",
    "Entertainment",
    "Social Media",
    "Browsing",
}

IDLE_GOALS = {
    "Idle",
    "System Idle",
    "Away",
}


def _get_value(item: Any, *names: str, default=None):
    """Read a value from either an object or dictionary."""

    for name in names:
        if isinstance(item, dict) and name in item:
            return item.get(name)

        if hasattr(item, name):
            return getattr(item, name)

    return default


def _parse_timestamp(item: Any):
    """Return a datetime when the activity contains a usable timestamp."""

    raw_timestamp = _get_value(
        item,
        "timestamp",
        "created_at",
        "date_created",
        "date_updated",
        "time",
    )

    if not raw_timestamp:
        return None

    if isinstance(raw_timestamp, datetime):
        return raw_timestamp

    try:
        return datetime.fromisoformat(
            str(raw_timestamp).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def _goal_group(goal: str) -> str:
    """
    Convert detailed inferred goals into human-level contexts.

    Moving between Coding, Research and Documentation is treated as
    remaining inside the same productive context.
    """

    clean_goal = str(goal or "").strip()

    if clean_goal in PRODUCTIVE_GOALS:
        return "PRODUCTIVE"

    if clean_goal in COMMUNICATION_GOALS:
        return "COMMUNICATION"

    if clean_goal in DISTRACTION_GOALS:
        return "DISTRACTION"

    if clean_goal in IDLE_GOALS:
        return "IDLE"

    lowered = clean_goal.lower()

    if any(
        keyword in lowered
        for keyword in (
            "code",
            "develop",
            "debug",
            "research",
            "document",
            "study",
            "learn",
            "write",
            "project",
        )
    ):
        return "PRODUCTIVE"

    if any(
        keyword in lowered
        for keyword in (
            "chat",
            "message",
            "meeting",
            "email",
            "communicat",
            "slack",
            "teams",
        )
    ):
        return "COMMUNICATION"

    if any(
        keyword in lowered
        for keyword in (
            "social",
            "entertain",
            "youtube",
            "instagram",
            "facebook",
            "netflix",
            "no productive",
            "unclassified",
        )
    ):
        return "DISTRACTION"

    if any(
        keyword in lowered
        for keyword in (
            "idle",
            "away",
            "inactive",
        )
    ):
        return "IDLE"

    return "OTHER"


def _elapsed_seconds(
    start_item: Any,
    current_item: Any,
    sample_count: int,
) -> int:
    """
    Calculate elapsed time using timestamps when possible.

    Falls back to the tracker's approximate sampling interval.
    """

    start_time = _parse_timestamp(start_item)
    current_time = _parse_timestamp(current_item)

    if start_time and current_time:
        try:
            elapsed = int(
                (current_time - start_time).total_seconds()
            )

            if elapsed >= 0:
                return elapsed
        except (TypeError, ValueError):
            pass

    return sample_count * DEFAULT_SAMPLE_SECONDS


def _infer(activity: Any) -> dict:
    app_name = _get_value(
        activity,
        "app_name",
        default="",
    )

    window_title = _get_value(
        activity,
        "window_title",
        default="",
    )

    activity_type = _get_value(
        activity,
        "activity_type",
        default="",
    )

    result = infer_intent(
        app_name,
        window_title,
        activity_type,
    )

    return {
        "goal": result.get("goal", "Needs Better Classification"),
        "intent": result.get("intent", "Unknown"),
        "group": _goal_group(result.get("goal")),
        "app_name": app_name,
        "window_title": window_title,
    }


def analyze_context_switches(activity_logs):
    """
    Count only meaningful changes in attention.

    A temporary change is ignored when the user returns to the original
    context before MIN_SWITCH_SECONDS.

    Examples:
        Coding -> Documentation -> Coding
        is treated as one productive context.

        Coding -> YouTube for 20 seconds -> Coding
        is ignored as a micro-switch.

        Coding -> YouTube for more than 2 minutes
        is counted as a meaningful distraction.
    """

    if len(activity_logs) < 2:
        return {
            "total_switches": 0,
            "goal_switches": 0,
            "distraction_switches": 0,
            "ignored_micro_switches": 0,
            "estimated_focus_loss_seconds": 0,
            "switches": [],
            "insight": "Not enough activity to analyse attention changes.",
        }

    switches = []
    ignored_micro_switches = 0
    distraction_switches = 0

    stable_activity = activity_logs[0]
    stable_context = _infer(stable_activity)

    pending_activity = None
    pending_context = None
    pending_samples = 0

    for current_activity in activity_logs[1:]:
        current_context = _infer(current_activity)

        # The user is still working inside the same broad context.
        if current_context["group"] == stable_context["group"]:
            if pending_context is not None:
                ignored_micro_switches += 1

            pending_activity = None
            pending_context = None
            pending_samples = 0
            continue

        # Start observing a possible context change.
        if (
            pending_context is None
            or current_context["group"] != pending_context["group"]
        ):
            if pending_context is not None:
                ignored_micro_switches += 1

            pending_activity = current_activity
            pending_context = current_context
            pending_samples = 1
            continue

        pending_samples += 1

        elapsed_seconds = _elapsed_seconds(
            pending_activity,
            current_activity,
            pending_samples,
        )

        # Do not count brief tab, title or application changes.
        if elapsed_seconds < MIN_SWITCH_SECONDS:
            continue

        is_distraction = (
            stable_context["group"] == "PRODUCTIVE"
            and pending_context["group"] in {
                "DISTRACTION",
                "IDLE",
            }
        )

        if is_distraction:
            distraction_switches += 1

        switches.append(
            {
                "from_goal": stable_context["goal"],
                "to_goal": pending_context["goal"],
                "from_intent": stable_context["intent"],
                "to_intent": pending_context["intent"],
                "from_group": stable_context["group"],
                "to_group": pending_context["group"],
                "from_app": stable_context["app_name"],
                "to_app": pending_context["app_name"],
                "is_distraction": is_distraction,
                "minimum_duration_seconds": elapsed_seconds,
            }
        )

        # The new context has persisted long enough to become stable.
        stable_activity = pending_activity
        stable_context = pending_context

        pending_activity = None
        pending_context = None
        pending_samples = 0

    # A switch that never reached the time threshold is a micro-switch.
    if pending_context is not None:
        ignored_micro_switches += 1

    meaningful_switches = len(switches)

    # Focus-loss estimation is now based mainly on genuine distractions,
    # rather than every normal productive transition.
    estimated_focus_loss_seconds = (
        distraction_switches * MIN_SWITCH_SECONDS
    )

    if meaningful_switches == 0:
        insight = (
            "Your attention remained steady. Brief changes were ignored."
        )
    elif distraction_switches == 0:
        insight = (
            "You changed contexts a few times, but the changes were "
            "mostly related to your work."
        )
    elif distraction_switches <= 2:
        insight = (
            "A small number of meaningful distractions interrupted "
            "your focus."
        )
    elif distraction_switches <= 5:
        insight = (
            "Several distractions interrupted your work. Protecting "
            "your next focus block may help."
        )
    else:
        insight = (
            "Your attention was fragmented by repeated, sustained "
            "distractions."
        )

    return {
        "total_switches": meaningful_switches,
        "goal_switches": meaningful_switches,
        "distraction_switches": distraction_switches,
        "ignored_micro_switches": ignored_micro_switches,
        "estimated_focus_loss_seconds": estimated_focus_loss_seconds,
        "switch_threshold_seconds": MIN_SWITCH_SECONDS,
        "switches": switches,
        "insight": insight,
    }