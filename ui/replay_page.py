import time
import html
import textwrap
import streamlit as st
import streamlit.components.v1 as components

PRODUCTIVE_ACTIVITY_TYPES = {"CODING", "BROWSING", "COMMUNICATION"}


def md(content):
    st.markdown(textwrap.dedent(content).strip(), unsafe_allow_html=True)


def safe(value, default=""):
    return html.escape(str(value if value is not None else default))


def render_replay_page(api, empty):
    replay = api("/replay")

    md("""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Replay</div>
        <div class="page-title">Productivity Playback.</div>
        <div class="page-sub">Watch your workday unfold session by session.</div>
    </div>
    """)

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

    md("""
    <div style="margin-top:28px;">
        <div class="eyebrow">Full Timeline</div>
    </div>
    """)

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
    summary = safe(replay.get("summary", "No summary available."))

    md(f"""
    <div class="card-cyan">
        <div class="eyebrow">Today's Story</div>
        <div style="font-size:15px;color:#CBD5E1;line-height:1.75;">
            {summary}
        </div>
    </div>
    """)


def render_stats(events):
    total_sessions = len(events)

    productive_sessions = [
        e for e in events
        if e.get("activity_type") in PRODUCTIVE_ACTIVITY_TYPES
        and not e.get("is_distraction", False)
    ]

    drift_sessions = [
        e for e in events
        if e.get("event_type") == "focus_lost" or e.get("is_distraction", False)
    ]

    recovered_sessions = [
        e for e in events
        if e.get("event_type") == "recovered"
    ]

    productive_minutes = round(sum(e.get("duration_minutes", 0) for e in productive_sessions), 2)
    drift_minutes = round(sum(e.get("duration_minutes", 0) for e in drift_sessions), 2)

    recovery_rate = 0
    if drift_sessions:
        recovery_rate = round((len(recovered_sessions) / len(drift_sessions)) * 100, 1)

    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("Total Sessions", total_sessions, "replay blocks"),
        ("Productive Time", f"{productive_minutes} min", "focused work"),
        ("Drift Time", f"{drift_minutes} min", "lost focus"),
        ("Recovery Rate", f"{recovery_rate}%", "recoveries / drifts"),
    ]

    for col, (label, value, sub) in zip([c1, c2, c3, c4], cards):
        with col:
            md(f"""
            <div class="stat-tile">
                <div class="stat-label">{safe(label)}</div>
                <div class="stat-value" style="font-size:22px;">{safe(value)}</div>
                <div class="stat-sub">{safe(sub)}</div>
            </div>
            """)


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
        filtered = [e for e in filtered if e.get("event_type") in ["start", "focused"]]

    elif selected_filter == "Focus Lost":
        filtered = [e for e in filtered if e.get("event_type") == "focus_lost"]

    elif selected_filter == "Recovered":
        filtered = [e for e in filtered if e.get("event_type") == "recovered"]

    elif selected_filter != "All":
        filtered = [e for e in filtered if e.get("activity_type") == selected_filter]

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

    md(f"""
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
    """)


def render_replay_map(events, current_index):
    total_minutes = sum(e.get("duration_minutes", 0) for e in events) or 1

    segments = ""

    for index, event in enumerate(events):
        _, _, color = get_event_style(event.get("event_type", "focused"))

        width = max((event.get("duration_minutes", 0) / total_minutes) * 100, 0.6)
        opacity = "1" if index == current_index else "0.45"
        border = "2px solid #F8FAFC" if index == current_index else "none"

        segments += f"""
        <div style="
            width:{width}%;
            background:{color};
            opacity:{opacity};
            border:{border};
            height:34px;
        "></div>
        """

    html = f"""
    <div style="
        background:rgba(13,20,35,.75);
        border:1px solid rgba(148,163,184,.1);
        border-radius:18px;
        padding:24px;
        margin-bottom:18px;
        font-family:Inter, sans-serif;
    ">
        <div style="
            font-size:10px;
            font-weight:700;
            letter-spacing:.12em;
            text-transform:uppercase;
            color:#22D3EE;
            margin-bottom:14px;
        ">Replay Map</div>

        <div style="
            display:flex;
            height:34px;
            border-radius:999px;
            overflow:hidden;
            background:rgba(30,41,59,.8);
        ">
            {segments}
        </div>

        <div style="
            display:flex;
            gap:18px;
            margin-top:12px;
            font-size:12px;
            color:#64748B;
            flex-wrap:wrap;
        ">
            <span>🚀 Started</span>
            <span>💻 Focused</span>
            <span>✅ Recovered</span>
            <span>⚠️ Focus Lost</span>
        </div>
    </div>
    """

    components.html(html, height=130)

def render_current_session(event):
    event_type = event.get("event_type", "focused")
    icon, label, color = get_event_style(event_type)

    with st.container(border=True):
        st.markdown(f"### {icon} {label}")
        st.markdown(f"## {event.get('mission', 'Unknown')}")
        st.write(event.get("story", ""))

        st.caption(
            f"{event.get('time', '—')} · "
            f"{event.get('duration_minutes', 0)} min · "
            f"{event.get('activity_type', 'Unknown')}"
        )

def render_timeline_row(event, index, current_index):
    event_type = event.get("event_type", "focused")
    icon, label, _ = get_event_style(event_type)

    with st.expander(
        f"{icon} {label} · {event.get('mission', 'Unknown')} · {event.get('duration_minutes', 0)} min",
        expanded=(index == current_index)
    ):
        st.markdown(f"### {event.get('mission', 'Unknown')}")
        st.write(event.get("story", ""))

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric("Activity", event.get("activity_type", "Unknown"))

        with c2:
            st.metric("Event", event.get("event_type", "Unknown"))

        with c3:
            st.metric("Duration", f"{event.get('duration_minutes', 0)}m")

        with c4:
            st.metric("Distraction", str(event.get("is_distraction", False)))

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