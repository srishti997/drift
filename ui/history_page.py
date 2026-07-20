from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st

from ui.components import metric_card, section_header


API_URL = "http://127.0.0.1:8000"


def api(endpoint: str) -> dict[str, Any]:
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, dict) else {}

    except requests.RequestException as error:
        st.error(f"History API error: {error}")
        return {}

    except ValueError as error:
        st.error(f"Invalid history response: {error}")
        return {}


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _format_minutes(value: Any) -> str:
    minutes = max(
        0,
        round(_safe_float(value)),
    )

    if minutes < 60:
        return f"{minutes} min"

    hours = minutes // 60
    remaining = minutes % 60

    if remaining == 0:
        return f"{hours} hr"

    return f"{hours} hr {remaining} min"


def _empty_chart(message: str) -> None:
    with st.container(border=True):
        st.markdown("### 🌱 Not enough history yet")
        st.write(message)


def history_page() -> None:
    section_header(
        title="Your productivity journey",
        description=(
            "See how your focus, deep work, and daily habits "
            "have changed over time."
        ),
        eyebrow="History",
    )

    selected_days = st.selectbox(
        "Time range",
        options=[7, 30, 90, 365],
        index=1,
        format_func=lambda value: f"Last {value} days",
        key="history_time_range",
    )

    data = api(
        f"/history?days={selected_days}"
    )

    if not data:
        with st.container(border=True):
            st.warning(
                "Historical analytics could not be loaded. "
                "Make sure the backend is running."
            )
        return

    summary = data.get("summary", {})
    daily = data.get("daily", [])
    tracked_days = _safe_int(
        summary.get("tracked_days")
    )

    best_day = summary.get("best_day") or {}
    best_day_label = (
        best_day.get("weekday")
        or best_day.get("date")
        or "Not available"
    )

    average_score = round(
        _safe_float(
            summary.get("average_score")
        ),
        1,
    )

    average_focus = round(
        _safe_float(
            summary.get(
                "average_focus_percentage"
            )
        ),
        1,
    )

    total_deep_work = _safe_float(
        summary.get(
            "total_deep_work_minutes"
        )
    )

    longest_streak = _safe_int(
        summary.get("longest_streak")
    )

    insight = str(
        data.get(
            "insight",
            "Keep tracking activity to unlock historical insights.",
        )
    ).strip()

    # ------------------------------------------------------------------
    # Historical insight
    # ------------------------------------------------------------------

    with st.container(border=True):
        insight_left, insight_right = st.columns(
            [3, 1],
            gap="large",
        )

        with insight_left:
            st.markdown("### 🧠 What Drift noticed")
            st.markdown(f"#### {insight}")

            if tracked_days < 3:
                st.caption(
                    "More tracked days will make this insight more reliable."
                )
            else:
                st.caption(
                    f"This insight is based on {tracked_days} tracked days."
                )

        with insight_right:
            st.metric(
                "Tracked days",
                tracked_days,
            )

            st.caption(
                f"Selected period: {selected_days} days"
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    section_header(
        title="Progress summary",
        description=(
            "The most important numbers from the selected period."
        ),
        eyebrow="At a glance",
    )

    card_1, card_2, card_3, card_4 = st.columns(
        4,
        gap="medium",
    )

    with card_1:
        metric_card(
            icon="📅",
            title="Tracked days",
            value=str(tracked_days),
            subtitle=(
                f"Activity recorded on "
                f"{tracked_days} of {selected_days} days."
            ),
            badge="Period",
        )

    with card_2:
        metric_card(
            icon="🧠",
            title="Average score",
            value=f"{average_score}/100",
            subtitle=(
                f"Average focus: {average_focus}%."
            ),
            badge="Average",
        )

    with card_3:
        metric_card(
            icon="🔥",
            title="Deep work",
            value=_format_minutes(
                total_deep_work
            ),
            subtitle=(
                "Total uninterrupted work in this period."
            ),
            badge="Total",
        )

    with card_4:
        metric_card(
            icon="🏆",
            title="Longest streak",
            value=f"{longest_streak} days",
            subtitle=(
                f"Strongest day: {best_day_label}."
            ),
            badge="Consistency",
        )

    if tracked_days == 0:
        with st.container(border=True):
            st.markdown(
                "### 🌱 Your history starts here"
            )

            st.write(
                "Keep the tracker running across multiple workdays. "
                "Drift will automatically build trend charts, streaks, "
                "mission history, and long-term insights."
            )

        return

    # ------------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------------

    history_df = pd.DataFrame(daily)

    if not history_df.empty:
        history_df["date"] = pd.to_datetime(
            history_df.get("date"),
            errors="coerce",
        )

        history_df = (
            history_df
            .dropna(subset=["date"])
            .sort_values("date")
            .set_index("date")
        )

    # ------------------------------------------------------------------
    # Main trends
    # ------------------------------------------------------------------

    section_header(
        title="How your productivity changed",
        description=(
            "Compare your score and focus quality across tracked days."
        ),
        eyebrow="Trends",
    )

    score_col, focus_col = st.columns(
        2,
        gap="medium",
    )

    with score_col:
        with st.container(border=True):
            st.markdown(
                "### 📈 Productivity over time"
            )

            if (
                not history_df.empty
                and "score" in history_df.columns
            ):
                st.line_chart(
                    history_df[["score"]],
                    height=300,
                )
            else:
                st.info(
                    "Track activity across multiple days "
                    "to unlock score trends."
                )

    with focus_col:
        with st.container(border=True):
            st.markdown(
                "### 🎯 Focus trend"
            )

            if (
                not history_df.empty
                and "focus_percentage"
                in history_df.columns
            ):
                st.line_chart(
                    history_df[
                        ["focus_percentage"]
                    ],
                    height=300,
                )
            else:
                st.info(
                    "Focus trends will appear after "
                    "several tracked days."
                )

    # ------------------------------------------------------------------
    # Behaviour trends
    # ------------------------------------------------------------------

    section_header(
        title="Work behaviour over time",
        description=(
            "See whether deep work is growing and attention "
            "changes are becoming easier to control."
        ),
        eyebrow="Behaviour",
    )

    deep_col, switch_col = st.columns(
        2,
        gap="medium",
    )

    with deep_col:
        with st.container(border=True):
            st.markdown(
                "### 🔥 Deep-work growth"
            )

            if (
                not history_df.empty
                and "deep_work_minutes"
                in history_df.columns
            ):
                st.bar_chart(
                    history_df[
                        ["deep_work_minutes"]
                    ],
                    height=280,
                )
            else:
                st.info(
                    "No historical deep-work data is available yet."
                )

    with switch_col:
        with st.container(border=True):
            st.markdown(
                "### 🔄 Attention changes"
            )

            if (
                not history_df.empty
                and "context_switches"
                in history_df.columns
            ):
                st.bar_chart(
                    history_df[
                        ["context_switches"]
                    ],
                    height=280,
                )
            else:
                st.info(
                    "Attention-change history will appear "
                    "after several tracked days."
                )

    # ------------------------------------------------------------------
    # Activity heatmap
    # ------------------------------------------------------------------

    section_header(
        title="Activity consistency",
        description=(
            "A calendar-style view of how consistently "
            "you tracked and worked."
        ),
        eyebrow="Heatmap",
    )

    heatmap = data.get("heatmap", [])

    with st.container(border=True):
        if heatmap:
            heatmap_colors = {
                0: "#172033",
                1: "#164E63",
                2: "#0E7490",
                3: "#06B6D4",
                4: "#67E8F9",
            }

            cells = []

            for item in heatmap:
                level = _safe_int(
                    item.get("level")
                )

                color = heatmap_colors.get(
                    level,
                    "#172033",
                )

                day = str(
                    item.get("date", "")
                )

                score_value = item.get(
                    "score",
                    0,
                )

                tracked = bool(
                    item.get("tracked", False)
                )

                status = (
                    f"Score {score_value}"
                    if tracked
                    else "No activity"
                )

                cells.append(
                    f'<span title="{day} · {status}" '
                    f'style="display:inline-block;'
                    f'width:18px;height:18px;'
                    f'border-radius:5px;'
                    f'background:{color};"></span>'
                )

            st.markdown(
                (
                    '<div style="display:flex;'
                    'flex-wrap:wrap;gap:7px;'
                    'align-items:center;">'
                    + "".join(cells)
                    + "</div>"
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                """
<div style="
display:flex;
align-items:center;
gap:7px;
margin-top:16px;
font-size:11px;
color:#64748B;
">
<span>Less</span>
<span style="width:13px;height:13px;border-radius:4px;background:#172033;"></span>
<span style="width:13px;height:13px;border-radius:4px;background:#164E63;"></span>
<span style="width:13px;height:13px;border-radius:4px;background:#0E7490;"></span>
<span style="width:13px;height:13px;border-radius:4px;background:#06B6D4;"></span>
<span style="width:13px;height:13px;border-radius:4px;background:#67E8F9;"></span>
<span>More</span>
</div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.info(
                "No activity heatmap data is available yet."
            )

    # ------------------------------------------------------------------
    # Mission distribution
    # ------------------------------------------------------------------

    section_header(
        title="Where your time went",
        description=(
            "Your most common missions across the selected period."
        ),
        eyebrow="Mission history",
    )

    missions = data.get(
        "missions",
        [],
    )

    with st.container(border=True):
        if missions:
            for index, mission in enumerate(
                missions[:8]
            ):
                name = (
                    mission.get("mission")
                    or "Unknown mission"
                )

                minutes = _safe_float(
                    mission.get("minutes")
                )

                percentage = max(
                    0,
                    min(
                        100,
                        _safe_float(
                            mission.get(
                                "percentage"
                            )
                        ),
                    ),
                )

                label_col, value_col = st.columns(
                    [3, 1]
                )

                with label_col:
                    st.markdown(
                        f"**{name}**"
                    )

                with value_col:
                    st.markdown(
                        f"**{minutes:g} min · "
                        f"{percentage:g}%**"
                    )

                st.progress(
                    percentage / 100
                )

                if index < len(missions[:8]) - 1:
                    st.divider()

        else:
            st.info(
                "Mission history will appear after "
                "activity is recorded across multiple dates."
            )

    # ------------------------------------------------------------------
    # Recent days
    # ------------------------------------------------------------------

    section_header(
        title="Recent workdays",
        description=(
            "A simple record of your most recent tracked days."
        ),
        eyebrow="Daily history",
    )

    if not history_df.empty:
        recent_rows = (
            history_df
            .reset_index()
            .sort_values(
                "date",
                ascending=False,
            )
            .head(7)
        )

        for _, row in recent_rows.iterrows():
            row_date = row["date"].strftime(
                "%A, %B %d"
            )

            score_value = round(
                _safe_float(
                    row.get("score")
                ),
                1,
            )

            focus_value = round(
                _safe_float(
                    row.get(
                        "focus_percentage"
                    )
                ),
                1,
            )

            deep_value = _safe_float(
                row.get(
                    "deep_work_minutes"
                )
            )

            switches = _safe_int(
                row.get(
                    "context_switches"
                )
            )

            with st.container(border=True):
                date_col, metrics_col = st.columns(
                    [1.2, 2.8],
                    gap="large",
                )

                with date_col:
                    st.markdown(
                        f"### {row_date}"
                    )

                    st.caption(
                        "Tracked workday"
                    )

                with metrics_col:
                    metric_a, metric_b, metric_c = (
                        st.columns(3)
                    )

                    with metric_a:
                        st.metric(
                            "Score",
                            f"{score_value}/100",
                        )

                    with metric_b:
                        st.metric(
                            "Deep work",
                            _format_minutes(
                                deep_value
                            ),
                        )

                    with metric_c:
                        st.metric(
                            "Attention changes",
                            switches,
                        )

                    st.caption(
                        f"Average focus: {focus_value}%"
                    )

    else:
        _empty_chart(
            "Recent workdays will appear once "
            "dated activity records are available."
        )