import time
import streamlit as st


PRODUCTIVE_ACTIVITY_TYPES = {"CODING", "BROWSING", "COMMUNICATION"}


def render_replay_page(api, empty):
    replay = api("/replay")

    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Replay</div>
        <div class="page-title">Productivity Playback.</div>
        <div class="page-sub">Watch your workday unfold session by session.</div>
    </div>
    """, unsafe_allow_html=True)

    if not replay or not replay.get("events"):
        empty("No replay events yet. Run the tracker for a few minutes.")
        return

    events = replay.get("events", [])

    initialize_state()

    filtered_events = apply_filters(events)

    if not filtered_events:
        st.warning("No sessions match your filters.")
        return

    total = len(filtered_events)
    current_index = min(st.session_state.playback_index, total - 1)
    current = filtered_events[current_index]

    render_summary(replay)
    render_stats(filtered_events)
    render_filters(events)
    render_controls(total, current_index)

    progress = int(((current_index + 1) / total) * 100)

    render_progress(current_index, total, progress)
    render_replay_map(filtered_events, current_index)
    render_current_session(current)

    st.markdown("""
    <div style="margin-top:28px;">
        <div class="eyebrow">Full Timeline</div>
    </div>
    """, unsafe_allow_html=True)

    for index, event in enumerate(filtered_events):
        render_timeline_row(event, index, current_index)

    handle_auto_play(total, current_index)


def initialize_state():
    defaults = {
        "playback_index": 0,
        "playback_running": False,
        "playback_speed": 1,
        "replay_filter": "All",
        "replay_search": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_summary(replay):
    st.markdown(f"""
    <div class="card-cyan">
        <div class="eyebrow">Today's Story</div>
        <div style="font-size:15px;color:#CBD5E1;line-height:1.75;">
            {replay.get("summary", "No summary available.")}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats(events):
    total_sessions = len(events)

    productive_sessions = [
        e for e in events
        if e.get("activity_type") in PRODUCTIVE_ACTIVITY_TYPES
        and not e.get("is_distraction", False)
    ]

    drift_sessions = [
        e for e in events
        if e.get("event_type") == "focus_lost"
        or e.get("is_distraction", False)
    ]

    recovered_sessions = [
        e for e in events
        if e.get("event_type") == "recovered"
    ]

    productive_minutes = round(
        sum(e.get("duration_minutes", 0) for e in productive_sessions),
        2
    )

    drift_minutes = round(
        sum(e.get("duration_minutes", 0) for e in drift_sessions),
        2
    )

    recovery_rate = 0
    if drift_sessions:
        recovery_rate = round(
            (len(recovered_sessions) / len(drift_sessions)) * 100,
            1
        )

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("Total Sessions", total_sessions, "replay blocks"),
        ("Productive Time", f"{productive_minutes} min", "focused work"),
        ("Drift Time", f"{drift_minutes} min", "lost focus"),
        ("Recovery Rate", f"{recovery_rate}%", "recoveries / drifts"),
    ]

    for col, (label, value, sub) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(f"""
            <div class="stat-tile">
                <div class="stat-label">{label}</div>
                <div class="stat-value" style="font-size:22px;">{value}</div>
                <div class="stat-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


def render_filters(events):
    st.write("")

    filter_options = ["All", "Focused", "Focus Lost", "Recovered"]

    activity_types = sorted(
        list(set(event.get("activity_type", "Unknown") for event in events))
    )

    filter_options.extend(activity_types)

    c1, c2 = st.columns([1, 2])

    with c1:
        selected_filter = st.selectbox(
            "Filter sessions",
            filter_options,
            index=filter_options.index(st.session_state.replay_filter)
            if st.session_state.replay_filter in filter_options
            else 0,
        )

    with c2:
        search = st.text_input(
            "Search sessions",
            value=st.session_state.replay_search,
            placeholder="Search mission, story, activity..."
        )

    if selected_filter != st.session_state.replay_filter:
        st.session_state.replay_filter = selected_filter
        st.session_state.playback_index = 0
        st.session_state.playback_running = False
        st.rerun()

    if search != st.session_state.replay_search:
        st.session_state.replay_search = search
        st.session_state.playback_index = 0
        st.session_state.playback_running = False
        st.rerun()


def apply_filters(events):
    selected_filter = st.session_state.get("replay_filter", "All")
    search = st.session_state.get("replay_search", "").lower().strip()

    filtered = events

    if selected_filter == "Focused":
        filtered = [
            e for e in filtered
            if e.get("event_type") in ["start", "focused"]
        ]

    elif selected_filter == "Focus Lost":
        filtered = [
            e for e in filtered
            if e.get("event_type") == "focus_lost"
        ]

    elif selected_filter == "Recovered":
        filtered = [
            e for e in filtered
            if e.get("event_type") == "recovered"
        ]

    elif selected_filter != "All":
        filtered = [
            e for e in filtered
            if e.get("activity_type") == selected_filter
        ]

    if search:
        filtered = [
            e for e in filtered
            if search in str(e.get("mission", "")).lower()
            or search in str(e.get("story", "")).lower()
            or search in str(e.get("activity_type", "")).lower()
            or search in str(e.get("event_type", "")).lower()
        ]

    return filtered


def render_controls(total, current_index):
    st.write("")

    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

    with c1:
        if st.button("← Previous", use_container_width=True):
            st.session_state.playback_running = False
            st.session_state.playback_index = max(0, current_index - 1)
            st.rerun()

    with c2:
        if st.session_state.playback_running:
            if st.button("⏸ Pause", use_container_width=True):
                st.session_state.playback_running = False
                st.rerun()
        else:
            if st.button("▶ Auto Play", use_container_width=True):
                if current_index >= total - 1:
                    st.session_state.playback_index = 0

                st.session_state.playback_running = True
                st.rerun()

    with c3:
        if st.button("▶ Next", use_container_width=True):
            st.session_state.playback_running = False
            st.session_state.playback_index = min(total - 1, current_index + 1)
            st.rerun()

    with c4:
        speed = st.selectbox(
            "Speed",
            options=[1, 2, 5],
            index=[1, 2, 5].index(st.session_state.playback_speed),
            format_func=lambda x: f"{x}x",
            label_visibility="collapsed"
        )
        st.session_state.playback_speed = speed

    with c5:
        if st.button("↺ Restart", use_container_width=True):
            st.session_state.playback_running = False
            st.session_state.playback_index = 0
            st.rerun()


def render_progress(current_index, total, progress):
    running_text = "Playing" if st.session_state.playback_running else "Paused"

    st.markdown(f"""
    <div class="card-purple">
        <div class="eyebrow">Playback Progress</div>
        <div style="display:flex;justify-content:space-between;font-size:13px;color:#64748B;margin-bottom:8px;">
            <span>{running_text} · Session {current_index + 1} of {total}</span>
            <span>{progress}%</span>
        </div>
        <div class="bar-track">
            <div class="bar-fill" style="width:{progress}%;background:linear-gradient(90deg,#4338CA,#22D3EE);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_replay_map(events, current_index):
    total_minutes = sum(e.get("duration_minutes", 0) for e in events) or 1

    html = """
    <div class="card">
        <div class="eyebrow">Replay Map</div>
        <div style="display:flex;height:34px;border-radius:999px;overflow:hidden;background:rgba(30,41,59,.8);">
    """

    for index, event in enumerate(events):
        event_type = event.get("event_type", "focused")
        _, _, color = get_event_style(event_type)

        width = max(
            (event.get("duration_minutes", 0) / total_minutes) * 100,
            0.6
        )

        opacity = "1" if index == current_index else "0.45"
        border = "2px solid #F8FAFC" if index == current_index else "none"

        title = (
            f"{event.get('time', '—')} | "
            f"{event.get('mission', 'Unknown')} | "
            f"{event.get('duration_minutes', 0)} min"
        )

        html += f"""
        <div title="{title}"
             style="
                width:{width}%;
                background:{color};
                opacity:{opacity};
                border:{border};
             ">
        </div>
        """

    html += """
        </div>
        <div style="display:flex;gap:18px;margin-top:12px;font-size:12px;color:#64748B;flex-wrap:wrap;">
            <span>🚀 Started</span>
            <span>💻 Focused</span>
            <span>✅ Recovered</span>
            <span>⚠️ Focus Lost</span>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_current_session(event):
    event_type = event.get("event_type", "focused")
    icon, label, color = get_event_style(event_type)

    st.markdown(f"""
    <div style="
        background:rgba(13,20,35,.85);
        border:1px solid rgba(34,211,238,.18);
        border-left:5px solid {color};
        border-radius:22px;
        padding:32px;
        margin-bottom:22px;
    ">
        <div style="font-size:13px;color:{color};font-weight:900;letter-spacing:.12em;text-transform:uppercase;margin-bottom:16px;">
            {icon} {label}
        </div>

        <div style="font-size:38px;font-weight:900;color:#F1F5F9;margin-bottom:10px;">
            {event.get("mission", "Unknown")}
        </div>

        <div style="font-size:16px;color:#94A3B8;line-height:1.7;margin-bottom:18px;">
            {event.get("story", "")}
        </div>

        <div style="font-size:12px;color:#64748B;">
            {event.get("time", "—")} · {event.get("duration_minutes", 0)} min · {event.get("activity_type", "Unknown")}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_timeline_row(event, index, current_index):
    event_type = event.get("event_type", "focused")
    icon, label, color = get_event_style(event_type)

    active_border = color if index == current_index else "rgba(148,163,184,.08)"
    active_bg = "rgba(34,211,238,.06)" if index == current_index else "rgba(20,30,50,.45)"

    with st.expander(
        f"{icon} {label} · {event.get('mission', 'Unknown')} · {event.get('duration_minutes', 0)} min",
        expanded=(index == current_index)
    ):
        st.markdown(f"""
        <div style="
            background:{active_bg};
            border:1px solid {active_border};
            border-left:4px solid {color};
            border-radius:14px;
            padding:16px 18px;
            margin-bottom:8px;
        ">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <div style="font-size:12px;color:{color};font-weight:800;letter-spacing:.08em;text-transform:uppercase;">
                    {icon} {label}
                </div>
                <div style="font-family:'JetBrains Mono',monospace;color:#64748B;font-size:12px;">
                    {event.get("time", "—")} · {event.get("duration_minutes", 0)} min
                </div>
            </div>

            <div style="font-size:18px;color:#E2E8F0;font-weight:800;margin-bottom:8px;">
                {event.get("mission", "Unknown")}
            </div>

            <div style="font-size:14px;color:#94A3B8;line-height:1.6;margin-bottom:12px;">
                {event.get("story", "")}
            </div>

            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px;">
                <div class="stat-tile">
                    <div class="stat-label">Activity</div>
                    <div class="stat-value" style="font-size:16px;">{event.get("activity_type", "Unknown")}</div>
                </div>

                <div class="stat-tile">
                    <div class="stat-label">Event</div>
                    <div class="stat-value" style="font-size:16px;">{event.get("event_type", "Unknown")}</div>
                </div>

                <div class="stat-tile">
                    <div class="stat-label">Duration</div>
                    <div class="stat-value" style="font-size:16px;">{event.get("duration_minutes", 0)}m</div>
                </div>

                <div class="stat-tile">
                    <div class="stat-label">Distraction</div>
                    <div class="stat-value" style="font-size:16px;">{str(event.get("is_distraction", False))}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def handle_auto_play(total, current_index):
    if st.session_state.playback_running:
        if current_index < total - 1:
            delay = 1.2 / st.session_state.playback_speed
            time.sleep(delay)
            st.session_state.playback_index = current_index + 1
            st.rerun()
        else:
            st.session_state.playback_running = False
            st.rerun()


def get_event_style(event_type):
    if event_type == "start":
        return "🚀", "Started", "#22D3EE"

    if event_type == "focus_lost":
        return "⚠️", "Focus Lost", "#F87171"

    if event_type == "recovered":
        return "✅", "Recovered", "#34D399"

    return "💻", "Focused", "#818CF8"