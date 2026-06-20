import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

API_BASE_URL = "http://127.0.0.1:8000"


def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


st.set_page_config(
    page_title="Drift Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top right, #164E63 0%, #0F172A 35%, #020617 100%);
    color: white;
}

.block-container {
    padding-top: 2rem;
}

.card {
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
}

.small-card {
    background: rgba(30, 41, 59, 0.9);
    border-radius: 18px;
    padding: 18px;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

.title {
    font-size: 42px;
    font-weight: 900;
}

.subtitle {
    color: #94A3B8;
    font-size: 16px;
}

.metric-title {
    color: #94A3B8;
    font-size: 14px;
}

.metric-value {
    font-size: 32px;
    font-weight: 900;
}

.big-score {
    font-size: 64px;
    font-weight: 900;
    color: #22D3EE;
}

.coach-box {
    background: rgba(8, 47, 73, 0.9);
    border-left: 5px solid #22D3EE;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 14px;
}

.timeline-box {
    background: rgba(30, 41, 59, 0.85);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


score = get_api_data("/score")
missions = get_api_data("/missions")
timeline = get_api_data("/timeline")
deep_work = get_api_data("/deep-work")
coach = get_api_data("/coach")
report = get_api_data("/daily-report")


st.markdown('<div class="title">🧠 Drift Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Human Observability Platform for focus, intent, and behavioral intelligence</div>', unsafe_allow_html=True)
st.write("")


left, right = st.columns([2.2, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Productivity Overview")

    overall = score.get("overall_score", 0) if score else 0
    grade = score.get("grade", "N/A") if score else "N/A"

    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown(f'<div class="big-score">{overall}</div>', unsafe_allow_html=True)
        st.markdown(f"### Grade: `{grade}`")

    with c2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=overall,
            number={"font": {"color": "white"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "white"},
                "bar": {"color": "#22D3EE"},
                "bgcolor": "#1E293B",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#7F1D1D"},
                    {"range": [50, 75], "color": "#78350F"},
                    {"range": [75, 100], "color": "#064E3B"},
                ],
            }
        ))
        fig.update_layout(
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    if score:
        st.info(score.get("summary", ""))

    st.markdown("</div>", unsafe_allow_html=True)


with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Today")

    top_mission = report.get("top_mission", "N/A") if report else "N/A"
    deep_minutes = deep_work.get("total_deep_work_minutes", 0) if deep_work else 0
    context_switches = report.get("context_switches", 0) if report else 0
    sessions = deep_work.get("count", 0) if deep_work else 0

    st.markdown(f"""
    <div class="small-card">
        <div class="metric-title">Top Mission</div>
        <div class="metric-value">{top_mission}</div>
    </div>
    <br>
    <div class="small-card">
        <div class="metric-title">Deep Work</div>
        <div class="metric-value">{deep_minutes} min</div>
    </div>
    <br>
    <div class="small-card">
        <div class="metric-title">Context Switches</div>
        <div class="metric-value">{context_switches}</div>
    </div>
    <br>
    <div class="small-card">
        <div class="metric-title">Deep Work Sessions</div>
        <div class="metric-value">{sessions}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


st.write("")

col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎯 Mission Breakdown")

    mission_items = missions.get("missions", []) if missions else []

    if mission_items:
        mission_df = pd.DataFrame(mission_items)

        fig = px.pie(
            mission_df,
            names="mission",
            values="time_seconds",
            hole=0.55
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label"
        )

        fig.update_layout(
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            showlegend=True,
            legend=dict(font=dict(color="white"))
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No mission data yet.")

    st.markdown("</div>", unsafe_allow_html=True)


with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🤖 AI Coach")

    advice_items = coach.get("advice", []) if coach else []

    if advice_items:
        for item in advice_items[:3]:
            st.markdown(f"""
            <div class="coach-box">
                <b>Observation:</b> {item.get("observation")}<br><br>
                <b>Impact:</b> {item.get("impact")}<br><br>
                <b>Suggestion:</b> {item.get("suggestion")}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("No coach advice yet.")

    st.markdown("</div>", unsafe_allow_html=True)


st.write("")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🕒 Cognitive Timeline")

timeline_items = timeline.get("timeline", []) if timeline else []

if timeline_items:
    for block in timeline_items:
        mission = block.get("mission", "Unknown")
        duration = block.get("duration_seconds", 0)
        minutes = round(duration / 60, 2)
        goals = ", ".join(block.get("goals", {}).keys())
        apps = ", ".join(block.get("apps", {}).keys())

        st.markdown(f"""
        <div class="timeline-box">
            <b>{mission}</b> · {minutes} min<br>
            <span style="color:#94A3B8;">Goals: {goals}</span><br>
            <span style="color:#94A3B8;">Apps: {apps}</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.write("No timeline data yet.")

st.markdown("</div>", unsafe_allow_html=True)


st.write("")

st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📌 Daily Report")

if report:
    st.write(report.get("executive_summary", "No report yet."))

    recs = report.get("recommendations", [])
    if recs:
        st.markdown("#### Recommendations")
        for rec in recs:
            st.write(f"• {rec}")
else:
    st.write("No daily report yet.")

st.markdown("</div>", unsafe_allow_html=True)