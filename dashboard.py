import csv
import hashlib
import io
import json
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from ui.replay_page import render_replay_page
from ui.history_page import history_page
from ui.chat_page import chat_page
from ui.goals_page import goals_page
from ui.components import (
    metric_card,
    recommendation_card,
    section_header,
)

API_BASE_URL = "http://127.0.0.1:8000"
USERS_FILE = "data/users.json"

# ── Auth ──────────────────────────────────────────────────────────────────────

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def load_users():
    os.makedirs("data", exist_ok=True)
    return json.load(open(USERS_FILE)) if os.path.exists(USERS_FILE) else {}

def save_users(u):
    os.makedirs("data", exist_ok=True)
    json.dump(u, open(USERS_FILE, "w"), indent=2)

def login_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True, users[username].get("name", username)
    return False, None

def signup_user(name, username, password):
    users = load_users()
    if username in users: return False, "Username already exists."
    users[username] = {"name": name, "password": hash_password(password), "joined": datetime.now().isoformat()}
    save_users(users)
    return True, "Account created."

# ── API ───────────────────────────────────────────────────────────────────────

def api(endpoint):
    try:
        r = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def api_alive():
    try: requests.get(f"{API_BASE_URL}/", timeout=2); return True
    except: return False

# ── Config ────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Drift", page_icon="🧠", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0}
html,body,[data-testid="stAppViewContainer"]{background:#070B12!important;font-family:'Inter',sans-serif;color:#E2E8F0}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse 70% 40% at 60% -5%,rgba(34,211,238,.07) 0%,transparent 60%),radial-gradient(ellipse 40% 30% at 5% 90%,rgba(99,102,241,.05) 0%,transparent 60%),#070B12!important}
[data-testid="stSidebar"]{background:rgba(7,11,18,.97)!important;border-right:1px solid rgba(34,211,238,.08)!important}
.block-container{padding:2rem 2.5rem 4rem!important;max-width:1400px}
.card{background:rgba(13,20,35,.75);border:1px solid rgba(148,163,184,.1);border-radius:18px;padding:24px;margin-bottom:18px;backdrop-filter:blur(10px)}
.card-cyan{background:rgba(13,20,35,.75);border:1px solid rgba(34,211,238,.18);border-radius:18px;padding:24px;margin-bottom:18px;backdrop-filter:blur(10px)}
.card-purple{background:rgba(13,20,35,.75);border:1px solid rgba(129,140,248,.2);border-radius:18px;padding:24px;margin-bottom:18px;backdrop-filter:blur(10px)}
.card-red{background:rgba(13,20,35,.75);border:1px solid rgba(248,113,113,.2);border-radius:18px;padding:24px;margin-bottom:18px;backdrop-filter:blur(10px)}
.eyebrow{font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#22D3EE;margin-bottom:14px}
.stat-tile{background:rgba(20,30,50,.7);border:1px solid rgba(148,163,184,.09);border-radius:14px;padding:18px 20px}
.stat-label{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#475569;margin-bottom:8px}
.stat-value{font-size:26px;font-weight:800;color:#F1F5F9;font-family:'JetBrains Mono',monospace;line-height:1}
.stat-sub{font-size:12px;color:#475569;margin-top:5px}
.score-big{font-size:68px;font-weight:900;color:#22D3EE;font-family:'JetBrains Mono',monospace;line-height:1;letter-spacing:-2px}
.grade-pill{display:inline-block;background:rgba(34,211,238,.12);border:1px solid rgba(34,211,238,.25);color:#22D3EE;font-size:12px;font-weight:700;padding:3px 12px;border-radius:100px;margin-top:8px;letter-spacing:.05em}
.bar-wrap{margin-bottom:14px}
.bar-row{display:flex;justify-content:space-between;font-size:12px;color:#64748B;margin-bottom:5px}
.bar-val{color:#CBD5E1;font-weight:600;font-family:'JetBrains Mono',monospace}
.bar-track{background:rgba(30,41,59,.9);border-radius:100px;height:6px;overflow:hidden}
.bar-fill{height:100%;border-radius:100px}
.drift-num{font-size:56px;font-weight:900;font-family:'JetBrains Mono',monospace;line-height:1;letter-spacing:-1px}
.dbadge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:100px;font-size:13px;font-weight:700;margin-top:10px}
.db-green{background:rgba(5,150,105,.12);border:1px solid rgba(5,150,105,.25);color:#34D399}
.db-yellow{background:rgba(217,119,6,.12);border:1px solid rgba(217,119,6,.25);color:#FBBF24}
.db-orange{background:rgba(234,88,12,.12);border:1px solid rgba(234,88,12,.25);color:#FB923C}
.db-red{background:rgba(185,28,28,.12);border:1px solid rgba(185,28,28,.25);color:#F87171}
.coach-card{background:rgba(6,35,55,.6);border-left:3px solid #22D3EE;border-radius:12px;padding:16px 18px;margin-bottom:12px}
.coach-lbl{font-size:9px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#22D3EE;margin-bottom:4px}
.coach-txt{font-size:13px;color:#94A3B8;line-height:1.6;margin-bottom:10px}
.sw-row{display:flex;justify-content:space-between;align-items:center;padding:11px 0;border-bottom:1px solid rgba(148,163,184,.06);font-size:13px;color:#64748B}
.sw-val{font-size:18px;font-weight:700;font-family:'JetBrains Mono',monospace}
.pat-row{padding:12px 0;border-bottom:1px solid rgba(148,163,184,.06)}
.pat-head{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.pat-name{font-size:13px;font-weight:600;color:#E2E8F0}
.pat-count{background:rgba(148,163,184,.1);border-radius:100px;padding:1px 8px;font-size:11px;color:#64748B}
.pat-desc{font-size:12px;color:#475569;padding-left:24px}
.dw-row{display:flex;align-items:center;gap:14px;padding:12px 0;border-bottom:1px solid rgba(148,163,184,.06)}
.dw-num{background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.15);border-radius:10px;padding:8px 14px;font-size:18px;font-weight:800;color:#22D3EE;font-family:'JetBrains Mono',monospace;min-width:52px;text-align:center}
.dw-intent{font-size:14px;font-weight:600;color:#E2E8F0}
.dw-meta{font-size:12px;color:#475569;margin-top:2px}
.dw-dur{font-size:20px;font-weight:800;color:#34D399;font-family:'JetBrains Mono',monospace}
.rec-item{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(148,163,184,.06);font-size:13px;color:#94A3B8;line-height:1.6}
.rec-arrow{color:#22D3EE;flex-shrink:0;margin-top:1px}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
.dot-green{background:#34D399;box-shadow:0 0 6px #34D399}
.dot-red{background:#F87171}
.risk-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:100px;font-size:12px;font-weight:700}
.risk-low{background:rgba(5,150,105,.12);border:1px solid rgba(5,150,105,.25);color:#34D399}
.risk-med{background:rgba(217,119,6,.12);border:1px solid rgba(217,119,6,.25);color:#FBBF24}
.risk-high{background:rgba(234,88,12,.12);border:1px solid rgba(234,88,12,.25);color:#FB923C}
.risk-crit{background:rgba(185,28,28,.12);border:1px solid rgba(185,28,28,.25);color:#F87171}
.loop-row{padding:10px 0;border-bottom:1px solid rgba(148,163,184,.06);font-size:13px;color:#94A3B8}
.loop-seq{font-size:12px;font-family:'JetBrains Mono',monospace;color:#818CF8;margin-top:3px}
.autopsy-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid rgba(148,163,184,.06);font-size:13px;color:#64748B}
.autopsy-val{font-weight:600;color:#E2E8F0;font-family:'JetBrains Mono',monospace}
.page-title{font-size:30px;font-weight:800;color:#F1F5F9;line-height:1.1;margin-bottom:4px}
.page-sub{font-size:14px;color:#475569;margin-bottom:20px}
[data-testid="stTextInput"] input{background:rgba(20,30,50,.9)!important;border:1px solid rgba(148,163,184,.12)!important;border-radius:10px!important;color:#E2E8F0!important;font-family:'Inter',sans-serif!important;font-size:14px!important}
[data-testid="stTextInput"] input:focus{border-color:rgba(34,211,238,.35)!important;box-shadow:0 0 0 3px rgba(34,211,238,.07)!important;outline:none!important}
[data-testid="stTextInput"] label{color:#64748B!important;font-size:12px!important;font-weight:600!important;letter-spacing:.04em!important;text-transform:uppercase!important}
.stButton>button{background:linear-gradient(135deg,#0E7490 0%,#22D3EE 100%)!important;color:#020617!important;font-weight:700!important;border:none!important;border-radius:10px!important;font-family:'Inter',sans-serif!important;font-size:13px!important;letter-spacing:.02em!important;transition:opacity .15s,transform .1s!important}
.stButton>button:hover{opacity:.85!important;transform:translateY(-1px)!important}
.stButton>button:active{transform:translateY(0)!important}
[data-testid="stSidebar"] .stButton>button{background:rgba(20,30,50,.6)!important;color:#94A3B8!important;border:1px solid rgba(148,163,184,.1)!important;font-weight:500!important}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(34,211,238,.07)!important;color:#E2E8F0!important;border-color:rgba(34,211,238,.15)!important;transform:none!important}
div[data-testid="stExpander"]{background:rgba(13,20,35,.5)!important;border:1px solid rgba(148,163,184,.08)!important;border-radius:12px!important}
div[data-testid="stExpander"] summary{color:#94A3B8!important;font-size:13px!important}
[data-testid="stAlert"]{border-radius:10px!important}
[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stSidebar"] *{color:#94A3B8!important}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────

SESSION_DEFAULTS = {
    "authenticated": False,
    "username": "",
    "display_name": "",
    "auth_tab": "login",
    "active_page": "Overview",
    "last_refresh": None,

    # Day 6 preferences
    "auto_refresh_enabled": True,
    "refresh_seconds": 30,
    "deep_work_goal": 240,
    "focus_score_goal": 80,
    "context_switch_goal": 40,
}

for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

MISSION_COLORS = {
    "Build Drift":"#22D3EE","Career Growth":"#818CF8","Skill Development":"#34D399",
    "Break / Distraction":"#F87171","Communication":"#FB923C","Unclassified Mission":"#64748B",
}

def mcolor(m): return MISSION_COLORS.get(m,"#94A3B8")

def empty(msg):
    st.markdown(f'<div style="color:#334155;padding:24px 0;text-align:center;font-size:13px;">{msg}</div>',
                unsafe_allow_html=True)
def build_daily_export_data():
    report = api("/daily-report") or {}
    score = api("/score") or {}
    drift = api("/drift") or {}
    deep_work = api("/deep-work") or {}
    recovery = api("/recovery-cost") or {}
    replay = api("/replay") or {}

    events = replay.get("events", [])

    focus_lost_events = sum(
        1
        for event in events
        if event.get("event_type") == "focus_lost"
    )

    recovered_events = sum(
        1
        for event in events
        if event.get("event_type") == "recovered"
    )

    return {
        "generated_at": datetime.now().isoformat(),
        "user": st.session_state.display_name,
        "summary": report.get("executive_summary", ""),
        "top_mission": report.get("top_mission", "Unknown"),
        "context_switches": report.get("context_switches", 0),
        "overall_score": score.get("overall_score", 0),
        "grade": score.get("grade", "N/A"),
        "focus_score": score.get("focus_score", 0),
        "mission_score": score.get("mission_score", 0),
        "recovery_score": score.get("recovery_score", 0),
        "switch_score": score.get("switch_score", 0),
        "productive_minutes": round(
            drift.get("productive_time", 0) / 60,
            2,
        ),
        "drift_index": drift.get("drift_index", 0),
        "deep_work_minutes": deep_work.get(
            "total_deep_work_minutes",
            0,
        ),
        "deep_work_sessions": deep_work.get(
            "count",
            len(deep_work.get("sessions", [])),
        ),
        "recovery_events": recovery.get("count", 0),
        "recovery_cost_minutes": round(
            recovery.get(
                "total_recovery_cost_seconds",
                0,
            ) / 60,
            2,
        ),
        "focus_lost_events": focus_lost_events,
        "recovered_events": recovered_events,
        "goals": {
            "deep_work_minutes": st.session_state.deep_work_goal,
            "focus_score": st.session_state.focus_score_goal,
            "maximum_context_switches": (
                st.session_state.context_switch_goal
            ),
        },
        "recommendations": report.get("recommendations", []),
        "events": events,
    }


def create_json_export(data):
    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )


def create_csv_export(data):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Metric", "Value"])

    excluded_fields = {
        "events",
        "recommendations",
        "goals",
    }

    for key, value in data.items():
        if key not in excluded_fields:
            writer.writerow([key, value])

    writer.writerow([])
    writer.writerow(["Goal", "Target"])

    for goal, target in data.get("goals", {}).items():
        writer.writerow([goal, target])

    writer.writerow([])
    writer.writerow(["Recommendation"])

    for recommendation in data.get("recommendations", []):
        writer.writerow([recommendation])

    writer.writerow([])
    writer.writerow(
        [
            "Block",
            "Activity",
            "Mission",
            "Event",
            "Duration Minutes",
            "Distraction",
        ]
    )

    for event in data.get("events", []):
        writer.writerow(
            [
                event.get("time", ""),
                event.get("activity_type", ""),
                event.get("mission", ""),
                event.get("event_type", ""),
                event.get("duration_minutes", 0),
                event.get("is_distraction", False),
            ]
        )

    return output.getvalue()
# ── Auth Page ─────────────────────────────────────────────────────────────────

def render_auth():
    st.markdown("""
    <div style="text-align:center;padding-top:50px;margin-bottom:36px;">
        <div style="font-size:40px;font-weight:900;color:#22D3EE;font-family:'JetBrains Mono',monospace;letter-spacing:-1px;">drift</div>
        <div style="font-size:14px;color:#334155;margin-top:8px;">Human observability for your workday</div>
    </div>""", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Sign In", use_container_width=True,
                         type="primary" if st.session_state.auth_tab=="login" else "secondary"):
                st.session_state.auth_tab = "login"; st.rerun()
        with c2:
            if st.button("Create Account", use_container_width=True,
                         type="primary" if st.session_state.auth_tab=="signup" else "secondary"):
                st.session_state.auth_tab = "signup"; st.rerun()
        st.write("")
        if st.session_state.auth_tab == "login":
            u = st.text_input("Username", placeholder="your_username", key="li_u")
            p = st.text_input("Password", placeholder="••••••••", type="password", key="li_p")
            st.write("")
            if st.button("Sign In →", use_container_width=True):
                if u and p:
                    ok, name = login_user(u, p)
                    if ok:
                        st.session_state.update({"authenticated":True,"username":u,
                                                  "display_name":name,"last_refresh":datetime.now()})
                        st.rerun()
                    else: st.error("Incorrect username or password.")
                else: st.warning("Please fill in all fields.")
        else:
            n = st.text_input("Full Name", placeholder="Srishti Gupta", key="su_n")
            u = st.text_input("Username", placeholder="srishti997", key="su_u")
            p = st.text_input("Password", placeholder="••••••••", type="password", key="su_p")
            st.write("")
            if st.button("Create Account →", use_container_width=True):
                if n and u and p:
                    ok, msg = signup_user(n, u, p)
                    if ok:
                        st.success("Account created. Sign in to continue.")
                        st.session_state.auth_tab = "login"; st.rerun()
                    else: st.error(msg)
                else: st.warning("Please fill in all fields.")
        st.markdown('<div style="text-align:center;margin-top:24px;color:#1E293B;font-size:11px;">Credentials stored locally · No external servers</div>',
                    unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar(alive):
    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 6px 20px;">
            <div style="font-size:24px;font-weight:900;color:#22D3EE;font-family:'JetBrains Mono',monospace;letter-spacing:-.5px;">drift</div>
            <div style="font-size:11px;color:#1E293B;margin-top:2px;">Human Observability</div>
        </div>
        <div style="border-top:1px solid rgba(148,163,184,.07);margin-bottom:14px;"></div>""",
        unsafe_allow_html=True)

        dot = "dot-green" if alive else "dot-red"
        stxt = "Tracker connected" if alive else "Tracker offline"
        sc = "#34D399" if alive else "#F87171"
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:8px 10px;background:rgba(20,30,50,.5);border-radius:10px;margin-bottom:14px;">
            <span class="status-dot {dot}"></span>
            <span style="font-size:11px;color:{sc};">{stxt}</span>
        </div>""", unsafe_allow_html=True)

        pages = [
            ("🧠", "Overview"),
            ("🔬", "Deep Dive"),
            ("🔮", "Intelligence"),
            ("📈", "History"),
            ("💬", "AI Coach"),
            ("🎬", "Replay"),
            ("📋", "Daily Report"),
            ("🎯", "Goals"),
        ]
        for icon, label in pages:
            active = st.session_state.active_page == label
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.active_page = label; st.rerun()

        st.markdown("<div style='border-top:1px solid rgba(148,163,184,.07);margin:16px 0;'></div>",
                    unsafe_allow_html=True)

        if st.button("↻  Refresh Now", use_container_width=True, key="rfbtn"):
            st.session_state.last_refresh = datetime.now(); st.rerun()

        if st.session_state.last_refresh:
            ts = st.session_state.last_refresh.strftime("%H:%M:%S")

            refresh_text = (
                f"Auto-refreshes every "
                f"{st.session_state.refresh_seconds}s"
                if st.session_state.auto_refresh_enabled
                else "Auto-refresh disabled"
            )

            st.markdown(
                f"""
<div style="font-size:10px;color:#334155;text-align:center;margin-top:4px;">
{refresh_text} · {ts}
</div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("⚙️ Settings", expanded=False):
            auto_refresh = st.toggle(
                "Auto refresh",
                value=st.session_state.auto_refresh_enabled,
                key="settings_auto_refresh",
            )

            refresh_options = [15, 30, 60, 120]
            current_refresh = st.session_state.refresh_seconds

            if current_refresh not in refresh_options:
                current_refresh = 30

            refresh_seconds = st.selectbox(
                "Refresh interval",
                options=refresh_options,
                index=refresh_options.index(current_refresh),
                format_func=lambda value: f"{value} seconds",
                disabled=not auto_refresh,
                key="settings_refresh_seconds",
            )

            st.markdown("##### Personal goals")

            deep_work_goal = st.number_input(
                "Deep-work goal (minutes)",
                min_value=15,
                max_value=720,
                value=int(st.session_state.deep_work_goal),
                step=15,
                key="settings_deep_work_goal",
            )

            focus_score_goal = st.number_input(
                "Focus-score goal",
                min_value=1,
                max_value=100,
                value=int(st.session_state.focus_score_goal),
                step=5,
                key="settings_focus_goal",
            )

            context_switch_goal = st.number_input(
                "Maximum context switches",
                min_value=1,
                max_value=1000,
                value=int(st.session_state.context_switch_goal),
                step=5,
                key="settings_switch_goal",
            )

            if st.button(
                "Save Settings",
                use_container_width=True,
                key="save_dashboard_settings",
            ):
                st.session_state.auto_refresh_enabled = auto_refresh
                st.session_state.refresh_seconds = refresh_seconds
                st.session_state.deep_work_goal = deep_work_goal
                st.session_state.focus_score_goal = focus_score_goal
                st.session_state.context_switch_goal = (
                    context_switch_goal
                )

                st.session_state.last_refresh = datetime.now()
                st.success("Settings saved.")
                st.rerun()

        with st.expander("⬇ Export Report", expanded=False):
            if st.button(
                "Prepare report",
                use_container_width=True,
                key="prepare_export",
            ):
                st.session_state.export_data = (
                    build_daily_export_data()
                )

            export_data = st.session_state.get("export_data")

            if export_data:
                date_value = datetime.now().strftime("%Y-%m-%d")

                st.download_button(
                    label="Download JSON",
                    data=create_json_export(export_data),
                    file_name=f"drift-report-{date_value}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_json_report",
                )

                st.download_button(
                    label="Download CSV",
                    data=create_csv_export(export_data),
                    file_name=f"drift-report-{date_value}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_csv_report",
                )

        st.markdown("<div style='border-top:1px solid rgba(148,163,184,.07);margin:16px 0 10px;'></div>",
                    unsafe_allow_html=True)
        st.markdown(f"""<div style="font-size:11px;color:#334155;padding:0 4px;">Signed in as<br>
            <span style="color:#CBD5E1;font-weight:600;">{st.session_state.display_name}</span></div>""",
            unsafe_allow_html=True)
        st.write("")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.update({"authenticated":False,"username":"","display_name":"","last_refresh":None})
            st.rerun()

# ── Page 1: Overview ──────────────────────────────────────────────────────────
def render_overview():
    score = api("/score") or {}
    missions = api("/missions") or {}
    deep_work = api("/deep-work") or {}
    report = api("/daily-report") or {}
    drift = api("/drift") or {}
    coach = api("/coach") or {}

    # -----------------------------
    # Helpers
    # -----------------------------
    def safe_int(value, default=0):
        try:
            return int(float(value or default))
        except (TypeError, ValueError):
            return default

    def format_time(minutes):
        minutes = max(0, safe_int(minutes))

        if minutes < 60:
            return f"{minutes} min"

        hours = minutes // 60
        remaining = minutes % 60

        if remaining == 0:
            return f"{hours} hr"

        return f"{hours} hr {remaining} min"

    # -----------------------------
    # Read API data
    # -----------------------------
    overall = safe_int(score.get("overall_score"))
    overall = max(0, min(100, overall))

    grade = score.get("grade", "N/A")
    focus_score = safe_int(score.get("focus_score"))
    recovery_score = safe_int(score.get("recovery_score"))
    mission_score = safe_int(score.get("mission_score"))
    switch_score = safe_int(score.get("switch_score"))

    deep_minutes = safe_int(
        deep_work.get("total_deep_work_minutes")
    )
    deep_sessions = safe_int(deep_work.get("count"))

    context_switches = safe_int(
        report.get("context_switches")
    )

    top_mission = (
        report.get("top_mission")
        or "No main activity yet"
    )

    productive_seconds = safe_int(
        drift.get("productive_time")
    )

    productive_minutes = productive_seconds // 60

    tracked_seconds = safe_int(
        drift.get("total_time")
        or drift.get("tracked_time")
        or report.get("tracked_time")
        or report.get("total_time")
    )

    if tracked_seconds > 0:
        productive_ratio = round(
            (productive_seconds / tracked_seconds) * 100
        )
    else:
        productive_ratio = safe_int(
            drift.get("focus_score")
        )

    productive_ratio = max(
        0,
        min(100, productive_ratio),
    )

    # -----------------------------
    # User and greeting
    # -----------------------------
    display_name = st.session_state.get(
        "display_name",
        "",
    )

    first_name = (
        display_name.split()[0]
        if display_name
        else "there"
    )

    hour = datetime.now().hour

    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # -----------------------------
    # Friendly daily story
    # -----------------------------
    if productive_minutes == 0:
        day_icon = "🌱"
        day_title = "Your focus story starts here"
        day_message = (
            "Start the tracker and work normally. Drift will show "
            "where your time went and what affected your concentration."
        )
        status = "Waiting for activity"

    elif overall >= 80:
        day_icon = "🏆"
        day_title = "You protected your focus well today"
        day_message = (
            "You maintained strong attention and completed meaningful "
            "work with relatively few interruptions."
        )
        status = "Excellent focus"

    elif overall >= 60:
        day_icon = "✨"
        day_title = "You made solid progress today"
        day_message = (
            "You completed useful work and maintained a healthy rhythm, "
            "with a few moments of distraction."
        )
        status = "Good progress"

    elif overall >= 40:
        day_icon = "🌤️"
        day_title = "Your focus had a few interruptions"
        day_message = (
            "You still moved important work forward. Drift found a few "
            "patterns that may help your next session feel smoother."
        )
        status = "Mixed focus"

    else:
        day_icon = "💛"
        day_title = "Your attention was interrupted more than usual"
        day_message = (
            "You still completed focused work. Drift can help you reduce "
            "friction and recover more quickly in your next session."
        )
        status = "Room to improve"

    productive_time = format_time(
        productive_minutes
    )

    deep_time = format_time(
        deep_minutes
    )

    # -----------------------------
    # Next best action
    # -----------------------------
    if productive_minutes == 0:
        next_action = (
            "Start the tracker and complete one 25-minute focus session."
        )
    elif context_switches > 100:
        next_action = (
            "Close unused tabs and keep only your main work app open "
            "for the next 25 minutes."
        )
    elif deep_minutes < 30:
        next_action = (
            "Block one uninterrupted 30-minute focus session next."
        )
    elif recovery_score < 50:
        next_action = (
            "After your next interruption, return immediately to one "
            "small, clearly defined task."
        )
    elif focus_score < 60:
        next_action = (
            "Mute notifications and protect your next work block."
        )
    else:
        next_action = (
            "Keep your current rhythm and protect your next focus block."
        )

    # -----------------------------
    # AI coach data
    # -----------------------------
    advice = coach.get("advice", []) if coach else []

    if advice:
        coach_item = advice[0]

        coach_observation = coach_item.get(
            "observation",
            "Your activity has been analysed.",
        )

        coach_impact = coach_item.get(
            "impact",
            "",
        )

        coach_suggestion = coach_item.get(
            "suggestion",
            next_action,
        )
    else:
        coach_observation = (
            "Drift needs a little more activity to understand your pattern."
        )
        coach_impact = ""
        coach_suggestion = next_action

    # -----------------------------
    # Header
    # -----------------------------
    st.caption(
        f"{greeting}, {first_name} 👋"
    )

    # -----------------------------
    # Hero section
    # -----------------------------
    with st.container(border=True):
        hero_left, hero_right = st.columns(
            [3, 1],
            gap="large",
        )

        with hero_left:
            st.markdown(
                f"## {day_icon} {day_title}"
            )

            st.write(day_message)

            st.markdown(
                f"### You completed **{productive_time}** "
                "of focused work today."
            )

            if (
                top_mission
                and top_mission
                not in {
                    "No main activity yet",
                    "—",
                }
            ):
                st.caption(
                    f"Most of your attention went toward "
                    f"**{top_mission}**."
                )
            else:
                st.caption(
                    "Your main activity will appear after "
                    "Drift records more work."
                )

        with hero_right:
            st.metric(
                label="Today's focus",
                value=f"{overall}/100",
            )

            st.caption(
                f"{status} · Grade {grade}"
            )

    st.info(
        f"🎯 **Your next step:** {next_action}"
    )

    st.write("")

    # -----------------------------
    # Snapshot
    # -----------------------------
    st.subheader("Today at a glance")

    st.caption(
        "The three numbers that best explain how your day went."
    )

    snapshot_1, snapshot_2, snapshot_3 = st.columns(
        3,
        gap="medium",
    )

    with snapshot_1:
        with st.container(border=True):
            st.markdown("### 🎯 Focused work")

            st.metric(
                label="Time",
                value=productive_time,
            )

            if tracked_seconds > 0:
                st.caption(
                    f"{productive_ratio}% of your tracked time "
                    "was focused work."
                )
            else:
                st.caption(
                    "Drift will calculate your focus percentage "
                    "after more activity is recorded."
                )

    with snapshot_2:
        with st.container(border=True):
            st.markdown("### 🔥 Deep focus")

            st.metric(
                label="Time",
                value=deep_time,
            )

            session_word = (
                "session"
                if deep_sessions == 1
                else "sessions"
            )

            st.caption(
                f"{deep_sessions} uninterrupted {session_word} completed."
            )

    with snapshot_3:
        with st.container(border=True):
            st.markdown("### 🔄 Attention changes")

            st.metric(
                label="Detected changes",
                value=context_switches,
            )

            if context_switches > 100:
                st.caption(
                    "This includes changes between apps, windows, "
                    "or browser contexts. A very high value may indicate "
                    "frequent title or tab changes."
                )
            else:
                st.caption(
                    "Fewer unnecessary changes usually make it easier "
                    "to maintain concentration."
                )

    st.write("")

    # -----------------------------
    # Explanation and coach
    # -----------------------------
    explanation_col, coach_col = st.columns(
        [1.1, 1],
        gap="medium",
    )

    with explanation_col:
        with st.container(border=True):
            st.subheader("How your focus felt")

            st.markdown(
                f"### {day_title}"
            )

            st.write(day_message)

            focus_col, recovery_col = st.columns(2)

            with focus_col:
                st.metric(
                    label="Focus consistency",
                    value=f"{focus_score}/100",
                )

            with recovery_col:
                st.metric(
                    label="Recovery ability",
                    value=f"{recovery_score}/100",
                )

            with st.expander(
                "How are these scores calculated?"
            ):
                st.write(
                    "**Focus consistency** reflects how steadily you "
                    "stayed on productive activities."
                )

                st.write(
                    "**Recovery ability** reflects how effectively you "
                    "returned to useful work after an interruption."
                )

                st.write(
                    "**Mission alignment** reflects how much of your time "
                    "supported your primary task."
                )

                st.write(
                    "**Switch control** reflects how well you limited "
                    "unnecessary changes between activities."
                )

                breakdown_1, breakdown_2 = st.columns(2)

                with breakdown_1:
                    st.metric(
                        "Mission alignment",
                        f"{mission_score}/100",
                    )

                with breakdown_2:
                    st.metric(
                        "Switch control",
                        f"{switch_score}/100",
                    )

    with coach_col:
        with st.container(border=True):
            st.subheader("🤖 Drift says")

            st.markdown(
                f"### {coach_observation}"
            )

            if coach_impact:
                st.write(coach_impact)

            st.success(
                f"💡 {coach_suggestion}"
            )

            with st.expander(
                "Questions you can ask Drift"
            ):
                st.write(
                    "• What distracted me today?"
                )
                st.write(
                    "• When was I most focused?"
                )
                st.write(
                    "• What should I improve tomorrow?"
                )

    st.write("")

    # -----------------------------
    # Goals
    # -----------------------------
    st.subheader("Your goals")

    st.caption(
        "A simple view of what is currently on track."
    )

    deep_goal = safe_int(
        st.session_state.get(
            "deep_work_goal",
            180,
        ),
        180,
    )

    focus_goal = safe_int(
        st.session_state.get(
            "focus_score_goal",
            80,
        ),
        80,
    )

    switch_goal = safe_int(
        st.session_state.get(
            "context_switch_goal",
            20,
        ),
        20,
    )

    deep_progress = (
        min(
            100,
            round(
                (deep_minutes / deep_goal) * 100
            ),
        )
        if deep_goal > 0
        else 0
    )

    focus_progress = (
        min(
            100,
            round(
                (focus_score / focus_goal) * 100
            ),
        )
        if focus_goal > 0
        else 0
    )

    if context_switches == 0:
        switch_progress = 0
    elif context_switches <= switch_goal:
        switch_progress = 100
    else:
        switch_progress = max(
            0,
            round(
                (switch_goal / context_switches) * 100
            ),
        )

    goal_1, goal_2, goal_3 = st.columns(
        3,
        gap="medium",
    )

    with goal_1:
        with st.container(border=True):
            st.markdown("### Deep focus")

            st.write(
                f"**{deep_time}** of "
                f"**{format_time(deep_goal)}**"
            )

            st.progress(
                deep_progress / 100
            )

            if deep_progress >= 100:
                st.caption(
                    "Goal completed 🎉"
                )
            else:
                remaining = max(
                    0,
                    deep_goal - deep_minutes,
                )

                st.caption(
                    f"{format_time(remaining)} remaining"
                )

    with goal_2:
        with st.container(border=True):
            st.markdown("### Focus score")

            st.write(
                f"**{focus_score}** of "
                f"**{focus_goal}**"
            )

            st.progress(
                focus_progress / 100
            )

            if focus_progress >= 100:
                st.caption(
                    "Goal completed 🎉"
                )
            else:
                remaining = max(
                    0,
                    focus_goal - focus_score,
                )

                st.caption(
                    f"{remaining} points remaining"
                )

    with goal_3:
        with st.container(border=True):
            st.markdown("### Attention changes")

            st.write(
                f"**{context_switches}** detected"
            )

            st.progress(
                switch_progress / 100
            )

            if context_switches == 0:
                st.caption(
                    "No activity recorded yet"
                )
            elif context_switches <= switch_goal:
                st.caption(
                    f"Within your limit of {switch_goal}"
                )
            else:
                difference = (
                    context_switches - switch_goal
                )

                st.caption(
                    f"{difference} above your current limit"
                )

    st.write("")

    # -----------------------------
    # Mission distribution
    # -----------------------------
    st.subheader("Where your time went")

    st.caption(
        "Your main activities, translated into a simple breakdown."
    )

    mission_items = (
        missions.get("missions", [])
        if missions
        else []
    )

    valid_missions = [
        item
        for item in mission_items
        if safe_int(
            item.get("time_seconds")
        ) > 0
    ]

    if valid_missions:
        total_mission_time = sum(
            safe_int(
                item.get("time_seconds")
            )
            for item in valid_missions
        ) or 1

        sorted_missions = sorted(
            valid_missions,
            key=lambda item: safe_int(
                item.get("time_seconds")
            ),
            reverse=True,
        )[:5]

        with st.container(border=True):
            for index, item in enumerate(
                sorted_missions
            ):
                mission = (
                    item.get("mission")
                    or "Other activity"
                )

                seconds = safe_int(
                    item.get("time_seconds")
                )

                minutes = round(
                    seconds / 60
                )

                percentage = round(
                    (seconds / total_mission_time)
                    * 100
                )

                label_col, value_col = st.columns(
                    [3, 1]
                )

                with label_col:
                    st.markdown(
                        f"**{mission}**"
                    )

                with value_col:
                    st.markdown(
                        f"**{minutes} min · "
                        f"{percentage}%**"
                    )

                st.progress(
                    percentage / 100
                )

                if index < len(
                    sorted_missions
                ) - 1:
                    st.divider()

        unclassified = next(
            (
                item
                for item in sorted_missions
                if "unclassified"
                in str(
                    item.get("mission", "")
                ).lower()
            ),
            None,
        )

        if unclassified:
            st.warning(
                "A large amount of time is currently unclassified. "
                "Improving app and window classification will make "
                "your insights more meaningful."
            )

    else:
        with st.container(border=True):
            st.markdown(
                "### No activity breakdown yet"
            )

            st.write(
                "Start the tracker and work for a few minutes. "
                "Drift will automatically organise your activity "
                "into meaningful categories."
            )

            st.info(
                "Drift can identify focused work, interruptions, "
                "idle time, and your main activity."
            )
# ── Page 2: Deep Dive ─────────────────────────────────────────────────────────

def render_deep_dive():
    timeline = api("/timeline") or {}
    deep_work = api("/deep-work") or {}
    switches = api("/context-switches") or {}
    patterns = api("/patterns") or {}
    recovery = api("/recovery-cost") or {}
    replay = api("/replay") or {}
    missions = api("/missions") or {}

    def safe_int(value, default=0):
        try:
            return int(float(value or default))
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value or default)
        except (TypeError, ValueError):
            return default

    def format_time(minutes):
        minutes = max(0, safe_int(minutes))

        if minutes < 60:
            return f"{minutes} min"

        hours = minutes // 60
        remaining = minutes % 60

        if remaining == 0:
            return f"{hours} hr"

        return f"{hours} hr {remaining} min"

    # ------------------------------------------------------------------
    # Read API data
    # ------------------------------------------------------------------

    deep_minutes = safe_int(
        deep_work.get("total_deep_work_minutes")
    )

    deep_sessions = safe_int(
        deep_work.get(
            "count",
            len(deep_work.get("sessions", [])),
        )
    )

    deep_goal = safe_int(
        st.session_state.get(
            "deep_work_goal",
            240,
        ),
        240,
    )

    deep_progress = (
        min(deep_minutes / deep_goal, 1.0)
        if deep_goal > 0
        else 0.0
    )

    total_switches = safe_int(
        switches.get("total_switches")
    )

    distraction_switches = safe_int(
        switches.get("distraction_switches")
    )

    ignored_micro_switches = safe_int(
        switches.get("ignored_micro_switches")
    )

    focus_loss_minutes = round(
        safe_float(
            switches.get("estimated_focus_loss_seconds")
        )
        / 60,
        1,
    )

    recovery_events = safe_int(
        recovery.get("count")
    )

    total_recovery_cost = round(
        safe_float(
            recovery.get("total_recovery_cost_seconds")
        )
        / 60,
        1,
    )

    average_recovery_cost = round(
        safe_float(
            recovery.get("average_recovery_cost_seconds")
        )
        / 60,
        1,
    )

    recovery_insight = recovery.get(
        "insight",
        "No recovery insight is available yet.",
    )

    mission_items = missions.get(
        "missions",
        [],
    )

    replay_events = replay.get(
        "events",
        [],
    )

    timeline_items = timeline.get(
        "timeline",
        [],
    )

    pattern_items = patterns.get(
        "patterns",
        [],
    )

    switch_insight = switches.get(
        "insight",
        "Drift needs more activity before it can analyse your attention.",
    )

    # ------------------------------------------------------------------
    # Page header
    # ------------------------------------------------------------------

    section_header(
        title="What actually happened",
        description=(
            "A detailed view of your focus blocks, attention changes, "
            "recovery behaviour, and work patterns."
        ),
        eyebrow="Deep dive",
    )

    # ------------------------------------------------------------------
    # Summary metrics
    # ------------------------------------------------------------------

    summary_1, summary_2, summary_3, summary_4 = st.columns(
        4,
        gap="medium",
    )

    with summary_1:
        metric_card(
            icon="🔥",
            title="Deep work",
            value=format_time(deep_minutes),
            subtitle=(
                f"{deep_sessions} uninterrupted "
                f"{'session' if deep_sessions == 1 else 'sessions'}."
            ),
            badge="Today",
        )

    with summary_2:
        if total_switches <= 20:
            switch_trend = "Stable attention rhythm"
            switch_type = "positive"
        elif total_switches <= 40:
            switch_trend = "Some fragmentation"
            switch_type = "neutral"
        else:
            switch_trend = "Frequent context changes"
            switch_type = "negative"

        metric_card(
            icon="🔄",
            title="Attention changes",
            value=str(total_switches),
            subtitle=(
                "Only sustained context changes are counted."
            ),
            trend=switch_trend,
            trend_type=switch_type,
            badge="Detected",
        )

    with summary_3:
        metric_card(
            icon="⚠️",
            title="Distraction switches",
            value=str(distraction_switches),
            subtitle=(
                "Transitions from productive work into distraction or idle time."
            ),
            trend=(
                "Low distraction impact"
                if distraction_switches <= 2
                else "Focus interruptions detected"
            ),
            trend_type=(
                "positive"
                if distraction_switches <= 2
                else "negative"
            ),
            badge="Focus",
        )

    with summary_4:
        metric_card(
            icon="⏳",
            title="Estimated focus loss",
            value=f"{focus_loss_minutes} min",
            subtitle=(
                f"{ignored_micro_switches} brief changes were ignored."
            ),
            badge="Estimate",
        )

    # ------------------------------------------------------------------
    # Deep-work progress and switch story
    # ------------------------------------------------------------------

    section_header(
        title="Focus quality",
        description=(
            "Understand how much uninterrupted work you completed "
            "and what broke your concentration."
        ),
        eyebrow="Attention analysis",
    )

    focus_col, switch_col = st.columns(
        [1, 1],
        gap="medium",
    )

    with focus_col:
        with st.container(border=True):
            st.markdown("### 🔥 Today's deep work")

            st.markdown(
                f"## {format_time(deep_minutes)}"
            )

            st.caption(
                f"Daily target: {format_time(deep_goal)}"
            )

            st.progress(deep_progress)

            if deep_progress >= 1:
                st.success(
                    "You completed your deep-work goal 🎉"
                )
            elif deep_minutes == 0:
                st.info(
                    "No uninterrupted deep-work session has been detected yet."
                )
            else:
                remaining = max(
                    0,
                    deep_goal - deep_minutes,
                )

                st.caption(
                    f"{format_time(remaining)} remaining"
                )

            sessions = deep_work.get(
                "sessions",
                [],
            )

            if sessions:
                with st.expander(
                    "View deep-work sessions"
                ):
                    for index, session in enumerate(
                        sessions[:10],
                        start=1,
                    ):
                        duration_seconds = safe_int(
                            session.get("duration_seconds")
                        )

                        duration_minutes = round(
                            duration_seconds / 60,
                            1,
                        )

                        intent = (
                            session.get("dominant_intent")
                            or session.get("intent")
                            or "Focused work"
                        )

                        apps = session.get(
                            "apps",
                            {},
                        )

                        app_names = (
                            ", ".join(
                                list(apps.keys())[:3]
                            )
                            if isinstance(apps, dict)
                            else ""
                        )

                        st.markdown(
                            f"**Session {index}: {intent}**"
                        )

                        st.caption(
                            f"{duration_minutes} min"
                            + (
                                f" · {app_names}"
                                if app_names
                                else ""
                            )
                        )

                        if index < len(sessions[:10]):
                            st.divider()

    with switch_col:
        with st.container(border=True):
            st.markdown("### 🔄 Attention-change analysis")

            switch_1, switch_2 = st.columns(2)

            with switch_1:
                st.metric(
                    "Meaningful switches",
                    total_switches,
                )

            with switch_2:
                st.metric(
                    "Distractions",
                    distraction_switches,
                )

            st.write(switch_insight)

            if ignored_micro_switches > 0:
                st.caption(
                    f"Drift ignored {ignored_micro_switches} "
                    "brief tab or application changes."
                )

            switch_list = switches.get(
                "switches",
                [],
            )

            if switch_list:
                with st.expander(
                    "View recent attention changes"
                ):
                    for index, switch in enumerate(
                        switch_list[-8:],
                        start=1,
                    ):
                        from_goal = switch.get(
                            "from_goal",
                            "Unknown",
                        )

                        to_goal = switch.get(
                            "to_goal",
                            "Unknown",
                        )

                        is_distraction = switch.get(
                            "is_distraction",
                            False,
                        )

                        icon = (
                            "⚠️"
                            if is_distraction
                            else "➡️"
                        )

                        st.markdown(
                            f"{icon} **{from_goal} → {to_goal}**"
                        )

                        from_app = switch.get(
                            "from_app",
                            "",
                        )

                        to_app = switch.get(
                            "to_app",
                            "",
                        )

                        if from_app or to_app:
                            st.caption(
                                f"{from_app or 'Unknown app'} → "
                                f"{to_app or 'Unknown app'}"
                            )

                        if index < len(switch_list[-8:]):
                            st.divider()

    # ------------------------------------------------------------------
    # Mission distribution
    # ------------------------------------------------------------------

    section_header(
        title="Where your effort went",
        description=(
            "A breakdown of the missions Drift detected throughout your day."
        ),
        eyebrow="Mission analytics",
    )

    mission_col, heatmap_col = st.columns(
        [1.1, 1],
        gap="medium",
    )

    with mission_col:
        with st.container(border=True):
            st.markdown("### Mission distribution")

            valid_missions = [
                item
                for item in mission_items
                if safe_int(
                    item.get("time_seconds")
                ) > 0
            ]

            if valid_missions:
                total_mission_seconds = sum(
                    safe_int(
                        item.get("time_seconds")
                    )
                    for item in valid_missions
                ) or 1

                sorted_missions = sorted(
                    valid_missions,
                    key=lambda item: safe_int(
                        item.get("time_seconds")
                    ),
                    reverse=True,
                )[:7]

                for index, item in enumerate(
                    sorted_missions
                ):
                    mission_name = (
                        item.get("mission")
                        or "Other activity"
                    )

                    mission_seconds = safe_int(
                        item.get("time_seconds")
                    )

                    mission_minutes = round(
                        mission_seconds / 60,
                        1,
                    )

                    mission_percentage = round(
                        mission_seconds
                        / total_mission_seconds
                        * 100
                    )

                    label_col, value_col = st.columns(
                        [3, 1]
                    )

                    with label_col:
                        st.markdown(
                            f"**{mission_name}**"
                        )

                    with value_col:
                        st.markdown(
                            f"**{mission_minutes} min**"
                        )

                    st.progress(
                        mission_percentage / 100
                    )

                    st.caption(
                        f"{mission_percentage}% of classified activity"
                    )

                    if index < len(
                        sorted_missions
                    ) - 1:
                        st.divider()

            else:
                st.info(
                    "No mission analytics are available yet."
                )

    with heatmap_col:
        with st.container(border=True):
            st.markdown("### Daily focus map")

            if replay_events:
                legend = {
                    "start": ("🚀", "Started"),
                    "focused": ("💻", "Focused"),
                    "recovered": ("✅", "Recovered"),
                    "focus_lost": ("⚠️", "Focus lost"),
                }

                displayed_events = replay_events[:40]

                for index, event in enumerate(
                    displayed_events,
                    start=1,
                ):
                    event_type = event.get(
                        "event_type",
                        "focused",
                    )

                    icon, label = legend.get(
                        event_type,
                        ("•", "Activity"),
                    )

                    mission = event.get(
                        "mission",
                        "Unknown",
                    )

                    duration = event.get(
                        "duration_minutes",
                        0,
                    )

                    time_value = event.get(
                        "time",
                        "",
                    )

                    st.markdown(
                        f"{icon} **{label} · {mission}**"
                    )

                    details = []

                    if time_value:
                        details.append(str(time_value))

                    if duration:
                        details.append(
                            f"{duration} min"
                        )

                    if details:
                        st.caption(
                            " · ".join(details)
                        )

                    if index < len(displayed_events):
                        st.divider()

                if len(replay_events) > 40:
                    st.caption(
                        f"Showing the first 40 of "
                        f"{len(replay_events)} events."
                    )

            else:
                st.info(
                    "No focus timeline data is available yet."
                )

    # ------------------------------------------------------------------
    # Behaviour and recovery
    # ------------------------------------------------------------------

    section_header(
        title="Behaviour and recovery",
        description=(
            "See repeated patterns and understand the cost of returning "
            "to focused work after an interruption."
        ),
        eyebrow="Behaviour intelligence",
    )

    behaviour_col, recovery_col = st.columns(
        2,
        gap="medium",
    )

    with behaviour_col:
        with st.container(border=True):
            st.markdown("### 🧠 Behavioural patterns")

            icons = {
                "Mission Abandonment": "⚠️",
                "Mission Recovery": "✅",
                "App Ping-Pong": "🔁",
                "Deep Work": "🔥",
            }

            if pattern_items:
                for index, pattern in enumerate(
                    pattern_items
                ):
                    pattern_type = pattern.get(
                        "type",
                        "Pattern",
                    )

                    pattern_count = safe_int(
                        pattern.get("count")
                    )

                    description = pattern.get(
                        "description",
                        "",
                    )

                    icon = icons.get(
                        pattern_type,
                        "◆",
                    )

                    st.markdown(
                        f"#### {icon} {pattern_type}"
                    )

                    st.caption(
                        f"Detected {pattern_count} "
                        f"{'time' if pattern_count == 1 else 'times'}"
                    )

                    if description:
                        st.write(description)

                    if index < len(pattern_items) - 1:
                        st.divider()

                pattern_insight = patterns.get(
                    "insight"
                )

                if pattern_insight:
                    st.info(pattern_insight)

            else:
                st.info(
                    "No repeated behavioural patterns have been detected yet."
                )

    with recovery_col:
        with st.container(border=True):
            st.markdown("### ♻️ Recovery cost")

            recovery_1, recovery_2, recovery_3 = st.columns(
                3
            )

            with recovery_1:
                st.metric(
                    "Events",
                    recovery_events,
                )

            with recovery_2:
                st.metric(
                    "Total cost",
                    f"{total_recovery_cost} min",
                )

            with recovery_3:
                st.metric(
                    "Average",
                    f"{average_recovery_cost} min",
                )

            st.write(recovery_insight)

            if recovery_events == 0:
                st.info(
                    "No recovery events have been detected yet."
                )
            elif average_recovery_cost <= 2:
                st.success(
                    "You usually return to focused work quickly."
                )
            elif average_recovery_cost <= 5:
                st.warning(
                    "Your recovery time is moderate. Clear next actions "
                    "may help you return faster."
                )
            else:
                st.error(
                    "Interruptions are creating a noticeable recovery cost."
                )

    # ------------------------------------------------------------------
    # Cognitive timeline
    # ------------------------------------------------------------------

    section_header(
        title="Cognitive timeline",
        description=(
            "Expand each block to see the goals and applications "
            "that shaped that period."
        ),
        eyebrow="Session history",
    )

    if timeline_items:
        for block in timeline_items:
            mission = (
                block.get("mission")
                or "Unknown mission"
            )

            duration_seconds = safe_int(
                block.get("duration_seconds")
            )

            duration_minutes = round(
                duration_seconds / 60,
                1,
            )

            goals = block.get(
                "goals",
                {},
            )

            apps = block.get(
                "apps",
                {},
            )

            top_goal = (
                max(
                    goals,
                    key=goals.get,
                )
                if goals
                else "No dominant goal"
            )

            with st.expander(
                f"{mission} · {duration_minutes} min · {top_goal}",
                expanded=False,
            ):
                goal_col, app_col = st.columns(
                    2,
                    gap="large",
                )

                with goal_col:
                    st.markdown("#### Goals")

                    if goals:
                        sorted_goals = sorted(
                            goals.items(),
                            key=lambda item: -item[1],
                        )

                        for goal, seconds in sorted_goals:
                            percentage = (
                                seconds / duration_seconds
                                if duration_seconds
                                else 0
                            )

                            st.markdown(
                                f"**{goal}**"
                            )

                            st.caption(
                                f"{round(seconds / 60, 1)} min"
                            )

                            st.progress(
                                min(
                                    percentage,
                                    1.0,
                                )
                            )
                    else:
                        st.caption(
                            "No goal breakdown is available."
                        )

                with app_col:
                    st.markdown("#### Applications")

                    if apps:
                        sorted_apps = sorted(
                            apps.items(),
                            key=lambda item: -item[1],
                        )[:7]

                        for app_name, seconds in sorted_apps:
                            percentage = (
                                seconds / duration_seconds
                                if duration_seconds
                                else 0
                            )

                            st.markdown(
                                f"**{app_name}**"
                            )

                            st.caption(
                                f"{round(seconds / 60, 1)} min"
                            )

                            st.progress(
                                min(
                                    percentage,
                                    1.0,
                                )
                            )
                    else:
                        st.caption(
                            "No application breakdown is available."
                        )

    else:
        with st.container(border=True):
            st.markdown(
                "### 🌱 No cognitive timeline yet"
            )

            st.write(
                "Run the tracker for a little longer. Drift will organise "
                "your activity into larger work blocks and show the goals "
                "and applications involved."
            )

# ── Page 3: Intelligence ──────────────────────────────────────────────────────
def render_intelligence():
    predict = api("/predict") or {}
    loops = api("/loops") or {}
    next_app = api("/next-app") or {}
    autopsy = api("/autopsy") or {}
    coach = api("/coach") or {}
    score = api("/score") or {}
    drift = api("/drift") or {}
    patterns = api("/patterns") or {}
    report = api("/daily-report") or {}
    deep_work = api("/deep-work") or {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def safe_int(value, default=0):
        try:
            return int(float(value or default))
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value or default)
        except (TypeError, ValueError):
            return default

    def percentage(value):
        number = safe_float(value)

        # Support APIs returning either 0.72 or 72.
        if 0 <= number <= 1:
            number *= 100

        return max(0, min(100, round(number)))

    def format_minutes(minutes):
        minutes = max(0, round(safe_float(minutes)))

        if minutes < 60:
            return f"{minutes} min"

        hours = minutes // 60
        remaining = minutes % 60

        if remaining == 0:
            return f"{hours} hr"

        return f"{hours} hr {remaining} min"

    # ------------------------------------------------------------------
    # Main values
    # ------------------------------------------------------------------

    overall_score = round(
        safe_float(score.get("overall_score")),
        1,
    )

    focus_score = percentage(
        score.get("focus_score")
    )

    recovery_score = percentage(
        score.get("recovery_score")
    )

    mission_score = percentage(
        score.get("mission_score")
    )

    switch_score = percentage(
        score.get("switch_score")
    )

    grade = str(
        score.get("grade", "N/A")
    )

    drift_index = round(
        safe_float(drift.get("drift_index")),
        1,
    )

    productive_minutes = round(
        safe_float(drift.get("productive_time")) / 60,
        1,
    )

    context_switches = safe_int(
        report.get("context_switches")
    )

    top_mission = (
        report.get("top_mission")
        or predict.get("current_mission")
        or "Not identified"
    )

    deep_minutes = safe_float(
        deep_work.get("total_deep_work_minutes")
    )

    deep_sessions = safe_int(
        deep_work.get(
            "count",
            len(deep_work.get("sessions", [])),
        )
    )

    risk_level = str(
        predict.get("risk_level", "UNKNOWN")
    ).upper()

    risk_score = round(
        safe_float(predict.get("risk_score")),
        1,
    )

    confidence = percentage(
        predict.get("confidence")
    )

    success_probability = percentage(
        predict.get("success_probability")
    )

    risk_reasons = predict.get(
        "risk_reasons",
        [],
    )

    # ------------------------------------------------------------------
    # Coach recommendation
    # ------------------------------------------------------------------

    advice = coach.get("advice", [])

    if isinstance(advice, list) and advice:
        primary_advice = advice[0]

        if isinstance(primary_advice, dict):
            observation = str(
                primary_advice.get(
                    "observation",
                    "Your workday has been analysed.",
                )
            ).strip()

            impact = str(
                primary_advice.get("impact", "")
            ).strip()

            suggestion = str(
                primary_advice.get(
                    "suggestion",
                    "Protect one uninterrupted focus block next.",
                )
            ).strip()
        else:
            observation = str(primary_advice)
            impact = ""
            suggestion = (
                "Protect one uninterrupted focus block next."
            )
    else:
        observation = (
            "Drift needs more activity before it can identify "
            "a reliable working pattern."
        )
        impact = ""
        suggestion = (
            "Keep the tracker running and complete one focused "
            "25–30 minute work block."
        )

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    section_header(
        title="Understand your work patterns",
        description=(
            "Predictions and behavioural signals translated into "
            "simple, useful explanations."
        ),
        eyebrow="Intelligence",
    )

    recommendation_card(
        text=suggestion,
        label="Best action to take next",
        icon="🎯",
    )

    # ------------------------------------------------------------------
    # Intelligence summary
    # ------------------------------------------------------------------

    summary_1, summary_2, summary_3, summary_4 = st.columns(
        4,
        gap="medium",
    )

    with summary_1:
        metric_card(
            icon="🧠",
            title="Productivity score",
            value=f"{overall_score}/100",
            subtitle=f"Current performance grade: {grade}.",
            badge="Today",
        )

    with summary_2:
        if risk_level in {"LOW"}:
            risk_trend = "Low risk of losing focus"
            risk_type = "positive"
        elif risk_level in {"MEDIUM", "UNKNOWN"}:
            risk_trend = "Some risk signals detected"
            risk_type = "neutral"
        else:
            risk_trend = "Focus is currently vulnerable"
            risk_type = "negative"

        metric_card(
            icon="⚠️",
            title="Focus risk",
            value=f"{risk_score}",
            subtitle=(
                f"{confidence}% confidence · {risk_level.title()} risk."
            ),
            trend=risk_trend,
            trend_type=risk_type,
            badge="Prediction",
        )

    with summary_3:
        metric_card(
            icon="🎯",
            title="Current mission",
            value=str(top_mission),
            subtitle=(
                f"{success_probability}% predicted chance of success."
            ),
            badge="Mission",
        )

    with summary_4:
        metric_card(
            icon="🔥",
            title="Deep work",
            value=format_minutes(deep_minutes),
            subtitle=(
                f"{deep_sessions} uninterrupted "
                f"{'session' if deep_sessions == 1 else 'sessions'}."
            ),
            badge="Focus",
        )

    # ------------------------------------------------------------------
    # What Drift noticed
    # ------------------------------------------------------------------

    section_header(
        title="What Drift noticed",
        description=(
            "The most important explanation behind today's scores."
        ),
        eyebrow="AI interpretation",
    )

    insight_col, risk_col = st.columns(
        [1.1, 1],
        gap="medium",
    )

    with insight_col:
        with st.container(border=True):
            st.markdown("### 🤖 Main observation")

            st.markdown(
                f"#### {observation}"
            )

            if impact:
                st.write(impact)

            st.divider()

            st.markdown("### What this means")

            if overall_score >= 80:
                st.success(
                    "Your work pattern was focused and well controlled."
                )
            elif overall_score >= 60:
                st.info(
                    "You made useful progress, although a few interruptions "
                    "reduced your focus quality."
                )
            elif overall_score >= 40:
                st.warning(
                    "Your work was productive in parts, but attention "
                    "changes made sustained focus difficult."
                )
            else:
                st.error(
                    "Your workday was fragmented. A smaller and more clearly "
                    "defined next task may help."
                )

            detail_1, detail_2 = st.columns(2)

            with detail_1:
                st.metric(
                    "Focused work",
                    format_minutes(productive_minutes),
                )

            with detail_2:
                st.metric(
                    "Attention changes",
                    context_switches,
                )

    with risk_col:
        with st.container(border=True):
            st.markdown("### 🔮 Focus-risk prediction")

            risk_left, risk_right = st.columns(2)

            with risk_left:
                st.metric(
                    "Risk score",
                    risk_score,
                )

            with risk_right:
                st.metric(
                    "Success probability",
                    f"{success_probability}%",
                )

            st.caption(
                f"Prediction confidence: {confidence}%"
            )

            if risk_reasons:
                st.markdown("#### Why this prediction was made")

                for reason in risk_reasons[:5]:
                    st.write(f"⚠️ {reason}")

            else:
                st.info(
                    "No specific risk signals are available yet."
                )

    # ------------------------------------------------------------------
    # Behaviour signals
    # ------------------------------------------------------------------

    section_header(
        title="Behaviour signals",
        description=(
            "Repeated patterns Drift detected while you worked."
        ),
        eyebrow="Pattern detection",
    )

    pattern_items = patterns.get(
        "patterns",
        [],
    )

    icons = {
        "Mission Abandonment": "⚠️",
        "Mission Recovery": "✅",
        "App Ping-Pong": "🔁",
        "Deep Work": "🔥",
        "Deep Focus": "🔥",
        "Context Switching": "🔄",
        "Recovery": "♻️",
    }

    fallback_patterns = [
        {
            "type": "Deep Focus",
            "count": deep_sessions,
            "description": (
                f"{format_minutes(deep_minutes)} of uninterrupted "
                "work was detected."
            ),
        },
        {
            "type": "Context Switching",
            "count": context_switches,
            "description": (
                "Meaningful changes between work contexts."
            ),
        },
        {
            "type": "Recovery",
            "count": recovery_score,
            "description": (
                "Your ability to return after an interruption."
            ),
        },
    ]

    display_patterns = (
        pattern_items[:3]
        if pattern_items
        else fallback_patterns
    )

    pattern_columns = st.columns(
        len(display_patterns),
        gap="medium",
    )

    for column, pattern in zip(
        pattern_columns,
        display_patterns,
    ):
        pattern_type = str(
            pattern.get("type", "Pattern")
        )

        pattern_count = safe_int(
            pattern.get("count")
        )

        pattern_description = str(
            pattern.get(
                "description",
                "Behavioural pattern detected.",
            )
        )

        with column:
            with st.container(border=True):
                st.markdown(
                    f"### {icons.get(pattern_type, '◆')} "
                    f"{pattern_type}"
                )

                st.markdown(
                    f"## {pattern_count}"
                )

                st.write(pattern_description)

    pattern_insight = patterns.get("insight")

    if pattern_insight:
        st.info(pattern_insight)

    # ------------------------------------------------------------------
    # Next app and behaviour loops
    # ------------------------------------------------------------------

    section_header(
        title="Habit predictions",
        description=(
            "See which application Drift expects next and which "
            "behaviour loops repeat most often."
        ),
        eyebrow="Behaviour prediction",
    )

    next_app_col, loops_col = st.columns(
        2,
        gap="medium",
    )

    with next_app_col:
        with st.container(border=True):
            st.markdown("### 💻 Next application prediction")

            predicted_app = (
                next_app.get("predicted_next_app")
                or "Not enough data"
            )

            app_confidence = percentage(
                next_app.get("confidence")
            )

            current_sequence = next_app.get(
                "current_sequence",
                [],
            )

            st.markdown(
                f"## {predicted_app}"
            )

            st.caption(
                f"{app_confidence}% confidence"
            )

            if current_sequence:
                st.markdown("#### Current pattern")
                st.code(
                    " → ".join(
                        str(item)
                        for item in current_sequence
                    ),
                    language=None,
                )

            app_insight = next_app.get("insight")

            if app_insight:
                st.info(app_insight)
            else:
                st.caption(
                    "Keep tracking to improve prediction quality."
                )

    with loops_col:
        with st.container(border=True):
            st.markdown("### 🔁 Repeated behaviour loops")

            loop_items = loops.get(
                "loops",
                [],
            )

            top_loop = loops.get(
                "top_loop"
            )

            if top_loop:
                top_sequence = " → ".join(
                    str(item)
                    for item in top_loop.get(
                        "sequence",
                        [],
                    )
                )

                top_count = safe_int(
                    top_loop.get("count")
                )

                st.markdown("#### Strongest loop")
                st.code(
                    top_sequence or "Unknown sequence",
                    language=None,
                )
                st.caption(
                    f"Repeated {top_count} times"
                )

                st.divider()

            if loop_items:
                st.markdown("#### Other detected loops")

                for index, loop in enumerate(
                    loop_items[:5],
                    start=1,
                ):
                    sequence = " → ".join(
                        str(item)
                        for item in loop.get(
                            "sequence",
                            [],
                        )
                    )

                    count = safe_int(
                        loop.get("count")
                    )

                    st.markdown(
                        f"**{index}. {sequence or 'Unknown sequence'}**"
                    )

                    st.caption(
                        f"Repeated {count} times"
                    )

                    if index < len(loop_items[:5]):
                        st.divider()

            elif not top_loop:
                st.info(
                    "No repeated behaviour loops have been detected yet."
                )

    # ------------------------------------------------------------------
    # Score explanation
    # ------------------------------------------------------------------

    section_header(
        title="Your focus profile",
        description=(
            "A simple breakdown of the abilities that shaped "
            "your productivity score."
        ),
        eyebrow="Productivity profile",
    )

    profile_left, profile_right = st.columns(
        2,
        gap="medium",
    )

    with profile_left:
        with st.container(border=True):
            st.markdown("### Score breakdown")

            score_items = [
                (
                    "Focus consistency",
                    focus_score,
                    "How steadily you stayed on useful work.",
                ),
                (
                    "Mission alignment",
                    mission_score,
                    "How much activity supported your main objective.",
                ),
                (
                    "Recovery ability",
                    recovery_score,
                    "How effectively you returned after interruptions.",
                ),
                (
                    "Switch control",
                    switch_score,
                    "How well you limited unnecessary context changes.",
                ),
            ]

            for index, (
                label,
                value,
                explanation,
            ) in enumerate(score_items):
                score_label, score_value = st.columns(
                    [3, 1]
                )

                with score_label:
                    st.markdown(f"**{label}**")

                with score_value:
                    st.markdown(f"**{value}/100**")

                st.progress(
                    value / 100
                )

                st.caption(explanation)

                if index < len(score_items) - 1:
                    st.divider()

    with profile_right:
        with st.container(border=True):
            st.markdown("### How to read this page")

            st.write(
                "**Predictions** estimate what may happen next based "
                "on repeated work patterns."
            )

            st.write(
                "**Behaviour signals** describe patterns already detected "
                "in your activity."
            )

            st.write(
                "**Mission analysis** evaluates whether your activity "
                "supported your dominant objective."
            )

            st.info(
                "These insights become more reliable as Drift records "
                "more activity across different workdays."
            )

    # ------------------------------------------------------------------
    # Mission autopsy
    # ------------------------------------------------------------------

    section_header(
        title="Mission autopsy",
        description=(
            "Understand why your main mission succeeded, stalled, "
            "or lost momentum."
        ),
        eyebrow="Mission analysis",
    )

    if autopsy and autopsy.get("mission"):
        autopsy_success = percentage(
            autopsy.get("success_probability")
        )

        autopsy_mission = (
            autopsy.get("mission")
            or "Unknown mission"
        )

        autopsy_summary = (
            autopsy.get("summary")
            or "No mission summary is available."
        )

        failure_reason = (
            autopsy.get("failure_reason")
            or "No major failure signal was detected."
        )

        autopsy_recommendation = (
            autopsy.get("recommendation")
            or "Continue protecting focused work sessions."
        )

        with st.container(border=True):
            autopsy_left, autopsy_right = st.columns(
                [1.5, 1],
                gap="large",
            )

            with autopsy_left:
                st.markdown(
                    f"### 🎯 {autopsy_mission}"
                )

                st.write(autopsy_summary)

                st.warning(
                    f"**Main risk:** {failure_reason}"
                )

                st.success(
                    f"**Recommendation:** {autopsy_recommendation}"
                )

            with autopsy_right:
                st.metric(
                    "Success probability",
                    f"{autopsy_success}%",
                )

                st.metric(
                    "Mission alignment",
                    f"{safe_int(autopsy.get('mission_alignment_percentage'))}%",
                )

                st.metric(
                    "Deep work",
                    f"{safe_float(autopsy.get('deep_work_minutes')):g} min",
                )

                st.caption(
                    f"{safe_int(autopsy.get('mission_abandonments'))} "
                    "abandonments · "
                    f"{safe_int(autopsy.get('mission_recoveries'))} "
                    "recoveries"
                )

    else:
        with st.container(border=True):
            st.markdown("### 🌱 No mission autopsy yet")

            st.write(
                "Drift needs a clearly detected mission and more activity "
                "before it can explain why the mission succeeded or stalled."
            )

    # ------------------------------------------------------------------
    # Quick wins
    # ------------------------------------------------------------------

    section_header(
        title="Quick wins for tomorrow",
        description=(
            "Small actions that can improve your next workday."
        ),
        eyebrow="Action plan",
    )

    recommendations = report.get(
        "recommendations",
        [],
    )

    if not recommendations:
        recommendations = [
            suggestion,
            "Reduce unnecessary application switching.",
            "Finish the current mission before starting another.",
            "Protect the first 30 minutes of your next work session.",
        ]

    with st.container(border=True):
        for index, recommendation in enumerate(
            recommendations[:5],
            start=1,
        ):
            st.markdown(
                f"### {index}. {recommendation}"
            )

            if index < len(recommendations[:5]):
                st.divider()
# ── Page 4: Daily Report ──────────────────────────────────────────────────────
def render_daily_report():
    report = api("/daily-report") or {}
    coach = api("/coach") or {}
    score = api("/score") or {}
    deep_work = api("/deep-work") or {}
    drift = api("/drift") or {}
    recovery = api("/recovery-cost") or {}
    replay = api("/replay") or {}

    def safe_int(value, default=0):
        try:
            return int(float(value or default))
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value or default)
        except (TypeError, ValueError):
            return default

    def clamp(value, minimum=0, maximum=100):
        return max(minimum, min(maximum, value))

    def format_minutes(value):
        minutes = max(0, round(safe_float(value)))

        if minutes < 60:
            return f"{minutes} min"

        hours = minutes // 60
        remaining = minutes % 60

        if remaining == 0:
            return f"{hours} hr"

        return f"{hours} hr {remaining} min"

    today = datetime.now().strftime("%A, %B %d")

    overall = round(
        safe_float(score.get("overall_score")),
        1,
    )

    grade = str(
        score.get("grade", "N/A")
    )

    focus_score = clamp(
        safe_int(score.get("focus_score"))
    )

    mission_score = clamp(
        safe_int(score.get("mission_score"))
    )

    recovery_score = clamp(
        safe_int(score.get("recovery_score"))
    )

    switch_score = clamp(
        safe_int(score.get("switch_score"))
    )

    deep_minutes = safe_float(
        deep_work.get("total_deep_work_minutes")
    )

    deep_sessions = safe_int(
        deep_work.get(
            "count",
            len(deep_work.get("sessions", [])),
        )
    )

    context_switches = safe_int(
        report.get("context_switches")
    )

    top_mission = (
        report.get("top_mission")
        or "Not identified"
    )

    productive_seconds = safe_float(
        drift.get("productive_time")
    )

    productive_minutes = productive_seconds / 60

    drift_index = round(
        safe_float(drift.get("drift_index")),
        1,
    )

    recovery_events = safe_int(
        recovery.get("count")
    )

    recovery_cost_minutes = round(
        safe_float(
            recovery.get("total_recovery_cost_seconds")
        )
        / 60,
        1,
    )

    replay_events = replay.get("events", [])

    focus_lost_count = sum(
        1
        for event in replay_events
        if event.get("event_type") == "focus_lost"
    )

    recovered_count = sum(
        1
        for event in replay_events
        if event.get("event_type") == "recovered"
    )

    recovery_rate = (
        round(
            recovered_count / focus_lost_count * 100
        )
        if focus_lost_count > 0
        else 100
    )

    recommendations = report.get(
        "recommendations",
        [],
    )

    advice = coach.get("advice", [])

    if isinstance(advice, list) and advice:
        primary = advice[0]

        if isinstance(primary, dict):
            coach_observation = str(
                primary.get(
                    "observation",
                    "Your workday has been analysed.",
                )
            ).strip()

            coach_impact = str(
                primary.get("impact", "")
            ).strip()

            coach_suggestion = str(
                primary.get(
                    "suggestion",
                    "Protect one focused work block tomorrow.",
                )
            ).strip()
        else:
            coach_observation = str(primary)
            coach_impact = ""
            coach_suggestion = (
                "Protect one focused work block tomorrow."
            )
    else:
        coach_observation = (
            "Drift needs more tracked activity to create "
            "a reliable coaching summary."
        )
        coach_impact = ""
        coach_suggestion = (
            "Keep the tracker running and complete one focused block."
        )

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------

    if productive_minutes == 0:
        summary_title = "There is not enough activity for a full report yet."
        summary_text = (
            "Keep the tracker running while you work. Drift will build "
            "a report once it has enough meaningful activity."
        )

    elif overall >= 80:
        summary_title = "You had a strong and focused workday."
        summary_text = (
            f"You completed {format_minutes(productive_minutes)} of productive "
            f"work, including {format_minutes(deep_minutes)} of deep work. "
            "Your attention stayed relatively steady."
        )

    elif overall >= 60:
        summary_title = "You made useful progress today."
        summary_text = (
            f"You completed {format_minutes(productive_minutes)} of productive "
            f"work. A few attention changes reduced the length of your "
            "focus sessions, but the day still moved forward."
        )

    elif overall >= 40:
        summary_title = "Your workday was productive in parts."
        summary_text = (
            f"You completed {format_minutes(productive_minutes)} of productive "
            f"work, but {context_switches} attention changes made it harder "
            "to build longer focus sessions."
        )

    else:
        summary_title = "Your workday felt fragmented."
        summary_text = (
            f"You completed {format_minutes(productive_minutes)} of productive "
            f"work, but repeated interruptions prevented longer deep-focus "
            "sessions from developing."
        )

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    section_header(
        title="Your day, decoded",
        description=(
            "A simple end-of-day summary of your focus, recovery, "
            "and what to improve tomorrow."
        ),
        eyebrow=f"Daily report · {today}",
    )

    # ------------------------------------------------------------------
    # Hero summary
    # ------------------------------------------------------------------

    with st.container(border=True):
        hero_left, hero_right = st.columns(
            [3, 1],
            gap="large",
        )

        with hero_left:
            st.markdown(
                f"## {summary_title}"
            )

            st.write(summary_text)

            if top_mission not in {
                "Not identified",
                "Unknown",
                "Unclassified Mission",
                "—",
            }:
                st.caption(
                    f"Your main mission was **{top_mission}**."
                )
            else:
                st.caption(
                    "Your main mission could not be classified reliably."
                )

        with hero_right:
            st.metric(
                "Final score",
                f"{overall}/100",
            )

            st.caption(
                f"Grade {grade} · Drift index {drift_index}"
            )

    recommendation_card(
        text=coach_suggestion,
        label="Tomorrow's priority",
        icon="🎯",
    )

    # ------------------------------------------------------------------
    # Key numbers
    # ------------------------------------------------------------------

    section_header(
        title="Key numbers",
        description=(
            "The four metrics that best explain your day."
        ),
        eyebrow="Today at a glance",
    )

    metric_1, metric_2, metric_3, metric_4 = st.columns(
        4,
        gap="medium",
    )

    with metric_1:
        metric_card(
            icon="⏱️",
            title="Productive time",
            value=format_minutes(productive_minutes),
            subtitle=(
                f"Focus score: {focus_score}/100."
            ),
            badge="Today",
        )

    with metric_2:
        metric_card(
            icon="🔥",
            title="Deep work",
            value=format_minutes(deep_minutes),
            subtitle=(
                f"{deep_sessions} uninterrupted "
                f"{'session' if deep_sessions == 1 else 'sessions'}."
            ),
            badge="Focus",
        )

    with metric_3:
        metric_card(
            icon="⚠️",
            title="Focus interruptions",
            value=str(focus_lost_count),
            subtitle=(
                f"{recovered_count} recoveries recorded."
            ),
            trend=(
                "Low interruption level"
                if focus_lost_count <= 2
                else "Attention was interrupted"
            ),
            trend_type=(
                "positive"
                if focus_lost_count <= 2
                else "negative"
            ),
            badge="Detected",
        )

    with metric_4:
        metric_card(
            icon="♻️",
            title="Recovery cost",
            value=f"{recovery_cost_minutes} min",
            subtitle=(
                f"{recovery_events} recovery "
                f"{'event' if recovery_events == 1 else 'events'}."
            ),
            badge="Estimate",
        )

    # ------------------------------------------------------------------
    # Performance and coaching
    # ------------------------------------------------------------------

    section_header(
        title="Performance breakdown",
        description=(
            "See which abilities helped or limited your productivity."
        ),
        eyebrow="Score analysis",
    )

    performance_col, coach_col = st.columns(
        [1.1, 1],
        gap="medium",
    )

    with performance_col:
        with st.container(border=True):
            score_rows = [
                (
                    "Focus consistency",
                    focus_score,
                    "How steadily you stayed on useful work.",
                ),
                (
                    "Mission alignment",
                    mission_score,
                    "How much activity supported your main objective.",
                ),
                (
                    "Recovery ability",
                    recovery_score,
                    "How effectively you returned after interruptions.",
                ),
                (
                    "Switch control",
                    switch_score,
                    "How well you limited unnecessary context changes.",
                ),
            ]

            for index, (
                label,
                value,
                explanation,
            ) in enumerate(score_rows):
                label_col, value_col = st.columns(
                    [3, 1]
                )

                with label_col:
                    st.markdown(f"**{label}**")

                with value_col:
                    st.markdown(f"**{value}/100**")

                st.progress(
                    value / 100
                )

                st.caption(explanation)

                if index < len(score_rows) - 1:
                    st.divider()

    with coach_col:
        with st.container(border=True):
            st.markdown("### 🤖 Drift Coach")

            st.markdown(
                f"#### {coach_observation}"
            )

            if coach_impact:
                st.write(coach_impact)

            st.success(
                f"💡 {coach_suggestion}"
            )

    # ------------------------------------------------------------------
    # Mission and recovery
    # ------------------------------------------------------------------

    section_header(
        title="Your work story",
        description=(
            "Understand what received your attention and how well "
            "you returned after interruptions."
        ),
        eyebrow="Daily interpretation",
    )

    mission_col, recovery_col = st.columns(
        2,
        gap="medium",
    )

    with mission_col:
        with st.container(border=True):
            st.markdown("### 🎯 Dominant mission")

            st.markdown(
                f"## {top_mission}"
            )

            st.write(
                "This was the main focus area detected across "
                "your tracked activity."
            )

            if top_mission in {
                "Not identified",
                "Unknown",
                "Unclassified Mission",
                "—",
            }:
                st.warning(
                    "A large part of your activity is still unclassified."
                )

    with recovery_col:
        with st.container(border=True):
            st.markdown("### ♻️ Recovery story")

            st.metric(
                "Recovery rate",
                f"{recovery_rate}%",
            )

            st.write(
                f"You recovered after {recovered_count} of "
                f"{focus_lost_count} detected interruptions."
            )

            if focus_lost_count == 0:
                st.success(
                    "No meaningful focus-loss event was detected."
                )
            elif recovery_rate >= 75:
                st.success(
                    "You usually returned to focused work successfully."
                )
            elif recovery_rate >= 40:
                st.warning(
                    "You recovered after some interruptions, "
                    "but several remained unresolved."
                )
            else:
                st.error(
                    "Many interruptions ended without a clear return "
                    "to focused work."
                )

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    section_header(
        title="Your day at a glance",
        description=(
            "A compact summary of focus, interruption, and recovery events."
        ),
        eyebrow="Timeline",
    )

    with st.container(border=True):
        if replay_events:
            displayed_events = replay_events[:30]

            for index, event in enumerate(
                displayed_events,
                start=1,
            ):
                event_type = str(
                    event.get(
                        "event_type",
                        "focused",
                    )
                ).lower()

                event_icons = {
                    "start": "🚀",
                    "focused": "💻",
                    "deep_work": "🔥",
                    "recovered": "✅",
                    "focus_lost": "⚠️",
                    "idle": "🌙",
                }

                event_labels = {
                    "start": "Started working",
                    "focused": "Focused activity",
                    "deep_work": "Deep work",
                    "recovered": "Recovered focus",
                    "focus_lost": "Focus interrupted",
                    "idle": "Away from work",
                }

                icon = event_icons.get(
                    event_type,
                    "•",
                )

                label = event_labels.get(
                    event_type,
                    "Activity",
                )

                mission = (
                    event.get("mission")
                    or "Unknown mission"
                )

                event_time = (
                    event.get("time")
                    or event.get("start_time")
                    or ""
                )

                duration = safe_float(
                    event.get("duration_minutes")
                )

                row_left, row_right = st.columns(
                    [4, 1]
                )

                with row_left:
                    st.markdown(
                        f"**{icon} {label} · {mission}**"
                    )

                with row_right:
                    details = []

                    if event_time:
                        details.append(str(event_time))

                    if duration:
                        details.append(f"{duration:g} min")

                    st.caption(
                        " · ".join(details)
                        if details
                        else " "
                    )

                if index < len(displayed_events):
                    st.divider()

            if len(replay_events) > 30:
                st.caption(
                    f"Showing 30 of {len(replay_events)} events."
                )

        else:
            st.info(
                "No replay events are available yet."
            )

    # ------------------------------------------------------------------
    # Tomorrow's focus plan
    # ------------------------------------------------------------------

    section_header(
        title="Tomorrow's focus plan",
        description=(
            "A few clear actions for your next workday."
        ),
        eyebrow="Recommendations",
    )

    if not recommendations:
        recommendations = [
            coach_suggestion,
            "Begin with one uninterrupted 30-minute focus block.",
            "Avoid switching applications while working on your main mission.",
            "Schedule distracting communication into specific time windows.",
        ]

    with st.container(border=True):
        for index, recommendation in enumerate(
            recommendations[:5],
            start=1,
        ):
            st.markdown(
                f"### {index}. {recommendation}"
            )

            if index < len(recommendations[:5]):
                st.divider()

    # ------------------------------------------------------------------
    # End message
    # ------------------------------------------------------------------

    if overall >= 75:
        final_message = (
            "Strong day. Protect the habits that created "
            "your focused sessions."
        )
    elif overall >= 50:
        final_message = (
            "A mixed day. Tomorrow, reduce switching and "
            "protect one clear mission."
        )
    else:
        final_message = (
            "Today was fragmented. Reset tomorrow with one "
            "small, uninterrupted goal."
        )

    with st.container(border=True):
        st.caption("END OF REPORT")
        st.markdown(
            f"## {final_message}"
        )
    # ── Page 5: Replay ────────────────────────────────────────────────────────────

def render_replay():
    render_replay_page(api, empty)



# ── Application Router ────────────────────────────────────────────────────────

if not st.session_state.authenticated:
    render_auth()

else:
    if st.session_state.auto_refresh_enabled:
        st_autorefresh(
            interval=st.session_state.refresh_seconds * 1000,
            limit=None,
            key="drift_auto_refresh",
        )

    if st.session_state.last_refresh is None:
        st.session_state.last_refresh = datetime.now()

    backend_alive = api_alive()
    render_sidebar(backend_alive)

    page = st.session_state.active_page

    try:
        if page == "Overview":
            render_overview()

        elif page == "Deep Dive":
            render_deep_dive()

        elif page == "Intelligence":
            render_intelligence()

        elif page == "History":
            history_page()

        elif page == "AI Coach":
            chat_page()

        elif page == "Replay":
            render_replay()

        elif page == "Daily Report":
            render_daily_report()

        elif page == "Goals":
            goals_page()

        else:
            st.session_state.active_page = "Overview"
            st.rerun()

    except Exception as error:
        st.error("The selected page could not be rendered.")
        st.exception(error)