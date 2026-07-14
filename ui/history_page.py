import pandas as pd
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"


def api(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"History API error: {error}")
        return {}

    except ValueError as error:
        st.error(f"Invalid history response: {error}")
        return {}


def history_page():
    # ── Page header ──────────────────────────────────────────────────────
    st.markdown(
        """
<div style="margin-bottom:30px;">
<div style="color:#22D3EE;font-size:11px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;margin-bottom:8px;">
HISTORY
</div>
<div class="page-title">
Your productivity journey.
</div>
<div class="page-sub">
Long-term patterns, trends, and behavioral evolution.
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ── Range selector ───────────────────────────────────────────────────
    selected_days = st.selectbox(
        "Time range",
        options=[7, 30, 90, 365],
        index=1,
        format_func=lambda value: f"Last {value} days",
        key="history_time_range",
    )

    data = api(f"/history?days={selected_days}")

    if not data:
        st.warning(
            "Historical analytics could not be loaded. "
            "Make sure the backend is running."
        )
        return

    summary = data.get("summary", {})
    daily = data.get("daily", [])
    tracked_days = summary.get("tracked_days", 0)

    # ── Empty historical state ───────────────────────────────────────────
    if tracked_days == 0:
        st.markdown(
            """
<div class="card-cyan">
<div class="eyebrow">Historical Analytics</div>
<div style="font-size:20px;font-weight:800;color:#F8FAFC;margin-bottom:10px;">
No historical activity yet
</div>
<div style="font-size:14px;color:#94A3B8;line-height:1.7;">
Drift needs activity records from multiple dates before it can display
long-term trends. Keep the tracker running across several days and this
page will automatically populate.
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    # ── Summary metrics ──────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    best_day = summary.get("best_day") or {}
    best_day_label = best_day.get("weekday", "—")

    metrics = [
        (
            "Tracked Days",
            tracked_days,
            f"of {selected_days} days",
        ),
        (
            "Average Score",
            summary.get("average_score", 0),
            f"{summary.get('average_focus_percentage', 0)}% average focus",
        ),
        (
            "Deep Work",
            f"{summary.get('total_deep_work_minutes', 0)} min",
            "total for selected period",
        ),
        (
            "Longest Streak",
            f"{summary.get('longest_streak', 0)} days",
            f"best day: {best_day_label}",
        ),
    ]

    for column, (label, value, subtitle) in zip(
        [c1, c2, c3, c4],
        metrics,
    ):
        with column:
            st.markdown(
                f"""
<div class="stat-tile">
<div class="stat-label">{label}</div>
<div class="stat-value">{value}</div>
<div class="stat-sub">{subtitle}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ── Prepare chart data ───────────────────────────────────────────────
    history_df = pd.DataFrame(daily)

    if not history_df.empty:
        history_df["date"] = pd.to_datetime(
            history_df["date"],
            errors="coerce",
        )
        history_df = history_df.dropna(subset=["date"])
        history_df = history_df.sort_values("date")
        history_df = history_df.set_index("date")

    # ── Productivity and focus trends ───────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown(
            '<div class="eyebrow">Productivity Score Trend</div>',
            unsafe_allow_html=True,
        )

        if (
            not history_df.empty
            and "score" in history_df.columns
            and tracked_days > 0
        ):
            st.line_chart(
                history_df[["score"]],
                height=300,
            )
        else:
            st.markdown(
                """
<div class="card">
<div style="color:#475569;text-align:center;padding:50px 20px;font-size:13px;">
Track activity across multiple days to unlock score trends.
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            '<div class="eyebrow">Focus Percentage Trend</div>',
            unsafe_allow_html=True,
        )

        if (
            not history_df.empty
            and "focus_percentage" in history_df.columns
            and tracked_days > 0
        ):
            st.line_chart(
                history_df[["focus_percentage"]],
                height=300,
            )
        else:
            st.markdown(
                """
<div class="card">
<div style="color:#475569;text-align:center;padding:50px 20px;font-size:13px;">
Focus trends will appear after several tracked days.
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # ── Deep work and context switching ─────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown(
            '<div class="eyebrow">Deep Work Evolution</div>',
            unsafe_allow_html=True,
        )

        if (
            not history_df.empty
            and "deep_work_minutes" in history_df.columns
            and tracked_days > 0
        ):
            st.bar_chart(
                history_df[["deep_work_minutes"]],
                height=280,
            )
        else:
            st.markdown(
                """
<div class="card">
<div style="color:#475569;text-align:center;padding:45px 20px;font-size:13px;">
No historical deep-work data yet.
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.markdown(
            '<div class="eyebrow">Context Switch Trend</div>',
            unsafe_allow_html=True,
        )

        if (
            not history_df.empty
            and "context_switches" in history_df.columns
            and tracked_days > 0
        ):
            st.bar_chart(
                history_df[["context_switches"]],
                height=280,
            )
        else:
            st.markdown(
                """
<div class="card">
<div style="color:#475569;text-align:center;padding:45px 20px;font-size:13px;">
Context-switch history will appear after several days.
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # ── Activity heatmap ─────────────────────────────────────────────────
    heatmap = data.get("heatmap", [])

    st.markdown(
        '<div class="card"><div class="eyebrow">Activity Heatmap</div>',
        unsafe_allow_html=True,
    )

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
            level = item.get("level", 0)
            color = heatmap_colors.get(level, "#172033")
            day = item.get("date", "")
            score = item.get("score", 0)
            tracked = item.get("tracked", False)

            status = (
                f"Score {score}"
                if tracked
                else "No activity"
            )

            cells.append(
                f'<span title="{day} · {status}" '
                f'style="display:inline-block;width:18px;height:18px;'
                f'border-radius:5px;background:{color};"></span>'
            )

        cells_html = "".join(cells)

        st.markdown(
            f"""
<div style="display:flex;flex-wrap:wrap;gap:7px;align-items:center;">
{cells_html}
</div>
<div style="display:flex;align-items:center;gap:7px;margin-top:16px;font-size:11px;color:#64748B;">
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
        st.markdown(
            """
<div style="color:#475569;text-align:center;padding:34px 20px;font-size:13px;">
No heatmap data available.
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Mission distribution ─────────────────────────────────────────────
    missions = data.get("missions", [])

    st.markdown(
        '<div class="card"><div class="eyebrow">Mission Distribution</div>',
        unsafe_allow_html=True,
    )

    if missions:
        for mission in missions[:8]:
            name = mission.get("mission", "Unknown")
            minutes = mission.get("minutes", 0)
            percentage = mission.get("percentage", 0)

            st.markdown(
                f"""
<div style="margin-bottom:16px;">
<div style="display:flex;justify-content:space-between;font-size:13px;color:#CBD5E1;margin-bottom:7px;">
<span>{name}</span>
<span>{minutes} min · {percentage}%</span>
</div>
<div style="height:8px;background:rgba(30,41,59,.9);border-radius:999px;overflow:hidden;">
<div style="height:100%;width:{min(percentage, 100)}%;background:#22D3EE;border-radius:999px;"></div>
</div>
</div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
<div style="color:#475569;text-align:center;padding:30px 20px;font-size:13px;">
Mission history will appear after dated activity records are available.
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Historical insight ───────────────────────────────────────────────
    insight = data.get(
        "insight",
        "Keep tracking to unlock historical insights.",
    )

    st.markdown(
        f"""
<div class="card-cyan">
<div class="eyebrow">Historical Insight</div>
<div style="color:#F8FAFC;font-size:16px;line-height:1.75;">
{insight}
</div>
</div>
        """,
        unsafe_allow_html=True,
    )