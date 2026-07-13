import streamlit as st
import requests
from datetime import datetime


API_URL = "http://127.0.0.1:8000"


def api(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

    except Exception as e:
        st.error(f"API error: {e}")

    return {}



def history_page():

    st.markdown("""
    <div style="
        margin-bottom:30px;
    ">
        <div style="
            color:#22D3EE;
            font-size:11px;
            font-weight:800;
            letter-spacing:.15em;
            text-transform:uppercase;
        ">
            HISTORY
        </div>

        <h1 style="
            color:#F8FAFC;
            margin-top:8px;
        ">
            Your productivity journey.
        </h1>

        <p style="
            color:#94A3B8;
            font-size:15px;
        ">
            Long-term patterns, trends, and behavioral evolution.
        </p>

    </div>
    """, unsafe_allow_html=True)


    # -------------------------
    # Range selector
    # -------------------------

    days = st.selectbox(
        "Time range",
        [7,30,90,365],
        index=1
    )


    data = api(
        f"/history?days={days}"
    )


    if not data:
        st.warning(
            "No history available yet."
        )
        return



    summary = data.get(
        "summary",
        {}
    )


    # -------------------------
    # Top metrics
    # -------------------------

    c1,c2,c3,c4 = st.columns(4)


    metrics = [
        (
            "Tracked Days",
            summary.get(
                "tracked_days",
                0
            )
        ),

        (
            "Avg Score",
            summary.get(
                "average_score",
                0
            )
        ),

        (
            "Deep Work",
            f"{summary.get('total_deep_work_minutes',0)} min"
        ),

        (
            "Longest Streak",
            summary.get(
                "longest_streak",
                0
            )
        )
    ]


    for col,(title,value) in zip(
        [c1,c2,c3,c4],
        metrics
    ):

        with col:

            st.markdown(
            f"""
            <div class="stat-tile">

                <div class="stat-label">
                    {title}
                </div>

                <div class="stat-value">
                    {value}
                </div>

            </div>
            """,
            unsafe_allow_html=True
            )



    st.write("")


    # -------------------------
    # Score history chart
    # -------------------------

    st.markdown(
        '<div class="card"><div class="eyebrow">PRODUCTIVITY TREND</div>',
        unsafe_allow_html=True
    )


    history = data.get(
        "score_history",
        []
    )


    if history:

        scores = [
            x.get(
                "score",
                0
            )
            for x in history
        ]

        dates = [
            x.get(
                "date",
                ""
            )
            for x in history
        ]


        st.line_chart(
            {
                "Score": scores
            }
        )


    else:

        st.info(
            "Track more days to unlock trends."
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )



    # -------------------------
    # Deep work chart
    # -------------------------

    st.markdown(
        '<div class="card"><div class="eyebrow">DEEP WORK EVOLUTION</div>',
        unsafe_allow_html=True
    )


    deep = data.get(
        "deep_work_history",
        []
    )


    if deep:

        values = [
            x.get(
                "deep_work_minutes",
                0
            )
            for x in deep
        ]

        st.bar_chart(
            values
        )

    else:

        st.info(
            "No deep work history."
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )



    # -------------------------
    # Insight
    # -------------------------

    insight = data.get(
        "insight",
        ""
    )


    st.markdown(
    f"""
    <div class="card-cyan">

        <div class="eyebrow">
            AI HISTORICAL INSIGHT
        </div>


        <div style="
            color:#F8FAFC;
            font-size:16px;
            margin-top:15px;
        ">
            {insight}
        </div>

    </div>
    """,
    unsafe_allow_html=True
    )