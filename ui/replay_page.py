from typing import Any, Callable

import streamlit as st

from ui.components import metric_card, section_header


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _format_minutes(value: Any) -> str:
    minutes = max(0, round(_safe_float(value)))

    if minutes < 60:
        return f"{minutes} min"

    hours = minutes // 60
    remaining = minutes % 60

    if remaining == 0:
        return f"{hours} hr"

    return f"{hours} hr {remaining} min"


def _event_details(event_type: str) -> tuple[str, str, str]:
    event_type = str(event_type or "").lower()

    if event_type == "start":
        return "🚀", "Started working", "positive"

    if event_type == "focus_lost":
        return "⚠️", "Focus interrupted", "negative"

    if event_type == "recovered":
        return "✅", "Focus recovered", "positive"

    if event_type == "deep_work":
        return "🔥", "Deep work", "positive"

    if event_type == "idle":
        return "🌙", "Away from work", "neutral"

    return "💻", "Focused activity", "neutral"


def _build_story(replay: dict) -> str:
    summary = str(replay.get("summary", "")).strip()

    if summary:
        return summary

    total_minutes = _safe_int(replay.get("total_minutes"))
    focus_lost = _safe_int(replay.get("focus_lost_events"))
    recoveries = _safe_int(replay.get("recovery_events"))
    top_mission = replay.get("top_mission") or "your main activity"

    if total_minutes == 0:
        return (
            "Drift has not recorded enough activity to build your daily story yet."
        )

    if focus_lost == 0:
        return (
            f"You spent {_format_minutes(total_minutes)} working mainly on "
            f"{top_mission}. Your attention remained relatively steady."
        )

    if recoveries >= focus_lost:
        return (
            f"You spent {_format_minutes(total_minutes)} working mainly on "
            f"{top_mission}. Your focus was interrupted {focus_lost} times, "
            "but you recovered after most interruptions."
        )

    return (
        f"You spent {_format_minutes(total_minutes)} working mainly on "
        f"{top_mission}. Several interruptions affected your rhythm, and "
        "some sessions ended before focus was fully recovered."
    )


