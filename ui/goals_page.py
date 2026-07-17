from __future__ import annotations

from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"


def goals_page(api_url: str = DEFAULT_API_URL) -> None:
    st.title("🎯 Productivity Goals")
    st.caption(
        "Set daily productivity targets and track your progress."
    )

    targets = _get_targets(api_url)

    if targets is None:
        st.error(
            "Could not load productivity targets. "
            "Make sure the FastAPI backend is running."
        )
        return

    _render_target_form(api_url, targets)

    st.divider()

    progress_data = _get_goal_progress(api_url)

    if progress_data is None:
        st.warning("Goal progress is currently unavailable.")
        return

    _render_progress(progress_data)


def _get_targets(api_url: str) -> dict[str, int] | None:
    try:
        response = requests.get(
            f"{api_url}/user-goals",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        print(f"Unable to load targets: {error}")
        return None


def _get_goal_progress(api_url: str) -> dict[str, Any] | None:
    try:
        response = requests.get(
            f"{api_url}/goal-progress",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        print(f"Unable to load goal progress: {error}")
        return None


def _render_target_form(
    api_url: str,
    targets: dict[str, int],
) -> None:
    st.subheader("Set daily targets")

    with st.form("productivity_targets_form"):
        left_column, right_column = st.columns(2)

        with left_column:
            deep_work_minutes = st.number_input(
                "Deep work target",
                min_value=0,
                max_value=1440,
                value=int(
                    targets.get("deep_work_minutes", 180)
                ),
                step=15,
                help="Minimum deep-work minutes you want to complete.",
            )

            max_idle_minutes = st.number_input(
                "Maximum idle time",
                min_value=0,
                max_value=1440,
                value=int(
                    targets.get("max_idle_minutes", 30)
                ),
                step=5,
                help="Maximum idle minutes allowed during the day.",
            )

        with right_column:
            max_context_switches = st.number_input(
                "Maximum context switches",
                min_value=0,
                value=int(
                    targets.get("max_context_switches", 20)
                ),
                step=1,
                help="Maximum number of app changes you want to allow.",
            )

            max_youtube_minutes = st.number_input(
                "Maximum YouTube time",
                min_value=0,
                max_value=1440,
                value=int(
                    targets.get("max_youtube_minutes", 45)
                ),
                step=5,
                help="Maximum time allowed on YouTube.",
            )

        submitted = st.form_submit_button(
            "Save targets",
            use_container_width=True,
        )

    if submitted:
        payload = {
            "deep_work_minutes": int(deep_work_minutes),
            "max_context_switches": int(
                max_context_switches
            ),
            "max_idle_minutes": int(max_idle_minutes),
            "max_youtube_minutes": int(
                max_youtube_minutes
            ),
        }

        _save_targets(api_url, payload)


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

        st.success("Productivity targets updated.")
        st.rerun()

    except requests.RequestException as error:
        st.error(
            "Unable to save productivity targets."
        )
        print(f"Unable to save targets: {error}")


def _render_progress(
    progress_data: dict[str, Any],
) -> None:
    st.subheader("Today's progress")

    metrics = progress_data.get("metrics", {})

    if not metrics:
        st.info("No goal progress is available yet.")
        return

    first_column, second_column = st.columns(2)

    metric_items = list(metrics.items())

    for index, (metric_name, metric) in enumerate(
        metric_items
    ):
        column = (
            first_column
            if index % 2 == 0
            else second_column
        )

        with column:
            _render_goal_card(metric_name, metric)

    suggestions = _build_suggestions(metrics)

    st.subheader("Suggestions")

    for suggestion in suggestions:
        st.write(f"• {suggestion}")


def _render_goal_card(
    metric_name: str,
    metric: dict[str, Any],
) -> None:
    readable_name = metric_name.replace("_", " ").title()

    current = metric.get("current", 0)
    target = metric.get("target", 0)
    unit = metric.get("unit", "")
    status = metric.get("status", "Unknown")
    progress = metric.get("progress", 0)

    safe_progress = max(
        0,
        min(100, int(progress)),
    )

    with st.container(border=True):
        st.markdown(f"### {readable_name}")

        st.metric(
            label="Current progress",
            value=f"{current} {unit}",
            delta=f"Target: {target} {unit}",
            delta_color="off",
        )

        st.progress(safe_progress / 100)

        st.write(f"**Progress:** {safe_progress}%")
        st.write(f"**Status:** {status}")


def _build_suggestions(
    metrics: dict[str, dict[str, Any]],
) -> list[str]:
    suggestions: list[str] = []

    deep_work = metrics.get("deep_work", {})
    deep_current = float(deep_work.get("current", 0))
    deep_target = float(deep_work.get("target", 0))

    if deep_current < deep_target:
        remaining = round(
            deep_target - deep_current,
            1,
        )
        suggestions.append(
            f"Complete {remaining} more minutes of deep work."
        )
    else:
        suggestions.append(
            "Your deep-work target has been completed."
        )

    context_switches = metrics.get(
        "context_switches",
        {},
    )

    if context_switches.get("status") == "Exceeded":
        suggestions.append(
            "Reduce app switching by grouping similar tasks."
        )
    else:
        suggestions.append(
            "Context switching is currently within your limit."
        )

    idle_time = metrics.get("idle_time", {})

    if idle_time.get("status") == "Exceeded":
        suggestions.append(
            "Idle time is above your target. "
            "Try using shorter scheduled breaks."
        )

    youtube_time = metrics.get("youtube_time", {})

    if youtube_time.get("status") == "Exceeded":
        suggestions.append(
            "YouTube usage has exceeded your daily limit."
        )

    if not suggestions:
        suggestions.append(
            "Keep tracking activity to receive suggestions."
        )

    return suggestions