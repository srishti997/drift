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
    dw = api("/deep-work") or {}
    switches = api("/context-switches") or {}
    patterns = api("/patterns") or {}
    recovery = api("/recovery-cost") or {}
    replay = api("/replay") or {}
    missions = api("/missions") or {}

    st.markdown(
        """
<div style="margin-bottom:24px;">
<div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Deep Dive</div>
<div class="page-title">What actually happened.</div>
<div class="page-sub">Visual breakdown of focus, context switching, recovery, and session behavior.</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    deep_minutes = dw.get("total_deep_work_minutes", 0)
    deep_sessions = dw.get("count", len(dw.get("sessions", [])))
    deep_goal = st.session_state.deep_work_goal
    deep_progress = min(100, round((deep_minutes / deep_goal) * 100))

    total_switches = switches.get("total_switches", 0)
    distraction_switches = switches.get("distraction_switches", 0)
    focus_loss_minutes = round(switches.get("estimated_focus_loss_seconds", 0) / 60, 1)

    left, right = st.columns(2)

    with left:
        st.markdown(
            f"""
<div class="card-cyan">
<div class="eyebrow">Today's Deep Work</div>
<div style="font-size:44px;font-weight:900;color:#F8FAFC;font-family:'JetBrains Mono',monospace;margin-bottom:8px;">{deep_minutes} min</div>
<div style="font-size:13px;color:#64748B;margin-bottom:12px;">{deep_sessions} deep work session(s) · Goal: {deep_goal} min</div>
<div class="bar-track" style="height:10px;">
<div class="bar-fill" style="width:{deep_progress}%;background:linear-gradient(90deg,#22D3EE,#34D399);"></div>
</div>
<div style="font-size:12px;color:#475569;margin-top:10px;">{deep_progress}% of daily deep work target completed</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="card"><div class="eyebrow">Context Switch Timeline</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total", total_switches)
        c2.metric("Distraction", distraction_switches)
        c3.metric("Focus Lost", f"{focus_loss_minutes} min")

        switch_density = min(40, total_switches)
        switch_timeline = "".join(["●" if i < switch_density else "─" for i in range(40)])

        st.markdown(
            f"""
<div style="font-size:20px;letter-spacing:2px;font-family:'JetBrains Mono',monospace;color:#FB923C;word-break:break-all;margin-top:12px;">
{switch_timeline}
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    mission_items = missions.get("missions", []) if missions else []
    replay_events = replay.get("events", []) if replay else []

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown('<div class="card"><div class="eyebrow">Mission Analytics</div>', unsafe_allow_html=True)

        if mission_items:
            total_time = sum(item.get("time_seconds", 0) for item in mission_items) or 1

            for item in sorted(mission_items, key=lambda x: x.get("time_seconds", 0), reverse=True)[:7]:
                mission = item.get("mission", "Unknown")
                seconds = item.get("time_seconds", 0)
                pct = round((seconds / total_time) * 100)
                mins = round(seconds / 60, 1)
                color = mcolor(mission)

                st.markdown(
                    f"""
<div style="margin-bottom:18px;">
<div style="display:flex;justify-content:space-between;font-size:13px;color:#CBD5E1;margin-bottom:6px;">
<span>{mission}</span>
<span>{mins} min · {pct}%</span>
</div>
<div class="bar-track" style="height:9px;">
<div class="bar-fill" style="width:{pct}%;background:{color};"></div>
</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            empty("No mission analytics yet. Run the tracker for a few minutes.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card-purple"><div class="eyebrow">Daily Focus Heatmap</div>', unsafe_allow_html=True)

        if replay_events:
            cols = st.columns(20)

            color_map = {
                "start": "#22D3EE",
                "focused": "#818CF8",
                "recovered": "#34D399",
                "focus_lost": "#F87171",
            }

            for i, event in enumerate(replay_events[:120]):
                event_type = event.get("event_type", "focused")
                color = color_map.get(event_type, "#64748B")

                with cols[i % 20]:
                    st.markdown(
                        f"""
<div style="width:14px;height:14px;border-radius:4px;background:{color};margin-bottom:8px;"></div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.caption("🚀 Start · 💻 Focused · ✅ Recovered · ⚠️ Focus Lost")
        else:
            empty("No focus heatmap data yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns(2)

    with left:
        st.markdown('<div class="card"><div class="eyebrow">Behavioral Patterns</div>', unsafe_allow_html=True)

        pats = patterns.get("patterns", []) if patterns else []
        icons = {
            "Mission Abandonment": "⚠️",
            "Mission Recovery": "✅",
            "App Ping-Pong": "🔁",
            "Deep Work": "🔥",
        }

        if pats:
            for p in pats:
                pt = p.get("type", "Pattern")
                cnt = p.get("count", 0)
                desc = p.get("description", "")

                st.markdown(
                    f"""
<div class="pat-row">
<div class="pat-head">
<span>{icons.get(pt, "◆")}</span>
<span class="pat-name">{pt}</span>
<span class="pat-count">×{cnt}</span>
</div>
<div class="pat-desc">{desc}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            if patterns.get("insight"):
                st.markdown(
                    f"<div style='font-size:12px;color:#475569;margin-top:12px;'>{patterns['insight']}</div>",
                    unsafe_allow_html=True,
                )
        else:
            empty("No behavioral patterns detected yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        count = recovery.get("count", 0)
        total_cost = round(recovery.get("total_recovery_cost_seconds", 0) / 60, 1)
        avg_cost = round(recovery.get("average_recovery_cost_seconds", 0) / 60, 1)
        insight = recovery.get("insight", "No recovery insight yet.")

        st.markdown('<div class="card-red"><div class="eyebrow">Recovery Cost Analysis</div>', unsafe_allow_html=True)

        r1, r2, r3 = st.columns(3)
        r1.metric("Events", count)
        r2.metric("Total Cost", f"{total_cost} min")
        r3.metric("Avg Cost", f"{avg_cost} min")

        st.markdown(
            f"""
<div style="font-size:13px;color:#94A3B8;line-height:1.6;margin-top:16px;">
{insight}
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="card"><div class="eyebrow">Cognitive Timeline — Click to Expand</div>', unsafe_allow_html=True)

    tl_items = timeline.get("timeline", []) if timeline else []

    if tl_items:
        for block in tl_items:
            mission = block.get("mission", "Unknown")
            dur_s = block.get("duration_seconds", 0)
            dur_m = round(dur_s / 60, 1)
            goals = block.get("goals", {})
            apps = block.get("apps", {})
            color = mcolor(mission)
            top_goal = max(goals, key=goals.get) if goals else "—"

            with st.expander(f"{mission} · {dur_m}m · {top_goal}", expanded=False):
                g1, g2 = st.columns(2)

                with g1:
                    st.markdown("**Goals**")
                    if goals:
                        for g, secs in sorted(goals.items(), key=lambda x: -x[1]):
                            pct = round(secs / dur_s * 100) if dur_s else 0
                            st.markdown(
                                f"""
<div style="margin-bottom:8px;">
<div style="display:flex;justify-content:space-between;font-size:12px;color:#94A3B8;margin-bottom:3px;">
<span>{g}</span>
<span>{round(secs / 60, 1)}m</span>
</div>
<div style="background:rgba(30,41,59,.8);border-radius:100px;height:5px;">
<div style="width:{pct}%;height:100%;background:{color};border-radius:100px;"></div>
</div>
</div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No goal breakdown.")

                with g2:
                    st.markdown("**Apps**")
                    if apps:
                        for app, secs in sorted(apps.items(), key=lambda x: -x[1])[:5]:
                            pct = round(secs / dur_s * 100) if dur_s else 0
                            st.markdown(
                                f"""
<div style="margin-bottom:8px;">
<div style="display:flex;justify-content:space-between;font-size:12px;color:#94A3B8;margin-bottom:3px;">
<span>{app}</span>
<span>{round(secs / 60, 1)}m</span>
</div>
<div style="background:rgba(30,41,59,.8);border-radius:100px;height:5px;">
<div style="width:{pct}%;height:100%;background:{color};border-radius:100px;"></div>
</div>
</div>
                                """,
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("No app breakdown.")
    else:
        empty("No cognitive timeline data yet.")

    st.markdown("</div>", unsafe_allow_html=True)

# ── Page 3: Intelligence ──────────────────────────────────────────────────────

def render_intelligence():
    predict = api("/predict") or {}
    loops = api("/loops") or {}
    next_app = api("/next-app") or {}
    autopsy = api("/autopsy") or {}
    coach = api("/coach") or {}
    score = api("/score") or {}
    drift = api("/drift") or {}
    missions = api("/missions") or {}
    patterns = api("/patterns") or {}
    report = api("/daily-report") or {}
    deep_work = api("/deep-work") or {}

    overall_score = score.get("overall_score", 0)
    grade = score.get("grade", "N/A")
    focus_score = score.get("focus_score", 0)
    mission_score = score.get("mission_score", 0)
    recovery_score = score.get("recovery_score", 0)
    switch_score = score.get("switch_score", 0)

    productive_seconds = drift.get("productive_time", 0)
    productive_minutes = round(productive_seconds / 60, 1)

    drift_index = drift.get("drift_index", 0)
    top_mission = report.get("top_mission", "Unknown")
    deep_minutes = deep_work.get("total_deep_work_minutes", 0)
    deep_sessions = deep_work.get("count", len(deep_work.get("sessions", [])))

    context_switches = report.get("context_switches", 0)

    st.markdown(
        """
<div style="margin-bottom:24px;">
<div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Intelligence</div>
<div class="page-title">Your productivity DNA.</div>
<div class="page-sub">Predictions, behavior signals, and AI coaching based on how you worked today.</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ── Executive summary ────────────────────────────────────────────────
    executive_summary = report.get(
        "executive_summary",
        (
            f"You recorded {productive_minutes} productive minutes today. "
            f"Your dominant mission was {top_mission}. "
            f"Your productivity score is {overall_score}/100 with grade {grade}."
        ),
    )

    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,rgba(34,211,238,.12),rgba(129,140,248,.08));border:1px solid rgba(34,211,238,.22);border-radius:24px;padding:30px;margin-bottom:22px;">
<div class="eyebrow">Today's Executive Summary</div>
<div style="font-size:20px;color:#E2E8F0;line-height:1.7;font-weight:600;max-width:1000px;">
{executive_summary}
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;">
<span class="grade-pill">Score {overall_score}</span>
<span class="grade-pill">Grade {grade}</span>
<span class="grade-pill">Drift {drift_index}</span>
<span class="grade-pill">{productive_minutes} productive min</span>
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ── AI Coach + prediction ────────────────────────────────────────────
    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            '<div class="card-cyan"><div class="eyebrow">AI Coach</div>',
            unsafe_allow_html=True,
        )

        advice = coach.get("advice", [])

        if advice:
            primary = advice[0]

            observation = primary.get(
                "observation",
                "Your workday has been analysed.",
            )
            impact = primary.get(
                "impact",
                "Your current pattern may be affecting sustained focus.",
            )
            suggestion = primary.get(
                "suggestion",
                "Protect one focused work block tomorrow.",
            )

            st.markdown(
                f"""
<div style="font-size:20px;font-weight:800;color:#F8FAFC;margin-bottom:12px;">
🎯 Best thing you can do next
</div>
<div style="font-size:16px;color:#CBD5E1;line-height:1.7;margin-bottom:16px;">
{observation}
</div>
<div style="font-size:14px;color:#64748B;line-height:1.7;margin-bottom:18px;">
{impact}
</div>
<div style="background:rgba(34,211,238,.08);border:1px solid rgba(34,211,238,.18);border-radius:14px;padding:16px;color:#E2E8F0;font-size:14px;line-height:1.7;">
💡 {suggestion}
</div>
                """,
                unsafe_allow_html=True,
            )

            if len(advice) > 1:
                st.markdown(
                    '<div style="margin-top:18px;"><div class="eyebrow">More Coaching</div>',
                    unsafe_allow_html=True,
                )

                for item in advice[1:4]:
                    st.markdown(
                        f"""
<div class="coach-card">
<div class="coach-lbl">Observation</div>
<div class="coach-txt">{item.get("observation", "")}</div>
<div class="coach-lbl">Suggestion</div>
<div class="coach-txt" style="margin-bottom:0;">{item.get("suggestion", "")}</div>
</div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

        else:
            empty("No coaching insight yet. Keep the tracker running.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        risk_level = predict.get("risk_level", "UNKNOWN")
        risk_score = predict.get("risk_score", 0)
        confidence = round(predict.get("confidence", 0) * 100)
        success_probability = round(
            predict.get("success_probability", 0) * 100
        )

        risk_class = {
            "LOW": "risk-low",
            "MEDIUM": "risk-med",
            "HIGH": "risk-high",
            "CRITICAL": "risk-crit",
        }.get(risk_level, "risk-med")

        st.markdown(
            f"""
<div class="card-purple">
<div class="eyebrow">Focus Risk Prediction</div>
<div style="display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:18px;">
<div>
<div style="font-size:54px;font-weight:900;font-family:'JetBrains Mono',monospace;color:#818CF8;line-height:1;">
{risk_score}
</div>
<div style="font-size:12px;color:#475569;margin-top:5px;">risk score</div>
</div>
<div style="text-align:right;">
<span class="risk-pill {risk_class}">{risk_level}</span>
<div style="font-size:12px;color:#64748B;margin-top:10px;">
{confidence}% confidence
</div>
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
<div class="stat-tile">
<div class="stat-label">Success Probability</div>
<div class="stat-value" style="font-size:22px;">{success_probability}%</div>
<div class="stat-sub">current mission</div>
</div>
<div class="stat-tile">
<div class="stat-label">Current Mission</div>
<div class="stat-value" style="font-size:16px;">{predict.get("current_mission", "—")}</div>
<div class="stat-sub">prediction context</div>
</div>
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        reasons = predict.get("risk_reasons", [])

        if reasons:
            st.markdown(
                '<div class="card"><div class="eyebrow">Risk Signals</div>',
                unsafe_allow_html=True,
            )

            for reason in reasons[:5]:
                st.markdown(
                    f"""
<div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(148,163,184,.06);font-size:13px;color:#94A3B8;">
<span style="color:#FBBF24;">⚠</span>
<span>{reason}</span>
</div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Behavior pattern cards ────────────────────────────────────────────
    st.markdown(
        '<div style="margin-top:6px;margin-bottom:12px;"><div class="eyebrow">Behavior Patterns</div></div>',
        unsafe_allow_html=True,
    )

    pattern_items = patterns.get("patterns", [])
    p1, p2, p3 = st.columns(3)

    pattern_cards = []

    if pattern_items:
        for item in pattern_items[:3]:
            pattern_cards.append(
                (
                    item.get("type", "Behavior Pattern"),
                    item.get("count", 0),
                    item.get("description", "Pattern detected."),
                )
            )

    while len(pattern_cards) < 3:
        if len(pattern_cards) == 0:
            pattern_cards.append(
                (
                    "Deep Focus",
                    deep_sessions,
                    f"{deep_minutes} minutes of deep work today.",
                )
            )
        elif len(pattern_cards) == 1:
            pattern_cards.append(
                (
                    "Context Switching",
                    context_switches,
                    "Total mission or application switches.",
                )
            )
        else:
            pattern_cards.append(
                (
                    "Recovery",
                    recovery_score,
                    "Your ability to return after distraction.",
                )
            )

    icons = {
        "Mission Abandonment": "⚠️",
        "Mission Recovery": "✅",
        "App Ping-Pong": "🔁",
        "Deep Work": "🔥",
        "Deep Focus": "🔥",
        "Context Switching": "⚡",
        "Recovery": "✅",
    }

    for col, item in zip([p1, p2, p3], pattern_cards):
        title, count, description = item

        with col:
            st.markdown(
                f"""
<div class="stat-tile" style="min-height:170px;">
<div style="font-size:25px;margin-bottom:12px;">{icons.get(title, "◆")}</div>
<div style="font-size:17px;font-weight:800;color:#F1F5F9;margin-bottom:8px;">
{title}
</div>
<div style="font-size:28px;font-weight:900;color:#22D3EE;font-family:'JetBrains Mono',monospace;margin-bottom:8px;">
{count}
</div>
<div style="font-size:12px;color:#64748B;line-height:1.6;">
{description}
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ── Predictions + next app ────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        predicted_app = next_app.get("predicted_next_app", "Not enough data")
        app_confidence = round(next_app.get("confidence", 0) * 100)
        current_sequence = next_app.get("current_sequence", [])
        sequence_text = " → ".join(current_sequence) if current_sequence else "No pattern available"

        st.markdown(
            f"""
<div class="card">
<div class="eyebrow">Next App Prediction</div>
<div style="font-size:12px;color:#64748B;margin-bottom:8px;">Current sequence</div>
<div style="font-size:13px;color:#818CF8;font-family:'JetBrains Mono',monospace;margin-bottom:18px;line-height:1.6;">
{sequence_text}
</div>
<div style="font-size:12px;color:#64748B;margin-bottom:5px;">Likely next app</div>
<div style="font-size:26px;font-weight:900;color:#22D3EE;font-family:'JetBrains Mono',monospace;">
{predicted_app}
</div>
<div style="font-size:13px;color:#475569;margin-top:8px;">
{app_confidence}% confidence
</div>
<div style="font-size:13px;color:#94A3B8;line-height:1.6;margin-top:16px;padding:14px;background:rgba(34,211,238,.05);border-radius:12px;">
{next_app.get("insight", "Keep tracking to improve prediction quality.")}
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        loop_items = loops.get("loops", [])
        top_loop = loops.get("top_loop")

        st.markdown(
            '<div class="card"><div class="eyebrow">Behavior Loops</div>',
            unsafe_allow_html=True,
        )

        if top_loop:
            sequence = " → ".join(top_loop.get("sequence", []))
            count = top_loop.get("count", 0)

            st.markdown(
                f"""
<div style="background:rgba(129,140,248,.08);border:1px solid rgba(129,140,248,.15);border-radius:14px;padding:16px;margin-bottom:15px;">
<div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#818CF8;margin-bottom:7px;">Strongest Loop</div>
<div style="font-size:14px;color:#E2E8F0;font-family:'JetBrains Mono',monospace;line-height:1.6;">
{sequence}
</div>
<div style="font-size:12px;color:#64748B;margin-top:6px;">
Repeated ×{count}
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

        if loop_items:
            for loop in loop_items[:5]:
                sequence = " → ".join(loop.get("sequence", []))
                count = loop.get("count", 0)

                st.markdown(
                    f"""
<div class="loop-row">
<div class="loop-seq">{sequence}</div>
<div style="font-size:11px;color:#475569;margin-top:3px;">repeated ×{count}</div>
</div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            empty("No repeated behavior loops detected yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Productivity DNA ──────────────────────────────────────────────────
    mission_items = missions.get("missions", [])
    mission_times = {
        item.get("mission", "Unknown"): item.get("time_seconds", 0)
        for item in mission_items
    }

    max_mission_time = max(mission_times.values()) if mission_times else 1

    def trait_score(*mission_names):
        total = sum(mission_times.get(name, 0) for name in mission_names)
        return min(5, max(0, round((total / max_mission_time) * 5)))

    traits = [
        ("Builder", trait_score("Build Drift"), "#22D3EE"),
        (
            "Researcher",
            trait_score("Career Growth", "Skill Development"),
            "#818CF8",
        ),
        (
            "Communicator",
            trait_score("Communication"),
            "#FB923C",
        ),
        (
            "Focus Recovery",
            min(5, max(0, round(recovery_score / 20))),
            "#34D399",
        ),
        (
            "Switch Control",
            min(5, max(0, round(switch_score / 20))),
            "#FBBF24",
        ),
    ]

    st.markdown(
        '<div class="card-purple"><div class="eyebrow">Productivity DNA</div>',
        unsafe_allow_html=True,
    )

    for trait, rating, color in traits:
        filled = "★" * rating
        empty_stars = "☆" * (5 - rating)

        st.markdown(
            f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid rgba(148,163,184,.06);">
<span style="font-size:14px;font-weight:700;color:#E2E8F0;">{trait}</span>
<span style="font-size:20px;letter-spacing:3px;color:{color};">{filled}<span style="color:#334155;">{empty_stars}</span></span>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Mission autopsy ──────────────────────────────────────────────────
    if autopsy and autopsy.get("mission"):
        success_probability = round(
            autopsy.get("success_probability", 0) * 100
        )

        st.markdown(
            '<div class="card-cyan"><div class="eyebrow">Mission Autopsy</div>',
            unsafe_allow_html=True,
        )

        left, right = st.columns([1.4, 1])

        with left:
            st.markdown(
                f"""
<div style="font-size:18px;font-weight:800;color:#F8FAFC;margin-bottom:10px;">
{autopsy.get("mission", "Unknown Mission")}
</div>
<div style="font-size:14px;color:#94A3B8;line-height:1.7;margin-bottom:18px;">
{autopsy.get("summary", "No summary available.")}
</div>
<div style="background:rgba(248,113,113,.07);border:1px solid rgba(248,113,113,.15);border-radius:12px;padding:14px;margin-bottom:12px;">
<div class="coach-lbl" style="color:#F87171;">Failure Signal</div>
<div style="font-size:13px;color:#CBD5E1;">{autopsy.get("failure_reason", "No major failure signal.")}</div>
</div>
<div style="background:rgba(52,211,153,.07);border:1px solid rgba(52,211,153,.15);border-radius:12px;padding:14px;">
<div class="coach-lbl" style="color:#34D399;">Recommendation</div>
<div style="font-size:13px;color:#CBD5E1;">{autopsy.get("recommendation", "Continue protecting focused sessions.")}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

        with right:
            probability_color = (
                "#34D399"
                if success_probability >= 60
                else "#FBBF24"
                if success_probability >= 40
                else "#F87171"
            )

            st.markdown(
                f"""
<div style="text-align:center;padding:14px 0 22px;">
<div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748B;margin-bottom:8px;">
Success Probability
</div>
<div style="font-size:60px;font-weight:900;font-family:'JetBrains Mono',monospace;color:{probability_color};">
{success_probability}%
</div>
</div>
                """,
                unsafe_allow_html=True,
            )

            autopsy_rows = [
                (
                    "Alignment",
                    f"{autopsy.get('mission_alignment_percentage', 0)}%",
                ),
                (
                    "Deep Work",
                    f"{autopsy.get('deep_work_minutes', 0)} min",
                ),
                (
                    "Abandonments",
                    autopsy.get("mission_abandonments", 0),
                ),
                (
                    "Recoveries",
                    autopsy.get("mission_recoveries", 0),
                ),
                (
                    "Recovery Cost",
                    f"{autopsy.get('estimated_recovery_cost_minutes', 0)} min",
                ),
            ]

            for label, value in autopsy_rows:
                st.markdown(
                    f"""
<div class="autopsy-row">
<span>{label}</span>
<span class="autopsy-val">{value}</span>
</div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Quick wins ────────────────────────────────────────────────────────
    recommendations = report.get("recommendations", [])

    if not recommendations:
        recommendations = [
            "Protect one uninterrupted focus block tomorrow.",
            "Reduce unnecessary application switching.",
            "Finish the current mission before starting another.",
            "Review your highest-risk distraction period.",
        ]

    st.markdown(
        '<div class="card"><div class="eyebrow">Quick Wins for Tomorrow</div>',
        unsafe_allow_html=True,
    )

    for recommendation in recommendations[:6]:
        st.markdown(
            f"""
<div class="rec-item">
<div class="rec-arrow">✓</div>
<div>{recommendation}</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
# ── Page 4: Daily Report ──────────────────────────────────────────────────────

def render_daily_report():
    report = api("/daily-report") or {}
    coach = api("/coach") or {}
    score = api("/score") or {}
    dw = api("/deep-work") or {}
    drift = api("/drift") or {}
    recovery = api("/recovery-cost") or {}
    replay = api("/replay") or {}

    today = datetime.now().strftime("%A, %B %d")

    overall = score.get("overall_score", 0)
    grade = score.get("grade", "N/A")
    focus_score = score.get("focus_score", 0)
    mission_score = score.get("mission_score", 0)
    recovery_score = score.get("recovery_score", 0)
    switch_score = score.get("switch_score", 0)

    deep_minutes = dw.get("total_deep_work_minutes", 0)
    deep_sessions = dw.get("count", len(dw.get("sessions", [])))

    context_switches = report.get("context_switches", 0)
    top_mission = report.get("top_mission", "Unknown")
    recommendations = report.get("recommendations", [])

    productive_seconds = drift.get("productive_time", 0)
    productive_minutes = round(productive_seconds / 60, 1)
    drift_index = drift.get("drift_index", 0)

    recovery_events = recovery.get("count", 0)
    recovery_cost = round(
        recovery.get("total_recovery_cost_seconds", 0) / 60,
        1,
    )

    replay_events = replay.get("events", [])
    focus_lost_count = sum(
        1 for event in replay_events
        if event.get("event_type") == "focus_lost"
    )
    recovered_count = sum(
        1 for event in replay_events
        if event.get("event_type") == "recovered"
    )

    executive_summary = report.get(
        "executive_summary",
        (
            f"You completed {productive_minutes} productive minutes today. "
            f"Your dominant mission was {top_mission}, with "
            f"{context_switches} context switches."
        ),
    )

    st.markdown(
        f"""
<div style="margin-bottom:24px;">
<div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">
Daily Report · {today}
</div>
<div class="page-title">Your day, decoded.</div>
<div class="page-sub">
A complete summary of your productivity, focus quality, recovery, and next steps.
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ── Hero summary ─────────────────────────────────────────────────────
    score_color = (
        "#34D399"
        if overall >= 75
        else "#FBBF24"
        if overall >= 50
        else "#F87171"
    )

    st.markdown(
        f"""
<div style="
background:linear-gradient(135deg,rgba(34,211,238,.11),rgba(129,140,248,.07));
border:1px solid rgba(34,211,238,.2);
border-radius:24px;
padding:30px;
margin-bottom:22px;
">
<div style="display:flex;justify-content:space-between;align-items:center;gap:28px;">
<div style="flex:1;">
<div class="eyebrow">Executive Summary</div>
<div style="font-size:18px;color:#E2E8F0;line-height:1.75;font-weight:600;">
{executive_summary}
</div>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:20px;">
<span class="grade-pill">{productive_minutes} productive min</span>
<span class="grade-pill">{deep_minutes} deep-work min</span>
<span class="grade-pill">{context_switches} switches</span>
<span class="grade-pill">Drift {drift_index}</span>
</div>
</div>

<div style="
width:145px;
height:145px;
border-radius:50%;
background:conic-gradient(
{score_color} {min(max(overall, 0), 100) * 3.6}deg,
rgba(30,41,59,.9) 0deg
);
display:flex;
align-items:center;
justify-content:center;
flex-shrink:0;
">
<div style="
width:112px;
height:112px;
border-radius:50%;
background:#0B1120;
display:flex;
align-items:center;
justify-content:center;
flex-direction:column;
">
<div style="
font-size:38px;
font-weight:900;
font-family:'JetBrains Mono',monospace;
color:{score_color};
">
{overall}
</div>
<div style="
font-size:11px;
font-weight:800;
color:#94A3B8;
letter-spacing:.08em;
">
GRADE {grade}
</div>
</div>
</div>
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ── Primary statistics ───────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    stats = [
        (
            "Productive Time",
            f"{productive_minutes} min",
            f"focus score {focus_score}",
        ),
        (
            "Deep Work",
            f"{deep_minutes} min",
            f"{deep_sessions} session(s)",
        ),
        (
            "Focus Lost",
            str(focus_lost_count),
            f"{recovered_count} recoveries",
        ),
        (
            "Recovery Cost",
            f"{recovery_cost} min",
            f"{recovery_events} event(s)",
        ),
    ]

    for col, (label, value, subtitle) in zip(
        [c1, c2, c3, c4],
        stats,
    ):
        with col:
            st.markdown(
                f"""
<div class="stat-tile" style="margin-bottom:18px;">
<div class="stat-label">{label}</div>
<div class="stat-value" style="font-size:23px;">{value}</div>
<div class="stat-sub">{subtitle}</div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # ── Score breakdown + AI coach ──────────────────────────────────────
    left, right = st.columns([1.15, 1])

    with left:
        score_rows = [
            ("Focus", focus_score, "#22D3EE"),
            ("Mission Alignment", mission_score, "#818CF8"),
            ("Recovery", recovery_score, "#34D399"),
            ("Switch Control", switch_score, "#FB923C"),
        ]

        html = """
<div class="card">
<div class="eyebrow">Performance Breakdown</div>
        """

        for label, value, color in score_rows:
            safe_value = min(max(value, 0), 100)

            html += f"""
<div style="margin-bottom:19px;">
<div style="
display:flex;
justify-content:space-between;
font-size:13px;
color:#94A3B8;
margin-bottom:7px;
">
<span>{label}</span>
<span style="
font-family:'JetBrains Mono',monospace;
font-weight:700;
color:#E2E8F0;
">
{value}%
</span>
</div>
<div style="
height:9px;
background:rgba(30,41,59,.9);
border-radius:999px;
overflow:hidden;
">
<div style="
width:{safe_value}%;
height:100%;
background:{color};
border-radius:999px;
"></div>
</div>
</div>
            """

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with right:
        advice = coach.get("advice", [])

        st.markdown(
            '<div class="card-cyan"><div class="eyebrow">AI Coach</div>',
            unsafe_allow_html=True,
        )

        if advice:
            primary = advice[0]

            st.markdown(
                f"""
<div style="
font-size:18px;
font-weight:800;
color:#F8FAFC;
margin-bottom:12px;
">
🎯 Your priority for tomorrow
</div>

<div style="
font-size:14px;
color:#CBD5E1;
line-height:1.7;
margin-bottom:12px;
">
{primary.get("observation", "Your workday has been analysed.")}
</div>

<div style="
font-size:13px;
color:#64748B;
line-height:1.7;
margin-bottom:16px;
">
{primary.get("impact", "")}
</div>

<div style="
background:rgba(34,211,238,.08);
border:1px solid rgba(34,211,238,.18);
border-radius:14px;
padding:15px;
font-size:14px;
color:#E2E8F0;
line-height:1.65;
">
💡 {primary.get("suggestion", "Protect one focused work block tomorrow.")}
</div>
                """,
                unsafe_allow_html=True,
            )
        else:
            empty("No coaching advice available yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Mission + recovery story ────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.markdown(
            f"""
<div class="card-purple">
<div class="eyebrow">Dominant Mission</div>
<div style="
font-size:25px;
font-weight:900;
color:#F8FAFC;
margin-bottom:10px;
">
{top_mission}
</div>
<div style="
font-size:13px;
color:#64748B;
line-height:1.7;
">
This was the primary focus area detected across your tracked sessions.
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        recovery_rate = 0

        if focus_lost_count:
            recovery_rate = round(
                recovered_count / focus_lost_count * 100,
                1,
            )

        recovery_color = (
            "#34D399"
            if recovery_rate >= 75
            else "#FBBF24"
            if recovery_rate >= 40
            else "#F87171"
        )

        st.markdown(
            f"""
<div class="card">
<div class="eyebrow">Recovery Story</div>
<div style="
font-size:38px;
font-weight:900;
font-family:'JetBrains Mono',monospace;
color:{recovery_color};
margin-bottom:8px;
">
{recovery_rate}%
</div>
<div style="
font-size:13px;
color:#64748B;
line-height:1.7;
">
You recovered after {recovered_count} of {focus_lost_count}
detected focus-loss sessions.
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    # ── Focus timeline summary ───────────────────────────────────────────
    st.markdown(
        '<div class="card"><div class="eyebrow">Focus Timeline Summary</div>',
        unsafe_allow_html=True,
    )

    if replay_events:
        color_map = {
            "start": "#22D3EE",
            "focused": "#818CF8",
            "recovered": "#34D399",
            "focus_lost": "#F87171",
        }

        event_blocks = []

        for event in replay_events[:120]:
            event_type = event.get("event_type", "focused")
            color = color_map.get(event_type, "#64748B")
            mission = event.get("mission", "Unknown")
            duration = event.get("duration_minutes", 0)

            event_blocks.append(
                f'<span title="{mission} · {duration} min" '
                f'style="display:inline-block;width:14px;height:14px;'
                f'border-radius:4px;background:{color};"></span>'
            )

        blocks_html = "".join(event_blocks)

        st.markdown(
            f"""
<div style="display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-top:4px;">
{blocks_html}
</div>
<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:#64748B;margin-top:18px;">
<span>🚀 Start</span>
<span>💻 Focused</span>
<span>✅ Recovered</span>
<span>⚠️ Focus Lost</span>
</div>
            """,
            unsafe_allow_html=True,
        )

    else:
        empty("No timeline activity available.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Recommendations ──────────────────────────────────────────────────
    st.markdown(
        '<div class="card"><div class="eyebrow">Recommendations for Tomorrow</div>',
        unsafe_allow_html=True,
    )

    if not recommendations:
        recommendations = [
            "Begin with one uninterrupted 30-minute focus block.",
            "Avoid switching applications while working on your main mission.",
            "Schedule distracting communication into specific time windows.",
            "Take a deliberate short break before fatigue becomes drift.",
        ]

    for index, recommendation in enumerate(recommendations[:6], start=1):
        st.markdown(
            f"""
<div style="
display:flex;
align-items:flex-start;
gap:13px;
padding:13px 0;
border-bottom:1px solid rgba(148,163,184,.06);
">
<div style="
width:26px;
height:26px;
border-radius:8px;
background:rgba(34,211,238,.1);
border:1px solid rgba(34,211,238,.16);
display:flex;
align-items:center;
justify-content:center;
color:#22D3EE;
font-size:12px;
font-weight:800;
flex-shrink:0;
">
{index}
</div>
<div style="
font-size:14px;
color:#CBD5E1;
line-height:1.65;
padding-top:2px;
">
{recommendation}
</div>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)
    
    
    # ── End-of-day message ───────────────────────────────────────────────
    message = (
        "Strong day. Protect the habits that created your focused sessions."
        if overall >= 75
        else
        "A mixed day. Tomorrow, reduce switching and protect one clear mission."
        if overall >= 50
        else
        "Today was fragmented. Reset tomorrow with one small, uninterrupted goal."
    )

    st.markdown(
        f"""
<div style="
text-align:center;
padding:26px;
border-radius:18px;
border:1px solid rgba(148,163,184,.08);
background:rgba(13,20,35,.55);
margin-top:4px;
">
<div style="
font-size:10px;
font-weight:800;
letter-spacing:.12em;
text-transform:uppercase;
color:#22D3EE;
margin-bottom:9px;
">
End of Report
</div>
<div style="
font-size:17px;
font-weight:700;
color:#E2E8F0;
">
{message}
</div>
</div>
        """,
        unsafe_allow_html=True,
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