def render_replay_page(
    api: Callable[[str], dict | None],
    empty: Callable[[str], None],
) -> None:
    replay = api("/replay") or {}
    events = replay.get("events", [])

    section_header(
        title="Replay your workday",
        description=(
            "Follow how your attention changed, where focus was lost, "
            "and how you returned to meaningful work."
        ),
        eyebrow="Day replay",
    )

    if not events:
        with st.container(border=True):
            st.markdown("### 🎬 No replay available yet")

            st.write(
                "Keep the tracker running while you work. Drift will turn "
                "your activity into a simple timeline of focus, interruption, "
                "and recovery."
            )

            st.info(
                "A replay appears after Drift records enough meaningful activity."
            )

        return

    total_minutes = _safe_int(
        replay.get("total_minutes")
    )

    top_mission = (
        replay.get("top_mission")
        or "Not identified"
    )

    focus_lost_events = _safe_int(
        replay.get("focus_lost_events")
    )

    recovery_events = _safe_int(
        replay.get("recovery_events")
    )

    story = _build_story(replay)

    # ------------------------------------------------------------------
    # Daily story
    # ------------------------------------------------------------------

    with st.container(border=True):
        story_col, result_col = st.columns(
            [3, 1],
            gap="large",
        )

        with story_col:
            st.markdown("### 📖 Today's story")
            st.markdown(f"#### {story}")

            if top_mission not in {
                "Not identified",
                "Unknown",
                "Unclassified Mission",
            }:
                st.caption(
                    f"Most of your tracked attention went toward "
                    f"**{top_mission}**."
                )
            else:
                st.caption(
                    "Drift needs better classification data to identify "
                    "your main mission."
                )

        with result_col:
            if focus_lost_events == 0:
                rhythm = "Steady"
            elif recovery_events >= focus_lost_events:
                rhythm = "Resilient"
            elif focus_lost_events <= 3:
                rhythm = "Mixed"
            else:
                rhythm = "Fragmented"

            st.metric(
                label="Focus rhythm",
                value=rhythm,
            )

            st.caption(
                f"{recovery_events} recoveries from "
                f"{focus_lost_events} interruptions"
            )

    # ------------------------------------------------------------------
    # Summary cards
    # ------------------------------------------------------------------

    section_header(
        title="Replay summary",
        description=(
            "The most important numbers from your recorded workday."
        ),
        eyebrow="Today",
    )

    card_1, card_2, card_3, card_4 = st.columns(
        4,
        gap="medium",
    )

    with card_1:
        metric_card(
            icon="⏱️",
            title="Tracked time",
            value=_format_minutes(total_minutes),
            subtitle="Total time included in today's replay.",
            badge="Today",
        )

    with card_2:
        metric_card(
            icon="🎯",
            title="Top mission",
            value=str(top_mission),
            subtitle="The activity that received most of your attention.",
            badge="Primary",
        )

    with card_3:
        metric_card(
            icon="⚠️",
            title="Focus interruptions",
            value=str(focus_lost_events),
            subtitle="Meaningful moments where focus was lost.",
            trend=(
                "Low interruption level"
                if focus_lost_events <= 2
                else "Attention was interrupted"
            ),
            trend_type=(
                "positive"
                if focus_lost_events <= 2
                else "negative"
            ),
            badge="Detected",
        )

    with card_4:
        recovery_rate = (
            round(
                recovery_events
                / focus_lost_events
                * 100
            )
            if focus_lost_events > 0
            else 100
        )

        metric_card(
            icon="✅",
            title="Recoveries",
            value=str(recovery_events),
            subtitle=(
                f"You recovered after approximately "
                f"{recovery_rate}% of interruptions."
            ),
            trend=(
                "Strong recovery"
                if recovery_rate >= 75
                else "Recovery can improve"
            ),
            trend_type=(
                "positive"
                if recovery_rate >= 75
                else "neutral"
            ),
            badge="Return",
        )

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    section_header(
        title="How your day unfolded",
        description=(
            "Each event shows a meaningful change in your attention."
        ),
        eyebrow="Timeline",
    )

    event_filter = st.segmented_control(
        "Show events",
        options=[
            "All",
            "Focus",
            "Interruptions",
            "Recoveries",
        ],
        default="All",
        key="replay_event_filter",
    )

    filtered_events = []

    for event in events:
        event_type = str(
            event.get("event_type", "focused")
        ).lower()

        include = (
            event_filter == "All"
            or (
                event_filter == "Focus"
                and event_type in {
                    "start",
                    "focused",
                    "deep_work",
                }
            )
            or (
                event_filter == "Interruptions"
                and event_type in {
                    "focus_lost",
                    "idle",
                }
            )
            or (
                event_filter == "Recoveries"
                and event_type == "recovered"
            )
        )

        if include:
            filtered_events.append(event)

    if not filtered_events:
        st.info(
            "No replay events match the selected filter."
        )
        return

    for index, event in enumerate(
        filtered_events,
        start=1,
    ):
        event_type = event.get(
            "event_type",
            "focused",
        )

        icon, event_label, event_tone = _event_details(
            event_type
        )

        event_time = (
            event.get("time")
            or event.get("start_time")
            or "Time unavailable"
        )

        duration_minutes = _safe_float(
            event.get("duration_minutes")
        )

        if duration_minutes == 0:
            duration_seconds = _safe_float(
                event.get("duration_seconds")
            )
            duration_minutes = round(
                duration_seconds / 60,
                1,
            )

        mission = (
            event.get("mission")
            or "Unclassified activity"
        )

        story_text = (
            event.get("story")
            or event.get("description")
            or ""
        )

        activity_type = (
            event.get("activity_type")
            or ""
        )

        app_name = (
            event.get("app_name")
            or event.get("app")
            or ""
        )

        with st.container(border=True):
            header_col, time_col = st.columns(
                [3, 1]
            )

            with header_col:
                st.markdown(
                    f"### {icon} {event_label}"
                )

                st.markdown(
                    f"#### {mission}"
                )

            with time_col:
                st.markdown(
                    f"**{event_time}**"
                )

                if duration_minutes > 0:
                    st.caption(
                        f"{duration_minutes:g} min"
                    )

            if story_text:
                st.write(story_text)

            details = []

            if activity_type:
                details.append(
                    f"Activity: {activity_type}"
                )

            if app_name:
                details.append(
                    f"App: {app_name}"
                )

            if details:
                st.caption(
                    " · ".join(details)
                )

            if event_tone == "negative":
                st.warning(
                    "This event interrupted the previous focus block."
                )

            elif event_type == "recovered":
                st.success(
                    "You returned to productive work after the interruption."
                )

        if index < len(filtered_events):
            st.markdown(
                "<div style='height:12px'></div>",
                unsafe_allow_html=True,
            )

    # ------------------------------------------------------------------
    # End-of-day takeaway
    # ------------------------------------------------------------------

    section_header(
        title="What to take from today",
        description=(
            "A simple action based on the pattern visible in your replay."
        ),
        eyebrow="Next step",
    )

    if focus_lost_events == 0:
        takeaway = (
            "Your attention remained steady. Preserve the same working "
            "environment for your next important task."
        )

    elif recovery_events >= focus_lost_events:
        takeaway = (
            "You recovered well after interruptions. Reduce the number "
            "of interruptions while keeping the recovery habits that worked."
        )

    elif focus_lost_events >= 5:
        takeaway = (
            "Your workday contained several unresolved interruptions. "
            "Start your next session with one task, fewer open apps, "
            "and notifications muted."
        )

    else:
        takeaway = (
            "Your focus was interrupted a few times. Define the exact "
            "next action before starting your next work block."
        )

    with st.container(border=True):
        st.markdown("### 🎯 Recommended next step")
        st.write(takeaway)