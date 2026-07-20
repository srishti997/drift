from __future__ import annotations

from typing import Any

import requests
import streamlit as st

from ui.components import metric_card, section_header


DEFAULT_API_URL = "http://127.0.0.1:8000"


def goals_page(api_url: str = DEFAULT_API_URL) -> None:
    section_header(
        title="Stay on track",
        description=(
            "Set simple daily targets and see which goals "
            "need your attention."
        ),
        eyebrow="Productivity goals",
    )

    targets = _get_targets(api_url)

    if targets is None:
        with st.container(border=True):
            st.error(
                "Could not load your goals. Make sure the "
                "FastAPI backend is running."
            )
        return

    progress_data = _get_goal_progress(api_url) or {}
    metrics = progress_data.get("metrics", {})

    if metrics:
        _render_summary(metrics)
        st.write("")

    _render_target_form(
        api_url=api_url,
        targets=targets,
    )

    st.write("")

    if not metrics:
        with st.container(border=True):
            st.markdown("### 🌱 No goal progress yet")
            st.write(
                "Keep the tracker running while you work. "
                "Drift will update this page automatically."
            )
        return

    _render_progress(metrics)


def _get_targets(
    api_url: str,
) -> dict[str, int] | None:
    try:
        response = requests.get(
            f"{api_url}/user-goals",
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, dict) else {}

    except (requests.RequestException, ValueError) as error:
        print(f"Unable to load targets: {error}")
        return None


def _get_goal_progress(
    api_url: str,
) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"{api_url}/goal-progress",
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, dict) else {}

    except (requests.RequestException, ValueError) as error:
        print(f"Unable to load goal progress: {error}")
        return None


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _format_value(
    value: Any,
    unit: str,
) -> str:
    number = _safe_float(value)

    if number.is_integer():
        display = str(int(number))
    else:
        display = f"{number:.1f}"

    return f"{display} {unit}".strip()


def _render_summary(
    metrics: dict[str, dict[str, Any]],
) -> None:
    section_header(
        title="Today's progress",
        description=(
            "A quick view of whether your daily targets are on track."
        ),
        eyebrow="Goal summary",
    )

    summary_items = [
        (
            "🔥",
            "Deep work",
            metrics.get("deep_work", {}),
        ),
        (
            "🔄",
            "Attention changes",
            metrics.get("context_switches", {}),
        ),
        (
            "🌙",
            "Idle time",
            metrics.get("idle_time", {}),
        ),
        (
            "▶️",
            "YouTube time",
            metrics.get("youtube_time", {}),
        ),
    ]

    columns = st.columns(
        4,
        gap="medium",
    )

    for column, (
        icon,
        title,
        metric,
    ) in zip(columns, summary_items):
        current = metric.get("current", 0)
        target = metric.get("target", 0)
        unit = str(metric.get("unit", ""))
        status = str(metric.get("status", "Unknown"))

        if status.lower() in {
            "completed",
            "on track",
            "within limit",
            "achieved",
        }:
            trend = "On track"
            trend_type = "positive"

        elif status.lower() in {
            "exceeded",
            "behind",
            "at risk",
        }:
            trend = "Needs attention"
            trend_type = "negative"

        else:
            trend = status
            trend_type = "neutral"

        with column:
            metric_card(
                icon=icon,
                title=title,
                value=_format_value(
                    current,
                    unit,
                ),
                subtitle=(
                    f"Target: "
                    f"{_format_value(target, unit)}"
                ),
                trend=trend,
                trend_type=trend_type,
                badge="Today",
            )


def _render_target_form(
    api_url: str,
    targets: dict[str, int],
) -> None:
    section_header(
        title="Set your daily targets",
        description=(
            "Adjust these goals to match the way you want to work."
        ),
        eyebrow="Goal settings",
    )

    with st.container(border=True):
        with st.form(
            "productivity_targets_form"
        ):
            left_column, right_column = st.columns(
                2,
                gap="large",
            )

            with left_column:
                deep_work_minutes = st.number_input(
                    "Deep-work target",
                    min_value=0,
                    max_value=1440,
                    value=_safe_int(
                        targets.get(
                            "deep_work_minutes",
                            180,
                        ),
                        180,
                    ),
                    step=15,
                    help=(
                        "The minimum number of deep-work "
                        "minutes you want each day."
                    ),
                )

                max_idle_minutes = st.number_input(
                    "Maximum idle time",
                    min_value=0,
                    max_value=1440,
                    value=_safe_int(
                        targets.get(
                            "max_idle_minutes",
                            30,
                        ),
                        30,
                    ),
                    step=5,
                    help=(
                        "The maximum idle time you want "
                        "during your workday."
                    ),
                )

            with right_column:
                max_context_switches = st.number_input(
                    "Maximum attention changes",
                    min_value=0,
                    max_value=1000,
                    value=_safe_int(
                        targets.get(
                            "max_context_switches",
                            20,
                        ),
                        20,
                    ),
                    step=1,
                    help=(
                        "The maximum number of meaningful "
                        "context changes you want to allow."
                    ),
                )

                max_youtube_minutes = st.number_input(
                    "Maximum YouTube time",
                    min_value=0,
                    max_value=1440,
                    value=_safe_int(
                        targets.get(
                            "max_youtube_minutes",
                            45,
                        ),
                        45,
                    ),
                    step=5,
                    help=(
                        "The maximum number of minutes you "
                        "want to spend on YouTube."
                    ),
                )

            submitted = st.form_submit_button(
                "Save targets",
                use_container_width=True,
            )

    if submitted:
        payload = {
            "deep_work_minutes": int(
                deep_work_minutes
            ),
            "max_context_switches": int(
                max_context_switches
            ),
            "max_idle_minutes": int(
                max_idle_minutes
            ),
            "max_youtube_minutes": int(
                max_youtube_minutes
            ),
        }

        _save_targets(
            api_url=api_url,
            payload=payload,
        )


