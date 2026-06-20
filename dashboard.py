import requests
import pandas as pd
import streamlit as st
import plotly.express as px

API_BASE_URL = "http://127.0.0.1:8000"


def get_api_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as error:
        st.error(f"Could not fetch {endpoint}: {error}")
        return None


st.set_page_config(
    page_title="Drift Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Drift")
st.caption("Human Observability Platform")


score_data = get_api_data("/score")
missions_data = get_api_data("/missions")
timeline_data = get_api_data("/timeline")
deep_work_data = get_api_data("/deep-work")
coach_data = get_api_data("/coach")
daily_report = get_api_data("/daily-report")


if score_data:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Productivity Score", score_data.get("overall_score", 0))
    col2.metric("Grade", score_data.get("grade", "N/A"))
    col3.metric("Focus Score", score_data.get("focus_score", 0))
    col4.metric("Switch Score", score_data.get("switch_score", 0))

    st.info(score_data.get("summary", ""))


st.divider()


if daily_report:
    st.subheader("📌 Daily Report")
    st.write(daily_report.get("executive_summary", "No summary available."))

    recommendations = daily_report.get("recommendations", [])
    if recommendations:
        st.write("### Recommendations")
        for recommendation in recommendations:
            st.write(f"- {recommendation}")


st.divider()


if deep_work_data:
    st.subheader("🔥 Deep Work")

    col1, col2, col3 = st.columns(3)
    col1.metric("Deep Work Minutes", deep_work_data.get("total_deep_work_minutes", 0))
    col2.metric("Longest Session", deep_work_data.get("longest_session_minutes", 0))
    col3.metric("Deep Work Sessions", deep_work_data.get("count", 0))

    st.write(deep_work_data.get("insight", ""))


st.divider()


if missions_data:
    st.subheader("🎯 Mission Breakdown")

    missions = missions_data.get("missions", [])

    if missions:
        mission_df = pd.DataFrame(missions)

        fig = px.pie(
            mission_df,
            names="mission",
            values="time_seconds",
            title="Time by Mission"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            mission_df[["mission", "time_seconds", "percentage"]],
            use_container_width=True
        )
    else:
        st.write("No mission data available.")


st.divider()


if timeline_data:
    st.subheader("🕒 Cognitive Timeline")

    timeline = timeline_data.get("timeline", [])

    if timeline:
        timeline_df = pd.DataFrame(timeline)

        st.dataframe(timeline_df, use_container_width=True)

        fig = px.bar(
            timeline_df,
            x="mission",
            y="duration_seconds",
            title="Timeline Blocks by Mission"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No timeline data available.")


st.divider()


if coach_data:
    st.subheader("🤖 AI Coach")

    advice_items = coach_data.get("advice", [])

    if advice_items:
        for item in advice_items:
            st.markdown(f"**Observation:** {item.get('observation')}")
            st.markdown(f"**Impact:** {item.get('impact')}")
            st.markdown(f"**Suggestion:** {item.get('suggestion')}")
            st.markdown("---")
    else:
        st.write("No coach advice available.")