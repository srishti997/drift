import time
import streamlit as st


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
    total = len(events)

    if "playback_index" not in st.session_state:
        st.session_state.playback_index = 0

    if "playback_running" not in st.session_state:
        st.session_state.playback_running = False

    if "playback_speed" not in st.session_state:
        st.session_state.playback_speed = 1

    current_index = min(st.session_state.playback_index, total - 1)
    current = events[current_index]

    render_summary(replay)
    render_stats(replay)
    render_controls(total, current_index)

    progress = int(((current_index + 1) / total) * 100)
    render_progress(current_index, total, progress)

    render_current_session(current)

    st.markdown("""
    <div style="margin-top:28px;">
        <div class="eyebrow">Full Timeline</div>
    </div>
    """, unsafe_allow_html=True)

    for index, event in enumerate(events):
        render_timeline_row(event, index, current_index)

    if st.session_state.playback_running:
        if current_index < total - 1:
            delay = 1.2 / st.session_state.playback_speed
            time.sleep(delay)
            st.session_state.playback_index = current_index + 1
            st.rerun()
        else:
            st.session_state.playback_running = False
            st.rerun()


def render_summary(replay):
    st.markdown(f"""
    <div class="card-cyan">
        <div class="eyebrow">Today's Story</div>
        <div style="font-size:15px;color:#CBD5E1;line-height:1.75;">
            {replay.get("summary", "No summary available.")}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats(replay):
    c1, c2, c3, c4 = st.columns(4)

    cards = [
        ("Total Time", f"{replay.get('total_minutes', 0)} min", "tracked"),
        ("Top Mission", replay.get("top_mission", "Unknown"), "dominant"),
        ("Focus Lost", replay.get("focus_lost_events", 0), "events"),
        ("Recovered", replay.get("recovery_events", 0), "events"),
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

    st.markdown(f"""
    <div style="
        background:{active_bg};
        border:1px solid {active_border};
        border-left:4px solid {color};
        border-radius:14px;
        padding:14px 18px;
        margin-bottom:10px;
    ">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <div style="font-size:12px;color:{color};font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px;">
                    {icon} {label}
                </div>
                <div style="font-size:16px;color:#E2E8F0;font-weight:700;">
                    {event.get("mission", "Unknown")}
                </div>
                <div style="font-size:13px;color:#64748B;margin-top:4px;">
                    {event.get("story", "")}
                </div>
            </div>
            <div style="text-align:right;font-family:'JetBrains Mono',monospace;color:#64748B;font-size:12px;">
                <div>{event.get("time", "—")}</div>
                <div>{event.get("duration_minutes", 0)} min</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def get_event_style(event_type):
    if event_type == "start":
        return "🚀", "Started", "#22D3EE"

    if event_type == "focus_lost":
        return "⚠️", "Focus Lost", "#F87171"

    if event_type == "recovered":
        return "✅", "Recovered", "#34D399"

    return "💻", "Focused", "#818CF8"