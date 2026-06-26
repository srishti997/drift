import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import hashlib
import json
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

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

for k, v in [("authenticated",False),("username",""),("display_name",""),
             ("auth_tab","login"),("active_page","Overview"),("last_refresh",None)]:
    if k not in st.session_state: st.session_state[k] = v

MISSION_COLORS = {
    "Build Drift":"#22D3EE","Career Growth":"#818CF8","Skill Development":"#34D399",
    "Break / Distraction":"#F87171","Communication":"#FB923C","Unclassified Mission":"#64748B",
}

def mcolor(m): return MISSION_COLORS.get(m,"#94A3B8")

def empty(msg):
    st.markdown(f'<div style="color:#334155;padding:24px 0;text-align:center;font-size:13px;">{msg}</div>',
                unsafe_allow_html=True)

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

        pages = [("🧠","Overview"),("🔬","Deep Dive"),("🔮","Intelligence"),("📋","Daily Report")]
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
            st.markdown(f"<div style='font-size:10px;color:#334155;text-align:center;margin-top:4px;'>Auto-refreshes every 30s · {ts}</div>",
                        unsafe_allow_html=True)

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
    score    = api("/score")
    missions = api("/missions")
    dw       = api("/deep-work")
    report   = api("/daily-report")
    drift    = api("/drift")
    coach    = api("/coach")
    predict  = api("/predict")

    overall     = score.get("overall_score",0) if score else 0
    grade       = score.get("grade","N/A") if score else "N/A"
    focus_s     = score.get("focus_score",0) if score else 0
    mission_s   = score.get("mission_score",0) if score else 0
    recovery_s  = score.get("recovery_score",0) if score else 0
    switch_s    = score.get("switch_score",0) if score else 0
    summary_txt = score.get("summary","") if score else ""
    deep_min    = dw.get("total_deep_work_minutes",0) if dw else 0
    deep_sess   = dw.get("count",0) if dw else 0
    ctx         = report.get("context_switches",0) if report else 0
    top_m       = report.get("top_mission","—") if report else "—"
    drift_idx   = drift.get("drift_index",0) if drift else 0
    prod_min    = (drift.get("productive_time",0)//60) if drift else 0
    focus_ratio = drift.get("focus_score",0) if drift else 0

    fname = st.session_state.display_name.split()[0] if st.session_state.display_name else "there"
    hour  = datetime.now().hour
    gr    = "Good morning" if hour<12 else ("Good afternoon" if hour<17 else "Good evening")

    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Overview</div>
        <div class="page-title">{gr}, {fname}.</div>
        <div class="page-sub">Here's how your focus held up today.</div>
    </div>""", unsafe_allow_html=True)

    # Row 1: Score · Breakdown · Drift
    c1, c2, c3 = st.columns([1,1.5,1])
    with c1:
        st.markdown(f"""
        <div class="card-cyan" style="text-align:center;padding:32px 16px;">
            <div class="eyebrow" style="text-align:center;">Productivity Score</div>
            <div class="score-big">{overall}</div>
            <div class="grade-pill">Grade {grade}</div>
            <div style="font-size:12px;color:#475569;margin-top:14px;line-height:1.5;">{summary_txt}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        bars = [("Focus",focus_s,"linear-gradient(90deg,#0891B2,#22D3EE)"),
                ("Mission Alignment",mission_s,"linear-gradient(90deg,#4338CA,#818CF8)"),
                ("Recovery",recovery_s,"linear-gradient(90deg,#059669,#34D399)"),
                ("Switch Control",switch_s,"linear-gradient(90deg,#C2410C,#FB923C)")]
        html = '<div class="card"><div class="eyebrow">Score Breakdown</div>'
        for lbl,val,grad in bars:
            html += f'<div class="bar-wrap"><div class="bar-row"><span>{lbl}</span><span class="bar-val">{val}</span></div><div class="bar-track"><div class="bar-fill" style="width:{val}%;background:{grad};"></div></div></div>'
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with c3:
        if drift_idx<25:   dc,dl,de="db-green","Stable","🟢"
        elif drift_idx<50: dc,dl,de="db-yellow","Minor Drift","🟡"
        elif drift_idx<75: dc,dl,de="db-orange","Significant","🟠"
        else:              dc,dl,de="db-red","Critical","🔴"
        st.markdown(f"""
        <div class="card" style="text-align:center;padding:32px 16px;">
            <div class="eyebrow" style="text-align:center;">Drift Index</div>
            <div class="drift-num" style="color:#F1F5F9;">{drift_idx}</div>
            <div><span class="dbadge {dc}">{de} {dl}</span></div>
            <div style="font-size:11px;color:#334155;margin-top:12px;">Fragmentation · lower is better</div>
        </div>""", unsafe_allow_html=True)

    # Row 2: Stat tiles
    t1,t2,t3,t4 = st.columns(4)
    for col,lbl,val,sub in [
        (t1,"Deep Work",f"{deep_min} min",f"{deep_sess} session{'s' if deep_sess!=1 else ''}"),
        (t2,"Context Switches",str(ctx),"goal changes today"),
        (t3,"Top Mission",top_m,"primary focus area"),
        (t4,"Productive Time",f"{prod_min} min",f"{focus_ratio}% focus ratio"),
    ]:
        with col:
            st.markdown(f'<div class="stat-tile"><div class="stat-label">{lbl}</div><div class="stat-value">{val}</div><div class="stat-sub">{sub}</div></div>',
                        unsafe_allow_html=True)

    st.write("")

    # Row 3: Prediction banner
    if predict:
        rl    = predict.get("risk_level","LOW")
        rs    = predict.get("risk_score",0)
        sp    = int(predict.get("success_probability",1)*100)
        pred  = predict.get("prediction","")
        pr    = predict.get("primary_risk","")
        rc    = {"LOW":"risk-low","MEDIUM":"risk-med","HIGH":"risk-high","CRITICAL":"risk-crit"}.get(rl,"risk-low")
        bcolor= {"LOW":"rgba(5,150,105,.08)","MEDIUM":"rgba(217,119,6,.08)",
                 "HIGH":"rgba(234,88,12,.08)","CRITICAL":"rgba(185,28,28,.08)"}.get(rl,"rgba(5,150,105,.08)")
        bcol2 = {"LOW":"rgba(5,150,105,.2)","MEDIUM":"rgba(217,119,6,.2)",
                 "HIGH":"rgba(234,88,12,.2)","CRITICAL":"rgba(185,28,28,.2)"}.get(rl,"rgba(5,150,105,.2)")
        st.markdown(f"""
        <div style="background:{bcolor};border:1px solid {bcol2};border-radius:16px;padding:18px 24px;margin-bottom:18px;display:flex;align-items:center;gap:20px;">
            <div>
                <div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748B;margin-bottom:4px;">Drift Risk Prediction</div>
                <div style="font-size:14px;color:#CBD5E1;line-height:1.5;">{pred}</div>
                <div style="font-size:12px;color:#475569;margin-top:4px;">{pr}</div>
            </div>
            <div style="text-align:center;flex-shrink:0;">
                <div style="font-size:32px;font-weight:900;font-family:'JetBrains Mono',monospace;color:#F1F5F9;">{sp}%</div>
                <div style="font-size:11px;color:#475569;">success prob.</div>
                <span class="risk-pill {rc}" style="margin-top:6px;">{rl}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    # Row 4: Mission pie + Coach
    cp,cc = st.columns([1.2,1])
    with cp:
        st.markdown('<div class="card"><div class="eyebrow">Mission Breakdown</div>', unsafe_allow_html=True)
        items = missions.get("missions",[]) if missions else []
        if items:
            df  = pd.DataFrame(items)
            fig = px.pie(df,names="mission",values="time_seconds",hole=0.52,
                         color_discrete_sequence=["#22D3EE","#818CF8","#34D399","#FB923C","#F472B6","#FBBF24"])
            fig.update_traces(textposition="inside",textinfo="percent+label",textfont=dict(color="white",size=11))
            fig.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",font_color="white",
                              showlegend=False,margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig,use_container_width=True)
        else: empty("No mission data yet — run the tracker first.")
        st.markdown("</div>", unsafe_allow_html=True)

    with cc:
        st.markdown('<div class="card"><div class="eyebrow">AI Coach</div>', unsafe_allow_html=True)
        advice = coach.get("advice",[]) if coach else []
        if advice:
            for item in advice[:3]:
                st.markdown(f"""
                <div class="coach-card">
                    <div class="coach-lbl">Observation</div><div class="coach-txt">{item.get('observation','')}</div>
                    <div class="coach-lbl">Suggestion</div><div class="coach-txt" style="margin-bottom:0">{item.get('suggestion','')}</div>
                </div>""", unsafe_allow_html=True)
        else: empty("No coaching advice yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Page 2: Deep Dive ─────────────────────────────────────────────────────────

def render_deep_dive():
    timeline = api("/timeline")
    dw       = api("/deep-work")
    switches = api("/context-switches")
    patterns = api("/patterns")
    recovery = api("/recovery-cost")

    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Deep Dive</div>
        <div class="page-title">What actually happened.</div>
        <div class="page-sub">Session-by-session breakdown of your focus, intent, and context switching.</div>
    </div>""", unsafe_allow_html=True)

    # Deep Work Sessions
    st.markdown('<div class="card"><div class="eyebrow">Deep Work Sessions</div>', unsafe_allow_html=True)
    sessions = dw.get("sessions",[]) if dw else []
    if sessions:
        for i,s in enumerate(sessions):
            dur    = round(s.get("duration_seconds",0)/60,1)
            intent = s.get("dominant_intent","—")
            apps   = ", ".join(list(s.get("apps",{}).keys())[:3]) or "—"
            start  = s.get("start_time","")[:16].replace("T","  ") if s.get("start_time") else "—"
            st.markdown(f"""
            <div class="dw-row">
                <div class="dw-num">#{i+1}</div>
                <div style="flex:1;"><div class="dw-intent">{intent}</div><div class="dw-meta">{start} · {apps}</div></div>
                <div style="text-align:right;"><div class="dw-dur">{dur}m</div><div style="font-size:10px;color:#334155;">uninterrupted</div></div>
            </div>""", unsafe_allow_html=True)
    else: empty("No deep work sessions yet. Aim for 30+ uninterrupted minutes.")
    st.markdown("</div>", unsafe_allow_html=True)

    sc,sp = st.columns(2)

    with sc:
        st.markdown('<div class="card"><div class="eyebrow">Context Switch Analysis</div>', unsafe_allow_html=True)
        if switches:
            total   = switches.get("total_switches",0)
            distrac = switches.get("distraction_switches",0)
            goal_sw = switches.get("goal_aligned_switches",switches.get("goal_switches",0))
            loss_m  = round(switches.get("estimated_focus_loss_seconds",0)/60,1)
            for lbl,val,col in [
                ("Total Switches",total,"#F1F5F9"),("Distraction Switches",distrac,"#F87171"),
                ("Goal-Aligned",goal_sw,"#34D399"),("Est. Focus Lost",f"{loss_m} min","#FBBF24"),
            ]:
                st.markdown(f'<div class="sw-row"><span>{lbl}</span><span class="sw-val" style="color:{col};">{val}</span></div>',
                            unsafe_allow_html=True)
            if switches.get("insight"):
                st.markdown(f"<div style='font-size:12px;color:#475569;margin-top:12px;'>{switches['insight']}</div>",
                            unsafe_allow_html=True)
            sw_list = switches.get("switches",[])
            if sw_list:
                st.markdown("<div style='margin-top:16px;'><div class='eyebrow'>Recent Switch Flow</div>", unsafe_allow_html=True)
                for sw in sw_list[-6:]:
                    c = "#F87171" if sw.get("is_distraction") else "#34D399"
                    a = "⚡" if sw.get("is_distraction") else "→"
                    st.markdown(f"""
                    <div style="font-size:11px;padding:5px 0;border-bottom:1px solid rgba(148,163,184,.05);display:flex;gap:6px;align-items:center;">
                        <span style="color:#64748B;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{sw.get('from_goal','?')}</span>
                        <span style="color:{c};">{a}</span>
                        <span style="color:{c};flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right;">{sw.get('to_goal','?')}</span>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: empty("No switch data yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with sp:
        st.markdown('<div class="card"><div class="eyebrow">Behavioral Patterns</div>', unsafe_allow_html=True)
        pats = patterns.get("patterns",[]) if patterns else []
        icons = {"Mission Abandonment":"⚠️","Mission Recovery":"✅","App Ping-Pong":"🔁","Deep Work":"🔥"}
        if pats:
            for p in pats:
                pt,cnt,desc = p.get("type",""),p.get("count",0),p.get("description","")
                st.markdown(f"""
                <div class="pat-row">
                    <div class="pat-head"><span>{icons.get(pt,'◆')}</span><span class="pat-name">{pt}</span><span class="pat-count">×{cnt}</span></div>
                    <div class="pat-desc">{desc}</div>
                </div>""", unsafe_allow_html=True)
            if patterns.get("insight"):
                st.markdown(f"<div style='font-size:12px;color:#334155;margin-top:12px;'>{patterns['insight']}</div>",
                            unsafe_allow_html=True)
        else: empty("No patterns detected yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Recovery Cost
    if recovery and recovery.get("count",0) > 0:
        st.markdown('<div class="card-red"><div class="eyebrow">Recovery Cost Analysis</div>', unsafe_allow_html=True)
        rc1,rc2,rc3 = st.columns(3)
        for col,lbl,val,sub in [
            (rc1,"Recovery Events",str(recovery.get("count",0)),"distraction interruptions"),
            (rc2,"Total Cost",f"{round(recovery.get('total_recovery_cost_seconds',0)/60,1)} min","estimated focus lost"),
            (rc3,"Avg Cost",f"{round(recovery.get('average_recovery_cost_seconds',0)/60,1)} min","per recovery event"),
        ]:
            with col:
                st.markdown(f'<div class="stat-tile"><div class="stat-label">{lbl}</div><div class="stat-value">{val}</div><div class="stat-sub">{sub}</div></div>',
                            unsafe_allow_html=True)
        if recovery.get("insight"):
            st.markdown(f"<div style='font-size:13px;color:#94A3B8;margin-top:14px;'>{recovery['insight']}</div>",
                        unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Cognitive Timeline
    st.write("")
    st.markdown('<div class="card"><div class="eyebrow">Cognitive Timeline — click to expand</div>', unsafe_allow_html=True)
    tl_items = timeline.get("timeline",[]) if timeline else []
    if tl_items:
        for block in tl_items:
            mission  = block.get("mission","Unknown")
            dur_s    = block.get("duration_seconds",0)
            dur_m    = round(dur_s/60,1)
            goals    = block.get("goals",{})
            apps     = block.get("apps",{})
            color    = mcolor(mission)
            top_goal = max(goals,key=goals.get) if goals else "—"
            with st.expander(f"{mission}  ·  {dur_m}m  ·  {top_goal}", expanded=False):
                g1,g2 = st.columns(2)
                with g1:
                    st.markdown("**Goals**")
                    for g,secs in sorted(goals.items(),key=lambda x:-x[1]):
                        pct = round(secs/dur_s*100) if dur_s else 0
                        st.markdown(f"""<div style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;font-size:12px;color:#94A3B8;margin-bottom:3px;"><span>{g}</span><span>{round(secs/60,1)}m</span></div><div style="background:rgba(30,41,59,.8);border-radius:100px;height:5px;"><div style="width:{pct}%;height:100%;background:{color};border-radius:100px;"></div></div></div>""",
                                    unsafe_allow_html=True)
                with g2:
                    st.markdown("**Apps**")
                    for a,secs in sorted(apps.items(),key=lambda x:-x[1])[:5]:
                        pct = round(secs/dur_s*100) if dur_s else 0
                        st.markdown(f"""<div style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;font-size:12px;color:#94A3B8;margin-bottom:3px;"><span>{a}</span><span>{round(secs/60,1)}m</span></div><div style="background:rgba(30,41,59,.8);border-radius:100px;height:5px;"><div style="width:{pct}%;height:100%;background:{color};border-radius:100px;"></div></div></div>""",
                                    unsafe_allow_html=True)
    else: empty("No timeline data yet.")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Page 3: Intelligence ──────────────────────────────────────────────────────

def render_intelligence():
    predict  = api("/predict")
    loops    = api("/loops")
    next_app = api("/next-app")
    bgraph   = api("/behavior-graph")
    autopsy  = api("/autopsy")

    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Intelligence</div>
        <div class="page-title">Prediction & behavioral analysis.</div>
        <div class="page-sub">ML-powered signals — drift risk, behavior loops, and mission autopsy.</div>
    </div>""", unsafe_allow_html=True)

    # Mission Autopsy
    if autopsy and autopsy.get("mission"):
        st.markdown('<div class="card-cyan"><div class="eyebrow">Mission Autopsy</div>', unsafe_allow_html=True)
        a1,a2 = st.columns([1.4,1])
        with a1:
            sp_val = int(autopsy.get("success_probability",0)*100)
            fr     = autopsy.get("failure_reason","—")
            rec    = autopsy.get("recommendation","—")
            summ   = autopsy.get("summary","")
            st.markdown(f"""
            <div style="font-size:15px;color:#CBD5E1;line-height:1.6;margin-bottom:16px;">{summ}</div>
            <div style="background:rgba(34,211,238,.06);border:1px solid rgba(34,211,238,.12);border-radius:12px;padding:14px 16px;margin-bottom:12px;">
                <div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#22D3EE;margin-bottom:4px;">Failure Signal</div>
                <div style="font-size:14px;color:#F87171;font-weight:600;">{fr}</div>
            </div>
            <div style="background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.12);border-radius:12px;padding:14px 16px;">
                <div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#34D399;margin-bottom:4px;">Recommendation</div>
                <div style="font-size:13px;color:#94A3B8;">{rec}</div>
            </div>""", unsafe_allow_html=True)
        with a2:
            st.markdown(f"""
            <div style="text-align:center;padding:20px 0;">
                <div style="font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#64748B;margin-bottom:8px;">Success Probability</div>
                <div style="font-size:64px;font-weight:900;font-family:'JetBrains Mono',monospace;color:{'#34D399' if sp_val>=60 else '#FBBF24' if sp_val>=40 else '#F87171'};">{sp_val}%</div>
            </div>""", unsafe_allow_html=True)
            rows = [
                ("Mission",autopsy.get("mission","—")),
                ("Alignment",f"{autopsy.get('mission_alignment_percentage',0)}%"),
                ("Deep Work",f"{autopsy.get('deep_work_minutes',0)} min"),
                ("Abandonments",str(autopsy.get("mission_abandonments",0))),
                ("Recoveries",str(autopsy.get("mission_recoveries",0))),
                ("Recovery Cost",f"{autopsy.get('estimated_recovery_cost_minutes',0)} min"),
            ]
            for lbl,val in rows:
                st.markdown(f'<div class="autopsy-row"><span>{lbl}</span><span class="autopsy-val">{val}</span></div>',
                            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Prediction + Next App
    p1,p2 = st.columns([1.3,1])
    with p1:
        st.markdown('<div class="card-purple"><div class="eyebrow">Drift Risk Prediction</div>', unsafe_allow_html=True)
        if predict:
            rl = predict.get("risk_level","LOW")
            rs = predict.get("risk_score",0)
            sp = int(predict.get("success_probability",1)*100)
            conf = int(predict.get("confidence",0)*100)
            rc = {"LOW":"risk-low","MEDIUM":"risk-med","HIGH":"risk-high","CRITICAL":"risk-crit"}.get(rl,"risk-low")

            pr1,pr2 = st.columns([1,1])
            with pr1:
                st.markdown(f"""
                <div style="text-align:center;padding:10px 0;">
                    <div style="font-size:48px;font-weight:900;font-family:'JetBrains Mono',monospace;color:#818CF8;">{rs}</div>
                    <div style="font-size:11px;color:#475569;">risk score</div>
                    <span class="risk-pill {rc}" style="margin-top:8px;display:inline-flex;">{rl}</span>
                </div>""", unsafe_allow_html=True)
            with pr2:
                st.markdown(f"""
                <div style="padding:10px 0;">
                    <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:6px;">Current Mission</div>
                    <div style="font-size:14px;font-weight:600;color:#E2E8F0;margin-bottom:14px;">{predict.get('current_mission','—')}</div>
                    <div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#64748B;margin-bottom:6px;">Confidence</div>
                    <div style="font-size:14px;font-weight:600;color:#818CF8;">{conf}%</div>
                </div>""", unsafe_allow_html=True)

            reasons = predict.get("risk_reasons",[])
            if reasons:
                st.markdown('<div style="margin-top:12px;"><div class="eyebrow">Risk Signals</div>', unsafe_allow_html=True)
                for r in reasons:
                    st.markdown(f'<div style="font-size:12px;color:#94A3B8;padding:5px 0;border-bottom:1px solid rgba(148,163,184,.06);">⚠ {r}</div>',
                                unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: empty("Not enough data for prediction.")
        st.markdown("</div>", unsafe_allow_html=True)

    with p2:
        st.markdown('<div class="card"><div class="eyebrow">Next App Prediction</div>', unsafe_allow_html=True)
        if next_app and next_app.get("predicted_next_app"):
            conf2 = int(next_app.get("confidence",0)*100)
            seq   = " → ".join(next_app.get("current_sequence",[]))
            pred_app = next_app.get("predicted_next_app","—")
            st.markdown(f"""
            <div style="text-align:center;padding:16px 0;">
                <div style="font-size:11px;color:#64748B;margin-bottom:8px;">Current pattern</div>
                <div style="font-size:13px;color:#818CF8;font-family:'JetBrains Mono',monospace;margin-bottom:16px;">{seq}</div>
                <div style="font-size:11px;color:#64748B;margin-bottom:4px;">Likely next</div>
                <div style="font-size:22px;font-weight:800;color:#22D3EE;font-family:'JetBrains Mono',monospace;">{pred_app}</div>
                <div style="font-size:13px;color:#475569;margin-top:6px;">{conf2}% confidence</div>
            </div>
            <div style="font-size:13px;color:#64748B;padding:12px;background:rgba(34,211,238,.04);border-radius:10px;margin-top:8px;">{next_app.get('insight','')}</div>""",
            unsafe_allow_html=True)
        else: empty("Not enough patterns to predict next app.")
        st.markdown("</div>", unsafe_allow_html=True)

    # Behavior Loops + Graph
    bl,bg = st.columns(2)
    with bl:
        st.markdown('<div class="card"><div class="eyebrow">Behavior Loops</div>', unsafe_allow_html=True)
        loop_list = loops.get("loops",[]) if loops else []
        if loop_list:
            top = loops.get("top_loop")
            if top:
                st.markdown(f"""
                <div style="background:rgba(129,140,248,.08);border:1px solid rgba(129,140,248,.15);border-radius:12px;padding:14px;margin-bottom:16px;">
                    <div style="font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#818CF8;margin-bottom:6px;">Strongest Loop</div>
                    <div style="font-size:14px;font-family:'JetBrains Mono',monospace;color:#E2E8F0;">{' → '.join(top['sequence'])}</div>
                    <div style="font-size:12px;color:#64748B;margin-top:4px;">×{top['count']} occurrences</div>
                </div>""", unsafe_allow_html=True)
            for loop in loop_list[:5]:
                seq = " → ".join(loop["sequence"])
                st.markdown(f"""
                <div class="loop-row">
                    <div class="loop-seq">{seq}</div>
                    <div style="font-size:11px;color:#475569;margin-top:2px;">repeated ×{loop['count']}</div>
                </div>""", unsafe_allow_html=True)
            if loops.get("insight"):
                st.markdown(f"<div style='font-size:12px;color:#334155;margin-top:12px;'>{loops['insight']}</div>",
                            unsafe_allow_html=True)
        else: empty("No repeated behavior loops detected yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    with bg:
        st.markdown('<div class="card"><div class="eyebrow">App Transition Graph</div>', unsafe_allow_html=True)
        if bgraph and bgraph.get("edges"):
            edges = bgraph["edges"][:8]
            df_e  = pd.DataFrame(edges)
            fig   = px.bar(df_e, x="count", y=df_e.apply(lambda r: f"{r['from_app']} → {r['to_app']}",axis=1),
                           orientation="h",
                           color="count", color_continuous_scale=["#1E3A5F","#22D3EE"])
            fig.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", font_color="#94A3B8",
                              showlegend=False, xaxis_title="", yaxis_title="",
                              coloraxis_showscale=False,
                              margin=dict(l=0,r=0,t=0,b=0),
                              yaxis=dict(tickfont=dict(size=10,color="#64748B")),
                              xaxis=dict(gridcolor="rgba(148,163,184,.08)"),
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            if bgraph.get("insight"):
                st.markdown(f"<div style='font-size:12px;color:#475569;margin-top:4px;'>{bgraph['insight']}</div>",
                            unsafe_allow_html=True)
        else: empty("Not enough app transitions yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# ── Page 4: Daily Report ──────────────────────────────────────────────────────

def render_daily_report():
    report = api("/daily-report")
    coach  = api("/coach")
    score  = api("/score")
    dw     = api("/deep-work")

    today = datetime.now().strftime("%A, %B %d")
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:#22D3EE;text-transform:uppercase;margin-bottom:6px;">Daily Report · {today}</div>
        <div class="page-title">End-of-day intelligence.</div>
        <div class="page-sub">Your full behavioral summary with AI coaching recommendations.</div>
    </div>""", unsafe_allow_html=True)

    summary = report.get("executive_summary","No report yet. Run the tracker and check back.") if report else "No data yet."
    st.markdown(f"""
    <div class="card-cyan">
        <div class="eyebrow">Executive Summary</div>
        <div style="font-size:15px;color:#CBD5E1;line-height:1.75;">{summary}</div>
    </div>""", unsafe_allow_html=True)

    overall = score.get("overall_score",0) if score else 0
    grade   = score.get("grade","—") if score else "—"
    dw_min  = dw.get("total_deep_work_minutes",0) if dw else 0
    dw_sess = dw.get("count",0) if dw else 0
    ctx     = report.get("context_switches",0) if report else 0
    top_m   = report.get("top_mission","—") if report else "—"

    s1,s2,s3,s4 = st.columns(4)
    for col,lbl,val,sub in [
        (s1,"Final Score",f"{overall}/100",f"Grade {grade}"),
        (s2,"Deep Work",f"{dw_min} min",f"{dw_sess} sessions"),
        (s3,"Context Switches",str(ctx),"goal changes"),
        (s4,"Top Mission",top_m,"dominant focus"),
    ]:
        with col:
            st.markdown(f'<div class="stat-tile" style="text-align:center;margin-bottom:18px;"><div class="stat-label">{lbl}</div><div class="stat-value" style="font-size:22px;">{val}</div><div class="stat-sub">{sub}</div></div>',
                        unsafe_allow_html=True)

    rc,lc = st.columns([1,1.4])
    with rc:
        st.markdown('<div class="card"><div class="eyebrow">Score Radar</div>', unsafe_allow_html=True)
        if score:
            labels = ["Focus","Mission","Recovery","Switch"]
            vals   = [score.get("focus_score",0),score.get("mission_score",0),
                      score.get("recovery_score",0),score.get("switch_score",0)]
            fig = go.Figure(go.Scatterpolar(r=vals+[vals[0]],theta=labels+[labels[0]],
                fill="toself",fillcolor="rgba(34,211,238,.07)",
                line=dict(color="#22D3EE",width=2),marker=dict(color="#22D3EE",size=5)))
            fig.update_layout(
                polar=dict(bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(visible=True,range=[0,100],tickfont=dict(color="#334155",size=9),
                                    gridcolor="rgba(148,163,184,.08)",linecolor="rgba(148,163,184,.08)"),
                    angularaxis=dict(tickfont=dict(color="#64748B",size=12),
                                     gridcolor="rgba(148,163,184,.08)",linecolor="rgba(148,163,184,.08)")),
                paper_bgcolor="rgba(0,0,0,0)",font_color="white",
                height=240,margin=dict(l=30,r=30,t=20,b=20),showlegend=False)
            st.plotly_chart(fig,use_container_width=True)
        else: empty("No score data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with lc:
        ca,cr = st.columns(2)
        with ca:
            st.markdown('<div class="card"><div class="eyebrow">AI Coach</div>', unsafe_allow_html=True)
            advice = coach.get("advice",[]) if coach else []
            if advice:
                for item in advice:
                    st.markdown(f"""
                    <div class="coach-card">
                        <div class="coach-lbl">Observation</div><div class="coach-txt">{item.get('observation','')}</div>
                        <div class="coach-lbl">Impact</div><div class="coach-txt">{item.get('impact','')}</div>
                        <div class="coach-lbl">Suggestion</div><div class="coach-txt" style="margin-bottom:0">{item.get('suggestion','')}</div>
                    </div>""", unsafe_allow_html=True)
            else: empty("No coaching advice yet.")
            st.markdown("</div>", unsafe_allow_html=True)

        with cr:
            st.markdown('<div class="card"><div class="eyebrow">Recommendations for Tomorrow</div>', unsafe_allow_html=True)
            recs = report.get("recommendations",[]) if report else []
            if recs:
                for rec in recs:
                    st.markdown(f'<div class="rec-item"><div class="rec-arrow">→</div><div>{rec}</div></div>',
                                unsafe_allow_html=True)
            else: empty("No recommendations yet.")
            st.markdown("</div>", unsafe_allow_html=True)

# ── Router ────────────────────────────────────────────────────────────────────

if not st.session_state.authenticated:
    render_auth()
else:
    count = st_autorefresh(interval=30000, limit=None, key="ar")
    if count > 0:
        st.session_state.last_refresh = datetime.now()
    alive = api_alive()
    render_sidebar(alive)
    page = st.session_state.active_page
    if page == "Overview":      render_overview()
    elif page == "Deep Dive":   render_deep_dive()
    elif page == "Intelligence": render_intelligence()
    elif page == "Daily Report": render_daily_report()