def _save_targets(
    api_url: str,
    payload: dict[str, int],
) -> None:
    try:
        response = requests.post(
            f"{api_url}/user-goals",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()

        st.success(
            "Productivity targets updated."
        )
        st.rerun()

    except requests.RequestException as error:
        st.error(
            "Unable to save productivity targets."
        )
        print(f"Unable to save targets: {error}")


def _render_progress(
    metrics: dict[str, dict[str, Any]],
) -> None:
    section_header(
        title="Goal details",
        description=(
            "See how close you are to each target."
        ),
        eyebrow="Progress",
    )

    metric_items = list(metrics.items())

    first_column, second_column = st.columns(
        2,
        gap="medium",
    )

    for index, (
        metric_name,
        metric,
    ) in enumerate(metric_items):
        column = (
            first_column
            if index % 2 == 0
            else second_column
        )

        with column:
            _render_goal_card(
                metric_name=metric_name,
                metric=metric,
            )

    suggestions = _build_suggestions(
        metrics
    )

    section_header(
        title="What to do next",
        description=(
            "Small actions based on your current progress."
        ),
        eyebrow="Suggestions",
    )

    with st.container(border=True):
        for index, suggestion in enumerate(
            suggestions,
            start=1,
        ):
            st.markdown(
                f"### {index}. {suggestion}"
            )

            if index < len(suggestions):
                st.divider()


def _render_goal_card(
    metric_name: str,
    metric: dict[str, Any],
) -> None:
    readable_name = (
        metric_name
        .replace("_", " ")
        .title()
    )

    icons = {
        "deep_work": "🔥",
        "context_switches": "🔄",
        "idle_time": "🌙",
        "youtube_time": "▶️",
    }

    current = metric.get("current", 0)
    target = metric.get("target", 0)
    unit = str(metric.get("unit", ""))
    status = str(metric.get("status", "Unknown"))

    safe_progress = max(
        0,
        min(
            100,
            _safe_int(
                metric.get("progress")
            ),
        ),
    )

    with st.container(border=True):
        st.markdown(
            f"### {icons.get(metric_name, '🎯')} "
            f"{readable_name}"
        )

        value_col, status_col = st.columns(
            [2, 1]
        )

        with value_col:
            st.metric(
                label="Current",
                value=_format_value(
                    current,
                    unit,
                ),
            )

        with status_col:
            st.metric(
                label="Target",
                value=_format_value(
                    target,
                    unit,
                ),
            )

        st.progress(
            safe_progress / 100
        )

        st.caption(
            f"{safe_progress}% complete"
        )

        status_lower = status.lower()

        if status_lower in {
            "completed",
            "on track",
            "within limit",
            "achieved",
        }:
            st.success(status)

        elif status_lower in {
            "exceeded",
            "behind",
            "at risk",
        }:
            st.warning(status)

        else:
            st.info(status)


def _build_suggestions(
    metrics: dict[str, dict[str, Any]],
) -> list[str]:
    suggestions: list[str] = []

    deep_work = metrics.get(
        "deep_work",
        {},
    )

    deep_current = _safe_float(
        deep_work.get("current")
    )

    deep_target = _safe_float(
        deep_work.get("target")
    )

    if deep_current < deep_target:
        remaining = round(
            deep_target - deep_current,
            1,
        )

        suggestions.append(
            f"Complete {remaining:g} more minutes "
            "of deep work."
        )
    else:
        suggestions.append(
            "Your deep-work target has been completed."
        )

    context_switches = metrics.get(
        "context_switches",
        {},
    )

    if (
        str(
            context_switches.get(
                "status",
                "",
            )
        ).lower()
        == "exceeded"
    ):
        suggestions.append(
            "Reduce attention changes by grouping "
            "similar tasks together."
        )
    else:
        suggestions.append(
            "Your attention changes are currently "
            "within the daily limit."
        )

    idle_time = metrics.get(
        "idle_time",
        {},
    )

    if (
        str(
            idle_time.get(
                "status",
                "",
            )
        ).lower()
        == "exceeded"
    ):
        suggestions.append(
            "Idle time is above your target. "
            "Use shorter, deliberate breaks."
        )

    youtube_time = metrics.get(
        "youtube_time",
        {},
    )

    if (
        str(
            youtube_time.get(
                "status",
                "",
            )
        ).lower()
        == "exceeded"
    ):
        suggestions.append(
            "YouTube usage has exceeded your "
            "daily limit."
        )

    if not suggestions:
        suggestions.append(
            "Keep tracking activity to receive "
            "goal suggestions."
        )

    return suggestions